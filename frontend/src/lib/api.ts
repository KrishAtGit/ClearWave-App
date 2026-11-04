// frontend's place for talking to the backend
const API_URL = import.meta.env.VITE_API_URL ?? ''

// health interface, this defines the expected structure of an object
export interface Health {
  status: 'ok'
  database: boolean
}

// custom apierror class, used to create custom api related failures
export class ApiError extends Error {
  readonly status: number

// eg: error.status = 401 --> constructor runs whenever a new apierror is created
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

// request function 
// first argument -> api endpoint
// last agument -> contains optional fetch config (={} means defaulting to empty object)
async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
    // creates a new config object
    const config: RequestInit = {
    // spread syntax, copies every property of the init object into a new object being built - config
    ...init,
    // tells the browser to include credentials, such as cookies with the request (including cross-origin)
    credentials: 'include',
  }

  // sending the http request using fetch
  const response = await fetch(`${API_URL}${path}`, config)

  // if response is unsuccessful
  if (!response.ok) {
    throw new ApiError(
      response.status,
      `${config.method ?? 'GET'} ${path} failed`
    )
  }

  // 204 No Content -> logout replies with 204 no body as .json would crash
  if (response.status === 204){
    return undefined as T
  }

  // returning the responses
  return response.json() as Promise<T>
}

// sends a json body with POST request
function post<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
}

// the signed-in user, as returned by /api/auth/me
export interface User {
  id: string
  email: string
}

// creating the api object
export const api = {
  health: () => request<Health>('/api/health'),
  me: () => request<User>('/api/auth/me'),
  requestLink: (email: string) => post<{ message: string }>('/api/auth/request-link', { email }),
  logout: () => post<void>('/api/auth/logout'),
}
