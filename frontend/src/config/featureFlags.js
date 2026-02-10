/**
 * Feature flags configuration
 */
export function getFeatureFlags() {
  return {
    journalEnabled: localStorage.getItem('ENABLE_JOURNAL') !== 'false',
    documentsEnabled: localStorage.getItem('ENABLE_DOCUMENTS') !== 'false',
  };
}

export const PAGE_INFO = {
  journal: { title: 'Journal', description: 'Daily notes, quick capture, and personal reflections' },
  upload: { title: 'Upload Image', description: 'Upload and analyze images with AI' },
  gallery: { title: 'Gallery', description: 'Browse and organize your photos with Immich-inspired layout' },
  notes: { title: 'Smart Notes', description: 'AI-generated notes from your images' },
  documents: { title: 'Documents', description: 'Upload and analyze PDFs with AI-powered extraction' },
  graph: { title: 'Brain', description: 'Your knowledge graph - visualize connections between notes and tags' },
  chat: { title: 'Mnemosyne', description: 'Your personal AI assistant - ask questions and get answers with citations from your notes' },
};
