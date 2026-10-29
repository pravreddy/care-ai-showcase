import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import SignatureDialog from '../../../components/FreeSignTool/SignatureDialog';

const defaultProps = {
  open: true,
  onClose: jest.fn(),
  onConfirm: jest.fn(),
  sigCanvasRef: { current: document.createElement('canvas') },
  sigTab: 0,
  setSigTab: jest.fn(),
  typedText: '',
  setTypedText: jest.fn(),
  sigImageUrl: null,
  onSigUpload: jest.fn(),
  isDrawing: false,
  setIsDrawing: jest.fn(),
  sigColor: '#1a1a1a',
  setSigColor: jest.fn(),
  selectedFont: '"Brush Script MT", cursive',
  setSelectedFont: jest.fn(),
};

describe('SignatureDialog', () => {
  beforeEach(() => jest.clearAllMocks());

  it('renders when open', () => {
    render(<SignatureDialog {...defaultProps} />);
    expect(screen.getByText('Create Your Signature')).toBeInTheDocument();
  });

  it('does not render when closed', () => {
    render(<SignatureDialog {...defaultProps} open={false} />);
    expect(screen.queryByText('Create Your Signature')).not.toBeInTheDocument();
  });

  it('renders all 3 tabs', () => {
    render(<SignatureDialog {...defaultProps} />);
    expect(screen.getByTestId('tab-draw')).toBeInTheDocument();
    expect(screen.getByTestId('tab-type')).toBeInTheDocument();
    expect(screen.getByTestId('tab-upload')).toBeInTheDocument();
  });

  it('shows draw canvas on Draw tab', () => {
    render(<SignatureDialog {...defaultProps} sigTab={0} />);
    expect(screen.getByTestId('sig-canvas')).toBeInTheDocument();
  });

  it('shows text input on Type tab', () => {
    render(<SignatureDialog {...defaultProps} sigTab={1} />);
    expect(screen.getByTestId('sig-type-input')).toBeInTheDocument();
  });

  it('shows font previews on Type tab when typedText is set', () => {
    render(<SignatureDialog {...defaultProps} sigTab={1} typedText="Praveen" />);
    // Font grid shows the typed text in each font preview
    expect(screen.getByTestId('sig-type-input').value).toBe('Praveen');
    expect(screen.getByTestId('sig-font-grid')).toBeInTheDocument();
  });

  it('shows font grid even when typedText is empty', () => {
    render(<SignatureDialog {...defaultProps} sigTab={1} typedText="" />);
    expect(screen.getByTestId('sig-font-grid')).toBeInTheDocument();
  });

  it('shows upload input on Upload tab', () => {
    render(<SignatureDialog {...defaultProps} sigTab={2} />);
    expect(screen.getByTestId('sig-upload-input')).toBeInTheDocument();
  });

  it('shows uploaded image preview when sigImageUrl is set', () => {
    render(<SignatureDialog {...defaultProps} sigTab={2} sigImageUrl="data:image/png;base64,abc" />);
    expect(screen.getByTestId('sig-upload-preview')).toBeInTheDocument();
  });

  it('calls onClose when Cancel is clicked', () => {
    render(<SignatureDialog {...defaultProps} />);
    fireEvent.click(screen.getByText('Cancel'));
    expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
  });

  it('calls onConfirm when Use This Signature is clicked', () => {
    render(<SignatureDialog {...defaultProps} />);
    fireEvent.click(screen.getByTestId('sig-confirm-btn'));
    expect(defaultProps.onConfirm).toHaveBeenCalledTimes(1);
  });

  it('does not show draw canvas on Type tab', () => {
    render(<SignatureDialog {...defaultProps} sigTab={1} />);
    expect(screen.queryByTestId('sig-canvas')).not.toBeInTheDocument();
  });

  it('does not show type input on Draw tab', () => {
    render(<SignatureDialog {...defaultProps} sigTab={0} />);
    expect(screen.queryByTestId('sig-type-input')).not.toBeInTheDocument();
  });

  it('renders colour picker on Draw tab', () => {
    render(<SignatureDialog {...defaultProps} sigTab={0} />);
    expect(screen.getByTestId('sig-color-picker')).toBeInTheDocument();
  });

  it('renders colour picker on Type tab', () => {
    render(<SignatureDialog {...defaultProps} sigTab={1} />);
    expect(screen.getByTestId('sig-color-picker')).toBeInTheDocument();
  });

  it('does not render colour picker on Upload tab', () => {
    render(<SignatureDialog {...defaultProps} sigTab={2} />);
    expect(screen.queryByTestId('sig-color-picker')).not.toBeInTheDocument();
  });
});
