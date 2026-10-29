import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import Login from '../../pages/Login';
import { createMockResponse, createMockError } from '../testUtils';

describe('Login Page', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  const renderLogin = () => {
    return render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    );
  };

  describe('Rendering', () => {
    it('should render login form', () => {
      renderLogin();
      
      expect(screen.getByRole('heading', { name: /login/i })).toBeInTheDocument();
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
    });

    it('should render register link', () => {
      renderLogin();
      
      expect(screen.getByText(/don't have an account/i)).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /register/i })).toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    it('should show error for empty email', async () => {
      renderLogin();
      const user = userEvent.setup();
      
      const submitButton = screen.getByRole('button', { name: /login/i });
      await user.click(submitButton);
      
      expect(await screen.findByText(/email is required/i)).toBeInTheDocument();
    });

    it('should show error for invalid email', async () => {
      renderLogin();
      const user = userEvent.setup();
      
      const emailInput = screen.getByLabelText(/email/i);
      await user.type(emailInput, 'invalid-email');
      
      const submitButton = screen.getByRole('button', { name: /login/i });
      await user.click(submitButton);
      
      expect(await screen.findByText(/valid email/i)).toBeInTheDocument();
    });
  });

  describe('Login Process', () => {
    it('should successfully login with valid credentials', async () => {
      const mockResponse = {
        access_token: 'mock-token',
        refresh_token: 'mock-refresh',
        expires_in: 3600,
      };
      
      global.fetch = vi.fn(() => createMockResponse(mockResponse));
      
      renderLogin();
      const user = userEvent.setup();
      
      await user.type(screen.getByLabelText(/email/i), 'test@example.com');
      await user.type(screen.getByLabelText(/password/i), 'Password123!');
      await user.click(screen.getByRole('button', { name: /login/i }));
      
      expect(localStorage.getItem('access_token')).toBe('mock-token');
    });

    it('should handle login error', async () => {
      global.fetch = vi.fn(() => createMockError('Invalid credentials', 401));
      
      renderLogin();
      const user = userEvent.setup();
      
      await user.type(screen.getByLabelText(/email/i), 'test@example.com');
      await user.type(screen.getByLabelText(/password/i), 'wrong');
      await user.click(screen.getByRole('button', { name: /login/i }));
      
      expect(await screen.findByText(/invalid credentials/i)).toBeInTheDocument();
    });
  });
});
