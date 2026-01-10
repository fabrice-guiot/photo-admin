import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { render } from '../utils/test-utils'
import ExternalIdBadge from '@/components/ExternalIdBadge'

// Mock the clipboard API
const mockWriteText = vi.fn()

describe('ExternalIdBadge', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockWriteText.mockResolvedValue(undefined)
    // Mock navigator.clipboard
    Object.defineProperty(navigator, 'clipboard', {
      value: {
        writeText: mockWriteText,
      },
      writable: true,
      configurable: true,
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should render full external ID', () => {
    render(<ExternalIdBadge externalId="col_01hgw2bbg00000000000000001" />)

    expect(screen.getByText('col_01hgw2bbg00000000000000001')).toBeInTheDocument()
  })

  it('should render label when showLabel is true', () => {
    render(
      <ExternalIdBadge
        externalId="col_01hgw2bbg00000000000000001"
        showLabel
        label="Collection ID"
      />
    )

    expect(screen.getByText('Collection ID:')).toBeInTheDocument()
  })

  it('should not render label by default', () => {
    render(<ExternalIdBadge externalId="col_01hgw2bbg00000000000000001" />)

    expect(screen.queryByText('ID:')).not.toBeInTheDocument()
  })

  it('should copy to clipboard on click', async () => {
    const user = userEvent.setup()
    render(<ExternalIdBadge externalId="col_01hgw2bbg00000000000000001" />)

    const button = screen.getByRole('button')
    await user.click(button)

    // Wait for the copy success indicator (check icon appears when copied)
    await waitFor(() => {
      const checkIcon = button.querySelector('.lucide-check')
      expect(checkIcon).toBeInTheDocument()
    })
  })

  it('should have accessible label', () => {
    render(<ExternalIdBadge externalId="col_01hgw2bbg00000000000000001" />)

    const button = screen.getByRole('button')
    expect(button).toHaveAttribute(
      'aria-label',
      'Copy external ID: col_01hgw2bbg00000000000000001'
    )
  })

  it('should show copy icon by default', () => {
    render(<ExternalIdBadge externalId="col_01hgw2bbg00000000000000001" />)

    const button = screen.getByRole('button')
    expect(button.querySelector('svg')).toBeInTheDocument()
  })

  it('should apply custom className', () => {
    render(
      <ExternalIdBadge
        externalId="col_01hgw2bbg00000000000000001"
        className="custom-class"
      />
    )

    const button = screen.getByRole('button')
    expect(button).toHaveClass('custom-class')
  })

  it('should handle different entity prefixes', () => {
    const { rerender } = render(<ExternalIdBadge externalId="col_01hgw2bbg00000000000000001" />)
    expect(screen.getByText('col_01hgw2bbg00000000000000001')).toBeInTheDocument()

    rerender(<ExternalIdBadge externalId="con_01hgw2bbg00000000000000001" />)
    expect(screen.getByText('con_01hgw2bbg00000000000000001')).toBeInTheDocument()

    rerender(<ExternalIdBadge externalId="pip_01hgw2bbg00000000000000001" />)
    expect(screen.getByText('pip_01hgw2bbg00000000000000001')).toBeInTheDocument()

    rerender(<ExternalIdBadge externalId="res_01hgw2bbg00000000000000001" />)
    expect(screen.getByText('res_01hgw2bbg00000000000000001')).toBeInTheDocument()
  })
})
