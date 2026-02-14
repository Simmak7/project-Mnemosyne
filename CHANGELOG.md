# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.1.0-beta] - 2026-02-13

### Added
- PDF document management with AI enrichment and review workflow
- Document collections for organizing PDFs
- Daily journal with calendar view, mood tracking, and AI insights
- Mnemosyne Brain AI companion with topic-based persistent knowledge
- NEXUS graph-native adaptive retrieval engine for AI chat
- Dual-mode AI chat (NEXUS RAG + Brain AI companion)
- User onboarding flow for first-time users
- Two-factor authentication (TOTP)
- Session management and security settings
- Neural Glass design system across all UI components
- Branded login page with monogram logo
- Brain staleness detection and incremental updates
- Community detection in knowledge graph
- Semantic edges and path finding in knowledge graph

### Changed
- Upgraded gallery to 3-column layout with albums
- Enhanced knowledge graph with D3.js communities and weighted edges
- Removed experimental feature flags — all components now permanent
- Version bump to v1.1.0

## [1.0.0-beta] - 2026-01-26

### Added
- Core note-taking with rich text editor (Tiptap)
- Wikilinks (`[[note]]`) for bidirectional linking
- Hashtag extraction and auto-tagging
- AI image analysis with Ollama (llama3.2-vision)
- Text recognition (OCR) from uploaded images
- Knowledge graph visualization with D3.js
- RAG-powered AI chat with citation-backed answers
- Smart buckets with AI clustering
- Inbox, orphan detection, and daily notes
- Semantic search with pgvector embeddings
- Full-text search across notes and images
- Smart gallery with tag filtering
- User authentication with JWT
- Docker Compose deployment
- PostgreSQL with pgvector extension
- Redis for caching and Celery task queue
- Ollama integration for 100% local AI inference
