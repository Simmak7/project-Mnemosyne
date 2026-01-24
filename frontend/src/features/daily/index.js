/**
 * Daily Feature - Daily Driver Workflow
 *
 * Provides the daily note focused experience with quick capture functionality.
 * This is the default landing experience in the Workspace view.
 */

// Components
export { default as DailyView } from './components/DailyView';
export { default as DailyHeader } from './components/DailyHeader';
export { default as CaptureStream } from './components/CaptureStream';
export { default as TodayOverview } from './components/TodayOverview';

// Hooks
export { useDailyNote } from './hooks/useDailyNote';
export { useCapture } from './hooks/useCapture';
