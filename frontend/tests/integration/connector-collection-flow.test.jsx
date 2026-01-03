import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import ConnectorsPage from '../../src/pages/ConnectorsPage';
import CollectionsPage from '../../src/pages/CollectionsPage';
import { HeaderStatsProvider } from '../../src/contexts/HeaderStatsContext';
import { resetMockData } from '../mocks/handlers';

// Helper to render with router and required providers
const renderWithProviders = (component) => {
  return render(
    <BrowserRouter>
      <HeaderStatsProvider>
        {component}
      </HeaderStatsProvider>
    </BrowserRouter>
  );
};

describe('Connector-Collection Integration', () => {
  beforeEach(() => {
    resetMockData();
  });

  it('should render ConnectorsPage with initial data', async () => {
    renderWithProviders(<ConnectorsPage />);

    // Wait for connectors to load
    await waitFor(() => {
      expect(screen.getByText('Test S3 Connector')).toBeInTheDocument();
    });

    // Should have "New Connector" button
    expect(screen.getByText(/New Connector/i)).toBeInTheDocument();
  });

  it('should render CollectionsPage with initial data', async () => {
    renderWithProviders(<CollectionsPage />);

    // Wait for collections to load
    await waitFor(() => {
      expect(screen.getByText('Test Collection')).toBeInTheDocument();
    });

    // Should have "New Collection" button
    expect(screen.getByText(/New Collection/i)).toBeInTheDocument();
  });
});
