export const getApiBaseUrl = () => {
  // 1. Check if VITE_API_BASE_URL is set (e.g. in development)
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL
  }

  // 2. Fallback: Construct based on current window location
  // This allows accessing from 192.168.x.x or localhost dynamically
  const { protocol, hostname } = window.location
  return `${protocol}//${hostname}:8000`
}

export const BASE_API_URL = getApiBaseUrl()
