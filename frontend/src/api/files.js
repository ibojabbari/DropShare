import { apiRequest } from './client'
import { fetchCsrfToken } from './auth'

const filesUrl = '/api/files/'

export function getFiles() {
  return apiRequest(filesUrl)
}

export async function uploadFiles(files) {
  const csrfToken = await fetchCsrfToken()
  const body = new FormData()
  files.forEach((file) => body.append('files', file))

  return apiRequest(filesUrl, {
    method: 'POST',
    headers: { 'X-CSRFToken': csrfToken },
    body,
  })
}

export async function deleteFile(fileId) {
  const csrfToken = await fetchCsrfToken()

  return apiRequest(`${filesUrl}${fileId}/`, {
    method: 'DELETE',
    headers: { 'X-CSRFToken': csrfToken },
  })
}

export async function createDocument(title) {
  const csrfToken = await fetchCsrfToken()
  return apiRequest(`${filesUrl}documents/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
    body: JSON.stringify({ title }),
  })
}

export function getDocument(fileId) {
  return apiRequest(`${filesUrl}${fileId}/document/`)
}

export async function saveDocument(fileId, content) {
  const csrfToken = await fetchCsrfToken()
  return apiRequest(`${filesUrl}${fileId}/document/`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
    body: JSON.stringify({ content }),
  })
}

