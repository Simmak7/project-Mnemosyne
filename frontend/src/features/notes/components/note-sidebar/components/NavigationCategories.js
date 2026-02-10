import React from 'react';
import {
  Inbox,
  Sparkles,
  FileText,
  Calendar,
  Heart,
  Clock,
  Trash2,
  FileStack,
} from 'lucide-react';

// Navigation categories configuration
export const categories = [
  { id: 'all', label: 'All Notes', icon: FileStack, description: 'All notes' },
  { id: 'inbox', label: 'Inbox', icon: Inbox, description: 'New & recent notes' },
  { id: 'smart', label: 'Smart Notes', icon: Sparkles, description: 'AI-generated notes' },
  { id: 'manual', label: 'Manual Notes', icon: FileText, description: 'User-created notes' },
  { id: 'daily', label: 'Daily Notes', icon: Calendar, description: 'Journal entries' },
  { id: 'favorites', label: 'Favorites', icon: Heart, description: 'Starred notes' },
  { id: 'review', label: 'Review Queue', icon: Clock, description: 'Needs attention', badge: true },
  { id: 'trash', label: 'Trash', icon: Trash2, description: 'Deleted notes (15 days)', isDanger: true }
];

/**
 * Navigation categories list
 */
function NavigationCategories({ currentCategory, categoryCounts, onCategoryClick }) {
  return (
    <nav className="sidebar-nav">
      {categories.map((category) => {
        const Icon = category.icon;
        const isActive = currentCategory === category.id;
        const count = categoryCounts[category.id] || 0;

        return (
          <button
            key={category.id}
            className={`sidebar-nav-item ${isActive ? 'active' : ''} ${category.isDanger ? 'danger-item' : ''}`}
            onClick={() => onCategoryClick(category.id)}
            title={category.description}
          >
            <Icon size={18} className="nav-icon" />
            <span className="nav-label">{category.label}</span>
            {category.badge && count > 0 ? (
              <span className="nav-badge">{count}</span>
            ) : count > 0 ? (
              <span className="nav-count">{count}</span>
            ) : null}
          </button>
        );
      })}
    </nav>
  );
}

export default NavigationCategories;
