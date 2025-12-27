import { configureStore } from '@reduxjs/toolkit';
import authReducer, { login, register, checkAuth, logout, clearError } from '../slices/authSlice';
import { authAPI } from '../../services/api';

// Mock the API
jest.mock('../../services/api');
const mockedAuthAPI = authAPI as jest.Mocked<typeof authAPI>;

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
});

describe('Auth Slice Tests', () => {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  let store: any;

  beforeEach(() => {
    store = configureStore({
      reducer: {
        auth: authReducer,
      },
    });
    jest.clearAllMocks();
    localStorageMock.clear.mockClear();
    localStorageMock.getItem.mockClear();
    localStorageMock.setItem.mockClear();
    localStorageMock.removeItem.mockClear();
  });

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const state = store.getState().auth;
      expect(state).toEqual({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      });
    });
  });

  describe('login thunk', () => {
    it('should handle successful login', async () => {
      const mockResponse = {
        access_token: 'test-token',
        user: {
          id: 1,
          email: 'test@example.com',
          full_name: 'Test User',
          risk_tolerance: 'moderate',
          trading_style: 'conservative',
          is_active: true,
          is_verified: true
        }
      };
      mockedAuthAPI.login.mockResolvedValue(mockResponse);

      const action = await store.dispatch(login({
        email: 'test@example.com',
        password: 'password'
      })) as any;

      expect(action.type).toBe('auth/login/fulfilled');
      expect(action.payload).toEqual(mockResponse);
      expect(localStorageMock.setItem).toHaveBeenCalledWith('token', 'test-token');

      const state = store.getState().auth;
      expect(state.user).toEqual(mockResponse.user);
      expect(state.isAuthenticated).toBe(true);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBe(null);
    });

    it('should handle login failure', async () => {
      const errorResponse = {
        response: {
          data: { detail: 'Invalid credentials' },
          status: 401
        }
      };
      mockedAuthAPI.login.mockRejectedValue(errorResponse);

      const action = await store.dispatch(login({
        email: 'test@example.com',
        password: 'wrong-password'
      })) as any;

      expect(action.type).toBe('auth/login/rejected');
      expect(action.payload).toBe('Invalid credentials');

      const state = store.getState().auth;
      expect(state.user).toBe(null);
      expect(state.isAuthenticated).toBe(false);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBe('Invalid credentials');
    });

    it('should handle network error during login', async () => {
      const networkError = new Error('Network Error');
      mockedAuthAPI.login.mockRejectedValue(networkError);

      const action = await store.dispatch(login({
        email: 'test@example.com',
        password: 'password'
      })) as any;

      expect(action.type).toBe('auth/login/rejected');
      expect(action.payload).toBe('Login failed');

      const state = store.getState().auth;
      expect(state.error).toBe('Login failed');
    });

    it('should set loading state during login', () => {
      // Set up a pending promise
      mockedAuthAPI.login.mockReturnValue(new Promise(() => {}));

      store.dispatch(login({
        email: 'test@example.com',
        password: 'password'
      }));

      const state = store.getState().auth;
      expect(state.isLoading).toBe(true);
      expect(state.error).toBe(null);
    });
  });

  describe('register thunk', () => {
    it('should handle successful registration', async () => {
      const userData = {
        email: 'test@example.com',
        password: 'password',
        full_name: 'Test User',
        risk_tolerance: 'moderate',
        trading_style: 'conservative'
      };
      const mockResponse = {
        access_token: 'test-token',
        user: {
          id: 1,
          ...userData,
          is_active: true,
          is_verified: false
        }
      };
      mockedAuthAPI.register.mockResolvedValue(mockResponse);

      const action = await store.dispatch(register(userData)) as any;

      expect(action.type).toBe('auth/register/fulfilled');
      expect(action.payload).toEqual(mockResponse);
      expect(localStorageMock.setItem).toHaveBeenCalledWith('token', 'test-token');

      const state = store.getState().auth;
      expect(state.user).toEqual(mockResponse.user);
      expect(state.isAuthenticated).toBe(true);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBe(null);
    });

    it('should handle registration validation errors', async () => {
      const errorResponse = {
        response: {
          data: { detail: 'Email already exists' },
          status: 400
        }
      };
      mockedAuthAPI.register.mockRejectedValue(errorResponse);

      const action = await store.dispatch(register({
        email: 'existing@example.com',
        password: 'password'
      })) as any;

      expect(action.type).toBe('auth/register/rejected');
      expect(action.payload).toBe('Email already exists');

      const state = store.getState().auth;
      expect(state.error).toBe('Email already exists');
      expect(state.isAuthenticated).toBe(false);
    });
  });

  describe('checkAuth thunk', () => {
    it('should handle successful auth check', async () => {
      const mockUser = {
        id: 1,
        email: 'test@example.com',
        full_name: 'Test User',
        risk_tolerance: 'moderate',
        trading_style: 'conservative',
        is_active: true,
        is_verified: true
      };
      mockedAuthAPI.getCurrentUser.mockResolvedValue(mockUser);

      const action = await store.dispatch(checkAuth()) as any;

      expect(action.type).toBe('auth/checkAuth/fulfilled');
      expect(action.payload).toEqual(mockUser);

      const state = store.getState().auth;
      expect(state.user).toEqual(mockUser);
      expect(state.isAuthenticated).toBe(true);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBe(null);
    });

    it('should handle auth check failure', async () => {
      const errorResponse = {
        response: {
          data: { detail: 'Token expired' },
          status: 401
        }
      };
      mockedAuthAPI.getCurrentUser.mockRejectedValue(errorResponse);

      const action = await store.dispatch(checkAuth()) as any;

      expect(action.type).toBe('auth/checkAuth/rejected');
      expect(action.payload).toBe('Token expired');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('token');

      const state = store.getState().auth;
      expect(state.user).toBe(null);
      expect(state.isAuthenticated).toBe(false);
      expect(state.error).toBe('Token expired');
    });

    it('should handle network error during auth check', async () => {
      const networkError = new Error('Network Error');
      mockedAuthAPI.getCurrentUser.mockRejectedValue(networkError);

      const action = await store.dispatch(checkAuth()) as any;

      expect(action.type).toBe('auth/checkAuth/rejected');
      expect(action.payload).toBe('Authentication check failed');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('token');
    });
  });

  describe('logout action', () => {
    it('should handle logout correctly', () => {
      // First set up an authenticated state
      store.dispatch({
        type: 'auth/login/fulfilled',
        payload: {
          user: {
            id: 1,
            email: 'test@example.com',
            full_name: 'Test User',
            risk_tolerance: 'moderate',
            trading_style: 'conservative',
            is_active: true,
            is_verified: true
          }
        }
      });

      // Then logout
      store.dispatch(logout());

      expect(localStorageMock.removeItem).toHaveBeenCalledWith('token');

      const state = store.getState().auth;
      expect(state.user).toBe(null);
      expect(state.isAuthenticated).toBe(false);
      expect(state.error).toBe(null);
    });
  });

  describe('clearError action', () => {
    it('should clear error state', () => {
      // First set an error state
      store.dispatch({
        type: 'auth/login/rejected',
        payload: 'Some error'
      });

      let state = store.getState().auth;
      expect(state.error).toBe('Some error');

      // Then clear the error
      store.dispatch(clearError());

      state = store.getState().auth;
      expect(state.error).toBe(null);
    });
  });

  describe('Loading states', () => {
    it('should set loading during login', () => {
      store.dispatch({ type: 'auth/login/pending' });

      const state = store.getState().auth;
      expect(state.isLoading).toBe(true);
      expect(state.error).toBe(null);
    });

    it('should set loading during register', () => {
      store.dispatch({ type: 'auth/register/pending' });

      const state = store.getState().auth;
      expect(state.isLoading).toBe(true);
      expect(state.error).toBe(null);
    });

    it('should set loading during checkAuth', () => {
      store.dispatch({ type: 'auth/checkAuth/pending' });

      const state = store.getState().auth;
      expect(state.isLoading).toBe(true);
    });
  });

  describe('Error handling integration', () => {
    it('should handle different error response formats', async () => {
      // Test undefined error response
      mockedAuthAPI.login.mockRejectedValue({});

      const action = await store.dispatch(login({
        email: 'test@example.com',
        password: 'password'
      }));

      expect(action.payload).toBe('Login failed');
    });

    it('should handle string error responses', async () => {
      mockedAuthAPI.login.mockRejectedValue({
        response: {
          data: { detail: 'Custom error message' }
        }
      });

      const action = await store.dispatch(login({
        email: 'test@example.com',
        password: 'password'
      }));

      expect(action.payload).toBe('Custom error message');
    });
  });
});