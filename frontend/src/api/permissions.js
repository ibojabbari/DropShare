import { apiRequest } from './client'
import { fetchCsrfToken } from './auth'

const permissionsUrl = '/api/permissions/'

export function getShares(fileId) {
  return apiRequest(`${permissionsUrl}files/${fileId}/shares/`)
}

export async function shareFile(fileId, values) {
  const csrfToken = await fetchCsrfToken()
  return apiRequest(`${permissionsUrl}files/${fileId}/shares/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
    body: JSON.stringify(values),
  })
}

export async function revokeShare(fileId, shareId) {
  const csrfToken = await fetchCsrfToken()
  return apiRequest(`${permissionsUrl}files/${fileId}/shares/${shareId}/`, {
    method: 'DELETE',
    headers: { 'X-CSRFToken': csrfToken },
  })
}
