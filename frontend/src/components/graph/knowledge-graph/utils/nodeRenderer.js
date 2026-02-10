/**
 * Node canvas rendering function for force graph
 */
export function createNodeCanvasObject(highlightedNodes, selectedNode) {
  return (node, ctx, globalScale) => {
    const label = node.name;
    const fontSize = 12 / globalScale;
    ctx.font = `${fontSize}px Sans-Serif`;

    // Detect theme for label color
    const isDarkMode = document.documentElement.getAttribute('data-theme') === 'dark';
    const labelColor = isDarkMode ? '#e0e0e0' : '#333';

    // Determine node color and shape
    let color = '#999';
    if (node.type === 'note') color = '#4A90E2'; // Blue
    if (node.type === 'tag') color = '#F5A623'; // Orange
    if (node.type === 'image') color = '#7ED321'; // Green

    // Highlight if searched or selected
    if (highlightedNodes.has(node.id)) {
      color = '#FF3B30'; // Red highlight
    }
    if (selectedNode?.id === node.id) {
      ctx.strokeStyle = '#FF3B30';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(node.x, node.y, node.size + 2, 0, 2 * Math.PI);
      ctx.stroke();
    }

    // Draw node
    ctx.fillStyle = color;
    ctx.beginPath();

    if (node.type === 'tag') {
      // Hexagon for tags
      const sides = 6;
      const radius = node.size;
      for (let i = 0; i < sides; i++) {
        const angle = (Math.PI / 3) * i;
        const x = node.x + radius * Math.cos(angle);
        const y = node.y + radius * Math.sin(angle);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.closePath();
    } else {
      // Circle for notes and images
      ctx.arc(node.x, node.y, node.size, 0, 2 * Math.PI);
    }

    ctx.fill();

    // Draw label
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.fillStyle = labelColor;
    ctx.fillText(label, node.x, node.y + node.size + 2);
  };
}

/**
 * Link canvas rendering function for force graph
 */
export function linkCanvasObject(link, ctx) {
  const start = link.source;
  const end = link.target;

  // Determine line style based on link type
  if (link.type === 'wikilink') {
    ctx.strokeStyle = '#999';
    ctx.lineWidth = 1.5;
    ctx.setLineDash([]);
  } else if (link.type === 'tag') {
    ctx.strokeStyle = '#f59e0b';
    ctx.lineWidth = 1;
    ctx.setLineDash([5, 5]);
  } else if (link.type === 'image') {
    ctx.strokeStyle = '#10b981';
    ctx.lineWidth = 1;
    ctx.setLineDash([2, 4]);
  } else {
    ctx.strokeStyle = '#CCC';
    ctx.lineWidth = 0.5;
    ctx.setLineDash([]);
  }

  ctx.beginPath();
  ctx.moveTo(start.x, start.y);
  ctx.lineTo(end.x, end.y);
  ctx.stroke();

  // Reset dash after drawing
  ctx.setLineDash([]);
}
