# Contributing to Mnemosyne

First off, thank you for considering contributing to Mnemosyne! 🧠

It's people like you that make Mnemosyne such a great tool for building private AI-powered knowledge bases.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Style Guidelines](#style-guidelines)

---

## Code of Conduct

This project and everyone participating in it is governed by our commitment to creating a welcoming, inclusive environment. By participating, you are expected to:

- **Be respectful** — Treat everyone with respect and kindness
- **Be constructive** — Provide helpful feedback and suggestions
- **Be patient** — Remember that this is maintained by a solo developer

---

## How Can I Contribute?

### 🐛 Reporting Bugs

Found a bug? Please help us fix it!

1. **Check existing issues** — Someone might have already reported it
2. **Create a new issue** with:
   - A clear, descriptive title
   - Steps to reproduce the bug
   - Expected vs actual behavior
   - Screenshots if applicable
   - Your environment (OS, Docker version, browser)

### 💡 Suggesting Features

Have an idea? We'd love to hear it!

1. **Check the [Roadmap](ROADMAP.md)** — It might already be planned
2. **Open a feature request** with:
   - A clear description of the feature
   - Why it would be useful
   - How you envision it working

### 📖 Improving Documentation

Documentation improvements are always welcome:

- Fix typos or unclear explanations
- Add examples or tutorials
- Translate documentation

### 🔧 Code Contributions

Ready to code? Here's how to get started:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

## Development Setup

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)
- Git

### Quick Start

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/project-Mnemosyne.git
cd project-Mnemosyne

# Start the development environment
docker-compose up -d --build

# Pull AI models (first time only)
docker exec -it ollama ollama pull llama3.2-vision:11b
docker exec -it ollama ollama pull nomic-embed-text
```

### Frontend Development

```bash
cd frontend
npm install
npm start  # Runs on http://localhost:3000
```

### Backend Development

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload  # Runs on http://localhost:8000
```

---

## Pull Request Process

1. **Create a feature branch** from `main`
2. **Make your changes** with clear, atomic commits
3. **Test your changes** thoroughly
4. **Update documentation** if needed
5. **Submit a PR** with:
   - A clear title and description
   - Reference to related issues (e.g., "Fixes #123")
   - Screenshots for UI changes

### PR Checklist

- [ ] Code follows the project's style guidelines
- [ ] Self-review completed
- [ ] Documentation updated (if applicable)
- [ ] No new warnings or errors
- [ ] Changes tested locally

---

## Style Guidelines

### Python (Backend)

- Follow PEP 8
- Use type hints where possible
- Maximum line length: 100 characters
- Use descriptive variable names

```python
# Good
def get_user_notes(user_id: int, limit: int = 50) -> list[Note]:
    """Fetch notes for a specific user."""
    pass

# Avoid
def get(id, l=50):
    pass
```

### JavaScript/React (Frontend)

- Use functional components with hooks
- Use descriptive component and variable names
- Keep components focused and small

```javascript
// Good
const NoteCard = ({ note, onSelect }) => {
  return (
    <div className="note-card" onClick={() => onSelect(note.id)}>
      <h3>{note.title}</h3>
    </div>
  );
};

// Avoid
const Card = ({ d, f }) => <div onClick={() => f(d.id)}>{d.t}</div>;
```

### Commit Messages

Use clear, descriptive commit messages:

```
feat: add semantic search to notes
fix: resolve wikilink parsing edge case
docs: update installation instructions
refactor: simplify image processing pipeline
```

---

## 🙏 Thank You!

Every contribution, no matter how small, makes Mnemosyne better. Thank you for being part of this journey to build the ultimate private AI brain!

---

<p align="center">
  <strong>Questions?</strong> Open an issue or reach out!
</p>
