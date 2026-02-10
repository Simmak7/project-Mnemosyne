/**
 * DeleteConfirmModal - Confirmation dialog for image deletion
 */
import React from 'react';
import { X, Trash2 } from 'lucide-react';

function DeleteConfirmModal({
  imageId,
  imageName,
  onClose,
  onConfirm,
  isDeleting,
}) {
  return (
    <div className="delete-modal-overlay" onClick={onClose}>
      <div className="delete-modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="delete-modal-close" onClick={onClose}>
          <X size={20} />
        </button>

        <div className="delete-modal-header">
          <Trash2 size={32} className="delete-modal-icon" />
          <h3>Delete Image?</h3>
        </div>

        <div className="delete-modal-body">
          <p>Are you sure you want to delete this image?</p>
          <p className="delete-modal-filename">{imageName}</p>
          <p className="delete-modal-warning">This action cannot be undone.</p>
        </div>

        <div className="delete-modal-actions">
          <button
            className="delete-modal-cancel-btn"
            onClick={onClose}
          >
            Cancel
          </button>
          <button
            className="delete-modal-confirm-btn"
            onClick={() => onConfirm(imageId)}
            disabled={isDeleting}
          >
            {isDeleting ? 'Deleting...' : 'Delete'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default DeleteConfirmModal;
