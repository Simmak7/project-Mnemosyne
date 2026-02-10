# Mnemosyne — Product Documentation

## AI-Powered Local Note-Taking with RAG | v1.0

---

## 1. Product Overview

**Mnemosyne** is a local-first AI note-taking application that transforms images, handwriting, diagrams, and documents into structured, interconnected knowledge. It builds a personal knowledge graph with automatic tagging, wiki-linking, and a RAG-powered AI assistant — all running privately on your machine.

**Core Principles:**

- **100% Local** — All data processing, storage, and AI inference runs on the user's device. No cloud dependency, no data leaves the machine.
- **AI-First Organisation** — Notes are automatically structured, tagged, and linked by AI, reducing manual effort.
- **Knowledge Graph** — Every note becomes a node in a visual graph, enabling discovery of connections and patterns.
- **Multi-Format Input** — Images, text, journal entries, and PDFs (planned) all feed into a unified knowledge base.

---

## 2. Core Features

### 2.1 Image Upload & Analysis

Upload any image — photographs, diagrams, whiteboard captures, handwritten notes — and Mnemosyne's AI will analyse it and generate a structured note.

**How it works:**

1. User uploads an image.
2. User optionally provides a custom analysis prompt, or uses the default prompt provided by Mnemosyne.
3. AI analyses the image content: extracts text, interprets diagrams, reads handwriting.
4. A structured note is auto-generated from the analysis.
5. A bidirectional link between the original image and the note is created, so the source material is always accessible.
6. Tags (#) and wikilinks ([[...]]) are generated automatically based on the content and existing notes in the knowledge base.

**Key behaviours:**

- Default prompt covers general-purpose analysis (text extraction, diagram interpretation, handwriting recognition).
- Custom prompts allow the user to focus the AI on specific aspects of the image (e.g., "Extract only the action items from this whiteboard photo").
- The original image is stored and permanently linked to its note.

---

### 2.2 Manual Note Creation

Users can create notes manually with full control over content, structure, and connections.

**How it works:**

1. User creates a new note.
2. User writes content freely.
3. User adds tags (#) and/or wikilinks ([[...]]) to establish connections.
4. Note is saved and indexed in the knowledge base and vector store.

**Key behaviours:**

- No AI processing is required — the user has full control.
- Tags and wikilinks entered manually are treated identically to AI-generated ones.
- Notes are immediately available in the Brain graph and to the RAG system.

---

### 2.3 Daily Note & Journal

A daily journaling system for fast capture of tasks, remarks, ideas, and observations throughout the day.

**How it works:**

1. One daily note is created per day (automatically or on first journal entry).
2. User adds journal entries throughout the day — these are quick, low-friction inputs.
3. Each journal entry is appended to the daily note chronologically.
4. Journal entries can include tasks, remarks, ideas, or any free-form text.
5. Users can add tags (#) and wikilinks ([[...]]) to individual journal entries.

**Key behaviours:**

- Journal entries are designed for speed — minimal friction to capture a thought.
- Tasks created in journal entries are trackable.
- Tags and wikilinks on journal entries create connections between daily activity and the broader knowledge base.
- Daily notes appear in the Brain graph like any other note.

---

### 2.4 PDF Import & Extraction *(Planned — Not Yet Implemented)*

Upload PDF documents for AI-powered extraction, analysis, and note creation.

**How it will work:**

1. User uploads a PDF document.
2. AI extracts and analyses all data from the PDF (text, tables, images, structure).
3. A special note is created containing the extracted and structured content.
4. AI suggests tags (#) and wikilinks ([[...]]) based on the content and existing notes.
5. User reviews the suggestions and either approves them (auto-link) or skips them (manual linking later).

**Key behaviours:**

- The approval step gives users control over which connections are made — preventing unwanted or inaccurate links.
- Skipping the approval step means the user can manually add tags and wikilinks later.
- The original PDF remains linked to its note.

---

## 3. Brain — Knowledge Graph

The Brain is the visual, interactive graph that displays all notes and their connections. It serves as the primary navigation, search, and discovery interface in Mnemosyne.

**What it shows:**

- **Nodes** — Each note is represented as a node in the graph.
- **Edges** — Tags and wikilinks form the edges (connections) between nodes.
- **Clusters** — Groups of densely connected notes form visible clusters, revealing topic areas.

**How users interact with it:**

- Click any node to open the corresponding note.
- Explore clusters to discover related knowledge.
- Filter the graph by tags, date, or note type.
- Use the graph as the primary way to search and navigate the entire knowledge base.

**Why it matters:**

The Brain makes implicit connections visible. Instead of searching by keyword, users can visually explore their knowledge and discover relationships they might not have found through traditional search.

---

## 4. Mnemosyne AI

Mnemosyne AI is the intelligent layer that sits on top of the knowledge base. It has two modes: **RAG Search** and **AI Brain**.

### 4.1 RAG Search

A retrieval-augmented generation system that answers questions using the user's personal notes as the knowledge source.

**How it works:**

1. User asks a question in natural language.
2. The RAG system retrieves the most relevant notes from the local vector store.
3. AI generates an answer grounded in the retrieved notes.
4. The response cites specific notes and provides context.

**Best for:** Precise retrieval — "Find my note about X", "What did I write about Y?", "Summarise everything related to Z."

### 4.2 AI Brain (.md Knowledge System)

AI Brain builds a structured .md (Markdown) file system from the user's notes, creating a persistent, queryable AI knowledge base. This is similar to how advanced AI systems manage their own context and memory.

**File structure:**

| File | Purpose |
|------|---------|
| `askimap.md` | Master index of all .md files — the entry point for AI navigation |
| `memory.md` | Persistent context, user preferences, and conversation history |
| `soul.md` | Core personality and behaviour configuration for the AI |
| `[topic].md` | One file per note/topic — structured knowledge on each subject |

**How it works:**

1. Each note in the knowledge base generates a corresponding .md file.
2. The askimap.md file maintains an index of all topic files.
3. When the user interacts with AI Brain, it reads the relevant .md files to build context.
4. Users can have general conversations, ask broad questions, and get responses informed by the full knowledge structure.

**Best for:** Broad understanding and synthesis — general discussion about notes, cross-topic insights, conversational exploration of the knowledge base.

### 4.3 RAG vs AI Brain — When to Use Which

| Aspect | RAG Search | AI Brain |
|--------|-----------|----------|
| **Query type** | Specific questions | General conversation |
| **Retrieval** | Vector similarity search | Structured .md file reading |
| **Strength** | Precision — finds exact notes | Breadth — understands full context |
| **Example** | "What were the key points from Monday's meeting?" | "How do my project notes relate to my quarterly goals?" |

---

## 5. Tags & Wikilinks — Connection System

Tags and wikilinks are the two mechanisms that create the knowledge graph.

### Tags (#)

- Categorise notes by topic or theme.
- AI auto-suggests tags based on content analysis.
- Users can add, edit, or remove tags manually.
- Used for filtering, grouping, and graph clustering.
- Example: `#meeting`, `#project-alpha`, `#architecture`

### Wikilinks ([[...]])

- Direct bidirectional connections between specific notes.
- AI detects related content and suggests wikilinks.
- Users can create wikilinks manually.
- Form the edges of the knowledge graph in the Brain.
- Example: `[[Project Alpha Kickoff]]`, `[[Q3 Budget Review]]`

### How Auto-Generation Works

When a note is created (via image analysis, PDF extraction, or AI processing):

1. AI analyses the note content.
2. AI identifies relevant topics → generates tags.
3. AI scans existing notes for related content → suggests wikilinks.
4. For PDF imports (planned): user approves or skips suggestions.
5. For image analysis: tags and wikilinks are created automatically.

---

## 6. System Architecture

```
┌──────────────────────────────────────────────────────┐
│                    INPUT LAYER                        │
│                                                      │
│   📸 Image    ✍️ Manual    📅 Journal    📄 PDF      │
│   Upload      Note        Entry        Import       │
│                                                      │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│                 AI PROCESSING LAYER                   │
│                                                      │
│   Content Analysis → Note Structuring → Auto-Tag     │
│   & Extraction       & Formatting      & Auto-Link   │
│                                                      │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│                  STORAGE LAYER                        │
│                                                      │
│   Notes + Metadata │ Tags & Wikilinks │ Source Links  │
│   Vector Embeddings │ .md Files (AI Brain)            │
│                                                      │
└────────────┬─────────────────────┬───────────────────┘
             │                     │
             ▼                     ▼
┌────────────────────┐  ┌─────────────────────────────┐
│   🧠 BRAIN         │  │   🤖 MNEMOSYNE AI           │
│                    │  │                             │
│   Knowledge Graph  │  │   RAG Search (precise)      │
│   Visual Navigation│  │   AI Brain (conversational)  │
│   Discovery        │  │   .md Knowledge System      │
│                    │  │                             │
└────────────────────┘  └─────────────────────────────┘

              🔒 100% LOCAL ON YOUR PC
```

---

## 7. Data Flow

**Input → Processing → Storage → Output**

1. **Input:** User provides content via image upload, manual note, journal entry, or PDF upload.
2. **Processing:** AI analyses the content, extracts information, creates a structured note, generates tags and wikilinks.
3. **Storage:** Note is saved with metadata, vector embeddings are created for RAG, .md file is generated for AI Brain, source material is linked.
4. **Output:** Note appears in the Brain graph. Content is searchable via RAG. AI Brain can reference the note in conversations.

---

## 8. Privacy & Security

Mnemosyne is built on a **local-first architecture**:

- All AI processing runs locally on the user's device.
- No data is sent to external servers or cloud services.
- No internet connection is required for core functionality.
- The user has full ownership and control over their entire knowledge base.
- Data can be backed up and exported by the user at any time.

---

*Mnemosyne — Your memory, your knowledge, your machine.*
