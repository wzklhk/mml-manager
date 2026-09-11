import axios from "axios";

const baseURL = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

const apiClient = axios.create({ baseURL });

export function apiUrl(path) {
  return `${baseURL}${path.startsWith("/") ? path : `/${path}`}`;
}

export default apiClient;
