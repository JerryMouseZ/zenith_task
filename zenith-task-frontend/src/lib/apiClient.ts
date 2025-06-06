import { Token, APIError, User, UserCreate } from '@/types/api'; // Added User, UserCreate

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api'; // Ensure this env var is set for external API

// Store token in a simple way for this example.
// In a real app, consider more secure storage or HttpOnly cookies.
let token: string | null = null;

if (typeof window !== 'undefined') {
  token = localStorage.getItem('authToken');
}

export function setAuthToken(newToken: string | null) {
  token = newToken;
  if (newToken) {
    localStorage.setItem('authToken', newToken);
  } else {
    localStorage.removeItem('authToken');
  }
}

export function getAuthToken(): string | null {
  // Ensure token is read from localStorage if available, especially upon initial load in a new context
  if (typeof window !== 'undefined' && !token) {
    token = localStorage.getItem('authToken');
  }
  return token;
}

interface RequestOptions extends RequestInit {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  body?: any; // Allow any body type for now, will be stringified if object
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const headers = new Headers(options.headers || {});
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) { // Don't set Content-Type if it's FormData
    headers.set('Content-Type', 'application/json');
  }


  const currentToken = getAuthToken();
  if (currentToken) {
    headers.set('Authorization', `Bearer ${currentToken}`);
  }

  const config: RequestInit = {
    ...options,
    headers,
  };

  if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
    config.body = JSON.stringify(options.body);
  } else {
    config.body = options.body; // Pass FormData as is
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

  if (!response.ok) {
    let errorData: APIError | { detail: string };
    try {
      errorData = await response.json();
    } catch (e) {
      errorData = { detail: response.statusText || 'Unknown API error' };
    }
    console.error('API Error:', errorData);
    // Throw an error object that includes the status and parsed error data
    const error = new Error(typeof errorData.detail === 'string' ? errorData.detail : 'API request failed');
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (error as any).response = response;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (error as any).data = errorData;
    throw error;
  }

  if (response.status === 204) { // No Content
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export const apiClient = {
  get: <T>(endpoint: string, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: 'GET' }),
  post: <T, U>(endpoint: string, body: U, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: 'POST', body }),
  put: <T, U>(endpoint: string, body: U, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: 'PUT', body }),
  delete: <T>(endpoint: string, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: 'DELETE' }),
  patch: <T, U>(endpoint: string, body: U, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: 'PATCH', body }),
};

// Example usage for login (will be in LoginForm.tsx)
/*
async function login(credentials: OAuth2PasswordRequestForm) {
  // FastAPI's OAuth2PasswordRequestForm expects form data, not JSON.
  // Our current apiClient sends JSON. This needs adjustment for this specific endpoint.
  // For now, we'll assume the backend /api/auth/token can accept JSON with username/password,
  // or this client will need a special method for form data.

  // Let's adjust for form data for the /token endpoint
  const formData = new URLSearchParams();
  formData.append('username', credentials.username);
  formData.append('password', credentials.password);
  // Potentially scope, client_id, client_secret if using full OAuth2 flow, but api.md implies simpler user/pass

  const response = await fetch(`${API_BASE_URL}/auth/token`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Login failed' }));
    throw new Error(errorData.detail || 'Login failed');
  }

  const data: Token = await response.json();
  setAuthToken(data.access_token);
  return data;
}
*/
// The above login example is illustrative. The actual call will be in the form component.
// The apiClient will be used for JSON endpoints. The /auth/token endpoint is special.

export async function loginWithJson(credentials: {username: string, password: string}): Promise<Token> {
    // This assumes /api/auth/token will be adapted or proxied to handle JSON
    // as per frontend.md section 4.1.1. (username (email) and password)
    // If it strictly requires form-data, the component calling this will need to use a direct fetch or a modified apiClient method.
    // For now, proceeding with JSON as per frontend.md's description of POST /api/auth/token.
    const data = await apiClient.post<Token, {username: string, password: string}>('/auth/token', credentials);
    if (data.access_token) {
        setAuthToken(data.access_token);
    }
    return data;
}

export async function registerUser(userData: UserCreate): Promise<User> {
    return apiClient.post<User, UserCreate>('/auth/register', userData);
}


export function logout() {
  setAuthToken(null);
  // Optionally, call a backend /logout endpoint if it exists and is needed for session invalidation.
  // await apiClient.post('/auth/logout', {});
}
