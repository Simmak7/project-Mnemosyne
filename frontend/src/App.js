import React, { lazy, Suspense, useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import './App.css';

// Neural Glass Design System
import './styles/neural-glass/index.css';

// Hooks
import { useAuth } from './hooks/useAuth';
import { useTheme } from './hooks/useTheme';
import { useAppNavigation } from './hooks/useAppNavigation';

// Config
import { getFeatureFlags } from './config/featureFlags';

// Feature imports
import { Login, EmailVerification } from './features/auth';

// Component imports
import Sidebar from './components/Sidebar';
import UnifiedSearch from './components/search/UnifiedSearch';
import LoadingSpinner from './components/LoadingSpinner';
import ErrorBoundary from './components/ErrorBoundary';

// Lazy load heavy components
const GalleryLayout = lazy(() => import('./features/gallery').then(m => ({ default: m.GalleryLayout })));
const NoteLayout = lazy(() => import('./features/notes').then(m => ({ default: m.NoteLayout })));
const BrainGraph = lazy(() => import('./features/brain-graph').then(m => ({ default: m.BrainGraph })));
const AIChatLayout = lazy(() => import('./features/ai_chat').then(m => ({ default: m.AIChatLayout })));
const JournalLayout = lazy(() => import('./features/journal').then(m => ({ default: m.JournalLayout })));
const UploadLayout = lazy(() => import('./features/upload').then(m => ({ default: m.UploadLayout })));
const DocumentLayout = lazy(() => import('./features/documents').then(m => ({ default: m.DocumentLayout })));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { refetchOnWindowFocus: false, retry: 1, staleTime: 30000 },
  },
});

function App() {
  const { isAuthenticated, username, handleLoginSuccess, handleLogout } = useAuth();
  const { isDarkMode, toggleDarkMode } = useTheme();
  const nav = useAppNavigation();
  // Mount Brain once on first visit, keep alive across tab switches
  const [brainMounted, setBrainMounted] = useState(false);

  if (window.location.pathname === '/verify-email-change') {
    return <EmailVerification onComplete={() => window.location.href = '/'} />;
  }
  if (!isAuthenticated) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  const flags = getFeatureFlags();
  const tab = nav.activeTab;
  const brainActive = tab === 'graph';
  if (brainActive && !brainMounted) setBrainMounted(true);

  const brainNavigate = (path) => {
    if (path.startsWith('/notes/')) {
      nav.handleNavigateToNote(parseInt(path.split('/')[2]));
    } else if (path.startsWith('/gallery')) {
      const id = new URLSearchParams(path.split('?')[1]).get('image');
      if (id) nav.handleNavigateToImage(parseInt(id));
    } else if (path.startsWith('/tags/')) {
      nav.handleNavigateToTag(path.split('/')[2]);
    } else if (path.startsWith('/documents/')) {
      nav.handleNavigateToDocument(parseInt(path.split('/')[2]));
    }
  };

  return (
    <QueryClientProvider client={queryClient}>
      <div className="App">
        <Sidebar
          activeTab={tab}
          onTabChange={nav.handleTabChange}
          username={username}
          onLogout={handleLogout}
          isDarkMode={isDarkMode}
          onToggleDarkMode={toggleDarkMode}
          onOpenSearch={() => nav.setSearchOpen(true)}
        />

        <UnifiedSearch
          isOpen={nav.searchOpen}
          onClose={() => nav.setSearchOpen(false)}
          onResultClick={nav.handleSearchResultClick}
        />

        {/* Main content area - hidden when Brain is active */}
        <main className="main-content" style={brainActive ? { display: 'none' } : undefined}>
          {tab === 'journal' && flags.journalEnabled ? (
            <ErrorBoundary>
              <Suspense fallback={<LoadingSpinner size="large" message="Loading journal..." />}>
                <div className="ng-theme ng-ambient-bg" style={{ width: '100%', height: '100%' }}>
                  <JournalLayout
                    onNavigateToNote={nav.handleNavigateToNote}
                    onNavigateToImage={nav.handleNavigateToImage}
                  />
                </div>
              </Suspense>
            </ErrorBoundary>
          ) : tab === 'upload' ? (
            <ErrorBoundary>
              <Suspense fallback={<LoadingSpinner size="large" message="Loading Neural Studio..." />}>
                <div className="ng-theme ng-ambient-bg" style={{ width: '100%', height: '100%' }}>
                  <UploadLayout
                    onUploadSuccess={nav.handleImageUploadSuccess}
                    onNavigateToDocument={nav.handleNavigateToDocument}
                  />
                </div>
              </Suspense>
            </ErrorBoundary>
          ) : tab === 'gallery' ? (
            <ErrorBoundary>
              <Suspense fallback={<LoadingSpinner size="large" message="Loading gallery..." />}>
                <div className="ng-theme ng-ambient-bg" style={{ width: '100%', height: '100%' }}>
                  <GalleryLayout
                    onNavigateToNote={nav.handleNavigateToNote}
                    onNavigateToAI={nav.handleNavigateToAI}
                    selectedImageId={nav.selectedImageId}
                    onClearSelection={() => nav.setSelectedImageId(null)}
                  />
                </div>
              </Suspense>
            </ErrorBoundary>
          ) : tab === 'notes' ? (
            <ErrorBoundary>
              <Suspense fallback={<LoadingSpinner size="large" message="Loading notes..." />}>
                <div className="ng-theme ng-ambient-bg" style={{ width: '100%', height: '100%' }}>
                  <NoteLayout
                    onNavigateToGraph={nav.handleNavigateToGraph}
                    onNavigateToImage={nav.handleNavigateToImage}
                    onNavigateToAI={nav.handleNavigateToAI}
                    onNavigateToDocument={nav.handleNavigateToDocument}
                    selectedNoteId={nav.selectedNoteId}
                  />
                </div>
              </Suspense>
            </ErrorBoundary>
          ) : tab === 'documents' && flags.documentsEnabled ? (
            <ErrorBoundary>
              <Suspense fallback={<LoadingSpinner size="large" message="Loading documents..." />}>
                <div className="ng-theme ng-ambient-bg" style={{ width: '100%', height: '100%' }}>
                  <DocumentLayout
                    onNavigateToNote={nav.handleNavigateToNote}
                    selectedDocumentId={nav.selectedDocumentId}
                    onClearSelection={() => nav.setSelectedDocumentId(null)}
                  />
                </div>
              </Suspense>
            </ErrorBoundary>
          ) : tab === 'chat' ? (
            <ErrorBoundary>
              <Suspense fallback={<LoadingSpinner size="large" message="Loading AI chat..." />}>
                <div className="ng-theme ng-ambient-bg" style={{ width: '100%', height: '100%' }}>
                  <AIChatLayout
                    onNavigateToNote={nav.handleNavigateToNote}
                    onNavigateToImage={nav.handleNavigateToImage}
                    initialContext={nav.aiChatContext}
                    onClearContext={nav.clearAiChatContext}
                  />
                </div>
              </Suspense>
            </ErrorBoundary>
          ) : null}
        </main>

        {/* BrainGraph: mounted once on first visit, kept alive across tab switches.
            Hidden via display:none, simulation paused when not active. */}
        {brainMounted && (
          <div
            className="main-content ng-theme ng-ambient-bg"
            style={{ display: brainActive ? 'block' : 'none' }}
          >
            <ErrorBoundary>
              <Suspense fallback={<LoadingSpinner size="large" message="Loading brain graph..." />}>
                <BrainGraph
                  initialNodeId={nav.graphFocusNodeId}
                  isVisible={brainActive}
                  onNavigate={brainNavigate}
                  showLeftPanel={true}
                  showInspector={true}
                />
              </Suspense>
            </ErrorBoundary>
          </div>
        )}
      </div>
    </QueryClientProvider>
  );
}

export default App;
