/**
 * Unit tests for graphDataTransform utility functions
 * Tests node/link generation, filtering, and graph algorithms
 */

import {
  transformToGraphData,
  filterGraphData,
  searchNodes,
  getNeighbors,
  getClusteringCoefficient,
  detectClusters,
} from './graphDataTransform';

describe('graphDataTransform', () => {
  // Mock data
  const mockNotes = [
    {
      id: 1,
      title: 'First Note',
      content: 'Some content',
      slug: 'first-note',
      linked_notes: [2],
      backlinks: [],
      tags: [{ id: 1, name: 'tag1' }],
      image_ids: [1],
      created_at: '2025-11-27T00:00:00Z',
      updated_at: '2025-11-27T00:00:00Z',
    },
    {
      id: 2,
      title: 'Second Note',
      content: 'More content',
      slug: 'second-note',
      linked_notes: [],
      backlinks: [1],
      tags: [{ id: 1, name: 'tag1' }, { id: 2, name: 'tag2' }],
      image_ids: [],
      created_at: '2025-11-27T00:00:00Z',
      updated_at: '2025-11-27T00:00:00Z',
    },
  ];

  const mockTags = [
    { id: 1, name: 'tag1', created_at: '2025-11-27T00:00:00Z' },
    { id: 2, name: 'tag2', created_at: '2025-11-27T00:00:00Z' },
  ];

  const mockImages = [
    {
      id: 1,
      filename: 'test.jpg',
      filepath: '/uploads/test.jpg',
      ai_analysis_status: 'completed',
      uploaded_at: '2025-11-27T00:00:00Z',
    },
  ];

  describe('transformToGraphData', () => {
    it('should create nodes for all notes, tags, and images', () => {
      const result = transformToGraphData(mockNotes, mockTags, mockImages);

      expect(result.nodes).toHaveLength(5); // 2 notes + 2 tags + 1 image
      expect(result.nodes.find(n => n.id === 'note-1')).toBeDefined();
      expect(result.nodes.find(n => n.id === 'note-2')).toBeDefined();
      expect(result.nodes.find(n => n.id === 'tag-1')).toBeDefined();
      expect(result.nodes.find(n => n.id === 'tag-2')).toBeDefined();
      expect(result.nodes.find(n => n.id === 'image-1')).toBeDefined();
    });

    it('should set correct node types', () => {
      const result = transformToGraphData(mockNotes, mockTags, mockImages);

      const noteNode = result.nodes.find(n => n.id === 'note-1');
      const tagNode = result.nodes.find(n => n.id === 'tag-1');
      const imageNode = result.nodes.find(n => n.id === 'image-1');

      expect(noteNode.type).toBe('note');
      expect(tagNode.type).toBe('tag');
      expect(imageNode.type).toBe('image');
    });

    it('should calculate node sizes based on connectivity', () => {
      const result = transformToGraphData(mockNotes, mockTags, mockImages);

      const note1 = result.nodes.find(n => n.id === 'note-1');
      const note2 = result.nodes.find(n => n.id === 'note-2');

      // Note 2 has 1 backlink, so should be larger than minimum
      expect(note2.size).toBeGreaterThan(5);
      // Note 1 has no backlinks, so should be minimum size
      expect(note1.size).toBe(5);
    });

    it('should create wikilink edges between notes', () => {
      const result = transformToGraphData(mockNotes, mockTags, mockImages);

      const wikilink = result.links.find(
        l => l.source === 'note-1' && l.target === 'note-2' && l.type === 'wikilink'
      );

      expect(wikilink).toBeDefined();
    });

    it('should create tag edges from notes to tags', () => {
      const result = transformToGraphData(mockNotes, mockTags, mockImages);

      const tagLink1 = result.links.find(
        l => l.source === 'note-1' && l.target === 'tag-1' && l.type === 'tag'
      );
      const tagLink2 = result.links.find(
        l => l.source === 'note-2' && l.target === 'tag-1' && l.type === 'tag'
      );

      expect(tagLink1).toBeDefined();
      expect(tagLink2).toBeDefined();
    });

    it('should create image edges from notes to images', () => {
      const result = transformToGraphData(mockNotes, mockTags, mockImages);

      const imageLink = result.links.find(
        l => l.source === 'note-1' && l.target === 'image-1' && l.type === 'image'
      );

      expect(imageLink).toBeDefined();
    });

    it('should handle empty input arrays', () => {
      const result = transformToGraphData([], [], []);

      expect(result.nodes).toHaveLength(0);
      expect(result.links).toHaveLength(0);
    });

    it('should handle notes without relationships', () => {
      const isolatedNote = [{
        id: 99,
        title: 'Isolated',
        content: 'Alone',
        slug: 'isolated',
        linked_notes: [],
        backlinks: [],
        tags: [],
        image_ids: [],
        created_at: '2025-11-27T00:00:00Z',
      }];

      const result = transformToGraphData(isolatedNote, [], []);

      expect(result.nodes).toHaveLength(1);
      expect(result.links).toHaveLength(0);
    });
  });

  describe('filterGraphData', () => {
    let graphData;

    beforeEach(() => {
      graphData = transformToGraphData(mockNotes, mockTags, mockImages);
    });

    it('should filter out notes when showNotes is false', () => {
      const filters = { showNotes: false, showTags: true, showImages: true };
      const result = filterGraphData(graphData, filters);

      const noteNodes = result.nodes.filter(n => n.type === 'note');
      expect(noteNodes).toHaveLength(0);
    });

    it('should filter out tags when showTags is false', () => {
      const filters = { showNotes: true, showTags: false, showImages: true };
      const result = filterGraphData(graphData, filters);

      const tagNodes = result.nodes.filter(n => n.type === 'tag');
      expect(tagNodes).toHaveLength(0);
    });

    it('should filter out images when showImages is false', () => {
      const filters = { showNotes: true, showTags: true, showImages: false };
      const result = filterGraphData(graphData, filters);

      const imageNodes = result.nodes.filter(n => n.type === 'image');
      expect(imageNodes).toHaveLength(0);
    });

    it('should remove links to filtered nodes', () => {
      const filters = { showNotes: true, showTags: false, showImages: true };
      const result = filterGraphData(graphData, filters);

      // All links to tags should be removed
      const tagLinks = result.links.filter(l => l.type === 'tag');
      expect(tagLinks).toHaveLength(0);
    });

    it('should keep all nodes when all filters are true', () => {
      const filters = { showNotes: true, showTags: true, showImages: true };
      const result = filterGraphData(graphData, filters);

      expect(result.nodes).toHaveLength(graphData.nodes.length);
    });
  });

  describe('searchNodes', () => {
    let nodes;

    beforeEach(() => {
      nodes = [
        { id: 'note-1', name: 'JavaScript Basics', type: 'note' },
        { id: 'note-2', name: 'Python Tutorial', type: 'note' },
        { id: 'tag-1', name: 'programming', type: 'tag' },
        { id: 'tag-2', name: 'javascript', type: 'tag' },
      ];
    });

    it('should return all nodes when search term is empty', () => {
      const result = searchNodes(nodes, '');
      expect(result).toHaveLength(4);
    });

    it('should return matching nodes (case-insensitive)', () => {
      const result = searchNodes(nodes, 'javascript');
      expect(result).toHaveLength(2);
      expect(result.find(n => n.id === 'note-1')).toBeDefined();
      expect(result.find(n => n.id === 'tag-2')).toBeDefined();
    });

    it('should return nodes with partial matches', () => {
      const result = searchNodes(nodes, 'prog');
      expect(result).toHaveLength(1);
      expect(result[0].id).toBe('tag-1');
    });

    it('should return empty array when no matches', () => {
      const result = searchNodes(nodes, 'nonexistent');
      expect(result).toHaveLength(0);
    });
  });

  describe('getNeighbors', () => {
    const links = [
      { source: 'note-1', target: 'note-2', type: 'wikilink' },
      { source: 'note-2', target: 'note-3', type: 'wikilink' },
      { source: 'note-1', target: 'tag-1', type: 'tag' },
    ];

    it('should find all neighbors of a node', () => {
      const neighbors = getNeighbors('note-1', links);
      expect(neighbors.size).toBe(2);
      expect(neighbors.has('note-2')).toBe(true);
      expect(neighbors.has('tag-1')).toBe(true);
    });

    it('should work for target nodes', () => {
      const neighbors = getNeighbors('note-2', links);
      expect(neighbors.size).toBe(2);
      expect(neighbors.has('note-1')).toBe(true);
      expect(neighbors.has('note-3')).toBe(true);
    });

    it('should return empty set for isolated nodes', () => {
      const neighbors = getNeighbors('note-99', links);
      expect(neighbors.size).toBe(0);
    });

    it('should handle object sources/targets', () => {
      const objectLinks = [
        { source: { id: 'note-1' }, target: { id: 'note-2' }, type: 'wikilink' },
      ];

      const neighbors = getNeighbors('note-1', objectLinks);
      expect(neighbors.size).toBe(1);
      expect(neighbors.has('note-2')).toBe(true);
    });
  });

  describe('getClusteringCoefficient', () => {
    it('should return 0 for nodes with less than 2 neighbors', () => {
      const links = [{ source: 'A', target: 'B', type: 'wikilink' }];
      const coefficient = getClusteringCoefficient('A', links);
      expect(coefficient).toBe(0);
    });

    it('should return 1 when all neighbors are connected', () => {
      const links = [
        { source: 'A', target: 'B', type: 'wikilink' },
        { source: 'A', target: 'C', type: 'wikilink' },
        { source: 'B', target: 'C', type: 'wikilink' }, // B and C are connected
      ];

      const coefficient = getClusteringCoefficient('A', links);
      expect(coefficient).toBe(1);
    });

    it('should return 0 when no neighbors are connected', () => {
      const links = [
        { source: 'A', target: 'B', type: 'wikilink' },
        { source: 'A', target: 'C', type: 'wikilink' },
        // B and C are NOT connected
      ];

      const coefficient = getClusteringCoefficient('A', links);
      expect(coefficient).toBe(0);
    });
  });

  describe('detectClusters', () => {
    it('should detect separate clusters', () => {
      const graphData = {
        nodes: [
          { id: 'A' },
          { id: 'B' },
          { id: 'C' },
          { id: 'D' },
        ],
        links: [
          { source: 'A', target: 'B', type: 'wikilink' },
          { source: 'C', target: 'D', type: 'wikilink' },
        ],
      };

      const clusters = detectClusters(graphData);
      expect(clusters).toHaveLength(2);
      expect(clusters[0]).toHaveLength(2);
      expect(clusters[1]).toHaveLength(2);
    });

    it('should detect single cluster when all connected', () => {
      const graphData = {
        nodes: [
          { id: 'A' },
          { id: 'B' },
          { id: 'C' },
        ],
        links: [
          { source: 'A', target: 'B', type: 'wikilink' },
          { source: 'B', target: 'C', type: 'wikilink' },
        ],
      };

      const clusters = detectClusters(graphData);
      expect(clusters).toHaveLength(1);
      expect(clusters[0]).toHaveLength(3);
    });

    it('should handle isolated nodes as separate clusters', () => {
      const graphData = {
        nodes: [
          { id: 'A' },
          { id: 'B' },
        ],
        links: [],
      };

      const clusters = detectClusters(graphData);
      expect(clusters).toHaveLength(2);
      expect(clusters[0]).toHaveLength(1);
      expect(clusters[1]).toHaveLength(1);
    });

    it('should sort clusters by size (largest first)', () => {
      const graphData = {
        nodes: [
          { id: 'A' },
          { id: 'B' },
          { id: 'C' },
          { id: 'D' },
        ],
        links: [
          { source: 'A', target: 'B', type: 'wikilink' },
          { source: 'B', target: 'C', type: 'wikilink' },
          // D is isolated
        ],
      };

      const clusters = detectClusters(graphData);
      expect(clusters[0].length).toBeGreaterThan(clusters[1].length);
    });
  });
});
