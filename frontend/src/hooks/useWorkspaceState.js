import { useContext } from 'react';
import { WorkspaceContext } from '../contexts/WorkspaceContext';

/**
 * Custom hook to access workspace state and methods
 * @returns {Object} Workspace state and methods
 */
export const useWorkspaceState = () => {
  const context = useContext(WorkspaceContext);

  if (!context) {
    throw new Error('useWorkspaceState must be used within a WorkspaceProvider');
  }

  return context;
};
