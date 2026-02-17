# 🎨 Frontend - Crop Recommendation System

![React](https://img.shields.io/badge/React-18.3.1-61dafb)
![Vite](https://img.shields.io/badge/Vite-6.3.5-646cff)
![Tailwind](https://img.shields.io/badge/TailwindCSS-4.1.12-38bdf8)
![TypeScript](https://img.shields.io/badge/TypeScript-Latest-3178c6)

Modern, responsive, and intuitive user interface for the Crop Recommendation System, built with React, Vite, and Tailwind CSS.

---

## 🌐 Live Deployment

**Production URL**: https://crop-recomandation-system.vercel.app/

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Technology Stack](#-technology-stack)
- [Project Structure](#-project-structure)
- [Installation & Setup](#-installation--setup)
- [Environment Configuration](#-environment-configuration)
- [Development Guide](#-development-guide)
- [Build & Deployment](#-build--deployment)
- [Component Documentation](#-component-documentation)
- [API Integration](#-api-integration)
- [Styling Guidelines](#-styling-guidelines)
- [Performance Optimization](#-performance-optimization)
- [Browser Support](#-browser-support)

---

## 🎯 Overview

The frontend is a single-page application (SPA) that provides an elegant, user-friendly interface for farmers and agricultural professionals to get crop recommendations. Built with modern web technologies, it offers a fast, responsive experience across all devices.

### Key Objectives

- **Simplicity**: Easy-to-use interface requiring no technical knowledge
- **Speed**: Lightning-fast interactions with optimized performance
- **Responsiveness**: Works seamlessly on desktop, tablet, and mobile devices
- **Accessibility**: Follows WCAG guidelines for inclusive design
- **Visual Appeal**: Modern, clean design with agricultural theming

---

## ⚡ Features

### 1. **Smart Input Form**
- **7 Input Parameters**: N, P, K, Temperature, Humidity, pH, Rainfall
- **Real-time Validation**: Instant feedback on invalid inputs
- **Range Hints**: Display acceptable ranges for each parameter
- **Auto-formatting**: Numeric inputs with proper decimal handling
- **Clear Error Messages**: User-friendly validation messages

### 2. **Results Visualization**
- **Top 3 Recommendations**: Display best-suited crops
- **Confidence Scores**: Visual progress bars showing prediction confidence
- **Crop Images**: High-quality images for visual identification
- **Detailed Information**: Cultivation tips, nutritional requirements, climate preferences

### 3. **Crop Gallery**
- **22 Crop Cards**: Browse all supported crops
- **Responsive Masonry Grid**: Beautiful card-based layout
- **Search & Filter**: Find crops quickly
- **Detailed Views**: Expandable cards with comprehensive information

### 4. **User Experience**
- **Loading States**: Skeleton screens and spinners during API calls
- **Error Handling**: Graceful error messages with retry options
- **Responsive Design**: Mobile-first approach
- **Dark Mode Ready**: Prepared for dark theme (coming soon)
- **Smooth Animations**: Subtle transitions for better UX

### 5. **Performance Features**
- **Code Splitting**: Lazy loading for optimal bundle size
- **Image Optimization**: WebP format with fallbacks
- **Caching Strategy**: HTTP caching for static assets
- **Prefetching**: Predictive loading for better perceived performance

---

## 🛠️ Technology Stack

### Core Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| **React** | 18.3.1 | UI framework with hooks |
| **Vite** | 6.3.5 | Build tool & dev server |
| **TypeScript** | Latest | Type safety |
| **Tailwind CSS** | 4.1.12 | Utility-first CSS framework |

### UI Component Libraries

- **Radix UI**: Accessible, unstyled component primitives
  - Dialog, Dropdown Menu, Popover, Tabs, Accordion, etc.
- **Material-UI**: Icons and some components
- **Motion (Framer Motion)**: Smooth animations
- **Lucide React**: Beautiful icons

### Utilities & Tools

- **clsx & tailwind-merge**: Conditional class names
- **date-fns**: Date manipulation
- **recharts**: Data visualization (charts)
- **react-hook-form**: Form validation
- **React DnD**: Drag and drop functionality
- **Embla Carousel**: Carousels and sliders

### Development Tools

- **Vite**: Lightning-fast HMR and builds
- **PostCSS**: CSS processing
- **ESLint**: Code linting (future)
- **Prettier**: Code formatting (future)

---

## 📁 Project Structure

```
Frontend/
├── src/
│   ├── app/                    # Main application
│   │   ├── App.tsx            # Root component
│   │   ├── components/        # Reusable UI components
│   │   │   ├── InputForm.tsx  # Recommendation form
│   │   │   ├── ResultsDisplay.tsx
│   │   │   ├── CropCard.tsx
│   │   │   └── ...
│   │   └── services/
│   │       └── api.ts         # API integration
│   ├── assets/                # Static assets
│   ├── lib/                   # Utility functions
│   └── index.css             # Global styles
│
├── public/                    # Static files
├── index.html                # Entry HTML
├── vite.config.ts           # Vite configuration
├── tailwind.config.js       # Tailwind configuration
├── package.json             # Dependencies
├── pnpm-lock.yaml          # Lock file (pnpm)
└── README.md               # This file
```

---

## 🚀 Installation & Setup

### Prerequisites

- **Node.js**: 18.x or higher
- **pnpm**: 8.x or higher (recommended) or npm

### Step-by-Step Installation

1. **Navigate to Frontend Directory**
   ```bash
   cd Frontend
   ```

2. **Install Dependencies**
   ```bash
   pnpm install
   # or
   npm install
   ```

3. **Set Up Environment Variables**
   ```bash
   cp .env.example .env
   ```

4. **Edit `.env` File**
   ```env
   VITE_API_BASE_URL=http://localhost:8000/api
   ```

5. **Start Development Server**
   ```bash
   pnpm dev
   # or
   npm run dev
   ```

6. **Open Browser**
   Navigate to `http://localhost:5173`

---

## ⚙️ Environment Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `VITE_API_BASE_URL` | Backend API base URL | `http://localhost:8000/api` | ✅ Yes |

### Environment Files

- **`.env`**: Local development (not committed to Git)
- **`.env.example`**: Template file (committed to Git)
- **Vercel**: Environment variables set in dashboard

### Sample `.env`

```env
# For local development
VITE_API_BASE_URL=http://localhost:8000/api

# For production (Vercel handles this automatically)
# VITE_API_BASE_URL=https://crop-recomandation-system.onrender.com/api
```

---

## 💻 Development Guide

### Running Development Server

```bash
pnpm dev
```

This starts:
- **Dev server** at `http://localhost:5173`
- **Hot Module Replacement (HMR)** for instant updates
- **Type checking** in watch mode

### Building for Production

```bash
pnpm build
```

Output: `dist/` directory with optimized bundles

### Preview Production Build

```bash
pnpm preview
```

Serves the production build locally for testing

### Linting & Formatting (Future)

```bash
# Coming soon
pnpm lint
pnpm format
```

---

## 🎨 Component Documentation

### Core Components

#### 1. **InputForm.tsx**
The main form for collecting user inputs.

**Props**:
- `onSubmit(data)`: Callback when form is submitted
- `isLoading`: Boolean for loading state

**Features**:
- Real-time validation
- Range indicators
- Clear/Reset functionality
- Responsive layout

**Example Usage**:
```tsx
<InputForm 
  onSubmit={handleRecommendation}
  isLoading={loading}
/>
```

#### 2. **ResultsDisplay.tsx**
Displays the top-3 crop recommendations.

**Props**:
- `results`: Array of crop predictions
- `onReset`: Callback to reset and show form again

**Features**:
- Confidence percentage bars
- Crop images
- Expandable details
- Print-friendly format

#### 3. **CropCard.tsx**
Individual crop card component.

**Props**:
- `crop`: Crop object with name, image, description
- `onClick`: Optional click handler
- `variant`: 'compact' | 'detailed'

### Styling Components

All components use Tailwind CSS utility classes for styling:
- Consistent spacing with Tailwind's spacing scale
- Responsive breakpoints (sm, md, lg, xl, 2xl)
- Semantic color classes
- Dark mode ready (with `dark:` prefix)

---

## 🔌 API Integration

### API Service (`services/api.ts`)

```typescript
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export const recommendCrop = async (data: CropInputData) => {
  const response = await axios.post(`${API_BASE_URL}/recommend/`, data);
  return response.data;
};

export const getCrops = async () => {
  const response = await axios.get(`${API_BASE_URL}/crops/`);
  return response.data;
};
```

### Error Handling

```typescript
try {
  const results = await recommendCrop(formData);
  setRecommendations(results);
} catch (error) {
  if (error.response?.status === 400) {
    showErrorMessage('Invalid input parameters');
  } else if (error.response?.status === 503) {
    showErrorMessage('Model is warming up, please retry in 30 seconds');
  } else {
    showErrorMessage('Network error, please check your connection');
  }
}
```

---

## 🎨 Styling Guidelines

### Tailwind CSS Philosophy

We use **utility-first CSS** with Tailwind:

```jsx
// ✅ Good: Utility classes
<div className="flex items-center gap-4 p-6 rounded-lg bg-white shadow-md">
  
// ❌ Avoid: Inline styles
<div style={{display: 'flex', alignItems: 'center', gap: '16px'}}>
```

### Color Palette

```css
/* Primary Colors (Agricultural Green) */
--primary-50: #f0fdf4
--primary-500: #22c55e
--primary-700: #15803d

/* Accent Colors (Earthy Brown) */
--accent-500: #92400e
--accent-700: #78350f

/* Neutral */
--gray-50: #f9fafb
--gray-900: #111827
```

### Responsive Design

```jsx
<div className="
  grid 
  grid-cols-1        /* Mobile: 1 column */
  md:grid-cols-2     /* Tablet: 2 columns */
  lg:grid-cols-3     /* Desktop: 3 columns */
  gap-4
">
```

### Component Composition

```jsx
// Use cn() utility for conditional classes
import { cn } from '@/lib/utils';

<Button className={cn(
  "base classes",
  variant === 'primary' && "primary classes",
  isDisabled && "opacity-50 cursor-not-allowed"
)} />
```

---

## ⚡ Performance Optimization

### Current Optimizations

1. **Code Splitting**
   ```typescript
   const CropGallery = lazy(() => import('./components/CropGallery'));
   ```

2. **Image Optimization**
   - Use WebP format
   - Lazy loading with `loading="lazy"`
   - Responsive images with `srcset`

3. **Bundle Optimization**
   - Tree-shaking unused code
   - Minification in production
   - Compression (gzip/brotli)

4. **Caching Strategy**
   - Static assets cached via CDN
   - API responses cached when appropriate
   - Service worker (future enhancement)

### Performance Metrics

- **First Contentful Paint**: < 1.5s
- **Time to Interactive**: < 3.0s
- **Lighthouse Score**: 90+

### Best Practices

```typescript
// ✅ Memoize expensive calculations
const expensiveValue = useMemo(() => computeValue(data), [data]);

// ✅ Debounce user inputs
const debouncedSearch = useDebounce(searchTerm, 300);

// ✅ Use React.memo for pure components
export const CropCard = React.memo(({ crop }) => {
  // ...
});
```

---

## 🌐 Browser Support

### Supported Browsers

| Browser | Version |
|---------|---------|
| Chrome | Last 2 versions|
| Firefox | Last 2 versions |
| Safari | Last 2 versions |
| Edge | Last 2 versions |
| Mobile Safari | iOS 12+ |
| Chrome Android | Last 2 versions |

### Polyfills

Vite automatically includes necessary polyfills for:
- ES6+ features
- Fetch API
- Promise
- Array methods

---

## 📦 Build & Deployment

### Production Build

```bash
pnpm build
```

**Output**: `dist/` directory

**Build Optimizations**:
- Minified JavaScript
- CSS purging (removes unused Tailwind classes)
- Asset optimization
- Source maps for debugging

### Deployment to Vercel

**Automatic Deployment**:
- Push to `main` branch triggers auto-deploy
- Preview deployments for all PRs

**Manual Deployment**:
```bash
vercel --prod
```

**Vercel Configuration**:
```json
{
  "framework": "vite",
  "buildCommand": "pnpm run build",
  "outputDirectory": "dist",
  "installCommand": "pnpm install",
  "env": {
    "VITE_API_BASE_URL": "https://crop-recomandation-system.onrender.com/api"
  }
}
```

---

## 🧪 Testing (Future Enhancement)

### Planned Testing Strategy

```bash
# Unit tests (Jest + React Testing Library)
pnpm test

# E2E tests (Playwright)
pnpm test:e2e

# Coverage report
pnpm test:coverage
```

### Example Test

```typescript
import { render, screen } from '@testing-library/react';
import { InputForm } from './InputForm';

test('renders input form with all fields', () => {
  render(<InputForm onSubmit={jest.fn()} />);
  expect(screen.getByLabelText(/Nitrogen/i)).toBeInTheDocument();
  expect(screen.getByLabelText(/Phosphorus/i)).toBeInTheDocument();
  // ... more assertions
});
```

---

## 🐛 Common Issues & Solutions

### Issue 1: API Not Connecting

**Symptom**: CORS errors or 404 on API calls

**Solution**:
1. Check `.env` file has correct `VITE_API_BASE_URL`
2. Ensure backend is running
3. Verify CORS settings on backend

### Issue 2: Slow First Load

**Symptom**: Long initial page load

**Solution**:
- HuggingFace model may be warming up (15-30s)
- Show appropriate loading message
- Consider implementing retry logic

### Issue 3: Build Errors

**Symptom**: `pnpm build` fails

**Solution**:
```bash
# Clear node_modules and reinstall
rm -rf node_modules pnpm-lock.yaml
pnpm install

# Clear Vite cache
rm -rf .vite
```

---

## 📚 Additional Resources

- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vitejs.dev/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Radix UI Documentation](https://www.radix-ui.com/primitives/docs/overview/introduction)

---

## 🤝 Contributing

### Development Workflow

1. Create feature branch
2. Make changes
3. Test locally
4. Submit PR with description
5. Wait for review

### Code Style

- Use TypeScript for type safety
- Follow React best practices
- Write self-documenting code
- Add comments for complex logic

---

## 📝 Changelog

### v1.0.0 (Current)
- ✅ Initial release
- ✅ Deployed to Vercel
- ✅ Integrated with backend API
- ✅ Responsive design
- ✅ 22 crop support

### Upcoming (v1.1.0)
- [ ] Dark mode
- [ ] Multi-language support
- [ ] PWA features
- [ ] Offline mode
- [ ] Unit tests

---

**Built with ❤️ using React, Vite, and Tailwind CSS**

*Last Updated: February 2026*