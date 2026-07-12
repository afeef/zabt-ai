// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (C) 2025-2026 Afeef Janjua
import axios, { AxiosInstance, AxiosRequestConfig } from "axios";

export interface ApiClientConfig {
  /** Base URL for backend API (e.g., https://api.zabt.ai/api/v1) */
  baseURL: string;
  /** Returns the current auth token, or null if unauthenticated */
  getAuthToken: () => Promise<string | null>;
  /** Called when the backend returns 401. Platform-specific logout + redirect. */
  onUnauthorized: () => Promise<void> | void;
  /** Additional axios options */
  axiosConfig?: AxiosRequestConfig;
}

export function createApiClient(config: ApiClientConfig): AxiosInstance {
  const client = axios.create({
    baseURL: config.baseURL,
    headers: { "Content-Type": "application/json" },
    ...config.axiosConfig,
  });

  client.interceptors.request.use(async (cfg) => {
    const token = await config.getAuthToken();
    if (token) {
      cfg.headers.Authorization = `Bearer ${token}`;
    }
    return cfg;
  });

  client.interceptors.response.use(
    (response) => response,
    async (error) => {
      if (error.response?.status === 401) {
        await config.onUnauthorized();
      }
      return Promise.reject(error);
    }
  );

  return client;
}
