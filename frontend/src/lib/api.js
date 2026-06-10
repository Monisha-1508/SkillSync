const TOKEN_STORAGE_KEY = "skillsync.token";

let _token = null;

function setAuthToken(token) {
  _token = token;
  if (typeof window === "undefined") return;
  if (token) window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
  else window.localStorage.removeItem(TOKEN_STORAGE_KEY);
}

function loadStoredToken() {
  if (typeof window === "undefined") return null;
  const stored = window.localStorage.getItem(TOKEN_STORAGE_KEY);
  _token = stored;
  return stored;
}

class ApiError extends Error {
  constructor(message, status, detail) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

async function request(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (_token) headers.Authorization = `Bearer ${_token}`;

  const response = await fetch(`/api${path}`, {
    headers,
    ...options,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const parsed = await response.json();
      detail = parsed.detail || detail;
    } catch {
    }
    throw new ApiError(`${response.status}: ${detail}`, response.status, detail);
  }

  if (response.status === 204) return null;
  return response.json();
}

export const api = {
  get: (path) => request(path),
  post: (path, body) => request(path, { method: "POST", body }),
  patch: (path, body) => request(path, { method: "PATCH", body }),
  streamUrl: (path) => `/api${path}`,
};

export { ApiError, setAuthToken, loadStoredToken };
