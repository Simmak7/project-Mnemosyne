import {
  Search, Upload, Image, FileScan, FileText,
  BookOpen, Brain, Sparkles, Settings
} from 'lucide-react';

/**
 * Accent theme keys map to Neural Glass CSS variables:
 * 'ai'    -> --ng-accent-ai-*
 * 'image' -> --ng-accent-image-*
 * 'note'  -> --ng-accent-note-*
 * 'link'  -> --ng-accent-link-*
 */

export const ONBOARDING_STEPS = [
  // Step 0 - Welcome
  {
    type: 'welcome',
    title: 'Welcome to Mnemosyne',
    subtitle: 'Your AI-Powered Knowledge Companion',
    description:
      'Mnemosyne helps you capture, organize, and rediscover your ideas ' +
      'using intelligent image recognition, smart notes, and AI-powered search.',
  },

  // Step 1
  {
    type: 'feature',
    title: 'Instant Search',
    icon: Search,
    accent: 'ai',
    description:
      'Find anything across your entire knowledge base in milliseconds. ' +
      'Search spans notes, images, documents, and tags simultaneously.',
    tips: [
      'Press Ctrl+K (or Cmd+K) to open search from anywhere',
      'Results are ranked by relevance using AI embeddings',
    ],
  },

  // Step 2
  {
    type: 'feature',
    title: 'Neural Studio',
    icon: Upload,
    accent: 'image',
    description:
      'Upload images and documents to have AI analyze them automatically. ' +
      'Get intelligent descriptions, extracted text, and auto-generated tags.',
    tips: [
      'Drag and drop files directly onto the upload area',
      'AI processes images in the background - no waiting required',
      'Supported: images (JPG, PNG, WebP) and PDFs',
    ],
  },

  // Step 3
  {
    type: 'feature',
    title: 'Photo Gallery',
    icon: Image,
    accent: 'image',
    description:
      'Browse your images in a beautiful masonry grid with instant previews. ' +
      'Filter by tags, search by content, and manage collections.',
    tips: [
      'Click any image for a detailed view with AI analysis',
      'Use tag filters to narrow down your gallery',
    ],
  },

  // Step 4
  {
    type: 'feature',
    title: 'Document Management',
    icon: FileScan,
    accent: 'note',
    description:
      'Upload, preview, and organize PDF documents. AI extracts key information ' +
      'and makes your documents fully searchable.',
    tips: [
      'Documents are automatically indexed for RAG chat',
      'Organize files into collections for better structure',
    ],
  },

  // Step 5
  {
    type: 'feature',
    title: 'Smart Notes',
    icon: FileText,
    accent: 'note',
    description:
      'Write rich-text notes with a powerful block editor. Link notes to images, ' +
      'documents, and other notes to build a connected knowledge web.',
    tips: [
      'Use tags to categorize and cross-reference your notes',
      'Notes are included in AI search and chat context',
    ],
  },

  // Step 6
  {
    type: 'feature',
    title: 'Daily Journal',
    icon: BookOpen,
    accent: 'link',
    description:
      'Capture daily thoughts with a calendar-based journal. Each day gets its own ' +
      'note, making it easy to track ideas over time.',
    tips: [
      'Navigate between days using the calendar sidebar',
      'Journal entries are searchable like regular notes',
    ],
  },

  // Step 7
  {
    type: 'feature',
    title: 'Knowledge Brain',
    icon: Brain,
    accent: 'ai',
    description:
      'Visualize your entire knowledge base as an interactive 3D graph. See how ' +
      'notes, images, and tags connect to reveal hidden patterns.',
    tips: [
      'Click any node to inspect it and navigate to the source',
      'The brain builds automatically from your content',
    ],
  },

  // Step 8
  {
    type: 'feature',
    title: 'Mnemos AI Chat',
    icon: Sparkles,
    accent: 'ai',
    description:
      'Chat with an AI that has full context of your knowledge base. Ask questions, ' +
      'get summaries, and discover connections you never knew existed.',
    tips: [
      'Switch between Nexus RAG (search-based retrieval) and Zaia AI (brain mode)',
      'The AI cites its sources so you can verify answers',
      'Context Radar shows exactly which files inform each response',
    ],
  },

  // Step 9
  {
    type: 'feature',
    title: 'Make It Yours',
    icon: Settings,
    accent: 'link',
    description:
      'Customize AI models, toggle features, export your data, and personalize ' +
      'the experience. Access settings from the user menu in the sidebar.',
    tips: [
      'Choose between local (Ollama) and cloud AI models',
      'Toggle dark/light mode with the theme switch',
    ],
  },

  // Step 10 - Completion
  {
    type: 'completion',
    title: "You're Ready!",
    description:
      'You now know everything you need to get started. Explore, create, ' +
      'and let Mnemosyne help you build your second brain.',
  },
];

export const TOTAL_STEPS = ONBOARDING_STEPS.length;
