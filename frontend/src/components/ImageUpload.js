import React, { useState, useRef } from 'react';
import { Upload, X, FileImage } from 'lucide-react';
import './ImageUpload.css';

function ImageUpload({ onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const validateFile = (selectedFile) => {
    if (!selectedFile) {
      return { valid: false, error: 'No file selected' };
    }

    if (!selectedFile.type.startsWith('image/')) {
      return { valid: false, error: 'Please select a valid image file' };
    }

    const maxSize = 10 * 1024 * 1024; // 10MB
    if (selectedFile.size > maxSize) {
      return { valid: false, error: 'File size must be less than 10MB' };
    }

    return { valid: true };
  };

  const handleFileSelect = (selectedFile) => {
    const validation = validateFile(selectedFile);

    if (validation.valid) {
      setFile(selectedFile);
      setMessage('');
      setMessageType('');
    } else {
      setMessage(validation.error);
      setMessageType('error');
      setFile(null);
    }
  };

  const handleFileChange = (e) => {
    e.preventDefault();
    e.stopPropagation();
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      handleFileSelect(selectedFile);
    }
  };

  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile) {
      handleFileSelect(droppedFile);
    }
  };

  const handleDropZoneClick = () => {
    fileInputRef.current?.click();
  };

  const handleRemoveFile = () => {
    setFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    setMessage('');
    setMessageType('');
  };

  const handlePromptChange = (e) => {
    setPrompt(e.target.value);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setMessage('Please select an image file');
      setMessageType('error');
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);
    if (prompt) {
      formData.append('prompt', prompt);
    }

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        setMessage('Please login first');
        setMessageType('error');
        setLoading(false);
        return;
      }

      const response = await fetch('http://localhost:8000/upload-image/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        setMessage('Image uploaded successfully! AI analysis has started.');
        setMessageType('success');
        setFile(null);
        setPrompt('');
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
        onUploadSuccess(data);
      } else if (response.status === 401 || response.status === 403) {
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        setMessage('Session expired. Please login again.');
        setMessageType('error');
        setTimeout(() => {
          window.location.reload();
        }, 1500);
      } else {
        const errorData = await response.json();
        setMessage(`Upload failed: ${errorData.detail}`);
        setMessageType('error');
      }
    } catch (error) {
      setMessage(`Error uploading image: ${error.message}`);
      setMessageType('error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="component-container">
      <h2>Upload Image for AI Analysis</h2>
      {message && (
        <div className={`message ${messageType}`}>
          {message}
        </div>
      )}
      <form onSubmit={handleSubmit} className="upload-form">
        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileChange}
          disabled={loading}
          style={{ display: 'none' }}
          aria-label="File input"
        />

        {/* Drop Zone */}
        <div
          className={`drop-zone ${dragActive ? 'drag-active' : ''} ${file ? 'has-file' : ''} ${loading ? 'disabled' : ''}`}
          onClick={loading ? undefined : handleDropZoneClick}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              handleDropZoneClick();
            }
          }}
        >
          {!file ? (
            <div className="drop-zone-content">
              <Upload className="upload-icon" size={48} />
              <p className="drop-zone-title">Click or drag to upload</p>
              <p className="drop-zone-subtitle">
                Supports: JPG, PNG, GIF, WebP (max 10MB)
              </p>
            </div>
          ) : (
            <div className="file-preview">
              <FileImage className="file-icon" size={40} />
              <div className="file-details">
                <p className="file-name-display">{file.name}</p>
                <p className="file-size">{(file.size / 1024).toFixed(1)} KB</p>
              </div>
              <button
                type="button"
                className="remove-file-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  handleRemoveFile();
                }}
                disabled={loading}
                aria-label="Remove file"
              >
                <X size={20} />
              </button>
            </div>
          )}
        </div>

        <div className="form-group">
          <label htmlFor="prompt-input">Analysis Prompt (optional):</label>
          <textarea
            id="prompt-input"
            value={prompt}
            onChange={handlePromptChange}
            placeholder="e.g., 'Identify all objects in this image' or 'Extract text from this document'"
            rows="4"
            disabled={loading}
          />
        </div>

        <button type="submit" disabled={!file || loading} className="submit-button">
          {loading ? (
            <>
              <span className="loading-spinner"></span>
              <span>Uploading...</span>
            </>
          ) : (
            <>
              <Upload size={18} />
              <span>Upload & Analyze</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
}

export default ImageUpload;

