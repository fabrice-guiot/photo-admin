import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ConnectorList from '../../src/components/connectors/ConnectorList';

describe('ConnectorList', () => {
  const mockConnectors = [
    {
      id: 1,
      name: 'S3 Connector',
      type: 's3',
      is_active: true,
      last_validated: '2025-01-01T10:00:00Z',
    },
    {
      id: 2,
      name: 'GCS Connector',
      type: 'gcs',
      is_active: false,
      last_validated: null,
    },
    {
      id: 3,
      name: 'SMB Connector',
      type: 'smb',
      is_active: true,
      last_validated: '2025-01-02T12:00:00Z',
    },
  ];

  const mockOnEdit = vi.fn();
  const mockOnDelete = vi.fn();
  const mockOnTest = vi.fn();

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('should render loading state', () => {
    render(
      <ConnectorList
        connectors={[]}
        loading={true}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onTest={mockOnTest}
      />
    );

    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('should render connector list', () => {
    render(
      <ConnectorList
        connectors={mockConnectors}
        loading={false}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onTest={mockOnTest}
      />
    );

    expect(screen.getByText('S3 Connector')).toBeInTheDocument();
    expect(screen.getByText('GCS Connector')).toBeInTheDocument();
    expect(screen.getByText('SMB Connector')).toBeInTheDocument();
  });

  it('should display connector types as chips', () => {
    render(
      <ConnectorList
        connectors={mockConnectors}
        loading={false}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onTest={mockOnTest}
      />
    );

    expect(screen.getByText('S3')).toBeInTheDocument();
    expect(screen.getByText('GCS')).toBeInTheDocument();
    expect(screen.getByText('SMB')).toBeInTheDocument();
  });

  it('should display active/inactive status', () => {
    render(
      <ConnectorList
        connectors={mockConnectors}
        loading={false}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onTest={mockOnTest}
      />
    );

    const activeChips = screen.getAllByText('Active');
    const inactiveChips = screen.getAllByText('Inactive');

    expect(activeChips).toHaveLength(2);
    expect(inactiveChips).toHaveLength(1);
  });

  it('should display last validated timestamp', () => {
    render(
      <ConnectorList
        connectors={mockConnectors}
        loading={false}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onTest={mockOnTest}
      />
    );

    // Should show "Never" for unvalidated connector
    expect(screen.getByText('Never')).toBeInTheDocument();
  });

  it('should show confirmation dialog when delete button is clicked', async () => {
    const user = userEvent.setup();

    render(
      <ConnectorList
        connectors={mockConnectors}
        loading={false}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onTest={mockOnTest}
      />
    );

    const deleteButtons = screen.getAllByRole('button', { name: /Delete Connector/i });

    // Click first delete button
    await user.click(deleteButtons[0]);

    // Confirmation dialog should appear
    await waitFor(() => {
      expect(screen.getByText(/Delete Connector/i)).toBeInTheDocument();
      expect(screen.getByText(/Are you sure you want to delete "S3 Connector"/i)).toBeInTheDocument();
    });

    // Should have Cancel and Delete buttons in dialog
    const dialog = screen.getByRole('dialog');
    expect(within(dialog).getByText('Cancel')).toBeInTheDocument();
    expect(within(dialog).getByText('Delete')).toBeInTheDocument();
  });

  it('should call onDelete when delete is confirmed', async () => {
    const user = userEvent.setup();
    mockOnDelete.mockResolvedValue(undefined);

    render(
      <ConnectorList
        connectors={mockConnectors}
        loading={false}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onTest={mockOnTest}
      />
    );

    const deleteButtons = screen.getAllByRole('button', { name: /Delete Connector/i });

    // Click first delete button
    await user.click(deleteButtons[0]);

    // Wait for dialog
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    // Click Delete in confirmation dialog
    const dialog = screen.getByRole('dialog');
    const confirmButton = within(dialog).getByText('Delete');
    await user.click(confirmButton);

    // onDelete should be called
    await waitFor(() => {
      expect(mockOnDelete).toHaveBeenCalledTimes(1);
      expect(mockOnDelete).toHaveBeenCalledWith(1); // Connector ID 1
    });
  });

  it('should close dialog when cancel is clicked', async () => {
    const user = userEvent.setup();

    render(
      <ConnectorList
        connectors={mockConnectors}
        loading={false}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onTest={mockOnTest}
      />
    );

    const deleteButtons = screen.getAllByRole('button', { name: /Delete Connector/i });

    // Click first delete button
    await user.click(deleteButtons[0]);

    // Wait for dialog
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    // Click Cancel
    const dialog = screen.getByRole('dialog');
    const cancelButton = within(dialog).getByText('Cancel');
    await user.click(cancelButton);

    // Dialog should close and onDelete should not be called
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });
    expect(mockOnDelete).not.toHaveBeenCalled();
  });
});
