/**
 * usePdfLoader.js — Hook for loading, rendering, and navigating PDF pages.
 */
import { useState, useRef, useCallback } from 'react';
import * as pdfjsLib from 'pdfjs-dist';
import { PDFDocument } from 'pdf-lib';

pdfjsLib.GlobalWorkerOptions.workerSrc =
  `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;

export default function usePdfLoader() {
  const canvasRef = useRef(null);

  const [pdfDoc, setPdfDoc] = useState(null);
  const [pdfBytes, setPdfBytes] = useState(null);
  const [fileName, setFileName] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [converting, setConverting] = useState(false);
  const [error, setError] = useState('');

  const renderPage = useCallback(async (pdf, pageNum) => {
    const page = await pdf.getPage(pageNum);
    const viewport = page.getViewport({ scale: 1.5 });
    const canvas = canvasRef.current;
    if (!canvas) return;
    canvas.width = viewport.width;
    canvas.height = viewport.height;
    await page.render({ canvasContext: canvas.getContext('2d'), viewport }).promise;
  }, []);

  const loadPdfBytes = async (bytes, displayName) => {
    const pdf = await pdfjsLib.getDocument({ data: bytes.slice() }).promise;
    setPdfBytes(bytes);
    setFileName(displayName);
    setPdfDoc(pdf);
    setTotalPages(pdf.numPages);
    setCurrentPage(1);
    renderPage(pdf, 1);
    return pdf;
  };

  const handleFileSelect = async (file) => {
    if (!file) return;
    if (file.size > 20 * 1024 * 1024) { setError('File too large. Maximum 20MB.'); return; }
    setError('');

    const ext = file.name.split('.').pop().toLowerCase();
    const isPdf = file.type === 'application/pdf' || ext === 'pdf';
    const needsConversion = ['doc', 'docx', 'jpg', 'jpeg', 'png'].includes(ext);

    if (!isPdf && !needsConversion) {
      setError('Unsupported file type. Please upload PDF, DOC, DOCX, JPG or PNG.');
      return;
    }

    try {
      if (needsConversion) {
        setConverting(true);
        const formData = new FormData();
        formData.append('file', file);
        const resp = await fetch('/api/free-sign/convert/', { method: 'POST', body: formData });
        setConverting(false);
        if (!resp.ok) {
          const data = await resp.json().catch(() => ({}));
          setError(data.error || 'Conversion failed. Please try another file.');
          return;
        }
        const arrayBuffer = await resp.arrayBuffer();
        const bytes = new Uint8Array(arrayBuffer);
        const displayName = file.name.replace(/\.(doc|docx|jpg|jpeg|png)$/i, '.pdf');
        return await loadPdfBytes(bytes, displayName);
      } else {
        const arrayBuffer = await file.arrayBuffer();
        const bytes = new Uint8Array(arrayBuffer);
        try {
          await PDFDocument.load(bytes.slice(), { ignoreEncryption: true });
        } catch {
          setError('This PDF appears corrupted or invalid. Please try another file.');
          return;
        }
        return await loadPdfBytes(bytes, file.name);
      }
    } catch (e) {
      setConverting(false);
      setError(`Failed to open file: ${e?.message || 'Unknown error'}`);
    }
  };

  const goToPage = (n) => {
    if (!pdfDoc || n < 1 || n > totalPages) return;
    setCurrentPage(n);
    renderPage(pdfDoc, n);
  };

  const clearPdf = () => {
    setPdfDoc(null);
    setPdfBytes(null);
    setFileName('');
    setError('');
  };

  return {
    canvasRef, pdfDoc, pdfBytes, fileName, currentPage, totalPages,
    converting, error, setError,
    handleFileSelect, goToPage, clearPdf,
  };
}
