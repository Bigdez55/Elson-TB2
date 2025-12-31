import { http, HttpResponse, delay } from 'msw';

// Default test user data
export const defaultUser = {
  id: 1,
  email: 'test@example.com',
  full_name: 'Test User',
  risk_tolerance: 'moderate',
  trading_style: 'long_term',
  is_active: true,
  is_verified: true,
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-01-01T00:00:00Z',
};

export const authHandlers = [
  // Login endpoint
  http.post('/api/v1/auth/login', async ({ request }) => {
    await delay(50); // Simulate network latency

    const body = await request.json() as { email: string; password: string };

    // Simulate invalid credentials
    if (body.password === 'wrong-password') {
      return HttpResponse.json(
        { detail: 'Invalid credentials' },
        { status: 401 }
      );
    }

    // Simulate network error for specific email
    if (body.email === 'network-error@example.com') {
      return HttpResponse.error();
    }

    return HttpResponse.json({
      access_token: 'test-token-123',
      token_type: 'bearer',
      user: {
        ...defaultUser,
        email: body.email,
      },
    });
  }),

  // Register endpoint
  http.post('/api/v1/auth/register', async ({ request }) => {
    await delay(50);

    const body = await request.json() as {
      email: string;
      password: string;
      full_name?: string;
      risk_tolerance?: string;
      trading_style?: string;
    };

    // Simulate existing user
    if (body.email === 'existing@example.com') {
      return HttpResponse.json(
        { detail: 'Email already exists' },
        { status: 400 }
      );
    }

    return HttpResponse.json({
      access_token: 'test-token-123',
      token_type: 'bearer',
      user: {
        id: 1,
        email: body.email,
        full_name: body.full_name || 'New User',
        risk_tolerance: body.risk_tolerance || 'moderate',
        trading_style: body.trading_style || 'long_term',
        is_active: true,
        is_verified: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    });
  }),

  // Get current user endpoint
  http.get('/api/v1/auth/me', async ({ request }) => {
    await delay(50);

    const authHeader = request.headers.get('Authorization');

    // Check for valid token
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      );
    }

    const token = authHeader.replace('Bearer ', '');

    // Simulate expired token
    if (token === 'expired-token') {
      return HttpResponse.json(
        { detail: 'Token expired' },
        { status: 401 }
      );
    }

    return HttpResponse.json(defaultUser);
  }),

  // Logout endpoint
  http.post('/api/v1/auth/logout', async () => {
    await delay(50);
    return HttpResponse.json({ message: 'Logged out successfully' });
  }),

  // Refresh token endpoint
  http.post('/api/v1/auth/refresh', async ({ request }) => {
    await delay(50);

    const authHeader = request.headers.get('Authorization');
    if (!authHeader) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      );
    }

    return HttpResponse.json({
      access_token: 'new-test-token-456',
      token_type: 'bearer',
    });
  }),
];
