/**
 * Transform API data into graph format for react-force-graph
 *
 * Converts notes, tags, and images into nodes and links:
 * - Nodes: { id, name, type, size, ...metadata }
 * - Links: { source, target, type }
 *
 * Node types:
 * - note: Blue circles (size based on backlink count)
 * - tag: Orange hexagons (size based on note count)
 * - image: Green circles (fixed size)
 *
 * Link types:
 * - wikilink: Solid lines (note → note via [[wikilinks]])
 * - tag: Dashed lines (note → tag)
 * - image: Dotted lines (note → image)
 */

/**
 * Main transformation function
 * @param {Array} notes - Notes with relationships (linked_notes, backlinks, tags)
 * @param {Array} tags - All tags with counts
 * @param {Array} images - All images
 * @returns {Object} { nodes: [...], links: [...] }
 */
export function transformToGraphData(notes, tags, images) {
  const nodes = [];
  const links = [];
  const nodeIds = new Set();

  // Helper to add node if not exists
  const addNode = (node) => {
    if (!nodeIds.has(node.id)) {
      nodes.push(node);
      nodeIds.add(node.id);
    }
  };

  // 1. Create note nodes
  notes.forEach((note) => {
    const backlinkCount = note.backlinks ? note.backlinks.length : 0;
    const linkCount = note.linked_notes ? note.linked_notes.length : 0;

    // Size based on connectivity (more backlinks = bigger node)
    const size = Math.max(5, Math.min(15, 5 + backlinkCount * 2));

    addNode({
      id: `note-${note.id}`,
      name: note.title || `Note ${note.id}`,
      type: 'note',
      size,
      noteId: note.id,
      content: note.content,
      slug: note.slug,
      tags: note.tags ? note.tags.map((t) => t.name) : [],
      backlinkCount,
      linkCount,
      created_at: note.created_at,
      updated_at: note.updated_at,
    });
  });

  // 2. Create tag nodes
  tags.forEach((tag) => {
    // Count how many notes use this tag
    const noteCount = notes.filter(
      (note) => note.tags && note.tags.some((t) => t.id === tag.id)
    ).length;

    // Size based on usage
    const size = Math.max(6, Math.min(18, 6 + noteCount * 1.5));

    addNode({
      id: `tag-${tag.id}`,
      name: tag.name,
      type: 'tag',
      size,
      tagId: tag.id,
      noteCount,
      created_at: tag.created_at,
    });
  });

  // 3. Create image nodes
  images.forEach((image) => {
    addNode({
      id: `image-${image.id}`,
      name: image.filename || `Image ${image.id}`,
      type: 'image',
      size: 7,
      imageId: image.id,
      filename: image.filename,
      filepath: image.filepath,
      ai_analysis_status: image.ai_analysis_status,
      uploaded_at: image.uploaded_at,
    });
  });

  // 4. Create wikilink edges (note → note)
  notes.forEach((note) => {
    if (note.linked_notes && note.linked_notes.length > 0) {
      note.linked_notes.forEach((linkedNoteId) => {
        links.push({
          source: `note-${note.id}`,
          target: `note-${linkedNoteId}`,
          type: 'wikilink',
        });
      });
    }
  });

  // 5. Create tag edges (note → tag)
  notes.forEach((note) => {
    if (note.tags && note.tags.length > 0) {
      note.tags.forEach((tag) => {
        links.push({
          source: `note-${note.id}`,
          target: `tag-${tag.id}`,
          type: 'tag',
        });
      });
    }
  });

  // 6. Create image edges (note → image)
  notes.forEach((note) => {
    if (note.image_ids && note.image_ids.length > 0) {
      note.image_ids.forEach((imageId) => {
        links.push({
          source: `note-${note.id}`,
          target: `image-${imageId}`,
          type: 'image',
        });
      });
    }
  });

  return { nodes, links };
}

/**
 * Filter graph data by node type
 * @param {Object} graphData - { nodes, links }
 * @param {Object} filters - { showNotes, showTags, showImages }
 * @returns {Object} Filtered { nodes, links }
 */
export function filterGraphData(graphData, filters) {
  const filteredNodes = graphData.nodes.filter((node) => {
    if (node.type === 'note' && !filters.showNotes) return false;
    if (node.type === 'tag' && !filters.showTags) return false;
    if (node.type === 'image' && !filters.showImages) return false;
    return true;
  });

  const nodeIds = new Set(filteredNodes.map((n) => n.id));

  const filteredLinks = graphData.links.filter(
    (link) => nodeIds.has(link.source) && nodeIds.has(link.target)
  );

  return { nodes: filteredNodes, links: filteredLinks };
}

/**
 * Search nodes by name
 * @param {Array} nodes - All nodes
 * @param {string} searchTerm - Search query
 * @returns {Array} Matching nodes
 */
export function searchNodes(nodes, searchTerm) {
  if (!searchTerm) return nodes;

  const term = searchTerm.toLowerCase();
  return nodes.filter((node) => node.name.toLowerCase().includes(term));
}

/**
 * Get node neighbors (connected nodes)
 * @param {string} nodeId - Node ID to find neighbors for
 * @param {Array} links - All links
 * @returns {Set} Set of neighbor node IDs
 */
export function getNeighbors(nodeId, links) {
  const neighbors = new Set();

  links.forEach((link) => {
    if (link.source === nodeId || link.source.id === nodeId) {
      neighbors.add(typeof link.target === 'object' ? link.target.id : link.target);
    }
    if (link.target === nodeId || link.target.id === nodeId) {
      neighbors.add(typeof link.source === 'object' ? link.source.id : link.source);
    }
  });

  return neighbors;
}

/**
 * Calculate node clustering coefficient
 * Measures how connected a node's neighbors are to each other
 * @param {string} nodeId - Node ID
 * @param {Array} links - All links
 * @returns {number} Clustering coefficient (0-1)
 */
export function getClusteringCoefficient(nodeId, links) {
  const neighbors = Array.from(getNeighbors(nodeId, links));

  if (neighbors.length < 2) return 0;

  // Count connections between neighbors
  let connections = 0;
  for (let i = 0; i < neighbors.length; i++) {
    for (let j = i + 1; j < neighbors.length; j++) {
      const hasConnection = links.some(
        (link) =>
          (link.source === neighbors[i] && link.target === neighbors[j]) ||
          (link.source === neighbors[j] && link.target === neighbors[i]) ||
          (link.source.id === neighbors[i] && link.target.id === neighbors[j]) ||
          (link.source.id === neighbors[j] && link.target.id === neighbors[i])
      );
      if (hasConnection) connections++;
    }
  }

  // Max possible connections between neighbors
  const maxConnections = (neighbors.length * (neighbors.length - 1)) / 2;

  return maxConnections > 0 ? connections / maxConnections : 0;
}

/**
 * Detect clusters using simple connected components algorithm
 * @param {Object} graphData - { nodes, links }
 * @returns {Array} Array of cluster arrays (node IDs)
 */
export function detectClusters(graphData) {
  const { nodes, links } = graphData;
  const visited = new Set();
  const clusters = [];

  const dfs = (nodeId, cluster) => {
    if (visited.has(nodeId)) return;
    visited.add(nodeId);
    cluster.push(nodeId);

    const neighbors = getNeighbors(nodeId, links);
    neighbors.forEach((neighborId) => dfs(neighborId, cluster));
  };

  nodes.forEach((node) => {
    if (!visited.has(node.id)) {
      const cluster = [];
      dfs(node.id, cluster);
      if (cluster.length > 0) {
        clusters.push(cluster);
      }
    }
  });

  return clusters.sort((a, b) => b.length - a.length); // Sort by size
}
