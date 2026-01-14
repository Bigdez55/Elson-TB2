import React from 'react';

// Mock navigate function - can be spied on in tests
export const mockNavigate = jest.fn();

// Mock location
export const mockLocation = {
  pathname: '/',
  search: '',
  hash: '',
  state: null,
  key: 'default',
};

// Hooks
export const useNavigate = () => mockNavigate;
export const useLocation = () => mockLocation;
export const useParams = () => ({});
export const useSearchParams = (): [URLSearchParams, jest.Mock] => [new URLSearchParams(), jest.fn()];
export const useMatch = () => null;
export const useHref = (to: string) => to;
export const useLinkClickHandler = () => jest.fn();
export const useResolvedPath = (to: string) => ({ pathname: to, search: '', hash: '' });
export const useInRouterContext = () => true;
export const useNavigationType = () => 'POP';
export const useOutletContext = () => ({});

// Components
export const Link = ({ children, to, ...props }: any) => (
  <a href={to} {...props}>{children}</a>
);

export const NavLink = ({ children, to, ...props }: any) => (
  <a href={to} {...props}>{children}</a>
);

export const Navigate = () => null;
export const Outlet = () => null;

export const MemoryRouter = ({ children }: any) => <>{children}</>;
export const BrowserRouter = ({ children }: any) => <>{children}</>;
export const HashRouter = ({ children }: any) => <>{children}</>;
export const Routes = ({ children }: any) => <>{children}</>;
export const Route = () => null;

export const createBrowserRouter = jest.fn(() => ({}));
export const createMemoryRouter = jest.fn(() => ({}));
export const createHashRouter = jest.fn(() => ({}));
export const RouterProvider = ({ children }: any) => <>{children}</>;

// Re-export for compatibility
export default {
  useNavigate,
  useLocation,
  useParams,
  useSearchParams,
  useMatch,
  Link,
  NavLink,
  Navigate,
  Outlet,
  MemoryRouter,
  BrowserRouter,
  Routes,
  Route,
  createBrowserRouter,
  RouterProvider,
};
