import { apiRequest } from './client'

const authUrl = (path) => `/api/auth/${path}/`

export async function fetchCsrfToken() {
  const payload = await apiRequest(authUrl('csrf'))

  if (!payload?.csrfToken) {
    throw new Error('Unable to start a secure session. Please refresh and try again.')
  }

  return payload.csrfToken
}

export async function register(credentials) {
  const csrfToken = await fetchCsrfToken()

  return apiRequest(authUrl('register'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken,
    },
    body: JSON.stringify(credentials),
  })
}

export async function login(credentials) {
  const csrfToken = await fetchCsrfToken()

  return apiRequest(authUrl('login'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken,
    },
    body: JSON.stringify(credentials),
  })
}

export function getCurrentUser() {
  return apiRequest(authUrl('me'))
}

export async function logout(csrfToken) {
  const token = csrfToken || await fetchCsrfToken()

  return apiRequest(authUrl('logout'), {
    method: 'POST',
    headers: { 'X-CSRFToken': token },
  })
}
