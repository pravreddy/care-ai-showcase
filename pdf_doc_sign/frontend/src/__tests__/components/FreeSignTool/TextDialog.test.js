import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import TextDialog from '../../../components/FreeSignTool/TextDialog';

const defaultProps = {
  open: true,
  onClose: jest.fn(),
  onConfirm: jest.fn(),
  mode: 'text',
};

describe('TextDialog — text mode', () => {
  beforeEach(() => jest.clearAllMocks());

  it('renders with correct title for text mode', () => {
    render(<TextDialog {...defaultProps} />);
    expect(screen.getByText('Add Text')).toBeInTheDocument();
  });

  it('renders text input', () => {
    render(<TextDialog {...defaultProps} />);
    expect(screen.getByTestId('text-input')).toBeInTheDocument();
  });

  it('Place on PDF button is disabled when input is empty', () => {
    render(<TextDialog {...defaultProps} />);
    expect(screen.getByTestId('text-confirm-btn')).toBeDisabled();
  });

  it('Place on PDF button enables when text is typed', () => {
    render(<TextDialog {...defaultProps} />);
    fireEvent.change(screen.getByTestId('text-input'), { target: { value: 'Approved' } });
    expect(screen.getByTestId('text-confirm-btn')).not.toBeDisabled();
  });

  it('shows live preview when text is entered', () => {
    render(<TextDialog {...defaultProps} />);
    fireEvent.change(screen.getByTestId('text-input'), { target: { value: 'Approved' } });
    expect(screen.getByTestId('text-preview')).toHaveTextContent('Approved');
  });

  it('does not show preview when input is empty', () => {
    render(<TextDialog {...defaultProps} />);
    expect(screen.queryByTestId('text-preview')).not.toBeInTheDocument();
  });

  it('calls onConfirm with text, fontSize, color when confirmed', () => {
    render(<TextDialog {...defaultProps} />);
    fireEvent.change(screen.getByTestId('text-input'), { target: { value: 'Hello' } });
    fireEvent.click(screen.getByTestId('text-confirm-btn'));
    expect(defaultProps.onConfirm).toHaveBeenCalledTimes(1);
    const [text, fontSize, color] = defaultProps.onConfirm.mock.calls[0];
    expect(text).toBe('Hello');
    expect(typeof fontSize).toBe('number');
    expect(color).toMatch(/^#/);
  });

  it('calls onClose when Cancel clicked', () => {
    render(<TextDialog {...defaultProps} />);
    fireEvent.click(screen.getByText('Cancel'));
    expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
  });

  it('submits on Enter key', () => {
    render(<TextDialog {...defaultProps} />);
    fireEvent.change(screen.getByTestId('text-input'), { target: { value: 'Enter test' } });
    fireEvent.keyDown(screen.getByTestId('text-input'), { key: 'Enter' });
    expect(defaultProps.onConfirm).toHaveBeenCalledTimes(1);
  });

  it('does not submit on Enter when input empty', () => {
    render(<TextDialog {...defaultProps} />);
    fireEvent.keyDown(screen.getByTestId('text-input'), { key: 'Enter' });
    expect(defaultProps.onConfirm).not.toHaveBeenCalled();
  });

  it('does not render when closed', () => {
    render(<TextDialog {...defaultProps} open={false} />);
    expect(screen.queryByText('Add Text')).not.toBeInTheDocument();
  });

  it('renders font size selector', () => {
    render(<TextDialog {...defaultProps} />);
    expect(screen.getByTestId('font-size-group')).toBeInTheDocument();
  });

  it('renders colour swatches', () => {
    render(<TextDialog {...defaultProps} />);
    expect(screen.getByTestId('color-#000000')).toBeInTheDocument();
    expect(screen.getByTestId('color-#1565c0')).toBeInTheDocument();
    expect(screen.getByTestId('color-#c62828')).toBeInTheDocument();
  });

  it('trims whitespace from text before confirming', () => {
    render(<TextDialog {...defaultProps} />);
    fireEvent.change(screen.getByTestId('text-input'), { target: { value: '  Approved  ' } });
    fireEvent.click(screen.getByTestId('text-confirm-btn'));
    expect(defaultProps.onConfirm.mock.calls[0][0]).toBe('Approved');
  });
});

describe('TextDialog — date mode', () => {
  beforeEach(() => jest.clearAllMocks());

  it('renders with correct title for date mode', () => {
    render(<TextDialog {...defaultProps} mode="date" />);
    expect(screen.getByText('Add Date')).toBeInTheDocument();
  });

  it('pre-fills input with today\'s date', () => {
    render(<TextDialog {...defaultProps} mode="date" />);
    const input = screen.getByTestId('text-input');
    // Should have some date value pre-filled (not empty)
    expect(input.value.length).toBeGreaterThan(0);
  });

  it('Place on PDF button is enabled immediately (date pre-filled)', () => {
    render(<TextDialog {...defaultProps} mode="date" />);
    expect(screen.getByTestId('text-confirm-btn')).not.toBeDisabled();
  });

  it('user can edit the pre-filled date', () => {
    render(<TextDialog {...defaultProps} mode="date" />);
    const input = screen.getByTestId('text-input');
    fireEvent.change(input, { target: { value: '01 Jan 2026' } });
    expect(input.value).toBe('01 Jan 2026');
  });

  it('shows preview of pre-filled date', () => {
    render(<TextDialog {...defaultProps} mode="date" />);
    expect(screen.getByTestId('text-preview')).toBeInTheDocument();
  });

  it('calls onConfirm with date text on confirm', () => {
    render(<TextDialog {...defaultProps} mode="date" />);
    fireEvent.click(screen.getByTestId('text-confirm-btn'));
    expect(defaultProps.onConfirm).toHaveBeenCalledTimes(1);
    const [text] = defaultProps.onConfirm.mock.calls[0];
    expect(text.length).toBeGreaterThan(0);
  });
});
