/**
 * ConversationItem - Single conversation item with edit/delete
 */
import React from 'react';
import {
  MessageSquare,
  Trash2,
  MoreHorizontal,
  Pencil,
  Check,
  X,
} from 'lucide-react';

function ConversationItem({
  conv,
  isActive,
  isEditing,
  editTitle,
  setEditTitle,
  activeMenu,
  setActiveMenu,
  editInputRef,
  onSelect,
  onStartEdit,
  onSaveEdit,
  onCancelEdit,
  onEditKeyDown,
  onDelete,
}) {
  return (
    <div
      className={`conversation-item ${isActive ? 'active' : ''} ${isEditing ? 'editing' : ''}`}
      onClick={() => !isEditing && onSelect(conv)}
    >
      <MessageSquare size={16} className="conversation-icon" />

      {isEditing ? (
        <div className="conversation-edit-wrapper">
          <input
            ref={editInputRef}
            type="text"
            className="conversation-edit-input"
            value={editTitle}
            onChange={(e) => setEditTitle(e.target.value)}
            onKeyDown={(e) => onEditKeyDown(e, conv.id)}
            onClick={(e) => e.stopPropagation()}
          />
          <button
            className="conversation-edit-btn save"
            onClick={(e) => onSaveEdit(e, conv.id)}
            title="Save"
          >
            <Check size={14} />
          </button>
          <button
            className="conversation-edit-btn cancel"
            onClick={onCancelEdit}
            title="Cancel"
          >
            <X size={14} />
          </button>
        </div>
      ) : (
        <>
          <span className="conversation-title">
            {conv.title || 'Untitled conversation'}
          </span>
          <button
            className="conversation-menu-btn"
            onClick={(e) => {
              e.stopPropagation();
              setActiveMenu(activeMenu === conv.id ? null : conv.id);
            }}
          >
            <MoreHorizontal size={14} />
          </button>

          {activeMenu === conv.id && (
            <div className="conversation-menu">
              <button
                className="conversation-menu-item"
                onClick={(e) => onStartEdit(e, conv)}
              >
                <Pencil size={14} />
                Rename
              </button>
              <button
                className="conversation-menu-item delete"
                onClick={(e) => onDelete(e, conv.id)}
              >
                <Trash2 size={14} />
                Delete
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default ConversationItem;
