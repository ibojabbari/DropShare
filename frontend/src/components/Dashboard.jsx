import { useEffect, useState } from 'react'
import * as filesApi from '../api/files'
import * as connectionsApi from '../api/connections'
import * as permissionsApi from '../api/permissions'

const MAX_BATCH_UPLOAD_SIZE = 100 * 1024 * 1024

export function Dashboard({ user, onLogout }) {
  const [files, setFiles] = useState([])
  const [connections, setConnections] = useState([])
  const [selectedFile, setSelectedFile] = useState(null)
  const [document, setDocument] = useState(null)
  const [shares, setShares] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function loadWorkspace() {
      try {
        const [fileData, connectionData] = await Promise.all([filesApi.getFiles(), connectionsApi.getConnections()])
        setFiles(fileData.files)
        setConnections(connectionData.connections)
      } catch (loadError) {
        setError(loadError.message)
      } finally {
        setIsLoading(false)
      }
    }

    loadWorkspace()
  }, [])

  async function chooseFile(file) {
    setSelectedFile(file)
    setDocument(null)
    setShares([])
    setError(null)

    try {
      if (file.is_document) {
        const documentData = await filesApi.getDocument(file.id)
        setDocument(documentData)
      }
      if (file.access.role === 'owner') {
        const shareData = await permissionsApi.getShares(file.id)
        setShares(shareData.shares)
      }
    } catch (selectionError) {
      setError(selectionError.message)
    }
  }

  async function upload(event) {
    const input = event.target
    const selectedFiles = Array.from(input.files)
    const totalSize = selectedFiles.reduce((total, file) => total + file.size, 0)
    if (totalSize > MAX_BATCH_UPLOAD_SIZE) {
      setError('Choose files totalling 100 MB or less.')
      return
    }

    try {
      const payload = await filesApi.uploadFiles(selectedFiles)
      setFiles((currentFiles) => [...payload.files, ...currentFiles])
    } catch (uploadError) {
      setError(uploadError.message)
    } finally {
      input.value = ''
    }
  }

  async function createDocument() {
    const title = window.prompt('Document name')
    if (!title) return

    try {
      const payload = await filesApi.createDocument(title)
      setFiles((currentFiles) => [payload.file, ...currentFiles])
      setSelectedFile(payload.file)
      setDocument(payload.document)
      setShares([])
    } catch (creationError) {
      setError(creationError.message)
    }
  }

  async function saveDocument() {
    if (!selectedFile || !document) return
    setIsSaving(true)
    try {
      const savedDocument = await filesApi.saveDocument(selectedFile.id, document.content)
      setDocument(savedDocument)
    } catch (saveError) {
      setError(saveError.message)
    } finally {
      setIsSaving(false)
    }
  }

  async function addConnection(event) {
    event.preventDefault()
    const form = new FormData(event.target)
    try {
      const connection = await connectionsApi.addConnection(form.get('username'))
      setConnections((current) => [...current, connection])
      event.target.reset()
    } catch (connectionError) {
      setError(connectionError.message)
    }
  }

  async function acceptConnection(connectionId) {
    try {
      const updated = await connectionsApi.acceptConnection(connectionId)
      setConnections((current) => current.map((item) => item.id === updated.id ? updated : item))
    } catch (acceptError) {
      setError(acceptError.message)
    }
  }

  async function addShare(event) {
    event.preventDefault()
    if (!selectedFile) return
    const form = new FormData(event.target)
    const values = {
      username: form.get('username'),
      permission: form.get('permission'),
    }
    try {
      const share = await permissionsApi.shareFile(selectedFile.id, values)
      setShares((current) => [...current.filter((item) => item.username !== share.username), share])
      event.target.reset()
    } catch (shareError) {
      setError(shareError.message)
    }
  }

  async function revokeShare(shareId) {
    try {
      await permissionsApi.revokeShare(selectedFile.id, shareId)
      setShares((current) => current.filter((share) => share.id !== shareId))
    } catch (revokeError) {
      setError(revokeError.message)
    }
  }

  async function removeFile() {
    if (!selectedFile) return

    const confirmed = window.confirm(`Delete ${selectedFile.original_name}? This cannot be undone.`)
    if (!confirmed) return

    try {
      await filesApi.deleteFile(selectedFile.id)
      setFiles((currentFiles) => currentFiles.filter((file) => file.id !== selectedFile.id))
      setSelectedFile(null)
      setDocument(null)
      setShares([])
    } catch (deleteError) {
      setError(deleteError.message)
    }
  }

  function applyFormat(command) {
    const editor = window.document.getElementById('document-editor')
    if (!editor || selectedFile?.access.permission !== 'edit') return

    const start = editor.selectionStart
    const end = editor.selectionEnd
    const selectedText = document.content.slice(start, end) || 'text'
    const markers = command === 'bold' ? ['**', '**'] : command === 'italic' ? ['*', '*'] : ['__', '__']
    const nextContent = `${document.content.slice(0, start)}${markers[0]}${selectedText}${markers[1]}${document.content.slice(end)}`
    setDocument({ ...document, content: nextContent })
  }

  const acceptedConnections = connections.filter((connection) => connection.status === 'accepted')

  return (
    <>
      <header className="topbar workspace-topbar">
        <a className="brand" href="/"><span>Drop</span>Share</a>
        <div className="account-menu">
          <span>{user.username}</span>
          <button className="text-button" type="button" onClick={onLogout}>Sign out</button>
        </div>
      </header>

      <main className="document-workspace">
        <aside className="workspace-sidebar">
          <button className="primary-button" type="button" onClick={createDocument}>New document</button>
          <label className="upload-label" htmlFor="file-upload">Upload files</label>
          <input id="file-upload" className="file-input" type="file" multiple onChange={upload} />

          <h2>Files</h2>
          {isLoading && <p className="field-hint">Loading workspace…</p>}
          <ul className="workspace-file-list">
            {files.map((file) => (
              <li key={file.id}>
                <button
                  className={selectedFile?.id === file.id ? 'file-select selected' : 'file-select'}
                  type="button"
                  onClick={() => chooseFile(file)}
                >
                  {file.preview_url ? <img className="file-thumbnail" src={file.preview_url} alt="" /> : <span>{file.is_document ? 'DOC' : 'FILE'}</span>}
                  <strong>{file.original_name}</strong>
                  <small>{file.access.role === 'owner' ? 'Owned by you' : `Shared by ${file.owner}`}</small>
                </button>
              </li>
            ))}
          </ul>

          <h2>Connections</h2>
          <form className="connection-form" onSubmit={addConnection}>
            <input name="username" placeholder="Username" required />
            <button type="submit">Connect</button>
          </form>
          <ul className="connection-list">
            {connections.map((connection) => (
              <li key={connection.id}>
                <span>{connection.username}</span>
                {connection.status === 'pending' && connection.direction === 'received' ? (
                  <button type="button" onClick={() => acceptConnection(connection.id)}>Accept</button>
                ) : (
                  <small>{connection.status}</small>
                )}
              </li>
            ))}
          </ul>
        </aside>

        <section className="editor-area">
          {error && <p className="form-message error">{error}</p>}
          {!selectedFile && <div className="empty-editor"><h1>Your document workspace</h1><p>Create a document or select a file to get started.</p></div>}

          {selectedFile && !selectedFile.is_document && (
            <div className="empty-editor">
              {selectedFile.preview_url && <img className="image-preview" src={selectedFile.preview_url} alt={selectedFile.original_name} />}
              <h1>{selectedFile.original_name}</h1>
              <p>This file can be downloaded but is not an editable text document.</p>
              <a className="primary-button" href={selectedFile.download_url}>Download file</a>
              {selectedFile.access.role === 'owner' && <button className="delete-button" type="button" onClick={removeFile}>Delete file</button>}
            </div>
          )}

          {selectedFile && selectedFile.is_document && document && (
            <>
              <div className="editor-header">
                <div><h1>{selectedFile.original_name}</h1><p>{selectedFile.access.role === 'owner' ? 'Private document' : `${selectedFile.access.permission} access from ${selectedFile.owner}`}</p></div>
                <div className="editor-actions">
                  <a className="text-button" href={selectedFile.download_url}>Download</a>
                  {selectedFile.access.role === 'owner' && <button className="delete-button" type="button" onClick={removeFile}>Delete</button>}
                </div>
              </div>
              {selectedFile.access.permission === 'edit' && (
                <div className="formatting-toolbar" aria-label="Text formatting">
                  <button type="button" onClick={() => applyFormat('bold')}><strong>B</strong></button>
                  <button type="button" onClick={() => applyFormat('italic')}><em>I</em></button>
                  <button type="button" onClick={() => applyFormat('underline')}><u>U</u></button>
                </div>
              )}
              <textarea
                id="document-editor"
                className={selectedFile.access.permission === 'edit' ? 'document-editor' : 'document-editor read-only'}
                value={document.content}
                onChange={(event) => setDocument({ ...document, content: event.target.value })}
                readOnly={selectedFile.access.permission !== 'edit'}
                aria-label="Document content"
              />
              {selectedFile.access.permission === 'edit' && <button className="primary-button save-button" type="button" onClick={saveDocument} disabled={isSaving}>{isSaving ? 'Saving…' : 'Save changes'}</button>}
            </>
          )}
        </section>

        {selectedFile?.access.role === 'owner' && (
          <aside className="sharing-panel">
            <h2>Share access</h2>
            <p>Only accepted connections can receive access.</p>
            <form onSubmit={addShare}>
              <label htmlFor="share-user">Connected user</label>
              <select id="share-user" name="username" required defaultValue="">
                <option value="" disabled>Select a user</option>
                {acceptedConnections.map((connection) => <option key={connection.id} value={connection.username}>{connection.username}</option>)}
              </select>
              <label htmlFor="share-permission">Permission</label>
              <select id="share-permission" name="permission" defaultValue="read">
                <option value="read">Read</option>
                {selectedFile.is_document && <option value="edit">Edit</option>}
              </select>
              <button className="primary-button" type="submit">Share file</button>
            </form>
            <ul className="share-list">
              {shares.map((share) => <li key={share.id}><span><strong>{share.username}</strong><small>{share.permission} · download</small></span><button type="button" onClick={() => revokeShare(share.id)}>Revoke</button></li>)}
            </ul>
          </aside>
        )}
      </main>
    </>
  )
}
