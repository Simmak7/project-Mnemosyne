# Mnemosyne Brain Feature Blueprint

**Feature:** AI companion with deep, internalized knowledge of user's notes
**Status:** Complete (Phases 1-6)
**Location:** `backend/app/features/mnemosyne_brain/`

---

## Overview

Mnemosyne Brain is an alternative chat mode alongside RAG. Instead of searching notes per-query, the AI has **pre-built markdown brain files** that give it deep, internalized knowledge organized hierarchically using a fractal navigation pattern.

### Key Differences from RAG
- **No citations** — knowledge is internalized, responses are conversational
- **Personality** — soul.md defines how the AI communicates
- **Cross-topic connections** — proactively connects ideas across topics
- **Self-evolution** — memory.md grows after each conversation

---

## Architecture

```
User Notes → Louvain Clustering → Topic Files (topic_0.md, topic_1.md, ...)
                                → Core Files (mnemosyne.md, askimap.md, soul.md, memory.md, user_profile.md)

Query → Parse askimap → Select relevant topics → Assemble context → Generate response
      → Save to conversation → Queue memory evolution
```

---

## Database Models

| Model | Table | Purpose |
|-------|-------|---------|
| `BrainFile` | `brain_files` | Stores brain markdown files per user |
| `BrainBuildLog` | `brain_build_logs` | Tracks build operations |
| `BrainConversation` | `brain_conversations` | Brain chat conversations |
| `BrainMessage` | `brain_messages` | Messages in brain conversations |

---

## API Endpoints

### Build & Management (`router.py`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/mnemosyne/build` | Trigger brain build (Celery) |
| GET | `/mnemosyne/build/status` | Current build progress |
| GET | `/mnemosyne/build/history` | Past builds |
| GET | `/mnemosyne/files` | List brain files |
| GET | `/mnemosyne/files/{key}` | Get file content |
| PUT | `/mnemosyne/files/{key}` | User edit file |
| GET | `/mnemosyne/status` | Overall brain status |

### Chat (`router_chat.py`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/mnemosyne/query` | Non-streaming query |
| POST | `/mnemosyne/query/stream` | Streaming query (SSE) |
| POST | `/mnemosyne/conversations` | Create conversation |
| GET | `/mnemosyne/conversations` | List conversations |
| GET | `/mnemosyne/conversations/{id}` | Get with messages |
| PUT | `/mnemosyne/conversations/{id}` | Update |
| DELETE | `/mnemosyne/conversations/{id}` | Delete |

---

## Services

| Service | File | Purpose |
|---------|------|---------|
| `brain_builder` | `services/brain_builder.py` | Orchestrates full brain build |
| `topic_generator` | `services/topic_generator.py` | Generates topic.md from note clusters |
| `core_file_generator` | `services/core_file_generator.py` | Generates askimap, mnemosyne, profile |
| `topic_selector` | `services/topic_selector.py` | Scores topics for query relevance |
| `context_assembler` | `services/context_assembler.py` | Assembles system prompt with token budgets |
| `memory_evolver` | `services/memory_evolver.py` | Extracts learnings post-conversation |
| `prompts` | `services/prompts.py` | All LLM prompt templates |

---

## Celery Tasks

| Task | Trigger |
|------|---------|
| `build_brain_task` | POST /mnemosyne/build |
| `evolve_memory_task` | After streaming conversation |
| `mark_brain_stale_task` | After note create/update/delete |

---

## Config (`core/config.py`)

```python
BRAIN_MODEL = "llama3.2:3b"
BRAIN_MAX_CONTEXT_TOKENS = 6000
BRAIN_CORE_TOKEN_BUDGET = 2500
BRAIN_TOPIC_TOKEN_BUDGET = 3000
BRAIN_TEMPERATURE = 0.7
BRAIN_MIN_NOTES = 3
```

---

## Brain Files

| File Key | Type | Purpose |
|----------|------|---------|
| `mnemosyne` | core | Master overview of all topics |
| `soul` | core | Personality and communication style |
| `memory` | core | Accumulated learnings from conversations |
| `askimap` | core | Navigation index mapping topics to keywords |
| `user_profile` | core | User interests and patterns |
| `topic_0..N` | topic | Condensed topic summaries from note clusters |

---

## File Structure

```
features/mnemosyne_brain/
├── __init__.py
├── claude.md
├── models/
│   ├── __init__.py
│   ├── brain_file.py
│   ├── brain_build_log.py
│   └── brain_conversation.py
├── schemas.py
├── router.py
├── router_chat.py
├── tasks.py
└── services/
    ├── __init__.py
    ├── prompts.py
    ├── topic_generator.py
    ├── core_file_generator.py
    ├── brain_builder.py
    ├── topic_selector.py
    ├── context_assembler.py
    └── memory_evolver.py
```
