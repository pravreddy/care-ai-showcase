/**
 * useDownload.js — Hook for building and downloading the signed PDF.
 */
import { useState } from 'react';
import { PDFDocument } from 'pdf-lib';
import { dataUrlToBytes } from './signatureHelpers';

export default function useDownload(pdfBytes, items, canvasRef, fileName, setError) {
  const [downloading, setDownloading] = useState(false);
  const [downloadDone, setDownloadDone] = useState(false);
  const [signedBlobUrl, setSignedBlobUrl] = useState(null);

  const downloadSignedPdf = async () => {
    if (!pdfBytes) { setError('No PDF loaded.'); return; }
    if (items.length === 0) { setError('Please add at least one signature before downloading.'); return; }
    setError('');
    setDownloading(true);
    try {
      const pdfDocLib = await PDFDocument.load(pdfBytes.slice(), { ignoreEncryption: true });
      const pages = pdfDocLib.getPages();
      const canvas = canvasRef.current;
      for (const item of items) {
        const page = pages[item.page - 1];
        if (!page) continue;
        try {
          const imgBytes = dataUrlToBytes(item.dataUrl);
          const isJpeg = item.dataUrl.startsWith('data:image/jpeg') || item.dataUrl.startsWith('data:image/jpg');
          const embedded = isJpeg ? await pdfDocLib.embedJpg(imgBytes) : await pdfDocLib.embedPng(imgBytes);
          const { width: pageW, height: pageH } = page.getSize();
          const sx = pageW / canvas.width;
          const sy = pageH / canvas.height;
          page.drawImage(embedded, {
            x: (item.x - item.width / 2) * sx,
            y: pageH - (item.y + item.height / 2) * sy,
            width: item.width * sx,
            height: item.height * sy,
          });
        } catch (itemErr) {
          console.warn(`Skipped item ${item.id}:`, itemErr?.message);
        }
      }
      const signedBytes = await pdfDocLib.save();
      const blob = new Blob([signedBytes], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      setSignedBlobUrl(url);
      setDownloadDone(true);
      const a = document.createElement('a');
      a.href = url;
      a.download = `signed_${fileName || 'document.pdf'}`;
      a.style.display = 'none';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    } catch (err) {
      const msg = (err?.message || '').toLowerCase();
      if (msg.includes('header') || msg.includes('parse')) {
        setError('PDF parsing failed. Please try re-uploading the file.');
      } else if (msg.includes('encrypt') || msg.includes('password')) {
        setError('This PDF is password-protected. Please use an unlocked version.');
      } else {
        setError(`Download failed: ${err?.message || 'Unknown error'}`);
      }
    } finally {
      setDownloading(false);
    }
  };

  const resetDownload = () => {
    setDownloadDone(false);
    if (signedBlobUrl) { URL.revokeObjectURL(signedBlobUrl); setSignedBlobUrl(null); }
  };

  return { downloading, downloadDone, signedBlobUrl, downloadSignedPdf, resetDownload };
}
