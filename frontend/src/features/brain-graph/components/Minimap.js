/**
 * Minimap - Canvas-based graph minimap with viewport rectangle
 *
 * Shows downscaled node positions as dots with a viewport rectangle.
 * Click to pan the main canvas. Toggleable via button.
 */

import React, { useRef, useEffect, useState, useCallback } from 'react';
import { Map } from 'lucide-react';
import { isLightTheme } from '../utils/nodeRendering';

import './Minimap.css';

const W = 150, H = 100, PAD = 8;

const TYPE_COLORS = {
  note: '#f59e0b', tag: '#10b981', image: '#06b6d4',
  media: '#06b6d4', entity: '#818cf8',
};

export function Minimap({ graphRef, graphData, layout }) {
  const canvasRef = useRef(null);
  const [visible, setVisible] = useState(false);
  const rafRef = useRef(null);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    const fg = graphRef?.current;
    if (!canvas || !fg || !graphData?.nodes?.length) return;
    const ctx = canvas.getContext('2d');
    const light = isLightTheme();

    // Compute bounding box
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    for (const n of graphData.nodes) {
      if (n.x == null || n.y == null) continue;
      if (n.x < minX) minX = n.x;
      if (n.x > maxX) maxX = n.x;
      if (n.y < minY) minY = n.y;
      if (n.y > maxY) maxY = n.y;
    }
    const rangeX = (maxX - minX) || 1;
    const rangeY = (maxY - minY) || 1;
    const scale = Math.min((W - PAD * 2) / rangeX, (H - PAD * 2) / rangeY);

    ctx.clearRect(0, 0, W, H);

    // Draw nodes
    for (const n of graphData.nodes) {
      if (n.x == null) continue;
      const mx = PAD + (n.x - minX) * scale;
      const my = PAD + (n.y - minY) * scale;
      const type = n.id?.split('-')[0] || 'note';
      ctx.beginPath();
      ctx.arc(mx, my, 2, 0, Math.PI * 2);
      ctx.fillStyle = TYPE_COLORS[type] || '#9ca3af';
      ctx.fill();
    }

    // Draw viewport rectangle
    try {
      const tl = fg.screen2GraphCoords(0, 0);
      const br = fg.screen2GraphCoords(fg.width?.() || 800, fg.height?.() || 600);
      const vx = PAD + (tl.x - minX) * scale;
      const vy = PAD + (tl.y - minY) * scale;
      const vw = (br.x - tl.x) * scale;
      const vh = (br.y - tl.y) * scale;
      ctx.strokeStyle = light ? 'rgba(99, 102, 241, 0.7)' : 'rgba(255, 255, 255, 0.5)';
      ctx.lineWidth = 1.5;
      ctx.strokeRect(vx, vy, vw, vh);
    } catch { /* viewport coords unavailable during init */ }

    rafRef.current = requestAnimationFrame(draw);
  }, [graphRef, graphData]);

  useEffect(() => {
    if (!visible) { if (rafRef.current) cancelAnimationFrame(rafRef.current); return; }
    rafRef.current = requestAnimationFrame(draw);
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current); };
  }, [visible, draw]);

  // Click to pan
  const handleClick = useCallback((e) => {
    const fg = graphRef?.current;
    if (!fg || !graphData?.nodes?.length) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const cx = e.clientX - rect.left;
    const cy = e.clientY - rect.top;

    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    for (const n of graphData.nodes) {
      if (n.x == null) continue;
      if (n.x < minX) minX = n.x;
      if (n.x > maxX) maxX = n.x;
      if (n.y < minY) minY = n.y;
      if (n.y > maxY) maxY = n.y;
    }
    const rangeX = (maxX - minX) || 1;
    const rangeY = (maxY - minY) || 1;
    const scale = Math.min((W - PAD * 2) / rangeX, (H - PAD * 2) / rangeY);
    const worldX = minX + (cx - PAD) / scale;
    const worldY = minY + (cy - PAD) / scale;
    fg.centerAt(worldX, worldY, 300);
  }, [graphRef, graphData]);

  return (
    <div className="graph-minimap">
      {visible && (
        <canvas
          ref={canvasRef}
          className="graph-minimap__canvas"
          width={W}
          height={H}
          onClick={handleClick}
        />
      )}
      <button
        className={`graph-minimap__toggle ${visible ? 'graph-minimap__toggle--active' : ''}`}
        onClick={() => setVisible((v) => !v)}
        title="Toggle minimap"
      >
        <Map size={14} />
      </button>
    </div>
  );
}

export default Minimap;
