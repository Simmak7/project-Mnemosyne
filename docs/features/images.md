# Images Feature

The images feature provides AI-powered image upload, analysis, and automatic note generation.

---

## Overview

When you upload an image to Mnemosyne:
1. Image is stored immediately
2. AI analysis is queued (async)
3. AI generates description, title, and tags
4. A linked note is created automatically
5. Results appear in your gallery and notes

**Key principle:** AI processing never blocks the user interface.

---

## AI Analysis Pipeline

### Processing Flow

```
Upload Image
    ↓ (instant response)
Return task_id + queued status
    ↓
Celery Worker picks up task
    ↓
Ollama Vision Model analyzes image (30-60s)
    ├── Generate detailed description
    ├── Extract/generate title
    └── Identify relevant tags
    ↓
Create Note with AI content
    ↓
Link Image to Note
    ↓
Add Tags (create if new)
    ↓
Update status: completed
    ↓
Client polls task status → sees results
```

### Supported Models

| Model | Size | Quality | Speed |
|-------|------|---------|-------|
| `llama3.2-vision:11b` | 4.7GB | High | 30-60s |
| `qwen2.5vl:7b-q4_K_M` | 4GB | Medium | 20-40s |

---

## Uploading Images

### API Request

```http
POST /upload-image/
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <binary image data>
```

### Response (Immediate)

```json
{
  "id": 123,
  "task_id": "abc-123-def",
  "status": "queued",
  "filename": "image.jpg",
  "message": "Image queued for AI analysis"
}
```

### Supported Formats

- JPEG / JPG
- PNG
- GIF
- WebP
- HEIC (converted on upload)

### Size Limits

- Maximum file size: 10MB (configurable)
- Recommended: < 5MB for faster processing

---

## Checking Processing Status

Poll the task status endpoint:

```http
GET /task-status/{task_id}
Authorization: Bearer <token>
```

### Status Values

| Status | Description |
|--------|-------------|
| `queued` | Waiting in Celery queue |
| `processing` | AI actively analyzing |
| `completed` | Analysis finished successfully |
| `failed` | Error during processing |

### Completed Response

```json
{
  "status": "completed",
  "result": {
    "image_id": 123,
    "note_id": 456,
    "title": "Sunset Over Mountains",
    "description": "A beautiful sunset with orange and purple hues...",
    "tags": ["sunset", "mountains", "landscape", "nature"]
  }
}
```

### Failed Response

```json
{
  "status": "failed",
  "error": "Ollama service unavailable",
  "retry_available": true
}
```

---

## Retrying Failed Analysis

If processing fails:

```http
POST /retry-image/{id}
Authorization: Bearer <token>
```

Response:
```json
{
  "task_id": "new-task-id",
  "status": "queued",
  "message": "Image requeued for analysis"
}
```

**Rate limit:** 10 retries per minute

---

## Title Generation

AI extracts titles using this priority order:

### 1. Subject Extraction
Look for patterns like "shows a [SUBJECT]" in the description.

### 2. Noun Phrase Extraction
Extract the main noun phrase from the first sentence.

### 3. Pattern Matching
Match patterns: "contains", "depicts", "features".

### 4. EXIF Metadata
Use date and location from image metadata.

### 5. Filename Cleanup
Last resort: clean up the filename (remove UUID, extensions).

---

## Tag Extraction

### Adaptive Tag Extraction

The AI identifies tags from:
- Objects in the image
- Scene type (indoor, outdoor, etc.)
- Activities or actions
- Colors and mood
- Location indicators

### Tag Normalization

All tags are:
- Converted to lowercase
- Trimmed of whitespace
- Deduplicated
- Limited to relevant terms

---

## Blur Hash Placeholders

Mnemosyne generates blur hashes for instant visual feedback:

### What is Blur Hash?

A compact string (~20-30 chars) representing a blurred thumbnail:
```
LKO2?U%2Tw=w]~RBVZRi};RPxuwH
```

### Generation

On upload:
1. Image resized to thumbnail
2. Blur hash computed
3. Stored in `blur_hash` field

### Usage

Frontend displays blur hash while full image loads:
1. Show decoded blur hash (instant)
2. Load full image in background
3. Fade in full image when ready

---

## Image-Note Relationship

Every image has an associated note:

```
Image Upload
    ↓
AI Analysis
    ↓
Create Note
    ├── Title: AI-generated
    ├── Content: AI description
    └── Tags: AI-extracted
    ↓
Link Image ↔ Note
```

### Benefits

- Search finds images via note content
- Images appear in knowledge graph
- RAG chat can reference images
- Unified tagging system

---

## Gallery View

Images are displayed in a justified grid layout:

### Features

- **Justified rows** - Photos fill available width
- **Aspect ratio preservation** - No cropping
- **Date grouping** - Organized by upload date
- **Blur hash placeholders** - Instant feedback
- **Lazy loading** - Performance optimization

### Navigation

- Click: Select image
- Double-click: Open lightbox
- Arrow keys: Navigate in lightbox
- Escape: Close lightbox

---

## API Endpoints

### Upload and Processing

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| POST | `/upload-image/` | Upload image | 20/min |
| GET | `/task-status/{id}` | Check task status | - |
| POST | `/retry-image/{id}` | Retry failed | 10/min |

### Retrieval

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/images/` | List user images |
| GET | `/image/{id}` | Get image file |
| DELETE | `/images/{id}` | Delete image |

### Tag Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/images/{id}/tags/{name}` | Add tag |
| DELETE | `/images/{id}/tags/{tag_id}` | Remove tag |

---

## Image Metadata

### Stored Fields

| Field | Description |
|-------|-------------|
| `filename` | Original filename |
| `file_path` | Storage path |
| `mime_type` | MIME type (image/jpeg, etc.) |
| `file_size` | Size in bytes |
| `width` | Pixel width |
| `height` | Pixel height |
| `blur_hash` | Blur hash string |
| `analysis_status` | Processing status |
| `ai_description` | Generated description |

### EXIF Extraction

When available:
- Camera make/model
- Date taken
- GPS coordinates
- Orientation

---

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Ollama unavailable` | AI service down | Check Ollama container |
| `Model not found` | Model not downloaded | Pull model |
| `Timeout` | Analysis too slow | Retry or check resources |
| `Invalid image` | Corrupted file | Upload different file |

### Retry Strategy

Failed images can be retried:
1. Check error message
2. Fix underlying issue (if possible)
3. Call retry endpoint
4. Monitor new task status

---

## Performance Tips

### Upload Optimization

1. **Resize before upload** - Smaller files process faster
2. **Use JPEG for photos** - Better compression
3. **Batch wisely** - Don't overwhelm the queue

### Processing Speed

1. **GPU acceleration** - Enable for Ollama
2. **Model selection** - Smaller models are faster
3. **Queue management** - Scale Celery workers

---

## Best Practices

1. **Wait for completion** - Don't assume instant processing
2. **Handle failures gracefully** - Retry when appropriate
3. **Check task status** - Poll periodically, not continuously
4. **Use blur hashes** - Better user experience
5. **Review AI results** - Edit titles/tags if needed
