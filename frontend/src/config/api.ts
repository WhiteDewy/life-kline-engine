import axios from "axios";

const DEFAULT_API_BASE_URL = "/api";
const rawApiBaseUrl =
  import.meta.env.VITE_API_BASE_URL?.trim() || DEFAULT_API_BASE_URL;

export const API_BASE_URL = rawApiBaseUrl.endsWith("/")
  ? rawApiBaseUrl.slice(0, -1)
  : rawApiBaseUrl;

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
});
