import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import PdfViewer from '../../../components/FreeSignTool/PdfViewer';

const defaultProps = {
  canvasRef: { current: document.createElement('canvas') },
  currentPage: 2,
  totalPages: 5,
  onPageChange: jest.fn(),
  onCanvasClick: jest.fn(),
  placingSignature: null,
  onAddSig: jest.fn(),
  onAddInitials: jest.fn(),
  onAddText: jest.fn(),
  onAddDate: jest.fn(),
  onAddCheckmark: jest.fn(),
  onUndo: jest.fn(),
  onDownload: jest.fn(),
  onClear: jest.fn(),
  hasItems: false,
  downloading: false,
  signerName: '',
  onSignerNameChange: jest.fn(),
  sigSize: 150,
  onSigSizeChange: jest.fn(),
  overlayItems: [],
  selectedItemId: null,
  onSelectItem: jest.fn(),
  onDeleteItem: jest.fn(),
  onMoveItem: jest.fn(),
  onResizeItem: jest.fn(),
};

describe('PdfViewer', () => {
  beforeEach(() => jest.clearAllMocks());

  it('renders page info correctly', () => {
    render(<PdfViewer {...defaultProps} />);
    expect(screen.getByTestId('page-info')).toHaveTextContent('Page 2 of 5');
  });

  it('navigates to previous page', () => {
    render(<PdfViewer {...defaultProps} />);
    fireEvent.click(screen.getByTestId('prev-page'));
    expect(defaultProps.onPageChange).toHaveBeenCalledWith(1);
  });

  it('navigates to next page', () => {
    render(<PdfViewer {...defaultProps} />);
    fireEvent.click(screen.getByTestId('next-page'));
    expect(defaultProps.onPageChange).toHaveBeenCalledWith(3);
  });

  it('disables prev button on first page', () => {
    render(<PdfViewer {...defaultProps} currentPage={1} />);
    expect(screen.getByTestId('prev-page')).toBeDisabled();
  });

  it('disables next button on last page', () => {
    render(<PdfViewer {...defaultProps} currentPage={5} />);
    expect(screen.getByTestId('next-page')).toBeDisabled();
  });

  it('renders all 5 tool buttons in sidebar', () => {
    render(<PdfViewer {...defaultProps} />);
    expect(screen.getByTestId('add-signature-btn')).toBeInTheDocument();
    expect(screen.getByTestId('add-initials-btn')).toBeInTheDocument();
    expect(screen.getByTestId('add-text-btn')).toBeInTheDocument();
    expect(screen.getByTestId('add-date-btn')).toBeInTheDocument();
    expect(screen.getByTestId('add-checkmark-btn')).toBeInTheDocument();
  });

  it('calls onAddSig when Sign clicked', () => {
    render(<PdfViewer {...defaultProps} />);
    fireEvent.click(screen.getByTestId('add-signature-btn'));
    expect(defaultProps.onAddSig).toHaveBeenCalledTimes(1);
  });

  it('calls onAddInitials when Initials clicked', () => {
    render(<PdfViewer {...defaultProps} />);
    fireEvent.click(screen.getByTestId('add-initials-btn'));
    expect(defaultProps.onAddInitials).toHaveBeenCalledTimes(1);
  });

  it('calls onAddText when Text clicked', () => {
    render(<PdfViewer {...defaultProps} />);
    fireEvent.click(screen.getByTestId('add-text-btn'));
    expect(defaultProps.onAddText).toHaveBeenCalledTimes(1);
  });

  it('calls onAddDate when Date clicked', () => {
    render(<PdfViewer {...defaultProps} />);
    fireEvent.click(screen.getByTestId('add-date-btn'));
    expect(defaultProps.onAddDate).toHaveBeenCalledTimes(1);
  });

  it('calls onAddCheckmark when Checkmark clicked', () => {
    render(<PdfViewer {...defaultProps} />);
    fireEvent.click(screen.getByTestId('add-checkmark-btn'));
    expect(defaultProps.onAddCheckmark).toHaveBeenCalledTimes(1);
  });

  it('Download button is disabled when no items', () => {
    render(<PdfViewer {...defaultProps} hasItems={false} />);
    expect(screen.getByTestId('download-btn')).toBeDisabled();
  });

  it('Download button is enabled when hasItems is true', () => {
    render(<PdfViewer {...defaultProps} hasItems={true} />);
    expect(screen.getByTestId('download-btn')).not.toBeDisabled();
  });

  it('calls onDownload when Download clicked with items', () => {
    render(<PdfViewer {...defaultProps} hasItems={true} />);
    fireEvent.click(screen.getByTestId('download-btn'));
    expect(defaultProps.onDownload).toHaveBeenCalledTimes(1);
  });

  it('calls onClear when Close clicked', () => {
    render(<PdfViewer {...defaultProps} />);
    fireEvent.click(screen.getByText('Close'));
    expect(defaultProps.onClear).toHaveBeenCalledTimes(1);
  });

  it('sets crosshair cursor when placingSignature is truthy', () => {
    render(<PdfViewer {...defaultProps} placingSignature="signature" />);
    expect(screen.getByTestId('pdf-canvas').style.cursor).toBe('crosshair');
  });

  it('sets default cursor when placingSignature is null', () => {
    render(<PdfViewer {...defaultProps} placingSignature={null} />);
    expect(screen.getByTestId('pdf-canvas').style.cursor).toBe('default');
  });

  it('shows placing banner when placingSignature is set', () => {
    render(<PdfViewer {...defaultProps} placingSignature="signature" />);
    expect(screen.getByTestId('placing-banner')).toBeInTheDocument();
  });

  it('does not show placing banner when placingSignature is null', () => {
    render(<PdfViewer {...defaultProps} placingSignature={null} />);
    expect(screen.queryByTestId('placing-banner')).not.toBeInTheDocument();
  });

  it('renders signer name input in sidebar', () => {
    render(<PdfViewer {...defaultProps} signerName="John Smith" />);
    expect(screen.getByTestId('signer-name-input')).toBeInTheDocument();
    expect(screen.getByTestId('signer-name-input').value).toBe('John Smith');
  });

  it('calls onSignerNameChange when name input changes', () => {
    render(<PdfViewer {...defaultProps} />);
    fireEvent.change(screen.getByTestId('signer-name-input'), {
      target: { value: 'Jane Doe' },
    });
    expect(defaultProps.onSignerNameChange).toHaveBeenCalled();
  });

  it('renders for single-page PDF', () => {
    render(<PdfViewer {...defaultProps} currentPage={1} totalPages={1} />);
    expect(screen.getByTestId('page-info')).toHaveTextContent('Page 1 of 1');
    expect(screen.getByTestId('prev-page')).toBeDisabled();
    expect(screen.getByTestId('next-page')).toBeDisabled();
  });
});
