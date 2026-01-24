import React, { useEffect, useState } from 'react';
import './ImageGallery.css';

function ImageGallery({ images, refreshTrigger }) {
  const [galleryImages, setGalleryImages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [imageUrls, setImageUrls] = useState({});

  useEffect(() => {
    fetchImages();
  }, [refreshTrigger]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    // Cleanup object URLs when component unmounts
    return () => {
      Object.values(imageUrls).forEach(url => URL.revokeObjectURL(url));
    };
  }, [imageUrls]);

  const fetchImages = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        console.error('No token found, user needs to login');
        setLoading(false);
        return;
      }

      const response = await fetch('http://localhost:8000/images/', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setGalleryImages(data);

        // Fetch image blobs for each image
        await loadImageBlobs(data, token);
      } else if (response.status === 401 || response.status === 403) {
        // Token expired, redirect to login
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        window.location.reload();
      } else {
        console.error('Failed to fetch images:', response.status);
      }
    } catch (error) {
      console.error('Error fetching images:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadImageBlobs = async (images, token) => {
    const urls = {};

    for (const image of images) {
      try {
        const response = await fetch(`http://localhost:8000/image/${image.id}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const blob = await response.blob();
          urls[image.id] = URL.createObjectURL(blob);
        }
      } catch (error) {
        console.error(`Error loading image ${image.id}:`, error);
      }
    }

    setImageUrls(urls);
  };

  return (
    <div className="component-container">
      <h2>Image Gallery</h2>
      {loading ? (
        <div className="loading-container">
          <div className="loading"></div>
          <p>Loading images...</p>
        </div>
      ) : galleryImages.length === 0 ? (
        <p className="no-images">No images uploaded yet. Start by uploading an image!</p>
      ) : (
        <div className="gallery-grid">
          {galleryImages.map((image) => (
            <div key={image.id} className="gallery-item">
              <div className="image-container">
                {imageUrls[image.id] ? (
                  <img
                    src={imageUrls[image.id]}
                    alt={image.filename}
                  />
                ) : (
                  <div className="loading-placeholder">
                    <div className="loading"></div>
                    <p>Loading...</p>
                  </div>
                )}
              </div>
              <div className="image-info">
                <p className="filename">{image.filename}</p>
                <p className="status">
                  Status: <span className={`status-badge ${image.ai_analysis_status}`}>
                    {image.ai_analysis_status}
                  </span>
                </p>
                {image.prompt && (
                  <p className="prompt">
                    <strong>Prompt:</strong> {image.prompt.substring(0, 50)}...
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default ImageGallery;

