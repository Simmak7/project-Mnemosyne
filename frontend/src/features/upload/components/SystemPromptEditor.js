/**
 * SystemPromptEditor - Collapsible view/edit for the system prompt
 * Collapsed by default with a toggle, edit/save/reset when expanded
 */

import React, { useState } from 'react';
import { Edit3, Save, RotateCcw, ChevronDown, ChevronRight } from 'lucide-react';

function SystemPromptEditor({
  defaultPrompt,
  customPrompt,
  isCustom,
  onSave,
  onReset,
  isSaving,
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [draft, setDraft] = useState(customPrompt || defaultPrompt || '');

  const displayPrompt = customPrompt || defaultPrompt || '';

  const handleEdit = () => {
    setDraft(displayPrompt);
    setIsEditing(true);
    setIsOpen(true);
  };

  const handleSave = async () => {
    await onSave(draft);
    setIsEditing(false);
  };

  const handleReset = async () => {
    await onReset();
    setIsEditing(false);
    setDraft(defaultPrompt || '');
  };

  const handleCancel = () => {
    setIsEditing(false);
    setDraft(displayPrompt);
  };

  return (
    <div className="system-prompt-editor">
      <div className="system-prompt-header">
        <button
          className="system-prompt-toggle"
          onClick={() => setIsOpen(!isOpen)}
        >
          {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          <span>{isOpen ? 'Hide Prompt' : 'View Prompt'}</span>
          {isCustom && <span className="system-prompt-badge">Custom</span>}
        </button>
        <div className="system-prompt-actions">
          {isEditing ? (
            <>
              <button
                className="system-prompt-btn system-prompt-save"
                onClick={handleSave}
                disabled={isSaving}
                title="Save prompt"
              >
                <Save size={13} />
                {isSaving ? 'Saving...' : 'Save'}
              </button>
              <button
                className="system-prompt-btn"
                onClick={handleCancel}
                title="Cancel editing"
              >
                Cancel
              </button>
            </>
          ) : (
            <button
              className="system-prompt-btn"
              onClick={handleEdit}
              title="Edit prompt"
            >
              <Edit3 size={13} />
              Edit
            </button>
          )}
          {isCustom && !isEditing && (
            <button
              className="system-prompt-btn system-prompt-reset"
              onClick={handleReset}
              disabled={isSaving}
              title="Reset to default prompt"
            >
              <RotateCcw size={13} />
              Reset
            </button>
          )}
        </div>
      </div>

      {isOpen && (
        <>
          {isEditing ? (
            <textarea
              className="system-prompt-textarea ng-glass-inset"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              rows={12}
              spellCheck={false}
            />
          ) : (
            <div className="system-prompt-preview">
              {displayPrompt}
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default SystemPromptEditor;
