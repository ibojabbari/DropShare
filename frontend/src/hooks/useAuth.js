import { useEffect, useState } from 'react'
import { ApiError } from '../api/client'
import * as authApi from '../api/auth'

export function useAuth() {
  const [user, setUser] = useState(null)
  const [csrfToken, setCsrfToken] = useState(null)
  const [isRestoring, setIsRestoring] = useState(true)

  useEffect(() => {
    let isMounted = true

    async function restoreSession() {
      try {
        const payload = await authApi.getCurrentUser()
        if (isMounted) setUser(payload.user)
      } catch (error) {
        // A missing session is normal; show the sign-in screen instead.
        if (!(error instanceof ApiError && [401, 403].includes(error.status))) {
          console.error('Unable to restore the current session.', error)
        }
      } finally {
        if (isMounted) setIsRestoring(false)
      }
    }

    restoreSession()
    return () => { isMounted = false }
  }, [])

  async function register(credentials) {
    return authApi.register(credentials)
  }

  async function login(credentials) {
    const payload = await authApi.login(credentials)
    setUser(payload.user)
    setCsrfToken(payload.csrfToken)
  }

  async function logout() {
    await authApi.logout(csrfToken)
    setUser(null)
    setCsrfToken(null)
  }

  return {
    user,
    isRestoring,
    register,
    login,
    logout,
  }
}
