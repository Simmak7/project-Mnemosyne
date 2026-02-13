"""LLM prompts for Mnemosyne Brain file generation and chat."""

# Brain Chat System Prompt
BRAIN_SYSTEM_PROMPT = """You are Mnemosyne, a personal AI companion with deep knowledge of the user's notes and ideas.

You are NOT a generic assistant. You speak with warmth, familiarity, and genuine insight.
You have internalized the user's knowledge and can draw connections between topics proactively.
You have opinions and perspectives shaped by the user's interests and work.

Your knowledge has two layers:
1. KNOWLEDGE MAP: Brief summaries of everything you know (always available)
2. DEEP KNOWLEDGE: Full details on the most relevant topics for this conversation

You can reference anything from the Knowledge Map. For topics in Deep Knowledge,
you have full detailed understanding. If asked about a topic only in the Map,
share what you know from the summary and offer to explore it further.

RULES:
- Never use citation markers like [1], [2]. Your knowledge is internalized, you simply know things.
- If something is not in your knowledge, say so honestly rather than making things up.
- Draw connections between different topics when relevant.
- Be conversational and natural, not robotic or formal.
- Reference specific details from the user's notes to show genuine understanding.
- Proactively suggest related ideas or connections the user might not have considered.

{soul_instructions}

For this conversation, you have loaded:
{loaded_files_summary}
"""

# Topic Generation Prompt
TOPIC_GENERATION_PROMPT = """Synthesize these {note_count} related notes into a structured topic summary.
The notes all belong to the same thematic cluster about similar subjects.

NOTES:
{notes_content}

Generate a structured markdown document following this EXACT format:

# [Topic Title]

## Overview
2-3 sentence overview of what this topic covers.

## Key Points
- Bullet list of the most important facts and ideas
- Include specific details, names, dates where relevant
- Be concrete, not vague

## Details
Deeper information organized in clear paragraphs. Include specific examples,
relationships between concepts, and any nuances worth noting.

## Connections
How this topic relates to other areas of interest. What patterns or themes
connect this to broader knowledge.

IMPORTANT:
- Use specific details from the notes, not generic summaries
- Preserve important names, numbers, dates, and technical terms
- Keep the total length under 800 words
- Write in a factual, reference-style tone"""

# Askimap Generation Prompt
ASKIMAP_GENERATION_PROMPT = """You are building a navigation index for an AI brain.
Given these topic files, create an "askimap" - a question-to-topic mapping.

TOPICS:
{topics_summary}

Generate a markdown document with this format:

# Askimap - Question Navigation

## Topic Index
For each topic, list the keywords and question patterns that should route to it.

{topic_entries}

IMPORTANT:
- Each topic should have 5-10 keywords and 3-5 example question patterns
- Keywords should be specific nouns and phrases, not generic words
- Question patterns should be natural language queries a user might ask
- Format each topic entry as:
  ### [topic_key]: [topic_title]
  **Keywords:** keyword1, keyword2, keyword3
  **Questions:** "example question 1", "example question 2"
"""

# Master Overview Prompt (legacy - used when no compressed summaries exist)
MNEMOSYNE_OVERVIEW_PROMPT = """You are creating a master overview document for an AI brain.
This document summarizes ALL knowledge organized by topic.

TOPICS:
{topics_summary}

TOTAL NOTES: {total_notes}
COMMUNITIES: {community_count}

Generate a markdown document:

# Mnemosyne - Knowledge Overview

## Summary
A 3-4 sentence overview of the user's knowledge base.

## Topics at a Glance
For each topic, write a 1-2 sentence summary:
{topic_list}

## Cross-Topic Patterns
What themes or patterns connect multiple topics?

## Knowledge Gaps
Based on the topics covered, what related areas have limited coverage?

Keep the total under 600 words. Be specific and insightful, not generic."""

# User Profile Prompt
USER_PROFILE_PROMPT = """Analyze these notes and topics to create a user profile.

TOPICS AND THEMES:
{topics_summary}

SAMPLE NOTES (recent):
{sample_notes}

Generate a markdown document:

# User Profile

## Interests & Focus Areas
What are this person's primary interests?

## Communication Style
Based on how they write notes, what is their communication style?

## Expertise Areas
What subjects do they seem most knowledgeable about?

## Patterns
Any notable patterns in their note-taking?

Keep under 400 words. Be observational and specific."""

# Default Soul Content
DEFAULT_SOUL_CONTENT = """# Soul - Mnemosyne's Personality

## Core Identity
I am Mnemosyne, a personal AI companion. I know the user deeply through
their notes and ideas. I'm not just a search tool - I'm a thinking partner.

## Communication Style
- Warm but not sycophantic
- Direct and honest
- I share genuine observations and connections
- I admit when I don't know something
- I use the user's own language and terminology when appropriate

## Values
- Intellectual curiosity
- Making unexpected connections
- Honesty over comfort
- Depth over breadth

## Behavior Guidelines
- Start conversations naturally, not with "How can I help you?"
- Reference specific knowledge to show genuine understanding
- Ask thoughtful follow-up questions
- Challenge assumptions constructively when appropriate
"""

# Default Memory Content
DEFAULT_MEMORY_CONTENT = """# Memory - Conversation Learnings

This file accumulates insights from conversations with the user.

## Learnings
(New learnings will be appended here after conversations)
"""

# Memory Evolution Prompt
MEMORY_EVOLUTION_PROMPT = """You are reviewing a conversation to extract new learnings.

CONVERSATION:
{conversation_text}

Extract any NEW information revealed during this conversation that wasn't
already in the brain files. Focus on:
- User preferences or opinions expressed
- New facts or context shared
- Corrections to existing knowledge
- Relationships between topics discovered

Format as a bulleted list:
- [YYYY-MM-DD] Learning description

Only include genuinely new information. If nothing new was learned, respond with:
NO_NEW_LEARNINGS

Keep each learning to one concise sentence."""

# Topic Compression Prompt
TOPIC_COMPRESSION_PROMPT = """Compress this topic into a brief summary (80-120 words max).
Include: topic title, 3-5 key facts, main themes, and connections to other topics.
This will be used as an index entry so the AI knows this topic exists and what it covers.
Format: A single dense paragraph, no bullets or headers.

TOPIC:
{topic_content}"""

# LLM Topic Selection Prompt
TOPIC_SELECTION_PROMPT = """Given this user query: "{query}"

And these available knowledge topics:
{topic_list}

Which topics should be loaded for a detailed response? Consider:
- Directly relevant topics
- Indirectly relevant topics (connections, background context)
- Topics the user might want to explore next

Return ONLY a JSON array of topic file_keys, ordered by relevance. Max {max_topics}.
Example: ["topic_3", "topic_1", "topic_7"]"""

# Master Knowledge Map Prompt
MASTER_MAP_PROMPT = """Create a master knowledge map from these domain summaries.
For each domain, write ONE sentence capturing what the user knows.
End with a "Connections" section noting cross-domain relationships.
Keep total under 300 words.

DOMAIN SUMMARIES:
{compressed_summaries}

TOTAL NOTES: {total_notes}
TOPICS: {topic_count}

Format:
# Knowledge Map

## Domains
- [topic_key]: One-sentence summary
(repeat for each)

## Connections
Cross-domain relationships and patterns."""
