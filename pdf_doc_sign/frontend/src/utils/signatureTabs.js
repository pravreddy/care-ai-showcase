/**
 * signatureTabs.js — Data-driven tab configuration for signature input methods.
 *
 * Used by SignatureDialog and SigningPage fallback section.
 * To add a new signature method, just add an entry here — both
 * the dialog and fallback section will pick it up automatically.
 */
import React from 'react';
import DrawIcon from '@mui/icons-material/Draw';
import TextFieldsIcon from '@mui/icons-material/TextFields';
import FileUploadIcon from '@mui/icons-material/FileUpload';
import SignatureCanvas from '../components/Signing/SignatureCanvas';
import TypedSignature from '../components/Signing/TypedSignature';
import UploadSignature from '../components/Signing/UploadSignature';

/**
 * Each tab entry:
 *   label     - tab label text
 *   icon      - MUI icon element
 *   component - React component to render
 *   needsName - if true, passes signerName prop to the component
 */
const SIGNATURE_TABS = [
  { label: 'Draw',   icon: <DrawIcon />,       component: SignatureCanvas, needsName: false },
  { label: 'Type',   icon: <TextFieldsIcon />,  component: TypedSignature,  needsName: true  },
  { label: 'Upload', icon: <FileUploadIcon />,  component: UploadSignature, needsName: false },
];

export default SIGNATURE_TABS;
