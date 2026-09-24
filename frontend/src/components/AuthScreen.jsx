import { useState } from 'react'

const emptyForm = {
  username: '',
  password: '',
}

export function AuthScreen({ onLogin, onRegister }) {
  const [mode, setMode] = useState('login')
  const [form, setForm] = useState(emptyForm)
  const [feedback, setFeedback] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const isLogin = mode === 'login'

  function changeMode() {
    setMode(isLogin ? 'register' : 'login')
    setForm(emptyForm)
    setFeedback(null)
  }

  function updateField(event) {
    const { name, value } = event.target
    setForm((current) => ({ ...current, [name]: value }))
  }

  async function submitAuth(event) {
    event.preventDefault()
    setIsSubmitting(true)
    setFeedback(null)

    try {
      if (isLogin) {
        await onLogin(form)
        return
      }

      await onRegister(form)
      setMode('login')
      setForm({ username: form.username, password: '' })
      setFeedback({ type: 'success', text: 'Account created. You can now sign in.' })
    } catch (error) {
      setFeedback({ type: 'error', text: error.message })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <>
      <header className="topbar">
        <a className="brand" href="/">DropShare</a>
      </header>

      <main className="auth-card">
        <h1>{isLogin ? 'Welcome back' : 'Create your workspace'}</h1>
        <p className="card-subtitle">
          {isLogin ? 'Sign in to manage your files.' : 'Create a DropShare account to get started.'}
        </p>

        <form onSubmit={submitAuth}>
          <label htmlFor="username">Username</label>
          <input
            id="username"
            name="username"
            type="text"
            value={form.username}
            onChange={updateField}
            autoComplete="username"
            maxLength={150}
            disabled={isSubmitting}
            required
            autoFocus
          />

          <label htmlFor="password">Password</label>
          <input
            id="password"
            name="password"
            type="password"
            value={form.password}
            onChange={updateField}
            autoComplete={isLogin ? 'current-password' : 'new-password'}
            disabled={isSubmitting}
            required
          />

          {!isLogin && (
            <p className="field-hint">Use a long, unique password you do not reuse elsewhere.</p>
          )}

          {feedback && (
            <p className={`form-message ${feedback.type}`} role="status">
              {feedback.text}
            </p>
          )}

          <button className="primary-button" type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Please wait…' : isLogin ? 'Sign in' : 'Create account'}
          </button>
        </form>

        <p className="switch-copy">
          {isLogin ? 'New to DropShare? ' : 'Already have an account? '}
          <button
            className="text-button"
            type="button"
            onClick={changeMode}
            disabled={isSubmitting}
          >
            {isLogin ? 'Create an account' : 'Sign in'}
          </button>
        </p>
      </main>
    </>
  )
}
