/**
 * ConversationList - List of conversations grouped by date
 */
import React from 'react';
import { MessageSquare } from 'lucide-react';
import ConversationItem from './ConversationItem';

function ConversationList({
  conversations,
  groupedConversations,
  currentConversationId,
  editingId,
  editTitle,
  setEditTitle,
  activeMenu,
  setActiveMenu,
  editInputRef,
  isLoading,
  onSelect,
  onStartEdit,
  onSaveEdit,
  onCancelEdit,
  onEditKeyDown,
  onDelete,
}) {
  const renderGroup = (title, items) => {
    if (items.length === 0) return null;

    return (
      <div className="conversation-group" key={title}>
        <div className="conversation-group-header">{title}</div>
        {items.map(conv => (
          <ConversationItem
            key={conv.id}
            conv={conv}
            isActive={currentConversationId === conv.id}
            isEditing={editingId === conv.id}
            editTitle={editTitle}
            setEditTitle={setEditTitle}
            activeMenu={activeMenu}
            setActiveMenu={setActiveMenu}
            editInputRef={editInputRef}
            onSelect={onSelect}
            onStartEdit={onStartEdit}
            onSaveEdit={onSaveEdit}
            onCancelEdit={onCancelEdit}
            onEditKeyDown={onEditKeyDown}
            onDelete={onDelete}
          />
        ))}
      </div>
    );
  };

  if (isLoading) {
    return <div className="conversation-loading">Loading...</div>;
  }

  if (conversations.length === 0) {
    return (
      <div className="conversation-empty">
        <MessageSquare size={24} />
        <span>No conversations yet</span>
        <span className="conversation-empty-hint">
          Start a new chat to begin
        </span>
      </div>
    );
  }

  return (
    <>
      {renderGroup('Today', groupedConversations.today)}
      {renderGroup('Yesterday', groupedConversations.yesterday)}
      {renderGroup('Last 7 Days', groupedConversations.lastWeek)}
      {renderGroup('Older', groupedConversations.older)}
    </>
  );
}

export default ConversationList;
