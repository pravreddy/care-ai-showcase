import { renderHook, act, waitFor } from '@testing-library/react';

jest.mock('../../services/api', () => ({
  signingService: {
    getDocument: jest.fn(),
    sign: jest.fn(),
  },
}));
jest.mock('../../utils/errorHandling', () => ({
  getSigningErrorMessage: jest.fn(() => 'error'),
}));

import useSigningLogic from '../../hooks/useSigningLogic';
import { signingService } from '../../services/api';

const fields = [
  { id: 's1', field_type: 'SIGNATURE', page: 1, required: true },
  { id: 't1', field_type: 'TEXT', page: 1, required: true },
];

function mockLoad() {
  signingService.getDocument.mockResolvedValue({
    document: { id: 'd1', title: 'Doc' },
    signer: { signer_name: 'Praveen', status: 'PENDING' },
    fields,
  });
}

async function loadedHook() {
  const utils = renderHook(() => useSigningLogic('tok'));
  await waitFor(() => expect(utils.result.current.loading).toBe(false));
  return utils;
}

describe('useSigningLogic', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockLoad();
  });

  it('loads document fields from the token', async () => {
    const { result } = await loadedHook();
    expect(result.current.fields).toHaveLength(2);
    expect(result.current.hasFields).toBe(true);
  });

  it('fillField sets a value and clearField removes it', async () => {
    const { result } = await loadedHook();
    act(() => result.current.fillField('t1', 'hello'));
    expect(result.current.filledFields.t1).toBe('hello');
    act(() => result.current.clearField('t1'));
    expect(result.current.filledFields.t1).toBeUndefined();
  });

  it('fillSignatureFields marks signature fields and clearSignature resets them', async () => {
    const { result } = await loadedHook();
    const blob = new Blob(['x'], { type: 'image/png' });
    act(() => result.current.fillSignatureFields(blob));
    expect(result.current.signatureBlob).toBe(blob);
    expect(result.current.filledFields.s1).toBe('signed');
    act(() => result.current.clearSignature());
    expect(result.current.signatureBlob).toBeNull();
    expect(result.current.filledFields.s1).toBeUndefined();
  });

  it('allFieldsFilled becomes true only when every field is filled', async () => {
    const { result } = await loadedHook();
    expect(result.current.allFieldsFilled).toBe(false);
    const blob = new Blob(['x'], { type: 'image/png' });
    act(() => {
      result.current.fillSignatureFields(blob);
      result.current.fillField('t1', 'v');
    });
    expect(result.current.allFieldsFilled).toBe(true);
  });
});
