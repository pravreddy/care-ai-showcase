import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import SignatureBanner from '../../../components/FreeSignTool/SignatureBanner';

describe('SignatureBanner', () => {
  const defaultProps = {
    sigSize: 150,
    setSigSize: jest.fn(),
    onCancel: jest.fn(),
  };

  beforeEach(() => jest.clearAllMocks());

  it('renders the placing instructions', () => {
    render(<SignatureBanner {...defaultProps} />);
    expect(screen.getByTestId('placing-banner')).toBeInTheDocument();
    expect(screen.getByText(/Click on the PDF where you want to place your signature/)).toBeInTheDocument();
  });

  it('renders the size slider', () => {
    render(<SignatureBanner {...defaultProps} />);
    expect(screen.getByTestId('size-slider')).toBeInTheDocument();
  });

  it('calls onCancel when Cancel is clicked', () => {
    render(<SignatureBanner {...defaultProps} />);
    fireEvent.click(screen.getByText('Cancel'));
    expect(defaultProps.onCancel).toHaveBeenCalledTimes(1);
  });
});
