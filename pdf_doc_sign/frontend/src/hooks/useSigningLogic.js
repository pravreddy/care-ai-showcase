/**
 * useSigningLogic.js — Custom hook for signing page data and state management.
 *
 * Handles:
 *   - Loading document, signer info, and fields from the signing token
 *   - Tracking which fields have been filled
 *   - Signature blob management
 *   - Submitting the final signature
 *
 * Usage:
 *   const signing = useSigningLogic(token);
 *   signing.fillField(fieldId, value);
 *   signing.setSignatureBlob(blob);
 *   await signing.submitSignature();
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { signingService } from '../services/api';
import { getSigningErrorMessage } from '../utils/errorHandling';

export default function useSigningLogic(token) {
  const [document, setDocument] = useState(null);
  const [signer, setSigner] = useState(null);
  const [fields, setFields] = useState([]);
  const [filledFields, setFilledFields] = useState({});
  const [signed, setSigned] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [signatureBlob, setSignatureBlob] = useState(null);
  const [signaturePreviewUrl, setSignaturePreviewUrl] = useState(null);
  const loadedRef = useRef(false);

  // Load document data
  useEffect(() => {
    if (loadedRef.current) return;
    loadedRef.current = true;

    const loadData = async () => {
      try {
        const data = await signingService.getDocument(token);
        setDocument(data.document);
        setSigner(data.signer);
        setFields(data.fields || []);
        if (data.signer.status === 'SIGNED') setSigned(true);
      } catch (err) {
        setError(getSigningErrorMessage(err));
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [token]);

  // Auto-fill NAME and DATE fields when signer data arrives
  useEffect(() => {
    if (!signer || !fields.length) return;
    const auto = {};
    fields.forEach(f => {
      if (f.field_type === 'NAME') auto[f.id] = signer.signer_name;
      if (f.field_type === 'DATE') auto[f.id] = new Date().toLocaleDateString();
    });
    if (Object.keys(auto).length > 0) {
      setFilledFields(prev => ({ ...prev, ...auto }));
    }
  }, [signer, fields]);

  // Fill a single field
  const fillField = useCallback((fieldId, value) => {
    setFilledFields(prev => ({ ...prev, [fieldId]: value }));
  }, []);

  // Fill all signature/initials fields at once (when a signature is drawn)
  const fillSignatureFields = useCallback((blob) => {
    setSignatureBlob(blob);
    const url = URL.createObjectURL(blob);
    setSignaturePreviewUrl(url);

    setFilledFields(prev => {
      const updated = { ...prev };
      fields.forEach(f => {
        if (f.field_type === 'SIGNATURE' || f.field_type === 'INITIALS') {
          updated[f.id] = 'signed';
        }
      });
      return updated;
    });
  }, [fields]);

  // Clear a single filled field (text / name / date / checkbox) so the signer
  // can cancel/undo a value they entered.
  const clearField = useCallback((fieldId) => {
    setFilledFields(prev => {
      const updated = { ...prev };
      delete updated[fieldId];
      return updated;
    });
  }, []);

  // Remove the signature entirely: drop the blob/preview and un-mark every
  // signature/initials field, so the signer can start their signature over.
  // (One signature covers all signature fields, so clearing is all-or-nothing.)
  const clearSignature = useCallback(() => {
    setSignatureBlob(null);
    setSignaturePreviewUrl(prev => {
      if (prev) URL.revokeObjectURL(prev);
      return null;
    });
    setFilledFields(prev => {
      const updated = { ...prev };
      fields.forEach(f => {
        if (f.field_type === 'SIGNATURE' || f.field_type === 'INITIALS') {
          delete updated[f.id];
        }
      });
      return updated;
    });
  }, [fields]);

  // Check if all required fields are filled.
  // CHECKBOX has special rules:
  //   - required + must be ticked (filledValue === 'true')
  //   - optional   + any value (including untouched) is fine
  // Everything else: truthy filledValue counts as filled.
  const hasFields = fields.length > 0;
  const isFieldFilled = (f) => {
    const v = filledFields[f.id];
    if (f.field_type === 'CHECKBOX') {
      if (f.required === false) return true;
      return String(v || '').toLowerCase() === 'true';
    }
    return !!v;
  };
  const allFieldsFilled = hasFields
    ? fields.every(isFieldFilled)
    : !!signatureBlob;

  // Signing progress
  const sigFieldCount = fields.filter(f => f.field_type === 'SIGNATURE' || f.field_type === 'INITIALS').length;
  const filledSigCount = fields.filter(f => (f.field_type === 'SIGNATURE' || f.field_type === 'INITIALS') && filledFields[f.id]).length;

  // Submit signature to backend
  const submitSignature = useCallback(async () => {
    if (!signatureBlob) {
      setError(hasFields
        ? 'Please click on the "Sign here" fields in the document to add your signature.'
        : 'Please create your signature first.'
      );
      return false;
    }

    setSubmitting(true);
    setError('');
    try {
      const formData = new FormData();
      formData.append('signature', signatureBlob, 'signature.png');

      // Include any text / name / date / checkbox values the signer typed,
      // overrode, or toggled. The backend will use these in preference to
      // its auto-fill defaults for NAME/DATE, will write TEXT fields
      // verbatim, and will persist CHECKBOX state as 'true'/'false'.
      const textValues = {};
      for (const [fieldId, value] of Object.entries(filledFields)) {
        if (value === 'signed' || value == null) continue;
        const f = fields.find(x => x.id === fieldId);
        if (f && !['SIGNATURE', 'INITIALS'].includes(f.field_type)) {
          textValues[fieldId] = String(value);
        }
      }
      if (Object.keys(textValues).length > 0) {
        formData.append('filled_values', JSON.stringify(textValues));
      }

      await signingService.sign(token, formData);
      setSigned(true);
      return true;
    } catch (err) {
      setError(getSigningErrorMessage(err));
      return false;
    } finally {
      setSubmitting(false);
    }
  }, [signatureBlob, hasFields, token, filledFields, fields]);

  return {
    document,
    signer,
    fields,
    filledFields,
    signatureBlob,
    signaturePreviewUrl,
    loading,
    submitting,
    signed,
    error,
    hasFields,
    allFieldsFilled,
    sigFieldCount,
    filledSigCount,
    fillField,
    fillSignatureFields,
    clearField,
    clearSignature,
    setSignatureBlob,
    setError,
    submitSignature,
  };
}
