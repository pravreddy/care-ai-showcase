import { render } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi } from 'vitest';

// Custom render with router
export function renderWithRouter(ui, { route = '/' } = {}) {
  window.history.pushState({}, 'Test page', route);
  
  return render(ui, {
    wrapper: ({ children }) => (
      <BrowserRouter>{children}</BrowserRouter>
    ),
  });
}

// Mock navigate function
export const mockNavigate = vi.fn();

// Mock useNavigate hook
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Create mock API response
export function createMockResponse(data, status = 200) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: async () => data,
    text: async () => JSON.stringify(data),
  });
}

// Create mock error response
export function createMockError(message, status = 500) {
  return Promise.resolve({
    ok: false,
    status,
    json: async () => ({ detail: message }),
    text: async () => JSON.stringify({ detail: message }),
  });
}

// Wait for async updates
export const waitFor = (callback, options) => {
  return new Promise((resolve) => {
    const check = () => {
      try {
        callback();
        resolve();
      } catch (error) {
        setTimeout(check, options?.interval || 50);
      }
    };
    check();
  });
};
