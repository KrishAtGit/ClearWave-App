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
    const body = await response.json().catch(() => null)
    const detail = typeof body?.detail === 'string' ? body.detail : null
    throw new ApiError(
      response.status,
      detail ?? `${config.method ?? 'GET'} ${path} failed`
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

// patch helper - sends a json body with patch: "change part of an existing thing"
function patch<T>(path: string, body: unknown): Promise<T>{
  return request<T>(path, {
    method: 'PATCH',
    headers: { 'Content-Type' : 'application/json' },
    body: JSON.stringify(body),
  })
}

function postForm<T>(path: string, form: FormData): Promise<T> {
  // no Content-Type header: the browser sets it, including the boundary that separates the parts
  return request<T>(path, { method: 'POST', body: form })
}

// the signed-in user, as returned by /api/auth/me
export interface User {
  id: string
  email: string
}

export type ClaimStatus = 'uploaded' | 'matching' | 'matched' | 'failed'

export interface Claim{
  id: string
  title: string
  original_filename: string
  size_bytes: number
  status: ClaimStatus
  created_at: string
}

export interface Match {
  id: string,
  title: string,
  artists: string[]
  album: string | null,
  label: string | null
  release_date: string | null
  isrc: string | null
  score: number
  offset_seconds: number | null
  spotify_track_id: string | null
  youtube_video_id: string | null
  composers: string[]
  streams: number | null
  share_percent: number | null
  estimated_value: number | null
}

export interface ClaimDetail extends Claim {
  audio_url: string
  matches: Match[]
  payout_per_stream: number
  payout_source: string
}

// creating the api object
export const api = {
  health: () => request<Health>('/api/health'),
  me: () => request<User>('/api/auth/me'),
  requestLink: (email: string) => post<{ message: string }>('/api/auth/request-link', { email }),
  logout: () => post<void>('/api/auth/logout'),

  listClaims: () => request<Claim[]>('/api/claims'),
  getClaim: (id: string) => request<ClaimDetail>(`/api/claims/${id}`),
  uploadClaim: (title: string, file: File) => {
    const form = new FormData()
    form.append('title', title)
    form.append('file', file)
    return postForm<Claim>('/api/claims', form)
  },
  deleteClaim: (id: string) => request<void>(`/api/claims/${id}`, {
    method: 'DELETE'
  }),
  updateEstimate: (claimId: string, matchId: string, streams: number, sharePercent: number) =>
    patch<Match>(`/api/claims/${claimId}/matches/${matchId}`, {
      streams,
      share_percent: sharePercent,
    }),
}
