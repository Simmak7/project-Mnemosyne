import React, { lazy, Suspense, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import './App.css';

// Neural Glass Design System
import './styles/neural-glass/index.css';

// Hooks
import { useAuth } from './hooks/useAuth';
import { useTheme } from './hooks/useTheme';
import { useAppNavigation } from './hooks/useAppNavigation';
import { useIsMobile } from './hooks/useIsMobile';
import { useViewportHeight } from './hooks/useViewportHeight';
import { useTabSwipe } from './hooks/useTabSwipe';

// Config
import { getFeatureFlags } from './config/featureFlags';

// Feature imports
import { Login, EmailVerification } from './features/auth';

// Component imports
import Sidebar from './components/Sidebar';
import MobileBottomNav from './components/MobileBottomNav';
import UnifiedSearch from './components/search/UnifiedSearch';
import LoadingSpinner from './components/LoadingSpinner';
import ErrorBoundary from './components/ErrorBoundary';
import { ToastProvider } from './components/toast';

// Lazy load heavy components — direct file imports avoid pulling entire barrel exports
const OnboardingModal = lazy(() => import('./features/onboarding/components/OnboardingModal'));
const GalleryLayout = lazy(() => import('./features/gallery/components/GalleryLayout'));
const NoteLayout = lazy(() => import('./features/notes/components/NoteLayout'));
const BrainGraph = lazy(() => import('./features/brain-graph/components/BrainGraph').then(m => ({ default: m.BrainGraph })));
const AIChatLayout = lazy(() => import('./features/ai_chat/components/AIChatLayout'));
const JournalLayout = lazy(() => import('./features/journal/components/JournalLayout'));
const UploadLayout = lazy(() => import('./features/upload/components/UploadLayout'));
const DocumentLayout = lazy(() => import('./features/documents/components/DocumentLayout'));
const DashboardLayout = lazy(() => import('./features/dashboard/components/DashboardLayout'));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { refetchOnWindowFocus: false, retry: 1, staleTime: 30000 },
  },
});

function App() {
  const { isAuthenticated, username, handleLoginSuccess, handleLogout } = useAuth();
  const { isDarkMode, toggleDarkMode } = useTheme();
  const isMobile = useIsMobile();
  const { isKeyboardOpen } = useViewportHeight();
  const nav = useAppNavigation();
  const [brainMounted, setBrainMounted] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const { touchHandlers, navDirection, directionTabChange } = useTabSwipe({ activeTab: nav.activeTab, onTabChange: nav.handleTabChange, onOpenDrawer: () => setDrawerOpen(true), enabled: isMobile });

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

  const brainNavigate = (p) => {
    if (p.startsWith('/notes/')) nav.handleNavigateToNote(parseInt(p.split('/')[2]));
    else if (p.startsWith('/gallery')) { const id = new URLSearchParams(p.split('?')[1]).get('image'); if (id) nav.handleNavigateToImage(parseInt(id)); }
    else if (p.startsWith('/tags/')) nav.handleNavigateToTag(p.split('/')[2]);
    else if (p.startsWith('/documents/')) nav.handleNavigateToDocument(parseInt(p.split('/')[2]));
  };

  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
      <div className="App">
        {isMobile ? (
          <MobileBottomNav
            activeTab={tab}
            onTabChange={directionTabChange}
            username={username}
            onLogout={handleLogout}
            isDarkMode={isDarkMode}
            onToggleDarkMode={toggleDarkMode}
            onOpenSearch={() => nav.setSearchOpen(true)}
            isKeyboardOpen={isKeyboardOpen}
            isDrawerOpen={drawerOpen}
            onOpenDrawer={() => setDrawerOpen(true)}
            onCloseDrawer={() => setDrawerOpen(false)}
          />
        ) : (
          <Sidebar
            activeTab={tab}
            onTabChange={nav.handleTabChange}
            username={username}
            onLogout={handleLogout}
            isDarkMode={isDarkMode}
            onToggleDarkMode={toggleDarkMode}
            onOpenSearch={() => nav.setSearchOpen(true)}
            onLogoClick={() => nav.handleTabChange('dashboard')}
          />
        )}

        <UnifiedSearch
          isOpen={nav.searchOpen}
          onClose={() => nav.setSearchOpen(false)}
          onResultClick={nav.handleSearchResultClick}
        />

        <Suspense fallback={null}>
          <OnboardingModal />
        </Suspense>

        {/* Main content area - hidden when Brain is active */}
        <main className="main-content" style={brainActive ? { display: 'none' } : undefined} {...touchHandlers}>
          <AnimatePresence mode="wait">
          <motion.div
            key={tab}
            initial={isMobile ? { opacity: 0, x: navDirection.current * 60 } : { opacity: 0 }}
            animate={{ opacity: 1, x: 0 }}
            exit={isMobile ? { opacity: 0, x: navDirection.current * -60 } : { opacity: 0 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
            style={{ width: '100%', height: '100%' }}
          >
          {tab === 'dashboard' ? (
            <ErrorBoundary>
              <Suspense fallback={<LoadingSpinner size="large" message="Loading dashboard..." />}>
                <div className="ng-theme ng-ambient-bg" style={{ width: '100%', height: '100%' }}>
                  <DashboardLayout
                    onNavigateToNote={nav.handleNavigateToNote}
                    onNavigateToImage={nav.handleNavigateToImage}
                    onNavigateToDocument={nav.handleNavigateToDocument}
                    onNavigateToTag={nav.handleNavigateToTag}
                    onNavigateToSearch={nav.handleNavigateToSearch}
                    onTabChange={nav.handleTabChange}
                    onUploadSuccess={nav.handleImageUploadSuccess}
                  />
                </div>
              </Suspense>
            </ErrorBoundary>
          ) : tab === 'journal' && flags.journalEnabled ? (
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
              <Suspense fallback={<LoadingSpinner size="large" message="Loading Upload..." />}>
                <div className="ng-theme ng-ambient-bg" style={{ width: '100%', height: '100%' }}>
                  <UploadLayout
                    onUploadSuccess={nav.handleImageUploadSuccess}
                    onNavigateToDocument={nav.handleNavigateToDocument}
                    onNavigateToImage={nav.handleNavigateToImage}
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
                    initialSearchQuery={nav.searchQuery}
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
          </motion.div>
          </AnimatePresence>
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
      </ToastProvider>
    </QueryClientProvider>
  );
}

export default App;
