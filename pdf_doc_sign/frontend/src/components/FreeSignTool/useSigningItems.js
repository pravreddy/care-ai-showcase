/**
 * useSigningItems.js — Hook for managing placed signature/text/checkmark items.
 */
import { useState, useCallback } from 'react';

let itemIdCounter = 0;

export default function useSigningItems(canvasRef, currentPage, sigSize) {
  const [items, setItems] = useState([]);
  const [selectedItemId, setSelectedItemId] = useState(null);
  const [placing, setPlacing] = useState(null);

  const currentPageItems = items.filter(i => i.page === currentPage);

  const handleCanvasClick = useCallback((e) => {
    if (e?._cancel) { setPlacing(null); return; }
    if (!placing || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const cx = (e.clientX - rect.left) * scaleX;
    const cy = (e.clientY - rect.top) * scaleY;
    const isText  = ['text', 'date'].includes(placing.type);
    const isSmall = ['initials', 'checkmark'].includes(placing.type);
    const img = new Image();
    img.onload = () => {
      let w, h;
      if (isText) {
        w = img.naturalWidth; h = img.naturalHeight;
      } else {
        // Use the PNG's natural aspect ratio — previously hardcoded to 3.5:1
        // which stretched the image and made the overlay Box taller than the
        // actual text, causing it to cover adjacent table cell borders.
        const base = isSmall ? sigSize * 0.4 : sigSize;
        const aspect = img.naturalHeight / img.naturalWidth;
        w = base * scaleX;
        h = base * aspect * scaleY;
      }
      setItems(prev => [...prev, {
        id: `item_${++itemIdCounter}`,
        type: placing.type, dataUrl: placing.dataUrl,
        x: cx, y: cy, width: w, height: h,
        page: currentPage,
      }]);
    };
    img.src = placing.dataUrl;
    setPlacing(null);
  }, [placing, currentPage, sigSize, canvasRef]);

  const deleteItem = (id) => { setItems(p => p.filter(i => i.id !== id)); setSelectedItemId(null); };

  const undoItem = () => {
    setItems(prev => {
      const onPage = prev.filter(i => i.page === currentPage);
      if (!onPage.length) return prev;
      return prev.filter(i => i.id !== onPage[onPage.length - 1].id);
    });
    setSelectedItemId(null);
  };

  const moveItem = (id, x, y) => setItems(p => p.map(i => i.id === id ? { ...i, x, y } : i));
  const resizeItem = (id, width, height) => setItems(p => p.map(i => i.id === id ? { ...i, width, height } : i));

  const clearItems = () => { setItems([]); setPlacing(null); setSelectedItemId(null); };

  return {
    items, currentPageItems, selectedItemId, placing,
    setSelectedItemId, setPlacing,
    handleCanvasClick, deleteItem, undoItem, moveItem, resizeItem, clearItems,
  };
}
