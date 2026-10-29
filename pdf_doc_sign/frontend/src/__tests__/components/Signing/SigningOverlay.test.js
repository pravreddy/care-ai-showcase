import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import SigningOverlay from '../../../components/Signing/SigningOverlay';

const sigField = {
  id: 'f1', field_type: 'SIGNATURE', page: 1,
  x_percent: 10, y_percent: 10, width_percent: 20, height_percent: 6, label: '',
};
const textField = {
  id: 'f2', field_type: 'TEXT', page: 1,
  x_percent: 10, y_percent: 30, width_percent: 20, height_percent: 6, label: 'Company',
};
const checkboxField = {
  id: 'f3', field_type: 'CHECKBOX', page: 1,
  x_percent: 10, y_percent: 50, width_percent: 4, height_percent: 3, label: '',
};

const baseProps = {
  pageNum: 1,
  pageWidth: 600,
  pageHeight: 800,
  signaturePreviewUrl: 'blob:mock',
  onFieldClick: jest.fn(),
  onFieldClear: jest.fn(),
};

describe('SigningOverlay', () => {
  beforeEach(() => jest.clearAllMocks());

  it('renders nothing when no fields are on this page', () => {
    const { container } = render(
      <SigningOverlay {...baseProps} pageNum={2} fields={[sigField]} filledFields={{}} />
    );
    expect(container).toBeEmptyDOMElement();
  });

  it('shows an unfilled field label and calls onFieldClick when clicked', () => {
    render(<SigningOverlay {...baseProps} fields={[textField]} filledFields={{}} />);
    fireEvent.click(screen.getByText('Company'));
    expect(baseProps.onFieldClick).toHaveBeenCalledWith(textField);
  });

  it('does not show a clear button on an unfilled field', () => {
    render(<SigningOverlay {...baseProps} fields={[textField]} filledFields={{}} />);
    expect(screen.queryByTitle('Clear')).not.toBeInTheDocument();
  });

  it('renders the signature preview image when a signature field is filled', () => {
    render(<SigningOverlay {...baseProps} fields={[sigField]} filledFields={{ f1: 'signed' }} />);
    const img = screen.getByAltText('Signature');
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute('src', 'blob:mock');
  });

  it('shows a clear button on a filled field and clears it without triggering field click', () => {
    render(<SigningOverlay {...baseProps} fields={[textField]} filledFields={{ f2: 'Acme Ltd' }} />);
    expect(screen.getByText('Acme Ltd')).toBeInTheDocument();
    fireEvent.click(screen.getByTitle('Clear'));
    expect(baseProps.onFieldClear).toHaveBeenCalledWith(textField);
    // stopPropagation means the field's own click handler must NOT fire
    expect(baseProps.onFieldClick).not.toHaveBeenCalled();
  });

  it('does not show a clear button on a checkbox field', () => {
    render(<SigningOverlay {...baseProps} fields={[checkboxField]} filledFields={{ f3: 'true' }} />);
    expect(screen.queryByTitle('Clear')).not.toBeInTheDocument();
  });
});
