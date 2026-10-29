/**
 * PdfViewer.js — Renders a PDF using pdf.js, page by page as canvas elements.
 *
 * Props:
 *   pdfUrl        - URL to the PDF file (string, required)
 *   authToken     - JWT token for authenticated requests (optional; omit for public)
 *   scale         - Zoom level (default 1.2)
 *   onPageCount   - Callback(pageCount) when PDF is loaded
 *   renderOverlay - (pageNumber, pageWidth, pageHeight) => ReactNode — overlay per page
 *   onPageClick   - (pageNumber, xPercent, yPercent, event) => void — click handler
 *   onPageContextMenu - (pageNumber, xPercent, yPercent, event) => void — right-click
 */
import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Box, Typography, CircularProgress, IconButton } from '@mui/material';
import ZoomInIcon from '@mui/icons-material/ZoomIn';
import ZoomOutIcon from '@mui/icons-material/ZoomOut';

// pdf.js setup
import * as pdfjsLib from 'pdfjs-dist';

// Use CDN worker — .mjs for pdf.js v4+
pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.mjs`;

export default function PdfViewer({
  pdfUrl,
  authToken,
  scale: initialScale = 1.2,
  onPageCount,
  renderOverlay,
  onPageClick,
  onPageContextMenu,
}) {
  const [pdfDoc, setPdfDoc] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [scale, setScale] = useState(initialScale);
  const [pageCount, setPageCount] = useState(0);
  const [pageDims, setPageDims] = useState({});
  const canvasRefs = useRef({});
  const renderTasksRef = useRef({});
  const onPageCountRef = useRef(onPageCount);
  onPageCountRef.current = onPageCount;

  // Load the PDF document
  useEffect(() => {
    if (!pdfUrl) return;

    let cancelled = false;
    setLoading(true);
    setError('');
    setPdfDoc(null);
    setPageDims({});

    const loadingTask = pdfjsLib.getDocument({
      url: pdfUrl,
      ...(authToken ? {
        httpHeaders: { Authorization: `Bearer ${authToken}` },
        withCredentials: false,
      } : {}),
    });

    loadingTask.promise
      .then((doc) => {
        if (cancelled) return;
        setPdfDoc(doc);
        setPageCount(doc.numPages);
        if (onPageCountRef.current) onPageCountRef.current(doc.numPages);
        setLoading(false);
      })
      .catch((err) => {
        if (cancelled) return;
        console.error('PDF load error:', err);
        setError('Failed to load PDF. Please try again.');
        setLoading(false);
      });

    return () => {
      cancelled = true;
      loadingTask.destroy?.();
    };
  }, [pdfUrl, authToken]);

  // Render a single page to its canvas
  const renderPage = useCallback(async (pageNum) => {
    if (!pdfDoc) return;

    if (renderTasksRef.current[pageNum]) {
      renderTasksRef.current[pageNum].cancel();
    }

    try {
      const page = await pdfDoc.getPage(pageNum);
      const viewport = page.getViewport({ scale });
      const canvas = canvasRefs.current[pageNum];
      if (!canvas) return;

      canvas.width = viewport.width;
      canvas.height = viewport.height;

      const ctx = canvas.getContext('2d');
      const renderTask = page.render({ canvasContext: ctx, viewport });
      renderTasksRef.current[pageNum] = renderTask;

      await renderTask.promise;

      setPageDims(prev => ({
        ...prev,
        [pageNum]: { width: canvas.offsetWidth, height: canvas.offsetHeight },
      }));
    } catch (err) {
      if (err.name !== 'RenderingCancelledException') {
        console.error(`Failed to render page ${pageNum}:`, err);
      }
    }
  }, [pdfDoc, scale]);

  // Re-render all pages when scale or pdfDoc changes
  useEffect(() => {
    if (!pdfDoc) return;
    for (let i = 1; i <= pageCount; i++) {
      renderPage(i);
    }
  }, [pdfDoc, scale, pageCount, renderPage]);

  const handleZoomIn = () => setScale((s) => Math.min(s + 0.2, 3.0));
  const handleZoomOut = () => setScale((s) => Math.max(s - 0.2, 0.5));

  const getPageCoords = (event, pageNum) => {
    const canvas = canvasRefs.current[pageNum];
    if (!canvas) return { xPercent: 0, yPercent: 0 };
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    return {
      xPercent: (x / rect.width) * 100,
      yPercent: (y / rect.height) * 100,
    };
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 300, bgcolor: '#e0e0e0', borderRadius: 1 }}>
        <Box sx={{ textAlign: 'center' }}>
          <CircularProgress size={40} />
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>Loading PDF...</Typography>
        </Box>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 200, bgcolor: '#ffebee', borderRadius: 1 }}>
        <Typography color="error">{error}</Typography>
      </Box>
    );
  }

  return (
    <Box>
      {/* Zoom controls */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 1, gap: 1 }}>
        <IconButton size="small" onClick={handleZoomOut} disabled={scale <= 0.5}>
          <ZoomOutIcon />
        </IconButton>
        <Typography variant="body2" color="text.secondary">{Math.round(scale * 100)}%</Typography>
        <IconButton size="small" onClick={handleZoomIn} disabled={scale >= 3.0}>
          <ZoomInIcon />
        </IconButton>
        <Typography variant="body2" color="text.secondary" sx={{ ml: 2 }}>
          {pageCount} page{pageCount !== 1 ? 's' : ''}
        </Typography>
      </Box>

      {/* PDF pages container */}
      <Box
        sx={{
          maxHeight: '70vh',
          overflowY: 'auto',
          bgcolor: '#525659',
          borderRadius: 1,
          p: 2,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        {Array.from({ length: pageCount }, (_, i) => i + 1).map((pageNum) => (
          <Box
            key={pageNum}
            sx={{ position: 'relative', mb: 2 }}
          >
            <Typography
              variant="caption"
              sx={{
                display: 'block', textAlign: 'center',
                color: '#aaa', mb: 0.5,
              }}
            >
              Page {pageNum} of {pageCount}
            </Typography>

            <Box sx={{ position: 'relative', display: 'inline-block', boxShadow: '0 2px 8px rgba(0,0,0,0.3)' }}>
              <canvas
                ref={(el) => { canvasRefs.current[pageNum] = el; }}
                style={{
                  display: 'block',
                  cursor: (onPageClick || onPageContextMenu) ? 'crosshair' : 'default',
                }}
                onClick={(e) => {
                  if (onPageClick) {
                    const { xPercent, yPercent } = getPageCoords(e, pageNum);
                    onPageClick(pageNum, xPercent, yPercent, e);
                  }
                }}
                onContextMenu={(e) => {
                  if (onPageContextMenu) {
                    e.preventDefault();
                    const { xPercent, yPercent } = getPageCoords(e, pageNum);
                    onPageContextMenu(pageNum, xPercent, yPercent, e);
                  }
                }}
              />

              {renderOverlay && (
                <Box
                  sx={{
                    position: 'absolute',
                    top: 0, left: 0, right: 0, bottom: 0,
                    pointerEvents: 'none',
                  }}
                >
                  {renderOverlay(
                    pageNum,
                    canvasRefs.current[pageNum]?.offsetWidth || 0,
                    canvasRefs.current[pageNum]?.offsetHeight || 0,
                  )}
                </Box>
              )}
            </Box>
          </Box>
        ))}
      </Box>
    </Box>
  );
}
