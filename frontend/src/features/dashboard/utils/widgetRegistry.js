/**
 * widgetRegistry - Static registry of all dashboard widgets
 *
 * Each widget has an id, title, and icon. Used by WidgetManager and config.
 */
import {
  Zap, Heart, Sparkles, Calendar, CheckSquare, Upload,
  Brain, Server, FileText, Tag, Link, Activity,
} from 'lucide-react';

const WIDGET_REGISTRY = [
  { id: 'brain-focus', title: 'Brain Focus', icon: Zap },
  { id: 'quick-capture', title: 'Quick Capture', icon: Sparkles },
  { id: 'calendar', title: 'Calendar', icon: Calendar },
  { id: 'favorites', title: 'Favorite Images', icon: Heart },
  { id: 'tasks', title: 'Tasks', icon: CheckSquare },
  { id: 'quick-upload', title: 'Quick Upload', icon: Upload },
  { id: 'knowledge-graph', title: 'Knowledge Graph', icon: Brain },
  { id: 'system-status', title: 'System Status', icon: Server },
  { id: 'recent-notes', title: 'Recent Notes', icon: FileText },
  { id: 'top-tags', title: 'Top Tags', icon: Tag },
  { id: 'most-connected', title: 'Most Connected', icon: Link },
  { id: 'ai-activity', title: 'AI Activity', icon: Activity },
];

export function getWidget(id) {
  return WIDGET_REGISTRY.find(w => w.id === id) || null;
}

export function getAllWidgetIds() {
  return WIDGET_REGISTRY.map(w => w.id);
}

export default WIDGET_REGISTRY;
