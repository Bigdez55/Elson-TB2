import api, { handleApiError } from './api';

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  username: string;
}

export interface TwoFactorData {
  email: string;
  code: string;
  token?: string;
}

export const authService = {
  async login(credentials: LoginCredentials) {
    try {
      const response = await api.post('/auth/login', credentials);
      const { token, refreshToken, user } = response.data;
      localStorage.setItem('token', token);
      localStorage.setItem('refreshToken', refreshToken);
      return user;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async register(data: RegisterData) {
    try {
      const response = await api.post('/auth/register', data);
      const { token, refreshToken, user } = response.data;
      localStorage.setItem('token', token);
      localStorage.setItem('refreshToken', refreshToken);
      return user;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async logout() {
    try {
      await api.post('/auth/logout');
      localStorage.removeItem('token');
      localStorage.removeItem('refreshToken');
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async refreshToken() {
    try {
      const refreshToken = localStorage.getItem('refreshToken');
      const response = await api.post('/auth/refresh', { refreshToken });
      const { token } = response.data;
      localStorage.setItem('token', token);
      return token;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async enable2FA() {
    try {
      const response = await api.post('/auth/2fa/enable');
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async verify2FA(email: string, code: string) {
    try {
      const data: TwoFactorData = { email, code };
      const response = await api.post('/auth/2fa/verify', data);
      const { token, refreshToken, user } = response.data;
      localStorage.setItem('token', token);
      localStorage.setItem('refreshToken', refreshToken);
      return { token, refreshToken, user };
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  async request2FACode(email: string) {
    try {
      const response = await api.post('/auth/2fa/request-code', { email });
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async disable2FA(code: string) {
    try {
      await api.post('/auth/2fa/disable', { code });
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async requestPasswordReset(email: string) {
    try {
      const response = await api.post('/auth/forgot-password', { email });
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async resetPassword(token: string, password: string) {
    try {
      await api.post('/auth/reset-password', { token, password });
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async getProfile() {
    try {
      const response = await api.get('/auth/profile');
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async updateProfile(data: any) {
    try {
      const response = await api.put('/auth/profile', data);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async changePassword(currentPassword: string, newPassword: string) {
    try {
      await api.post('/auth/change-password', {
        currentPassword,
        newPassword,
      });
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async getSecurityLog() {
    try {
      const response = await api.get('/auth/security-log');
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
};