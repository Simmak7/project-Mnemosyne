/**
 * useAppNavigation - Tab navigation and deep linking handlers
 */
import { useState, useCallback, useEffect } from 'react';
import { API_URL } from '../utils/api';

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
  }, []);

  const handleNavigateToNote = useCallback((noteId) => {
    setActiveTab('notes');
    setSelectedNoteId(noteId);
    setSelectedImageId(null);
    setSearchQuery('');
  }, []);

  const handleNavigateToImage = useCallback((imageId) => {
    setActiveTab('gallery');
    setSelectedImageId(imageId);
    setSelectedNoteId(null);
    setSearchQuery('');
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
  }, []);

  const handleNavigateToAI = useCallback((context) => {
    setAiChatContext(context);
    setActiveTab('chat');
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
