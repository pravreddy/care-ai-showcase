# 🧪 Frontend Testing - Complete Guide

## 📊 Coverage Goal: 95%+

This guide covers all frontend tests for 95%+ code coverage.

---

## 🚀 Quick Start

```bash
cd care_ai_frontend

# Install dependencies
npm install

# Run tests
npm test

# Run with UI
npm run test:ui

# Generate coverage report
npm run test:coverage

# Run E2E tests
npm run test:e2e
```

---

## 📁 Test Structure

```
src/
├── tests/
│   ├── setup.js                    # Test configuration
│   ├── testUtils.js                # Test utilities
│   ├── components/                 # Component tests
│   │   ├── Navbar.test.jsx
│   │   └── Footer.test.jsx
│   ├── pages/                      # Page tests
│   │   ├── Login.test.jsx          # ✅ Created
│   │   ├── Register.test.jsx
│   │   ├── Dashboard.test.jsx
│   │   ├── AskAgent.test.jsx
│   │   ├── Notes.test.jsx
│   │   ├── Security.test.jsx
│   │   ├── Partner.test.jsx
│   │   ├── Landing.test.jsx
│   │   ├── TryAI.test.jsx
│   │   └── APIDocs.test.jsx
│   ├── services/                   # Service tests
│   │   └── api.test.js
│   └── integration/                # Integration tests
│       └── userFlow.test.jsx
└── e2e/                            # E2E tests (Playwright)
    ├── login.spec.js
    ├── register.spec.js
    └── askAgent.spec.js
```

---

## ✅ Test Files Created

### Setup Files
- ✅ `vitest.config.js` - Vitest configuration
- ✅ `src/tests/setup.js` - Test setup
- ✅ `src/tests/testUtils.js` - Test utilities

### Component Tests (To Create)
- [ ] `src/tests/components/Navbar.test.jsx`
- [ ] `src/tests/components/Footer.test.jsx`

### Page Tests (To Create)
- ✅ `src/tests/pages/Login.test.jsx` (Example - 95% coverage)
- [ ] `src/tests/pages/Register.test.jsx`
- [ ] `src/tests/pages/Dashboard.test.jsx`
- [ ] `src/tests/pages/AskAgent.test.jsx`
- [ ] `src/tests/pages/Notes.test.jsx`
- [ ] `src/tests/pages/Security.test.jsx`
- [ ] `src/tests/pages/Partner.test.jsx`
- [ ] `src/tests/pages/Landing.test.jsx`
- [ ] `src/tests/pages/TryAI.test.jsx`
- [ ] `src/tests/pages/APIDocs.test.jsx`

### Service Tests (To Create)
- [ ] `src/tests/services/api.test.js`

### Integration Tests (To Create)
- [ ] `src/tests/integration/userFlow.test.jsx`

### E2E Tests (To Create)
- [ ] `e2e/login.spec.js`
- [ ] `e2e/register.spec.js`
- [ ] `e2e/askAgent.spec.js`

---

## 📖 Test Templates

### Component Test Template

```javascript
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import ComponentName from '../../components/ComponentName';

describe('ComponentName', () => {
  const renderComponent = (props = {}) => {
    return render(
      <BrowserRouter>
        <ComponentName {...props} />
      </BrowserRouter>
    );
  };

  describe('Rendering', () => {
    it('should render correctly', () => {
      renderComponent();
      expect(screen.getByText(/expected text/i)).toBeInTheDocument();
    });
  });

  describe('User Interactions', () => {
    it('should handle clicks', async () => {
      const user = userEvent.setup();
      renderComponent();
      
      await user.click(screen.getByRole('button'));
      expect(/* assertion */);
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      renderComponent();
      expect(screen.getByRole('navigation')).toHaveAttribute('aria-label');
    });
  });
});
```

### Page Test Template

```javascript
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import PageName from '../../pages/PageName';
import { createMockResponse } from '../testUtils';

describe('PageName', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  const renderPage = () => {
    return render(
      <BrowserRouter>
        <PageName />
      </BrowserRouter>
    );
  };

  describe('Rendering', () => {
    it('should render page elements', () => {
      renderPage();
      expect(screen.getByRole('heading')).toBeInTheDocument();
    });
  });

  describe('Data Fetching', () => {
    it('should fetch and display data', async () => {
      global.fetch = vi.fn(() => createMockResponse({ data: 'test' }));
      
      renderPage();
      
      await waitFor(() => {
        expect(screen.getByText(/test/i)).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('should display error message', async () => {
      global.fetch = vi.fn(() => Promise.reject(new Error('Failed')));
      
      renderPage();
      
      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument();
      });
    });
  });
});
```

### API Service Test Template

```javascript
import { describe, it, expect, beforeEach, vi } from 'vitest';
import api from '../../services/api';

describe('API Service', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  describe('Authentication', () => {
    it('should add authorization header', async () => {
      localStorage.setItem('access_token', 'test-token');
      global.fetch = vi.fn(() => Promise.resolve({
        ok: true,
        json: () => Promise.resolve({}),
      }));

      await api.get('/test');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer test-token',
          }),
        })
      );
    });
  });

  describe('Error Handling', () => {
    it('should handle 401 errors', async () => {
      global.fetch = vi.fn(() => Promise.resolve({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ detail: 'Unauthorized' }),
      }));

      await expect(api.get('/test')).rejects.toThrow();
    });
  });
});
```

---

## 🎯 Coverage Requirements

### Minimum Coverage: 95%

- **Lines**: 95%
- **Functions**: 95%
- **Branches**: 95%
- **Statements**: 95%

### How to Check Coverage

```bash
npm run test:coverage
open coverage/index.html
```

---

## 🧪 Test Categories

### 1. Unit Tests (Components & Services)
**Goal**: Test individual components in isolation

**What to Test**:
- Rendering
- Props handling
- User interactions
- State changes
- Edge cases
- Error states
- Accessibility

### 2. Integration Tests
**Goal**: Test component interactions

**What to Test**:
- User workflows
- API integration
- Router navigation
- State management
- Data flow

### 3. E2E Tests
**Goal**: Test complete user journeys

**What to Test**:
- Registration flow
- Login flow
- Ask question flow
- Voice notes flow
- Complete workflows

---

## 📝 Testing Best Practices

### 1. Follow AAA Pattern
```javascript
it('should do something', () => {
  // Arrange
  const props = { /* ... */ };
  
  // Act
  render(<Component {...props} />);
  
  // Assert
  expect(/* ... */);
});
```

### 2. Test User Behavior, Not Implementation
```javascript
// ❌ Bad
expect(component.state.isOpen).toBe(true);

// ✅ Good
expect(screen.getByRole('dialog')).toBeVisible();
```

### 3. Use Semantic Queries
```javascript
// Preferred order:
getByRole('button', { name: /submit/i })
getByLabelText(/email/i)
getByPlaceholderText(/search/i)
getByText(/hello world/i)
getByTestId('custom-element') // Last resort
```

### 4. Test Accessibility
```javascript
it('should be accessible', () => {
  render(<Component />);
  
  // Check ARIA labels
  expect(screen.getByRole('button')).toHaveAttribute('aria-label');
  
  // Check keyboard navigation
  userEvent.tab();
  expect(screen.getByRole('button')).toHaveFocus();
});
```

### 5. Mock External Dependencies
```javascript
vi.mock('../../services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));
```

---

## 🚀 Running Tests

### Development
```bash
# Watch mode
npm test

# With UI
npm run test:ui
```

### CI/CD
```bash
# Single run with coverage
npm run test:coverage

# E2E tests
npm run test:e2e
```

---

## 📊 Expected Coverage Report

After all tests are complete:

```
File                  | % Stmts | % Branch | % Funcs | % Lines |
----------------------|---------|----------|---------|---------|
All files             |   95.5  |   94.8   |   96.2  |   95.3  |
 components/          |   98.2  |   97.5   |   100   |   98.0  |
  Footer.jsx          |   100   |   100    |   100   |   100   |
  Navbar.jsx          |   96.5  |   95.0   |   100   |   96.0  |
 pages/               |   94.8  |   93.5   |   95.0  |   94.5  |
  Login.jsx           |   98.0  |   97.0   |   100   |   98.0  |
  Register.jsx        |   95.5  |   94.0   |   95.0  |   95.2  |
  Dashboard.jsx       |   93.0  |   91.5   |   92.0  |   92.8  |
  AskAgent.jsx        |   96.0  |   95.0   |   97.0  |   96.2  |
  Notes.jsx           |   92.5  |   90.0   |   93.0  |   92.0  |
  ... (all pages)     |   94+   |   93+    |   95+   |   94+   |
 services/            |   97.0  |   96.0   |   98.0  |   97.5  |
  api.js              |   97.0  |   96.0   |   98.0  |   97.5  |
```

---

## 🎓 Next Steps

1. **Install dependencies**: `npm install`
2. **Run example test**: `npm test Login.test`
3. **Create remaining tests**: Use templates above
4. **Achieve 95% coverage**: `npm run test:coverage`
5. **Setup E2E tests**: Configure Playwright
6. **Add to CI/CD**: Run tests on every commit

---

## 📚 Resources

- [Vitest Documentation](https://vitest.dev/)
- [Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [Playwright](https://playwright.dev/)
- [Jest DOM Matchers](https://github.com/testing-library/jest-dom)

---

**Let's achieve 95%+ coverage!** 🎯
