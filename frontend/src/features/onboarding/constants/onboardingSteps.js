import {
  Search, Upload, Image, FileScan, FileText,
  BookOpen, Brain, Sparkles, Settings
} from 'lucide-react';

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

  // Step 1 - Upload & Discover
  {
    type: 'feature',
    title: 'Upload & Discover',
    icon: Upload,
    secondaryIcons: [Image, FileScan],
    accent: 'image',
    description:
      'Drop any file — photos, PDFs, documents. AI analyzes everything automatically. ' +
      'Find your content organized in Gallery and Documents.',
    tips: [
      'Drag and drop files directly onto the upload area',
      'AI processes files in the background — no waiting required',
      'Browse photos in Gallery, PDFs in Documents',
    ],
  },

  // Step 2 - Your Knowledge Base
  {
    type: 'feature',
    title: 'Your Knowledge Base',
    icon: FileText,
    secondaryIcons: [BookOpen],
    accent: 'note',
    description:
      'AI creates smart notes from your uploads. Write your own notes with the rich editor. ' +
      'Keep a daily journal with calendar view.',
    tips: [
      'Use tags to categorize and cross-reference your notes',
      'Navigate between days using the Journal calendar sidebar',
    ],
  },

  // Step 3 - AI That Knows You
  {
    type: 'feature',
    title: 'AI That Knows You',
    icon: Sparkles,
    secondaryIcons: [Brain, Search],
    accent: 'ai',
    description:
      'Search everything with Ctrl+K. Visualize connections in the Knowledge Graph. ' +
      'Chat with an AI that has full context of your knowledge.',
    tips: [
      'Press Ctrl+K (or Cmd+K) to search from anywhere',
      'The Knowledge Graph reveals hidden connections between your content',
      'AI cites its sources so you can verify answers',
    ],
  },

  // Step 4 - Completion
  {
    type: 'completion',
    title: "You're Ready!",
    description:
      'You now know everything you need to get started. Explore, create, ' +
      'and let Mnemosyne help you build your second brain. ' +
      'Tip: Press Ctrl+K anytime to search across your entire knowledge base.',
  },
];

export const TOTAL_STEPS = ONBOARDING_STEPS.length;
