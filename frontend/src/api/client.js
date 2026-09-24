export class ApiError extends Error {
  constructor(message, status, payload) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.payload = payload
  }
}

function getErrorMessage(payload, fallback) {
  if (!payload || typeof payload !== 'object') return fallback
  if (typeof payload.detail === 'string') return payload.detail

  const firstError = Object.values(payload)
    .flat()
    .find((value) => typeof value === 'string')

  return firstError || fallback
}

// All browser-to-server communication uses this one function.
export async function apiRequest(path, options = {}) {
  const response = await fetch(path, {
    credentials: 'include',
    ...options,
  })

  const payload = await response.json().catch(() => null)

  if (!response.ok) {
    throw new ApiError(
      getErrorMessage(payload, 'Something went wrong. Please try again.'),
      response.status,
      payload,
    )
  }

  return payload
}
