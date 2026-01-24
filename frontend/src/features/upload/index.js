/**
 * Upload Feature - Neural Studio
 * Multi-file upload with AI analysis configuration
 *
 * @module features/upload
 */

// Main layout component
export { default as UploadLayout } from './components/UploadLayout';

// Individual components (for customization)
export { default as FileDropZone } from './components/FileDropZone';
export { default as FileList } from './components/FileList';
export { default as FileCard } from './components/FileCard';
export { default as AnalysisConfig } from './components/AnalysisConfig';
export { default as AlbumSelector } from './components/AlbumSelector';

// Hooks
export { useUploadQueue } from './hooks/useUploadQueue';
export { useAnalysisConfig } from './hooks/useAnalysisConfig';

// Utils
export { composePrompt } from './utils/promptComposer';
export { getModelId, MODELS } from './utils/modelMapper';
export { validateFile, ALLOWED_TYPES } from './utils/fileValidation';

// Feature flags
export { UPLOAD_FLAGS } from './utils/featureFlags';
