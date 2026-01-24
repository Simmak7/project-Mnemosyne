import React, { createContext, useState, useEffect, useCallback } from 'react';

export const WorkspaceContext = createContext();

export const WorkspaceProvider = ({ children }) => {
  // Load persisted state from localStorage
  const [selectedNoteId, setSelectedNoteId] = useState(null);
  const [activeBucket, setActiveBucket] = useState('inbox');
  const [contextRailTab, setContextRailTab] = useState('backlinks');

  // Refresh trigger - increment to signal note refresh
  const [noteRefreshTrigger, setNoteRefreshTrigger] = useState(0);

  // Editor state (Phase 4 - Real-time Context Rail)
  // This is passed from CenterPane's TiptapEditor to RightPane's context panels
  const [editorState, setEditorState] = useState({
    editorInstance: null,
    noteTitle: '',
    wikilinks: [],
    hashtags: [],
    wordCount: 0,
    charCount: 0,
    isEditMode: false,
  });

  // Panel widths (percentages)
  const [leftPaneWidth, setLeftPaneWidth] = useState(() => {
    const saved = localStorage.getItem('mnemosyne_left_pane_width');
    return saved ? parseFloat(saved) : 25;
  });

  const [rightPaneWidth, setRightPaneWidth] = useState(() => {
    const saved = localStorage.getItem('mnemosyne_right_pane_width');
    return saved ? parseFloat(saved) : 25;
  });

  // Persist pane widths to localStorage
  useEffect(() => {
    localStorage.setItem('mnemosyne_left_pane_width', leftPaneWidth.toString());
  }, [leftPaneWidth]);

  useEffect(() => {
    localStorage.setItem('mnemosyne_right_pane_width', rightPaneWidth.toString());
  }, [rightPaneWidth]);

  // Methods
  const selectNote = (noteId) => {
    setSelectedNoteId(noteId);
  };

  const clearNoteSelection = () => {
    setSelectedNoteId(null);
  };

  const setBucket = (bucketName) => {
    setActiveBucket(bucketName);
  };

  const setContextTab = (tabName) => {
    setContextRailTab(tabName);
  };

  const updateEditorState = (newState) => {
    setEditorState(prev => ({ ...prev, ...newState }));
  };

  // Trigger note refresh - call this when note content is modified externally
  const triggerNoteRefresh = useCallback(() => {
    setNoteRefreshTrigger(prev => prev + 1);
  }, []);

  const value = {
    selectedNoteId,
    activeBucket,
    leftPaneWidth,
    rightPaneWidth,
    contextRailTab,
    editorState,
    noteRefreshTrigger,
    selectNote,
    clearNoteSelection,
    setBucket,
    setLeftPaneWidth,
    setRightPaneWidth,
    setContextTab,
    updateEditorState,
    triggerNoteRefresh,
  };

  return (
    <WorkspaceContext.Provider value={value}>
      {children}
    </WorkspaceContext.Provider>
  );
};
