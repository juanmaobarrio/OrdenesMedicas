import api from './api';
import { LoginCredentials, TokenResponse, UserSession } from '../types/auth';

export const authService = {
  async login(credentials: LoginCredentials): Promise<TokenResponse> {
    const response = await api.post<TokenResponse>('/auth/login', credentials);
    return response.data;
  },

  async refreshToken(refreshToken: string): Promise<TokenResponse> {
    const response = await api.post<TokenResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    });
    return response.data;
  },

  async getCurrentUser(): Promise<UserSession> {
    const response = await api.get<UserSession>('/auth/me');
    return response.data;
  },
};
