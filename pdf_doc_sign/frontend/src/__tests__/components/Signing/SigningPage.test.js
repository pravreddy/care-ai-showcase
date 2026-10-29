import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

// Mock the heavy / external pieces so this test stays focused on SigningPage.
jest.mock('../../../components/Pdf/PdfViewer', () => () => <div data-testid="pdf-viewer" />);
jest.mock('../../../components/Signing/SignatureDialog', () => () => null);
jest.mock('../../../utils/signatureTabs', () => ({ __esModule: true, default: [] }));
jest.mock('../../../hooks/useSigningLogic');

import useSigningLogic from '../../../hooks/useSigningLogic';
import SigningPage from '../../../components/Signing/SigningPage';

const baseSigning = {
  loading: false,
  error: '',
  document: { title: 'Office Agreement' },
  signer: { signer_name: 'Praveen', signer_email: 'p@example.com' },
  signed: false,
  signatureBlob: null,
  signaturePreviewUrl: null,
  fields: [],
  filledFields: {},
  hasFields: false,
  allFieldsFilled: false,
  submitting: false,
  sigFieldCount: 0,
  filledSigCount: 0,
  fillField: jest.fn(),
  fillSignatureFields: jest.fn(),
  clearField: jest.fn(),
  clearSignature: jest.fn(),
  setError: jest.fn(),
  submitSignature: jest.fn(),
};

function renderPage(overrides = {}) {
  useSigningLogic.mockReturnValue({ ...baseSigning, ...overrides });
  return render(
    <MemoryRouter initialEntries={['/sign/tok']}>
      <SigningPage />
    </MemoryRouter>
  );
}

describe('SigningPage', () => {
  beforeEach(() => jest.clearAllMocks());

  it('shows the document title', () => {
    renderPage();
    expect(screen.getByText('Office Agreement')).toBeInTheDocument();
  });

  it('hides the sidebar Clear button when there is no signature', () => {
    renderPage({ signatureBlob: null });
    expect(screen.queryByText('Clear')).not.toBeInTheDocument();
  });

  it('shows the sidebar Clear button when a signature exists and clears it on click', () => {
    const clearSignature = jest.fn();
    renderPage({ signatureBlob: new Blob(['x']), clearSignature });
    fireEvent.click(screen.getByText('Clear'));
    expect(clearSignature).toHaveBeenCalled();
  });

  it('disables Done until all fields are filled', () => {
    renderPage({ allFieldsFilled: false });
    expect(screen.getByRole('button', { name: /Done/i })).toBeDisabled();
  });

  it('enables Done when all fields are filled', () => {
    renderPage({ allFieldsFilled: true });
    expect(screen.getByRole('button', { name: /Done/i })).not.toBeDisabled();
  });
});
