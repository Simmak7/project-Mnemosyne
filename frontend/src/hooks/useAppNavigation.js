/**
 * useAppNavigation - Tab navigation and deep linking handlers
 */
import { useState, useCallback, useEffect } from 'react';
import { API_URL } from '../utils/api';

const VALID_TABS = ['dashboard', 'upload', 'gallery', 'documents', 'notes', 'journal', 'graph', 'chat'];

export function useAppNavigation() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [selectedNoteId, setSelectedNoteId] = useState(null);
  const [selectedImageId, setSelectedImageId] = useState(null);
  const [selectedDocumentId, setSelectedDocumentId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchOpen, setSearchOpen] = useState(false);
  const [aiChatContext, setAiChatContext] = useState(null);
  const [graphFocusNodeId, setGraphFocusNodeId] = useState(null);
  const [images, setImages] = useState([]);
  const [notes, setNotes] = useState([]);

  // Global keyboard shortcut for search (Cmd/Ctrl+K)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setSearchOpen(true);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Restore tab from URL hash on initial load
  useEffect(() => {
    const hash = window.location.hash.replace('#/', '');
    if (!hash) return;

    const parts = hash.split('/');
    const tab = parts[0];
    const itemId = parts[1] ? parseInt(parts[1], 10) : null;

    if (VALID_TABS.includes(tab)) {
      setActiveTab(tab);
      if (tab === 'notes' && itemId) setSelectedNoteId(itemId);
      else if (tab === 'gallery' && itemId) setSelectedImageId(itemId);
      else if (tab === 'documents' && itemId) setSelectedDocumentId(itemId);

      if (tab === 'gallery') fetchImages();
      else if (tab === 'notes') fetchNotes();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Listen for browser back/forward navigation
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace('#/', '');
      if (!hash) {
        setActiveTab('dashboard');
        return;
      }

      const parts = hash.split('/');
      const tab = parts[0];
      const itemId = parts[1] ? parseInt(parts[1], 10) : null;

      if (VALID_TABS.includes(tab)) {
        setActiveTab(tab);
        if (tab === 'notes' && itemId) setSelectedNoteId(itemId);
        else if (tab === 'gallery' && itemId) setSelectedImageId(itemId);
        else if (tab === 'documents' && itemId) setSelectedDocumentId(itemId);
      }
    };

    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const fetchImages = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/images/`);
      const data = await response.json();
      setImages(data);
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Error fetching images:', error);
      }
    }
  }, []);

  const fetchNotes = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      const response = await fetch(`${API_URL}/notes-enhanced/`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setNotes(data);
      }
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Error fetching notes:', error);
      }
    }
  }, []);

  const handleTabChange = useCallback((tab) => {
    setActiveTab(tab);
    window.location.hash = `#/${tab}`;
    if (tab === 'gallery') {
      fetchImages();
    } else if (tab === 'notes') {
      fetchNotes();
    }
  }, [fetchImages, fetchNotes]);

  const handleImageUploadSuccess = useCallback(() => {
    setRefreshTrigger(prev => prev + 1);
    window.dispatchEvent(new CustomEvent('gallery:refresh'));
  }, []);

  const handleNavigateToGraph = useCallback((noteId) => {
    setGraphFocusNodeId(noteId ? `note-${noteId}` : null);
    setActiveTab('graph');
    window.location.hash = `#/graph`;
  }, []);

  const handleNavigateToNote = useCallback((noteId) => {
    setActiveTab('notes');
    setSelectedNoteId(noteId);
    setSelectedImageId(null);
    setSearchQuery('');
    window.location.hash = `#/notes/${noteId}`;
  }, []);

  const handleNavigateToImage = useCallback((imageId) => {
    setActiveTab('gallery');
    setSelectedImageId(imageId);
    setSelectedNoteId(null);
    setSearchQuery('');
    window.location.hash = `#/gallery/${imageId}`;
  }, []);

  const handleNavigateToTag = useCallback((tagName) => {
    setActiveTab('notes');
    setSearchQuery(tagName.startsWith('#') ? tagName : `#${tagName}`);
    setSelectedNoteId(null);
    setSelectedImageId(null);
  }, []);

  const handleNavigateToSearch = useCallback((query) => {
    setActiveTab('notes');
    setSearchQuery(query);
    setSelectedNoteId(null);
    setSelectedImageId(null);
  }, []);

  const handleNavigateToDocument = useCallback((docId) => {
    setActiveTab('documents');
    setSelectedDocumentId(docId);
    setSelectedNoteId(null);
    setSelectedImageId(null);
    window.location.hash = `#/documents/${docId}`;
  }, []);

  const handleNavigateToAI = useCallback((context) => {
    setAiChatContext(context);
    setActiveTab('chat');
    window.location.hash = `#/chat`;
  }, []);

  const clearAiChatContext = useCallback(() => {
    setAiChatContext(null);
  }, []);

  const handleSearchResultClick = useCallback((result, query) => {
    setSearchQuery(query || '');

    if (result.type === 'note') {
      setSelectedNoteId(result.id);
      setSelectedImageId(null);
      setActiveTab('notes');
    } else if (result.type === 'image') {
      setSelectedImageId(result.id);
      setSelectedNoteId(null);
      setActiveTab('gallery');
    } else if (result.type === 'tag') {
      setSelectedNoteId(null);
      setSelectedImageId(null);
      setActiveTab('notes');
    }
    setSearchOpen(false);
  }, []);

  const resetTabState = useCallback(() => {
    setActiveTab('dashboard');
    window.location.hash = '';
  }, []);

  return {
    activeTab,
    refreshTrigger,
    selectedNoteId,
    selectedImageId,
    selectedDocumentId,
    searchQuery,
    searchOpen,
    aiChatContext,
    graphFocusNodeId,
    images,
    notes,
    setSearchOpen,
    setSelectedImageId,
    setSelectedDocumentId,
    handleTabChange,
    handleImageUploadSuccess,
    handleNavigateToGraph,
    handleNavigateToNote,
    handleNavigateToImage,
    handleNavigateToDocument,
    handleNavigateToTag,
    handleNavigateToSearch,
    handleNavigateToAI,
    clearAiChatContext,
    handleSearchResultClick,
    resetTabState,
  };
}

export default useAppNavigation;
