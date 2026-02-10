# Documents Feature Improvement Plan

## Analysis Summary

After thorough analysis of the backend (documents feature, graph services, models) and frontend (documents UI, notes UI, graph inspector), here are the key findings:

### What's Working
- PDF upload + async Celery processing pipeline
- AI summarization via Ollama (Qwen)
- Tag suggestions + approval workflow
- Thumbnail generation with blur hash
- Document nodes appear in knowledge graph with SOURCE edges (weight 0.9)
- Note creation from approved documents

### What's Broken / Missing
1. **Wikilinks don't resolve** - AI generates entity names (e.g., "Machine Learning") but these rarely match existing note titles/slugs, so they appear as dead `[[links]]` in note content and create zero graph edges
2. **No "Navigate to Document" from Notes** - Notes have no reverse link to their source document
3. **No "Navigate to Note" from Documents** - The "Summary note created" text isn't a clickable navigation link
4. **Document section UX is minimal** - No sorting, searching, grouping, or preview
5. **Text extraction feedback missing** - User can't tell if text was extracted or only AI-summarized; extraction method not shown in UI
6. **Focus mode doesn't show document connections** - Need to verify edge rendering for SOURCE type

---

## Implementation Plan (Priority Order)

### Phase 1: Fix Wikilink Resolution (Backend)
**Priority: HIGH | Files: 2-3 backend**

**Problem:** AI suggests wikilinks like "Machine Learning" but no note with that exact title/slug exists, so graph edges are never created.

**Fix:**
1. In `approval.py`, after creating the summary note, resolve each approved wikilink:
   - Search for existing notes matching the entity name (slug match + fuzzy title match)
   - If found: add `[[Existing Note Title]]` to note content
   - If NOT found: create a **stub note** with the entity name as title, minimal content ("Auto-created from document: {filename}"), and link it
2. This ensures every approved wikilink creates a real graph edge
3. Add a `is_stub` or `is_auto_created` boolean field on Note model so stubs can be identified later

**Files to modify:**
- `backend/app/features/documents/services/approval.py` - Add wikilink resolution logic
- `backend/app/models.py` - Add `is_stub` field to Note (optional)
- `backend/migrations/` - Migration for new field if needed

---

### Phase 2: Cross-Navigation Between Documents and Notes
**Priority: HIGH | Files: 4-5 frontend, 1-2 backend**

**Problem:** No way to navigate from a note to its source document, or from a completed document to its summary note.

#### 2A: Backend - Add "source document" endpoint for notes
- New endpoint: `GET /notes/{note_id}/source-document` → Returns document if `Document.summary_note_id == note_id`
- Or: include `source_document_id` in note detail response by doing a reverse lookup

#### 2B: Frontend - "View Document" button in Note Detail
- In `NoteDetail.js` header area, if the note has a source document:
  - Show a `FileScan` icon button: "View Source Document"
  - Clicking navigates to Documents tab with that document selected
- Query: `GET /notes/{note_id}/source-document` on note load

#### 2C: Frontend - "Open Note" button in Documents (ReviewPanel)
- In `ReviewPanel.js`, when status is "completed" and `summary_note_id` exists:
  - Make the "Summary note created (#123)" text a clickable button
  - Clicking navigates to Notes tab with that note selected
- Use app-level navigation callback (passed via props or context)

#### 2D: Frontend - Graph Inspector navigation
- In `Inspector.js`, for document nodes with `summaryNoteId`:
  - Add "Open Summary Note" action button
- For note nodes that are document summaries:
  - Add "Open Source Document" action button

**Files to modify:**
- `backend/app/features/notes/router.py` or `router_crud.py` - New endpoint
- `frontend/src/features/notes/components/note-detail/NoteDetail.js` - Source doc button
- `frontend/src/features/documents/components/ReviewPanel.js` - Navigate to note
- `frontend/src/features/brain-graph/components/Inspector.js` - Navigation buttons
- `frontend/src/App.js` or navigation context - Cross-tab navigation support

---

### Phase 3: Document Section UX Improvements
**Priority: MEDIUM-HIGH | Files: 4-6 frontend**

#### 3A: Sorting
Add sort dropdown to DocumentList with options:
- **Date uploaded** (newest first) - default
- **Date uploaded** (oldest first)
- **Name** (A-Z)
- **Name** (Z-A)
- **File size** (largest first)
- **Page count** (most first)
- **Status** (needs review first)

#### 3B: Search
Add search bar to filter documents by name (client-side filter on display_name/filename).

#### 3C: Grouping
Add group-by option:
- **None** (flat list) - default
- **By status** (sections: Needs Review, Completed, Failed, Processing)
- **By document type** (report, contract, letter, etc.)
- **By date** (Today, This Week, This Month, Older)

#### 3D: Document Preview
- Add a split/toggle between ReviewPanel and DocumentViewer
- Allow seeing PDF preview alongside review suggestions (side by side or toggle)
- Add page count and extraction method badge on document cards

#### 3E: Grid/List View Toggle
- Current: list view only
- Add: grid view (larger thumbnails, card layout like Gallery)

#### 3F: Empty State Improvement
- Better empty state with direct "Upload" action button
- Show recent upload activity

**Files to modify:**
- `frontend/src/features/documents/components/DocumentList.js` - Sort, search, group, view toggle
- `frontend/src/features/documents/components/DocumentList.css` - New styles
- `frontend/src/features/documents/components/DocumentCard.js` - Enhanced card with more metadata
- `frontend/src/features/documents/components/DocumentCard.css` - Grid view card styles
- `frontend/src/features/documents/components/DocumentLayout.js` - Layout adjustments for new controls
- `frontend/src/features/documents/hooks/useDocuments.js` - Sort/filter params if server-side

---

### Phase 4: Text Extraction Feedback & Transparency
**Priority: MEDIUM | Files: 2-3 frontend, 1 backend**

**Problem:** User can't tell if text was extracted from the PDF or only AI-summarized.

#### 4A: Show extraction method in UI
- On DocumentCard: small badge showing "Text extracted" vs "Vision OCR" vs "AI only"
- On ReviewPanel: section showing extraction stats (pages extracted, chars extracted, method used)

#### 4B: Show extracted text
- In ReviewPanel or DocumentViewer, add a "Extracted Text" tab/section
- Shows the raw `extracted_text` field so user can verify quality
- Collapsible, not shown by default

#### 4C: Backend - Include extraction metadata in response
- Ensure `extraction_method` and text length are included in document detail response
- Add `text_length` computed field to schema

**Files to modify:**
- `backend/app/features/documents/schemas.py` - Add extraction_method, text_length fields
- `frontend/src/features/documents/components/ReviewPanel.js` - Extraction info section
- `frontend/src/features/documents/components/DocumentCard.js` - Extraction badge

---

### Phase 5: Text Extraction Pipeline Fix
**Priority: MEDIUM | Files: 1-2 backend**

**Problem:** User reports all PDFs were "just AI summarized" without visible text extraction.

**Investigation needed:**
- The extraction pipeline DOES extract text (via pdfplumber) before sending to AI
- But the extracted text may not be displayed or distinguishable from the AI summary
- The AI summary is what gets shown; extracted text is stored but not surfaced

**Potential issues:**
1. `extracted_text` is populated but never shown to the user (Phase 4 fixes this)
2. For text-heavy PDFs, the extraction works but the summary doesn't mention "extracted from text"
3. The enrichment prompt should differentiate: "Here is extracted text from the PDF, summarize it" vs "Analyze this document"

**Fix:**
- Verify extraction is working by checking `extracted_text` field in DB for uploaded docs
- If extraction works but isn't visible, Phase 4 solves this
- If extraction is failing, investigate pdfplumber configuration
- Improve AI prompt to explicitly reference that it's working with extracted text

**Files to check/modify:**
- `backend/app/features/documents/services/extraction.py` - Verify extraction works
- `backend/app/features/documents/services/enrichment.py` - Improve prompt clarity
- `backend/app/features/documents/tasks.py` - Check pipeline flow

---

### Phase 6: Graph Focus Mode - Document Connections
**Priority: MEDIUM | Files: 1-2 frontend**

**Problem:** In Explore Focus mode, document connections don't appear for notes that are document summaries.

**Root cause:** The graph DOES create SOURCE edges between documents and notes. The issue might be:
1. Focus mode filtering out document nodes
2. Edge type "source" not being rendered
3. Node layer filters excluding documents

**Fix:**
- Verify document layer is enabled by default in `useGraphFilters.js`
- Ensure SOURCE edge type is included in edge rendering in `edgeRendering.js`
- Check that Focus mode expansion includes document neighbors

**Files to modify:**
- `frontend/src/features/brain-graph/hooks/useGraphFilters.js` - Ensure documents included
- `frontend/src/features/brain-graph/views/ExploreView.js` - Focus mode neighbor expansion
- `frontend/src/features/brain-graph/utils/edgeRendering.js` - SOURCE edge style

---

## Implementation Order

```
Phase 1 (Wikilinks)     ──→ Most impactful fix, enables graph connections
Phase 2 (Navigation)    ──→ Critical UX, users need to move between views
Phase 3 (Document UX)   ──→ Major UX improvement, multiple sub-tasks
Phase 4 (Extraction UI) ──→ Transparency, builds trust in AI processing
Phase 5 (Extraction Fix)──→ Verify + fix backend pipeline
Phase 6 (Graph Focus)   ──→ Debug + fix graph rendering
```

Phases 1-2 are the highest priority fixes.
Phases 3-4 are the biggest UX improvements.
Phases 5-6 are investigation + targeted fixes.

---

## Estimated File Changes

| Phase | Backend Files | Frontend Files | New Files | Migrations |
|-------|--------------|----------------|-----------|------------|
| 1     | 2-3          | 0              | 0-1       | 0-1        |
| 2     | 1            | 4-5            | 0         | 0          |
| 3     | 0-1          | 5-6            | 0-1       | 0          |
| 4     | 1            | 2-3            | 0         | 0          |
| 5     | 1-2          | 0              | 0         | 0          |
| 6     | 0            | 2-3            | 0         | 0          |
| **Total** | **5-8**  | **13-17**      | **0-2**   | **0-1**    |
