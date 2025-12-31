import { useState, useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/auth';
import { login as loginAction, register as registerAction, logout as logoutAction, verify2FA as verify2FAAction } from '../store/slices/userSlice';
import { RootState } from '../store/store';

export function useAuth() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const user = useSelector((state: RootState) => state.user?.currentUser || null);

  const login = useCallback(
    async (email: string, password: string) => {
      try {
        setLoading(true);
        setError(null);

        // Get the location state to see if we need to redirect back after login
        const location = window.location;
        const fromPath = new URLSearchParams(location.search).get('from');

        // Dispatch the login action which returns a promise
        const resultAction = await dispatch(loginAction({ email, password }) as any);

        if (loginAction.fulfilled.match(resultAction)) {
          // Check if 2FA is required
          if (resultAction.payload.requires2FA) {
            // Redirect to 2FA page, preserving the intended destination
            navigate(`/two-factor-auth${fromPath ? `?from=${encodeURIComponent(fromPath)}` : ''}`);
          } else {
            // Regular login successful, redirect to intended destination or dashboard
            navigate(fromPath || '/dashboard');
          }
          return true;
        } else if (loginAction.rejected.match(resultAction)) {
          // Login failed
          if (resultAction.payload) {
            setError(resultAction.payload as string);
          } else {
            setError('Login failed');
          }
          return false;
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Login failed');
        return false;
      } finally {
        setLoading(false);
      }
    },
    [dispatch, navigate]
  );

  const register = useCallback(
    async (email: string, password: string, username: string) => {
      try {
        setLoading(true);
        setError(null);

        // Dispatch the register action
        const resultAction = await dispatch(registerAction({ email, password, username }) as any);

        if (registerAction.fulfilled.match(resultAction)) {
          navigate('/dashboard');
          return true;
        } else if (registerAction.rejected.match(resultAction)) {
          if (resultAction.payload) {
            setError(resultAction.payload as string);
          } else {
            setError('Registration failed');
          }
          return false;
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Registration failed');
        return false;
      } finally {
        setLoading(false);
      }
    },
    [dispatch, navigate]
  );

  const logout = useCallback(async () => {
    try {
      await authService.logout();
      dispatch(logoutAction());
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  }, [dispatch, navigate]);

  const verify2FA = useCallback(async (email: string, code: string) => {
    try {
      setLoading(true);
      setError(null);

      // Get the intended destination from the URL query string
      const location = window.location;
      const fromPath = new URLSearchParams(location.search).get('from');

      // First call the service directly
      const authResponse = await authService.verify2FA(email, code);

      // Then dispatch the action to update the store
      const resultAction = await dispatch(verify2FAAction(authResponse) as any);

      if (verify2FAAction.fulfilled.match(resultAction)) {
        // Navigate to the intended destination or dashboard
        navigate(fromPath || '/dashboard');
        return true;
      } else if (verify2FAAction.rejected.match(resultAction)) {
        if (resultAction.payload) {
          setError(resultAction.payload as string);
        } else {
          setError('2FA verification failed');
        }
        return false;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '2FA verification failed');
      return false;
    } finally {
      setLoading(false);
    }
  }, [dispatch, navigate]);

  return {
    user,
    login,
    register,
    logout,
    verify2FA,
    loading,
    error,
  };
}

export default useAuth;
