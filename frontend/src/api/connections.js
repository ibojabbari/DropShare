import { apiRequest } from './client'
import { fetchCsrfToken } from './auth'

const connectionsUrl = '/api/connections/'

export function getConnections() {
  return apiRequest(connectionsUrl)
}

export async function addConnection(username) {
  const csrfToken = await fetchCsrfToken()
  return apiRequest(connectionsUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
    body: JSON.stringify({ username }),
  })
}

export async function acceptConnection(connectionId) {
  const csrfToken = await fetchCsrfToken()
  return apiRequest(`${connectionsUrl}${connectionId}/accept/`, {
    method: 'POST',
    headers: { 'X-CSRFToken': csrfToken },
  })
}
