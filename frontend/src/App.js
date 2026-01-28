import React, { useState, useEffect, lazy, Suspense } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import './App.css';

// Neural Glass Design System (Phase 2)
import './styles/neural-glass/index.css';

// API utility for centralized URL configuration
import { API_URL, api } from './utils/api';

// Feature imports (fractal architecture)
import { Login, EmailVerification } from './features/auth';

// Component imports (legacy - to be migrated to features)
import Sidebar from './components/Sidebar';
import ImageUpload from './components/ImageUpload';
import UnifiedSearch from './components/search/UnifiedSearch';
import LoadingSpinner from './components/LoadingSpinner';
import ErrorBoundary from './components/ErrorBoundary';

// Lazy load heavy components to reduce initial bundle size
const VirtualizedImageGallery = lazy(() => import('./components/virtualized/VirtualizedImageGallery'));
// New Immich-inspired gallery (Phase 1)
const GalleryLayout = lazy(() => import('./features/gallery').then(m => ({ default: m.GalleryLayout })));
// New 3-pane notes layout (Phase 1)
const NoteLayout = lazy(() => import('./features/notes').then(m => ({ default: m.NoteLayout })));
const VirtualizedNoteList = lazy(() => import('./components/virtualized/VirtualizedNoteList'));
// Graph feature (migrated to fractal architecture)
const KnowledgeGraph = lazy(() => import('./features/graph/components/KnowledgeGraph'));
// New Brain Graph (Phase 3-4)
const BrainGraph = lazy(() => import('./features/brain-graph').then(m => ({ default: m.BrainGraph })));
const AIChat = lazy(() => import('./components/AIChat'));
// RAG Chat feature (migrated to fractal architecture)
const RAGChat = lazy(() => import('./features/rag_chat/components/RAGChat'));
// New AI Chat with 3-pane layout (Phase 1)
const AIChatLayout = lazy(() => import('./features/ai_chat').then(m => ({ default: m.AIChatLayout })));
const WorkspaceLayout = lazy(() => import('./components/workspace/WorkspaceLayout'));
// New Neural Studio Upload (2-pane layout)
const UploadLayout = lazy(() => import('./features/upload').then(m => ({ default: m.UploadLayout })));

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 30000, // 30 seconds
    },
  },
});

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [username, setUsername] = useState('');
  const [activeTab, setActiveTab] = useState('upload');
  const [images, setImages] = useState([]);
  const [notes, setNotes] = useState([]);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode');
    return saved ? JSON.parse(saved) : false;
  });
  const [searchOpen, setSearchOpen] = useState(false);
  const [selectedNoteId, setSelectedNoteId] = useState(null);
  const [selectedImageId, setSelectedImageId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  // AI Chat initial context for deep linking
  const [aiChatContext, setAiChatContext] = useState(null);

  // Check for existing token on app load and validate it
  useEffect(() => {
    const validateToken = async () => {
      const token = localStorage.getItem('token');
      const savedUsername = localStorage.getItem('username');

      if (token && savedUsername) {
        // Validate token by calling /me endpoint
        try {
          const response = await fetch(`${API_URL}/me`, {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
            credentials: 'include', // Include cookies for auth
          });

          if (response.ok) {
            setIsAuthenticated(true);
            setUsername(savedUsername);
            // Fetch profile to get display name
            try {
              const profileRes = await fetch(`${API_URL}/profile`, {
                headers: { 'Authorization': `Bearer ${token}` },
              });
              if (profileRes.ok) {
                const profile = await profileRes.json();
                if (profile.display_name) {
                  localStorage.setItem('displayName', profile.display_name);
                }
              }
            } catch (e) {
              // Profile fetch failed, not critical
            }
          } else {
            // Token is invalid, clear it
            if (process.env.NODE_ENV === 'development') {
              console.log('Token validation failed, clearing localStorage');
            }
            localStorage.removeItem('token');
            localStorage.removeItem('username');
          }
        } catch (error) {
          if (process.env.NODE_ENV === 'development') {
            console.error('Token validation failed:', error);
          }
          // Network error, clear token to be safe
          localStorage.removeItem('token');
          localStorage.removeItem('username');
        }
      }
    };

    validateToken();
  }, []);

  // Apply dark mode to document
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', isDarkMode ? 'dark' : 'light');
    localStorage.setItem('darkMode', JSON.stringify(isDarkMode));
  }, [isDarkMode]);

  // Apply saved accent color and UI density on load
  useEffect(() => {
    const root = document.documentElement;

    // Apply accent color
    const savedAccentColor = localStorage.getItem('accentColor');
    if (savedAccentColor) {
      const accentColors = {
        blue: { primary: '#3B82F6', hover: '#2563EB', light: '#DBEAFE' },
        purple: { primary: '#8B5CF6', hover: '#7C3AED', light: '#EDE9FE' },
        green: { primary: '#10B981', hover: '#059669', light: '#D1FAE5' },
        orange: { primary: '#F59E0B', hover: '#D97706', light: '#FEF3C7' },
        pink: { primary: '#EC4899', hover: '#DB2777', light: '#FCE7F3' },
      };
      const colors = accentColors[savedAccentColor] || accentColors.blue;
      root.style.setProperty('--accent-color', colors.primary);
      root.style.setProperty('--accent-hover', colors.hover);
      root.style.setProperty('--accent-light', colors.light);
    }

    // Apply UI density
    const savedDensity = localStorage.getItem('uiDensity');
    if (savedDensity) {
      const densityValues = {
        compact: { spacing: '8px', padding: '12px', fontSize: '13px' },
        comfortable: { spacing: '16px', padding: '16px', fontSize: '14px' },
        spacious: { spacing: '24px', padding: '20px', fontSize: '15px' },
      };
      const density = densityValues[savedDensity] || densityValues.comfortable;
      root.style.setProperty('--density-spacing', density.spacing);
      root.style.setProperty('--density-padding', density.padding);
      root.style.setProperty('--density-font-size', density.fontSize);
      root.setAttribute('data-density', savedDensity);
    }
  }, []);

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

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
  };

  const handleImageUploadSuccess = (newImage) => {
    // Just trigger refresh - ImageGallery will fetch the updated list
    setRefreshTrigger(refreshTrigger + 1);
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    if (tab === 'gallery') {
      fetchImages();
    } else if (tab === 'notes') {
      fetchNotes();
    }
  };

  // Navigation callback for note viewer -> graph
  const handleNavigateToGraph = (noteId) => {
    setActiveTab('graph');
    // Could pass noteId to graph to highlight specific node (future enhancement)
  };

  // Navigation callback for graph -> note
  const handleNavigateToNote = (noteId) => {
    setActiveTab('notes');
    setSelectedNoteId(noteId);
    setSelectedImageId(null);
    setSearchQuery('');
  };

  // Navigation callback for graph -> image
  const handleNavigateToImage = (imageId) => {
    setActiveTab('gallery');
    setSelectedImageId(imageId);
    setSelectedNoteId(null);
    setSearchQuery('');
  };

  // Navigation callback for graph -> tag (filter notes by tag)
  const handleNavigateToTag = (tagName) => {
    setActiveTab('notes');
    setSearchQuery(tagName); // Use searchQuery to filter by tag
    setSelectedNoteId(null);
    setSelectedImageId(null);
  };

  // Navigation callback for Note/Gallery -> AI Chat (deep linking)
  const handleNavigateToAI = (context) => {
    // context = { type: 'note' | 'image', id: number, title: string }
    setAiChatContext(context);
    setActiveTab('chat');
  };

  // Clear AI context after it's been consumed
  const clearAiChatContext = () => {
    setAiChatContext(null);
  };

  const fetchImages = async () => {
    try {
      const response = await fetch(`${API_URL}/images/`);
      const data = await response.json();
      setImages(data);
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Error fetching images:', error);
      }
    }
  };

  const fetchNotes = async () => {
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
  };

  const handleLoginSuccess = async (token, user) => {
    setIsAuthenticated(true);
    setUsername(user);
    // Fetch profile to get display name
    try {
      const profileRes = await fetch(`${API_URL}/profile`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (profileRes.ok) {
        const profile = await profileRes.json();
        if (profile.display_name) {
          localStorage.setItem('displayName', profile.display_name);
        }
      }
    } catch (e) {
      // Profile fetch failed, not critical
    }
  };

  const handleLogout = async () => {
    // Call logout endpoint to clear httpOnly cookie
    try {
      await fetch(`${API_URL}/logout`, {
        method: 'POST',
        credentials: 'include', // Include cookies for auth
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
    } catch (error) {
      // Continue with local logout even if server call fails
      console.warn('Logout API call failed:', error);
    }

    // Clear local storage
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    localStorage.removeItem('displayName');
    localStorage.removeItem('accentColor');
    localStorage.removeItem('uiDensity');

    // Clear API client state
    api.clearAuth();

    // Reset CSS variables to defaults
    const root = document.documentElement;
    root.style.removeProperty('--accent-color');
    root.style.removeProperty('--accent-hover');
    root.style.removeProperty('--accent-light');
    root.style.removeProperty('--density-spacing');
    root.style.removeProperty('--density-padding');
    root.style.removeProperty('--density-font-size');
    root.removeAttribute('data-density');
    setIsAuthenticated(false);
    setUsername('');
    setActiveTab('upload');
  };

  // Handle search result click - navigate to appropriate tab and select item
  const handleSearchResultClick = (result, query) => {
    // Store the search query for highlighting
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
    setSearchOpen(false); // Close search modal after navigation
  };

  // Show login screen if not authenticated
  // Check for email verification URL
  if (window.location.pathname === '/verify-email-change') {
    return <EmailVerification onComplete={() => window.location.href = '/'} />;
  }

  if (!isAuthenticated) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  // Feature flag for Workspace (opt-out)
  const workspaceEnabled = localStorage.getItem('ENABLE_WORKSPACE') !== 'false';
  // Feature flag for new Gallery (opt-in during development, will become default)
  const newGalleryEnabled = localStorage.getItem('ENABLE_NEW_GALLERY') !== 'false';
  // Feature flag for new Notes layout (opt-in during development)
  const newNotesEnabled = localStorage.getItem('ENABLE_NEW_NOTES') !== 'false';
  // Feature flag for new AI Chat layout (opt-in, becomes default)
  const newAIChatEnabled = localStorage.getItem('ENABLE_NEW_AI_CHAT') !== 'false';
  // Feature flag for new Neural Studio Upload (opt-in, will become default)
  const newUploadEnabled = localStorage.getItem('ENABLE_NEW_UPLOAD') !== 'false';
  // Feature flag for new Brain Graph (opt-in for testing Phase 3-4)
  const newBrainGraphEnabled = localStorage.getItem('ENABLE_NEW_BRAIN_GRAPH') === 'true';

  // Debug log
  console.log('Brain Graph flag:', newBrainGraphEnabled, 'activeTab:', activeTab);

  const pageInfo = {
    workspace: { title: 'Workspace', description: 'Your personal note-taking workspace' },
    upload: { title: 'Upload Image', description: 'Upload and analyze images with AI' },
    gallery: { title: 'Gallery', description: 'Browse and organize your photos with Immich-inspired layout' },
    notes: { title: 'Smart Notes', description: 'AI-generated notes from your images' },
    graph: { title: 'Brain', description: 'Your knowledge graph - visualize connections between notes and tags' },
    chat: { title: 'Mnemosyne', description: 'Your personal AI assistant - ask questions and get answers with citations from your notes' }
  };

  return (
    <QueryClientProvider client={queryClient}>
      <div className="App">
        <Sidebar
          activeTab={activeTab}
          onTabChange={handleTabChange}
          username={username}
          onLogout={handleLogout}
          isDarkMode={isDarkMode}
          onToggleDarkMode={toggleDarkMode}
          onOpenSearch={() => setSearchOpen(true)}
        />

        <UnifiedSearch
          isOpen={searchOpen}
          onClose={() => setSearchOpen(false)}
          onResultClick={handleSearchResultClick}
        />

        <main className="main-content">
          {/* Workspace has no wrapper - it uses full viewport */}
          {activeTab === 'workspace' && workspaceEnabled ? (
            <ErrorBoundary>
              <Suspense fallback={<LoadingSpinner size="large" message="Loading workspace..." />}>
                <WorkspaceLayout />
              </Suspense>
            </ErrorBoundary>
          ) : activeTab === 'upload' && newUploadEnabled ? (
            /* New Neural Studio Upload - full viewport 2-pane layout */
            <ErrorBoundary>
              <Suspense fallback={<LoadingSpinner size="large" message="Loading Neural Studio..." />}>
                <div className="ng-theme ng-ambient-bg" style={{ width: '100%', height: '100%' }}>
                  <UploadLayout onUploadSuccess={handleImageUploadSuccess} />
                </div>
              </Suspense>
            </ErrorBoundary>
          ) : activeTab === 'gallery' && newGalleryEnabled ? (
            /* New Gallery - full viewport like workspace */
            <ErrorBoundary>
              <Suspense fallback={<LoadingSpinner size="large" message="Loading gallery..." />}>
                <div className="ng-theme ng-ambient-bg" style={{ width: '100%', height: '100%' }}>
                  <GalleryLayout
                    onNavigateToNote={handleNavigateToNote}
                    onNavigateToAI={handleNavigateToAI}
                    selectedImageId={selectedImageId}
                    onClearSelection={() => setSelectedImageId(null)}
                  />
                </div>
              </Suspense>
            </ErrorBoundary>
          ) : activeTab === 'notes' && newNotesEnabled ? (
            /* New Notes - full viewport 3-pane layout */
            <ErrorBoundary>
              <Suspense fallback={<LoadingSpinner size="large" message="Loading notes..." />}>
                <div className="ng-theme ng-ambient-bg" style={{ width: '100%', height: '100%' }}>
                  <NoteLayout
                    onNavigateToGraph={handleNavigateToGraph}
                    onNavigateToImage={handleNavigateToImage}
                    onNavigateToAI={handleNavigateToAI}
                    selectedNoteId={selectedNoteId}
                  />
                </div>
              </Suspense>
            </ErrorBoundary>
          ) : activeTab === 'chat' && newAIChatEnabled ? (
            /* New AI Chat - full viewport 3-pane layout */
            <ErrorBoundary>
              <Suspense fallback={<LoadingSpinner size="large" message="Loading AI chat..." />}>
                <div className="ng-theme ng-ambient-bg" style={{ width: '100%', height: '100%' }}>
                  <AIChatLayout
                    onNavigateToNote={handleNavigateToNote}
                    onNavigateToImage={handleNavigateToImage}
                    initialContext={aiChatContext}
                    onClearContext={clearAiChatContext}
                  />
                </div>
              </Suspense>
            </ErrorBoundary>
          ) : activeTab === 'graph' && newBrainGraphEnabled ? (
            /* New Brain Graph - Neural Glass styled graph visualization */
            <ErrorBoundary>
              <Suspense fallback={<LoadingSpinner size="large" message="Loading brain graph..." />}>
                <div className="ng-theme ng-ambient-bg" style={{ width: '100%', height: '100%' }}>
                  <BrainGraph
                    onNavigate={(path) => {
                      if (path.startsWith('/notes/')) {
                        handleNavigateToNote(parseInt(path.split('/')[2]));
                      } else if (path.startsWith('/gallery')) {
                        const imageId = new URLSearchParams(path.split('?')[1]).get('image');
                        if (imageId) handleNavigateToImage(parseInt(imageId));
                      } else if (path.startsWith('/tags/')) {
                        handleNavigateToTag(path.split('/')[2]);
                      }
                    }}
                    showLeftPanel={true}
                    showInspector={true}
                  />
                </div>
              </Suspense>
            </ErrorBoundary>
          ) : (
            <div className="content-wrapper fade-in">
              <div className="page-header">
                <h1 className="page-title">{pageInfo[activeTab].title}</h1>
                <p className="page-description">{pageInfo[activeTab].description}</p>
              </div>

              {activeTab === 'upload' && <ImageUpload onUploadSuccess={handleImageUploadSuccess} />}
              {activeTab === 'gallery' && (
                <ErrorBoundary>
                  <Suspense fallback={<LoadingSpinner message="Loading gallery..." />}>
                    <VirtualizedImageGallery
                      refreshTrigger={refreshTrigger}
                      selectedImageId={selectedImageId}
                      onViewNote={handleNavigateToNote}
                    />
                  </Suspense>
                </ErrorBoundary>
              )}
              {activeTab === 'notes' && (
                <ErrorBoundary>
                  <Suspense fallback={<LoadingSpinner message="Loading notes..." />}>
                    <VirtualizedNoteList onNavigateToGraph={handleNavigateToGraph} selectedNoteId={selectedNoteId} searchQuery={searchQuery} />
                  </Suspense>
                </ErrorBoundary>
              )}
              {activeTab === 'graph' && (
                <ErrorBoundary>
                  <Suspense fallback={<LoadingSpinner message="Loading knowledge graph..." />}>
                    <KnowledgeGraph onNavigateToNote={handleNavigateToNote} onNavigateToImage={handleNavigateToImage} onNavigateToTag={handleNavigateToTag} />
                  </Suspense>
                </ErrorBoundary>
              )}
              {activeTab === 'chat' && (
                <ErrorBoundary>
                  <Suspense fallback={<LoadingSpinner message="Loading AI chat..." />}>
                    <RAGChat
                      mode="standalone"
                      onNavigateToNote={handleNavigateToNote}
                      onNavigateToImage={handleNavigateToImage}
                    />
                  </Suspense>
                </ErrorBoundary>
              )}
            </div>
          )}
        </main>
      </div>
    </QueryClientProvider>
  );
}

export default App;
