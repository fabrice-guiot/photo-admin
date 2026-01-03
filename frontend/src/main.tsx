import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import { ThemeProvider, createTheme } from '@mui/material'
import './globals.css'

// MUI theme for legacy components (Collections/Connectors forms still use MUI internally)
// Note: Forms now use shadcn/ui but MUI ThemeProvider remains for compatibility
const theme = createTheme({
  palette: {
    mode: 'dark', // Match our dark theme
    primary: {
      main: '#3b82f6' // Match our --primary color
    },
    secondary: {
      main: '#6b7280' // Match our --secondary color
    }
  }
})

const rootElement = document.getElementById('root')

if (!rootElement) {
  throw new Error('Failed to find the root element')
}

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <ThemeProvider theme={theme}>
      <App />
    </ThemeProvider>
  </React.StrictMode>
)
