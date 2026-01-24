/**
 * Editor Feature - Block Canvas
 * Enhanced TiptapEditor with slash commands and Neural Glass styling
 */

// Components
export { default as BlockEditor } from './components/BlockEditor';
export { default as SlashCommandMenu } from './components/SlashCommandMenu';
export { default as ImageBlock } from './components/ImageBlock';
export { default as NoteLink, NoteLinkInline } from './components/NoteLink';

// Extensions
export {
  SlashCommandExtension,
  defaultSlashCommands
} from './extensions/SlashCommandExtension';

// Hooks
export {
  useSlashCommands,
  configureSlashCommands
} from './hooks/useSlashCommands';
