/**
 * Feature flags configuration
 */
export function getFeatureFlags() {
  return {
    workspaceEnabled: localStorage.getItem('ENABLE_WORKSPACE') === 'true',
    journalEnabled: localStorage.getItem('ENABLE_JOURNAL') !== 'false',
    newGalleryEnabled: localStorage.getItem('ENABLE_NEW_GALLERY') !== 'false',
    newNotesEnabled: localStorage.getItem('ENABLE_NEW_NOTES') !== 'false',
    newAIChatEnabled: localStorage.getItem('ENABLE_NEW_AI_CHAT') !== 'false',
    newUploadEnabled: localStorage.getItem('ENABLE_NEW_UPLOAD') !== 'false',
    newBrainGraphEnabled: localStorage.getItem('ENABLE_NEW_BRAIN_GRAPH') === 'true',
    documentsEnabled: localStorage.getItem('ENABLE_DOCUMENTS') !== 'false',
  };
}

export const PAGE_INFO = {
  workspace: { title: 'Workspace', description: 'Your personal note-taking workspace' },
  journal: { title: 'Journal', description: 'Daily notes, quick capture, and personal reflections' },
  upload: { title: 'Upload Image', description: 'Upload and analyze images with AI' },
  gallery: { title: 'Gallery', description: 'Browse and organize your photos with Immich-inspired layout' },
  notes: { title: 'Smart Notes', description: 'AI-generated notes from your images' },
  documents: { title: 'Documents', description: 'Upload and analyze PDFs with AI-powered extraction' },
  graph: { title: 'Brain', description: 'Your knowledge graph - visualize connections between notes and tags' },
  chat: { title: 'Mnemosyne', description: 'Your personal AI assistant - ask questions and get answers with citations from your notes' },
};
