/**
 * MetricsRow - Four metric cards in a horizontal row
 */
import React from 'react';
import { FileText, Image, FileScan, Tag } from 'lucide-react';
import MetricCard from './MetricCard';
import './MetricsRow.css';

function getNotesCount(data) {
  if (data.graphStats?.node_counts?.note != null) return data.graphStats.node_counts.note;
  if (Array.isArray(data.recentNotes)) return data.recentNotes.length;
  return null;
}

function getImagesCount(data) {
  if (data.graphStats?.node_counts?.image != null) return data.graphStats.node_counts.image;
  if (Array.isArray(data.images)) return data.images.length;
  if (data.images?.total != null) return data.images.total;
  return null;
}

function getDocumentsCount(data) {
  if (data.documents?.total != null) return data.documents.total;
  if (Array.isArray(data.documents?.documents)) return data.documents.documents.length;
  return null;
}

function getTagsCount(data) {
  if (Array.isArray(data.tags)) return data.tags.length;
  if (data.graphStats?.node_counts?.tag != null) return data.graphStats.node_counts.tag;
  return null;
}

function getTopTag(data) {
  if (!Array.isArray(data.tags) || data.tags.length === 0) return null;
  const sorted = [...data.tags].sort((a, b) => (b.note_count || 0) - (a.note_count || 0));
  return sorted[0]?.name || null;
}

function MetricsRow({ data, onTabChange }) {
  const topTag = getTopTag(data);

  return (
    <div className="metrics-row">
      <MetricCard
        icon={FileText}
        value={getNotesCount(data)}
        label="Notes"
        accent="note"
        onClick={() => onTabChange('notes')}
      />
      <MetricCard
        icon={Image}
        value={getImagesCount(data)}
        label="Images"
        accent="image"
        onClick={() => onTabChange('gallery')}
      />
      <MetricCard
        icon={FileScan}
        value={getDocumentsCount(data)}
        label="Documents"
        accent="document"
        onClick={() => onTabChange('documents')}
      />
      <MetricCard
        icon={Tag}
        value={getTagsCount(data)}
        label="Tags"
        subtitle={topTag ? `top: #${topTag}` : undefined}
        accent="tag"
        onClick={() => onTabChange('notes')}
      />
    </div>
  );
}

export default MetricsRow;
