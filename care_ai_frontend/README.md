# Care AI Frontend

**React + Vite frontend for Care AI medical knowledge engine**

---

## 🚀 Quick Start

### Using Docker (Recommended)

From the project root:

```bash
# Start full stack (frontend + backend)
docker-compose -f docker-compose.dev.yml up -d

# View frontend logs
docker-compose -f docker-compose.dev.yml logs -f frontend

# Open in browser
open http://localhost:3000
```

### Local Development (Without Docker)

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Open in browser
open http://localhost:3000
```

---

## 📁 Project Structure

```
care_ai_frontend/
├── src/
│   ├── components/          # Reusable components
│   │   ├── Navbar.jsx      # Navigation bar
│   │   └── Footer.jsx      # Footer
│   ├── pages/              # Page components
│   │   ├── Landing.jsx     # Home page
│   │   ├── Login.jsx       # Login page
│   │   ├── Register.jsx    # Registration page
│   │   ├── Dashboard.jsx   # User dashboard
│   │   ├── AskAgent.jsx    # AI question interface
│   │   ├── Notes.jsx       # Voice notes
│   │   ├── Security.jsx    # 2FA settings
│   │   ├── Partner.jsx     # Partner dashboard
│   │   ├── TryAI.jsx       # Free trial
│   │   └── APIDocs.jsx     # API documentation
│   ├── services/
│   │   └── api.js          # API client
│   ├── styles/
│   │   └── nhs-theme.css   # NHS styling
│   ├── App.jsx             # Main app component
│   └── main.jsx            # Entry point
├── index.html              # HTML template
├── vite.config.js          # Vite configuration
├── package.json            # Dependencies
├── Dockerfile              # Production build
├── Dockerfile.dev          # Development build
└── README.md               # This file
```

---

## 🛠️ Technology Stack

- **React 18** - UI library
- **Vite 6** - Build tool & dev server
- **React Router 6** - Routing
- **Lucide React** - Icons
- **NHS Design System** - Styling

---

## 🎨 Features

### Pages

1. **Landing Page** - Marketing & information
2. **Authentication**
   - Login
   - Registration
   - Password reset
3. **Dashboard** - User overview
4. **Ask Agent** - AI medical questions
5. **Voice Notes** - Clinical note generation
6. **Security** - 2FA setup
7. **Partner** - API partner dashboard
8. **Try AI** - Free trial interface
9. **API Docs** - Developer documentation

### Components

- **Navbar** - Navigation with user menu
- **Footer** - Site footer

---

## 🔧 Development

### Available Scripts

```bash
# Start dev server (hot reload)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Environment Variables

Create `.env.local` (optional):

```bash
# API URL (defaults to http://localhost:8000)
VITE_API_URL=http://localhost:8000
```

### API Proxy

Vite automatically proxies `/api` requests to the backend (configured in `vite.config.js`):

```javascript
server: {
  port: 3000,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

---

## 📡 API Integration

### API Service (`src/services/api.js`)

The `api.js` file provides a centralized API client:

```javascript
import api from './services/api';

// Login
const response = await api.post('/auth/login', {
  username: 'user@example.com',
  password: 'password123'
});

// Get user profile
const user = await api.get('/auth/me');

// Ask AI question
const answer = await api.post('/agent/ask', {
  question: 'What is paracetamol?'
});
```

### Authentication

The API client automatically:
- Stores JWT tokens in localStorage
- Adds Authorization header to requests
- Handles token refresh
- Redirects to login on 401

---

## 🎨 Styling

### NHS Design System

The app uses NHS-inspired styling with:
- NHS blue (#005eb8)
- Accessible colors
- Clear typography
- Mobile-first responsive design

Custom styles in `src/styles/nhs-theme.css`:

```css
:root {
  --nhs-blue: #005eb8;
  --nhs-dark-blue: #003087;
  --nhs-warm-yellow: #ffb81c;
  --nhs-green: #007f3b;
  --nhs-grey-1: #4c6272;
  --nhs-grey-2: #768692;
}
```

---

## 🧪 Testing

### Running Tests

```bash
# Run tests (when implemented)
npm test

# Run tests with coverage
npm run test:coverage
```

### Writing Tests

```javascript
// Example test
import { render, screen } from '@testing-library/react';
import Landing from './pages/Landing';

test('renders landing page', () => {
  render(<Landing />);
  expect(screen.getByText(/Care AI/i)).toBeInTheDocument();
});
```

---

## 📦 Building for Production

### Using Docker

```bash
# Build production image
docker build -t careai-frontend .

# Run production container
docker run -p 80:80 careai-frontend
```

### Manual Build

```bash
# Build
npm run build

# Output in dist/
# Serve with any static file server
npx serve -s dist
```

---

## 🚀 Deployment

### Production Dockerfile

The production Dockerfile:
1. Builds the React app
2. Serves with Nginx
3. Includes API proxy configuration

```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
```

---

## 🔍 Useful Commands

### Development

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build production
npm run build

# Preview production build
npm run preview

# Lint code (when configured)
npm run lint

# Format code (when configured)
npm run format
```

### Docker

```bash
# Build dev image
docker build -f Dockerfile.dev -t careai-frontend-dev .

# Run dev container
docker run -p 3000:3000 -v $(pwd)/src:/app/src careai-frontend-dev

# Build production image
docker build -t careai-frontend .

# Run production container
docker run -p 80:80 careai-frontend
```

---

## 🐛 Troubleshooting

### Common Issues

#### Port Already in Use

```bash
# Find what's using port 3000
lsof -i :3000

# Kill the process
kill -9 <PID>

# Or use a different port
npm run dev -- --port 3001
```

#### API Connection Error

```bash
# Check backend is running
curl http://localhost:8000/health

# Check proxy configuration in vite.config.js
# Make sure CORS is enabled in backend
```

#### Build Errors

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf node_modules/.vite
npm run dev
```

#### Hot Reload Not Working

```bash
# In Docker, set polling in vite.config.js:
server: {
  watch: {
    usePolling: true
  }
}
```

---

## 📚 Additional Resources

- **Vite Documentation**: https://vitejs.dev/
- **React Documentation**: https://react.dev/
- **React Router**: https://reactrouter.com/
- **NHS Design System**: https://service-manual.nhs.uk/design-system

---

## 🎯 Next Steps

1. **Run locally**: Follow Quick Start above
2. **Explore pages**: Navigate through all pages
3. **Test features**: Register, login, ask questions
4. **Customize**: Update styling and content
5. **Add tests**: Write component tests
6. **Deploy**: Build and deploy to production

---

## 📝 Development Guidelines

### Component Structure

```javascript
// Good component structure
import React from 'react';
import { useNavigate } from 'react-router-dom';

const MyComponent = () => {
  const navigate = useNavigate();
  
  const handleClick = () => {
    // Handle click
  };
  
  return (
    <div className="my-component">
      {/* Component content */}
    </div>
  );
};

export default MyComponent;
```

### API Calls

```javascript
// Good API call pattern
import { useState, useEffect } from 'react';
import api from '../services/api';

const MyComponent = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await api.get('/endpoint');
        setData(response.data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);
  
  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  
  return <div>{/* Render data */}</div>;
};
```

### Styling

```javascript
// Use CSS classes
<div className="container">
  <h1 className="heading">Title</h1>
  <p className="text">Content</p>
</div>

// Avoid inline styles (unless dynamic)
<div style={{ color: isActive ? 'blue' : 'gray' }}>
```

---

## ✅ Checklist

Before committing:

- [ ] Code runs without errors: `npm run dev`
- [ ] No console errors in browser
- [ ] Components are responsive (mobile, tablet, desktop)
- [ ] API calls handle errors
- [ ] Loading states implemented
- [ ] Code follows project conventions
- [ ] No hardcoded API URLs (use proxy)

---
**Need to Do This!** 🚀

- Frontend Code is not Good need to templeted it . 
- Lot of code is ther
- not easy to maintane
- Need t write lot of test
- updatgeat he erver
- Beed to write lot of integration test
- Addotehr funtcatinly later for (win loign/linkein/facebook aut/github)

**Happy coding!** 🚀
