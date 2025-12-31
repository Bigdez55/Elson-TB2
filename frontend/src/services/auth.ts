import api from './api';

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  username: string;
}

export interface LoginResponse {
  token: string;
  refreshToken?: string;
  user: any;
  requires2FA?: boolean;
  email?: string;
  message?: string;
}

export interface RegisterResponse {
  token: string;
  refreshToken?: string;
  user: any;
}

export const authService = {
  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    const response = await api.post('/auth/login', credentials);
    const data = response.data;

    // Handle 2FA case
    if (data.requires2FA) {
      return {
        token: '',
        user: null,
        requires2FA: true,
      };
    }

    // Store token if provided
    if (data.token || data.access_token) {
      const token = data.token || data.access_token;
      localStorage.setItem('token', token);
      if (data.refreshToken || data.refresh_token) {
        localStorage.setItem('refreshToken', data.refreshToken || data.refresh_token);
      }
    }

    return {
      token: data.token || data.access_token,
      refreshToken: data.refreshToken || data.refresh_token,
      user: data.user || data,
      requires2FA: false,
    };
  },

  async register(data: RegisterData): Promise<RegisterResponse> {
    const response = await api.post('/auth/register', {
      email: data.email,
      password: data.password,
      full_name: data.username,
    });
    const responseData = response.data;

    if (responseData.token || responseData.access_token) {
      const token = responseData.token || responseData.access_token;
      localStorage.setItem('token', token);
      if (responseData.refreshToken || responseData.refresh_token) {
        localStorage.setItem('refreshToken', responseData.refreshToken || responseData.refresh_token);
      }
    }

    return {
      token: responseData.token || responseData.access_token,
      refreshToken: responseData.refreshToken || responseData.refresh_token,
      user: responseData.user || responseData,
    };
  },

  async logout(): Promise<void> {
    try {
      await api.post('/auth/logout');
    } catch {
      // Ignore logout errors
    }
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
  },

  async getProfile(): Promise<any> {
    const response = await api.get('/auth/me');
    return response.data;
  },

  async refreshToken(): Promise<string> {
    const refreshToken = localStorage.getItem('refreshToken');
    const response = await api.post('/auth/refresh', { refreshToken });
    const token = response.data.token || response.data.access_token;
    localStorage.setItem('token', token);
    return token;
  },

  async verify2FA(email: string, code: string): Promise<LoginResponse> {
    const response = await api.post('/auth/2fa/verify', { email, code });
    const data = response.data;

    if (data.token || data.access_token) {
      const token = data.token || data.access_token;
      localStorage.setItem('token', token);
      if (data.refreshToken || data.refresh_token) {
        localStorage.setItem('refreshToken', data.refreshToken || data.refresh_token);
      }
    }

    return {
      token: data.token || data.access_token,
      refreshToken: data.refreshToken || data.refresh_token,
      user: data.user || data,
    };
  },
};

export default authService;
