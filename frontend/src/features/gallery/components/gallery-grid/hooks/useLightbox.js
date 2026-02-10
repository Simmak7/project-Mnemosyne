import { useState, useEffect, useCallback } from 'react';

/**
 * Hook for lightbox state and navigation
 */
export function useLightbox({
  sortedImages,
  images,
  selectedImageId,
  onClearImageSelection,
  renameImage,
}) {
  const [selectedImage, setSelectedImage] = useState(null);

  // Open lightbox
  const openLightbox = useCallback((image) => {
    setSelectedImage(image);
  }, []);

  // Close lightbox
  const closeLightbox = useCallback(() => {
    setSelectedImage(null);
  }, []);

  // Navigate between images in lightbox
  const handleLightboxNavigate = useCallback((direction) => {
    if (!selectedImage) return;

    const allImages = sortedImages;
    const currentIndex = allImages.findIndex(img => img.id === selectedImage.id);

    let newIndex;
    if (direction === 'prev') {
      newIndex = currentIndex > 0 ? currentIndex - 1 : allImages.length - 1;
    } else {
      newIndex = currentIndex < allImages.length - 1 ? currentIndex + 1 : 0;
    }

    setSelectedImage(allImages[newIndex]);
  }, [selectedImage, sortedImages]);

  // Sync selectedImage with updated images data (for optimistic updates)
  useEffect(() => {
    if (selectedImage && images.length > 0) {
      const updatedImage = images.find(img => img.id === selectedImage.id);
      if (updatedImage && (
        updatedImage.is_favorite !== selectedImage.is_favorite ||
        updatedImage.display_name !== selectedImage.display_name
      )) {
        setSelectedImage(updatedImage);
      }
    }
  }, [images, selectedImage]);

  // Open lightbox when navigating from another view with selectedImageId
  useEffect(() => {
    if (selectedImageId && images.length > 0) {
      const imageToOpen = images.find(img => img.id === selectedImageId);
      if (imageToOpen) {
        setSelectedImage(imageToOpen);
        if (onClearImageSelection) {
          onClearImageSelection();
        }
      }
    }
  }, [selectedImageId, images, onClearImageSelection]);

  // Handle image rename
  const handleRenameImage = useCallback((imageId, displayName) => {
    renameImage({ imageId, displayName });
  }, [renameImage]);

  return {
    selectedImage,
    openLightbox,
    closeLightbox,
    handleLightboxNavigate,
    handleRenameImage,
  };
}
