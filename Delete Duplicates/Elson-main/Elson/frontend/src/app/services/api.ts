import axios, { AxiosInstance, AxiosError, AxiosRequestConfig } from 'axios';

import config from '../core/config';

// Create base API instance
const api: AxiosInstance = axios.create({
  baseURL: config.apiUrl,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    const token = localStorage.getItem('token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config;

    // Handle 401 Unauthorized errors
    if (error.response?.status === 401) {
      // Try to refresh token if available
      const refreshToken = localStorage.getItem('refreshToken');
      if (refreshToken && !originalRequest?.url?.includes('auth/refresh')) {
        try {
          const response = await api.post('/auth/refresh', {
            refreshToken,
          });
          const { token } = response.data;
          localStorage.setItem('token', token);

          // Retry the original request
          if (originalRequest && originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          }
        } catch (refreshError) {
          // If refresh fails, logout user
          localStorage.removeItem('token');
          localStorage.removeItem('refreshToken');
          window.location.href = '/login';
        }
      } else {
        // No refresh token available, redirect to login
        localStorage.removeItem('token');
        window.location.href = '/login';
      }
    }

    // Handle 403 Forbidden errors
    if (error.response?.status === 403) {
      // Handle permission denied
      console.error('Permission denied');
    }

    // Handle 404 Not Found errors
    if (error.response?.status === 404) {
      // Handle resource not found
      console.error('Resource not found');
    }

    // Handle 429 Too Many Requests
    if (error.response?.status === 429) {
      // Handle rate limiting
      console.error('Rate limit exceeded');
    }

    // Handle network errors
    if (error.message === 'Network Error') {
      console.error('Network error - please check your connection');
    }

    return Promise.reject(error);
  }
);

// Error handler helper
export const handleApiError = (error: unknown) => {
  if (axios.isAxiosError(error)) {
    return {
      message: error.response?.data?.message || 'An error occurred',
      status: error.response?.status,
      details: error.response?.data?.details,
    };
  }
  return {
    message: 'An unexpected error occurred',
    status: 500,
    details: null,
  };
};

export default api;