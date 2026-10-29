import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import FileUploadArea from '../../../components/FreeSignTool/FileUploadArea';

describe('FileUploadArea', () => {
  it('renders the upload prompt', () => {
    render(<FileUploadArea onFileSelect={jest.fn()} />);
    expect(screen.getByText(/Drop your file/i)).toBeInTheDocument();
    expect(screen.getByText(/PDF, DOC, DOCX, JPG, PNG/i)).toBeInTheDocument();
    expect(screen.getByText('Choose PDF File')).toBeInTheDocument();
  });

  it('calls onFileSelect when a file is chosen via input', () => {
    const onFileSelect = jest.fn();
    render(<FileUploadArea onFileSelect={onFileSelect} />);
    const input = screen.getByTestId('file-input');
    const file = new File(['dummy'], 'test.pdf', { type: 'application/pdf' });
    fireEvent.change(input, { target: { files: [file] } });
    expect(onFileSelect).toHaveBeenCalledWith(file);
  });

  it('calls onFileSelect on drag and drop', () => {
    const onFileSelect = jest.fn();
    render(<FileUploadArea onFileSelect={onFileSelect} />);
    const dropzone = screen.getByTestId('upload-area');
    const file = new File(['dummy'], 'dropped.pdf', { type: 'application/pdf' });
    fireEvent.drop(dropzone, { dataTransfer: { files: [file] } });
    expect(onFileSelect).toHaveBeenCalledWith(file);
  });

  it('does not call onFileSelect if no file is selected', () => {
    const onFileSelect = jest.fn();
    render(<FileUploadArea onFileSelect={onFileSelect} />);
    const input = screen.getByTestId('file-input');
    fireEvent.change(input, { target: { files: [] } });
    expect(onFileSelect).not.toHaveBeenCalled();
  });

  it('has a hidden file input accepting PDF and other formats', () => {
    render(<FileUploadArea onFileSelect={jest.fn()} />);
    const input = screen.getByTestId('file-input');
    const accept = input.getAttribute('accept');
    expect(accept).toContain('application/pdf');
    expect(accept).toContain('.docx');
    expect(accept).toContain('image/jpeg');
    expect(accept).toContain('image/png');
    expect(input.getAttribute('type')).toBe('file');
  });
});
