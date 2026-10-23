async function request(path, options = {}) {
  let response
  try {
    response = await fetch(path, {
      ...options,
      headers: { 'Content-Type': 'application/json', ...options.headers },
    })
  } catch {
    throw new Error('Could not reach CelebrAI. Check that the Flask server is running.')
  }

  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    const error = new Error(body.error || 'The request could not be completed.')
    error.details = body.details || {}
    throw error
  }
  return body
}

export const getEvents = () => request('/api/events')
export const createEvent = (event) => request('/api/events', {
  method: 'POST',
  body: JSON.stringify(event),
})
export const setTaskCompletion = (eventId, taskId, completed) => request(
  `/api/events/${eventId}/tasks/${taskId}`,
  { method: 'PATCH', body: JSON.stringify({ completed }) },
)
