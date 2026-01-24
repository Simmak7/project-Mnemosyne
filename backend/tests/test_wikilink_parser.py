"""
Comprehensive tests for wikilink_parser.py module.

Tests cover:
- Basic wikilink extraction
- Wikilinks with aliases
- Multiple wikilinks
- Nested brackets edge cases
- Hashtag extraction
- Multi-word and camelCase hashtags
- Slug creation with unicode
- Empty/malformed input handling
- Wikilink position finding
- Markdown replacement
- Syntax validation
"""

import pytest
from app.wikilink_parser import (
    extract_wikilinks,
    parse_wikilink,
    extract_hashtags,
    create_slug,
    find_wikilink_positions,
    replace_wikilinks_with_markdown,
    validate_wikilink_syntax
)


class TestExtractWikilinks:
    """Tests for extract_wikilinks() function"""

    def test_simple_wikilink(self):
        """Test extraction of single simple wikilink"""
        content = "This is a [[Simple Note]] reference"
        result = extract_wikilinks(content)
        assert result == ["Simple Note"]

    def test_multiple_wikilinks(self):
        """Test extraction of multiple wikilinks"""
        content = "See [[First Note]] and [[Second Note]] for details"
        result = extract_wikilinks(content)
        assert result == ["First Note", "Second Note"]

    def test_wikilink_with_alias(self):
        """Test extraction ignores alias, returns target only"""
        content = "Check [[Target Note|Custom Alias]] here"
        result = extract_wikilinks(content)
        assert result == ["Target Note"]

    def test_multiple_wikilinks_with_aliases(self):
        """Test multiple wikilinks with mixed aliases"""
        content = "See [[First|Link 1]] and [[Second Note]] and [[Third|Link 3]]"
        result = extract_wikilinks(content)
        assert result == ["First", "Second Note", "Third"]

    def test_wikilink_with_spaces(self):
        """Test wikilinks with leading/trailing spaces are trimmed"""
        content = "Test [[  Spaced Note  ]] reference"
        result = extract_wikilinks(content)
        assert result == ["Spaced Note"]

    def test_empty_content(self):
        """Test empty string returns empty list"""
        result = extract_wikilinks("")
        assert result == []

    def test_no_wikilinks(self):
        """Test content without wikilinks returns empty list"""
        content = "This is regular text without any links"
        result = extract_wikilinks(content)
        assert result == []

    def test_empty_wikilink(self):
        """Test empty [[]] doesn't match (requires at least one character)"""
        content = "Empty [[]] wikilink"
        result = extract_wikilinks(content)
        assert result == []  # Empty wikilinks don't match the pattern

    def test_nested_brackets(self):
        """Test nested brackets don't cause issues"""
        content = "Code [[function[0]]] example"
        result = extract_wikilinks(content)
        # Should extract "function[0" (stops at first closing ]])
        assert len(result) == 1

    def test_wikilink_at_start(self):
        """Test wikilink at start of content"""
        content = "[[First Word]] is a wikilink"
        result = extract_wikilinks(content)
        assert result == ["First Word"]

    def test_wikilink_at_end(self):
        """Test wikilink at end of content"""
        content = "Ends with [[Last Word]]"
        result = extract_wikilinks(content)
        assert result == ["Last Word"]

    def test_unicode_wikilinks(self):
        """Test wikilinks with unicode characters"""
        content = "See [[日本語ノート]] and [[Café Notes]] and [[Übersicht]]"
        result = extract_wikilinks(content)
        assert result == ["日本語ノート", "Café Notes", "Übersicht"]

    def test_wikilink_with_numbers(self):
        """Test wikilinks containing numbers"""
        content = "See [[Note 123]] and [[2024 Planning]]"
        result = extract_wikilinks(content)
        assert result == ["Note 123", "2024 Planning"]

    def test_wikilink_with_special_chars(self):
        """Test wikilinks with punctuation"""
        content = "Check [[What's Next?]] and [[It's complicated!]]"
        result = extract_wikilinks(content)
        assert result == ["What's Next?", "It's complicated!"]

    def test_single_bracket_ignored(self):
        """Test single brackets don't match"""
        content = "Array[0] and [text] are not wikilinks"
        result = extract_wikilinks(content)
        assert result == []


class TestParseWikilink:
    """Tests for parse_wikilink() function"""

    def test_simple_wikilink(self):
        """Test parsing simple wikilink without alias"""
        target, alias = parse_wikilink("Note Title")
        assert target == "Note Title"
        assert alias is None

    def test_wikilink_with_alias(self):
        """Test parsing wikilink with alias"""
        target, alias = parse_wikilink("Target Note|Display Text")
        assert target == "Target Note"
        assert alias == "Display Text"

    def test_wikilink_with_spaces(self):
        """Test parsing trims spaces from target and alias"""
        target, alias = parse_wikilink("  Target  |  Alias  ")
        assert target == "Target"
        assert alias == "Alias"

    def test_wikilink_with_multiple_pipes(self):
        """Test parsing with multiple pipes (uses first split only)"""
        target, alias = parse_wikilink("Target|First|Second")
        assert target == "Target"
        assert alias == "First|Second"  # Everything after first pipe

    def test_empty_target(self):
        """Test empty target"""
        target, alias = parse_wikilink("")
        assert target == ""
        assert alias is None

    def test_empty_alias(self):
        """Test empty alias after pipe"""
        target, alias = parse_wikilink("Target|")
        assert target == "Target"
        assert alias == ""

    def test_pipe_only(self):
        """Test pipe only"""
        target, alias = parse_wikilink("|")
        assert target == ""
        assert alias == ""


class TestExtractHashtags:
    """Tests for extract_hashtags() function"""

    def test_simple_hashtag(self):
        """Test extraction of single hashtag"""
        content = "This is a #test hashtag"
        result = extract_hashtags(content)
        assert result == {"test"}

    def test_multiple_hashtags(self):
        """Test extraction of multiple hashtags"""
        content = "Tags: #python #coding #development"
        result = extract_hashtags(content)
        assert result == {"python", "coding", "development"}

    def test_hashtag_case_insensitive(self):
        """Test hashtags are lowercased"""
        content = "Mix of #Python #JAVA #JavaScript"
        result = extract_hashtags(content)
        assert result == {"python", "java", "javascript"}

    def test_multi_word_hashtag(self):
        """Test multi-word hashtags with hyphens"""
        content = "Using #multi-word-tag and #another-tag"
        result = extract_hashtags(content)
        assert result == {"multi-word-tag", "another-tag"}

    def test_camel_case_hashtag(self):
        """Test camelCase hashtags"""
        content = "Tags: #camelCaseTag #PascalCaseTag"
        result = extract_hashtags(content)
        assert result == {"camelcasetag", "pascalcasetag"}

    def test_hashtag_with_underscore(self):
        """Test hashtags with underscores"""
        content = "Using #snake_case_tag and #another_one"
        result = extract_hashtags(content)
        assert result == {"snake_case_tag", "another_one"}

    def test_hashtag_with_numbers(self):
        """Test hashtags with numbers"""
        content = "Tags: #tag123 #2024goals #v2"
        result = extract_hashtags(content)
        assert result == {"tag123", "2024goals", "v2"}

    def test_hashtag_at_start(self):
        """Test hashtag at start of content"""
        content = "#first is the tag"
        result = extract_hashtags(content)
        assert result == {"first"}

    def test_hashtag_at_end(self):
        """Test hashtag at end of content"""
        content = "Ends with #last"
        result = extract_hashtags(content)
        assert result == {"last"}

    def test_no_hashtags(self):
        """Test content without hashtags returns empty set"""
        content = "No tags here"
        result = extract_hashtags(content)
        assert result == set()

    def test_empty_content(self):
        """Test empty string returns empty set"""
        result = extract_hashtags("")
        assert result == set()

    def test_duplicate_hashtags(self):
        """Test duplicate hashtags return single entry (set behavior)"""
        content = "#test and #test again #test"
        result = extract_hashtags(content)
        assert result == {"test"}

    def test_hashtag_in_middle_of_word_ignored(self):
        """Test hashtag in middle of word is ignored"""
        content = "price=$100 and email@example.com"
        result = extract_hashtags(content)
        # Should not extract '100' or anything after @ that looks like tag
        assert result == set() or "100" not in result

    def test_multiple_hashes_ignored(self):
        """Test multiple consecutive hashes don't match"""
        content = "### Markdown heading"
        result = extract_hashtags(content)
        # Pattern should not match multiple hashes
        assert result == set()

    def test_hashtag_after_newline(self):
        """Test hashtags work across multiple lines"""
        content = "Line 1 #tag1\nLine 2 #tag2\nLine 3 #tag3"
        result = extract_hashtags(content)
        assert result == {"tag1", "tag2", "tag3"}


class TestCreateSlug:
    """Tests for create_slug() function"""

    def test_simple_title(self):
        """Test simple title conversion"""
        result = create_slug("My Note Title")
        assert result == "my-note-title"

    def test_uppercase_to_lowercase(self):
        """Test uppercase conversion"""
        result = create_slug("UPPERCASE TITLE")
        assert result == "uppercase-title"

    def test_mixed_case(self):
        """Test mixed case conversion"""
        result = create_slug("CamelCaseTitle")
        assert result == "camelcasetitle"

    def test_special_characters_removed(self):
        """Test special characters are removed"""
        result = create_slug("Title! With? Special@ Characters#")
        assert result == "title-with-special-characters"

    def test_accents_removed(self):
        """Test accents/diacritics are removed"""
        result = create_slug("Café Notes")
        assert result == "cafe-notes"

    def test_unicode_accents(self):
        """Test various unicode accents"""
        result = create_slug("Übersicht Résumé Naïve")
        assert result == "ubersicht-resume-naive"

    def test_multiple_spaces_to_single_hyphen(self):
        """Test multiple spaces become single hyphen"""
        result = create_slug("Too    Many     Spaces")
        assert result == "too-many-spaces"

    def test_leading_trailing_spaces(self):
        """Test leading/trailing spaces are removed"""
        result = create_slug("  Spaced Out  ")
        assert result == "spaced-out"

    def test_multiple_hyphens_collapsed(self):
        """Test multiple hyphens become single hyphen"""
        result = create_slug("Word---With---Hyphens")
        assert result == "word-with-hyphens"

    def test_leading_trailing_hyphens_removed(self):
        """Test leading/trailing hyphens are removed"""
        result = create_slug("-Leading-And-Trailing-")
        assert result == "leading-and-trailing"

    def test_empty_title(self):
        """Test empty title returns empty string"""
        result = create_slug("")
        assert result == ""

    def test_only_special_characters(self):
        """Test title with only special characters returns empty string"""
        result = create_slug("!@#$%^&*()")
        assert result == ""

    def test_numbers_preserved(self):
        """Test numbers are preserved"""
        result = create_slug("Note 123 Year 2024")
        assert result == "note-123-year-2024"

    def test_existing_hyphens_preserved(self):
        """Test existing hyphens are preserved"""
        result = create_slug("Multi-Word-Title")
        assert result == "multi-word-title"

    def test_chinese_characters_removed(self):
        """Test non-ASCII characters like Chinese are removed"""
        result = create_slug("中文标题")
        # Chinese chars removed, results in empty string
        assert result == ""

    def test_emoji_removed(self):
        """Test emojis are removed"""
        result = create_slug("Note with 🎉 Emoji 🔥")
        assert result == "note-with-emoji"


class TestFindWikilinkPositions:
    """Tests for find_wikilink_positions() function"""

    def test_single_wikilink_position(self):
        """Test finding position of single wikilink"""
        content = "Text [[Note]] more"
        result = find_wikilink_positions(content)
        assert len(result) == 1
        start, end, target = result[0]
        assert content[start:end] == "[[Note]]"
        assert target == "Note"

    def test_multiple_wikilink_positions(self):
        """Test finding positions of multiple wikilinks"""
        content = "See [[First]] and [[Second]] links"
        result = find_wikilink_positions(content)
        assert len(result) == 2

        start1, end1, target1 = result[0]
        assert content[start1:end1] == "[[First]]"
        assert target1 == "First"

        start2, end2, target2 = result[1]
        assert content[start2:end2] == "[[Second]]"
        assert target2 == "Second"

    def test_wikilink_with_alias_position(self):
        """Test position extraction with alias (target only)"""
        content = "Link: [[Target|Alias]] here"
        result = find_wikilink_positions(content)
        assert len(result) == 1
        start, end, target = result[0]
        assert content[start:end] == "[[Target|Alias]]"
        assert target == "Target"

    def test_no_wikilinks(self):
        """Test empty list when no wikilinks"""
        content = "No links here"
        result = find_wikilink_positions(content)
        assert result == []

    def test_wikilink_at_start(self):
        """Test position of wikilink at start"""
        content = "[[Start]] of text"
        result = find_wikilink_positions(content)
        start, end, target = result[0]
        assert start == 0
        assert target == "Start"

    def test_wikilink_at_end(self):
        """Test position of wikilink at end"""
        content = "End with [[Link]]"
        result = find_wikilink_positions(content)
        start, end, target = result[0]
        assert end == len(content)
        assert target == "Link"


class TestReplaceWikilinksWithMarkdown:
    """Tests for replace_wikilinks_with_markdown() function"""

    def test_simple_replacement(self):
        """Test simple wikilink to markdown conversion"""
        content = "See [[My Note]] for details"
        resolver = lambda target, alias: f"/notes/{target.lower().replace(' ', '-')}"
        result = replace_wikilinks_with_markdown(content, resolver)
        assert result == "See [My Note](/notes/my-note) for details"

    def test_replacement_with_alias(self):
        """Test wikilink with alias shows alias as display text"""
        content = "Check [[Target Note|Click Here]] out"
        resolver = lambda target, alias: f"/notes/{target.lower().replace(' ', '-')}"
        result = replace_wikilinks_with_markdown(content, resolver)
        assert result == "Check [Click Here](/notes/target-note) out"

    def test_multiple_replacements(self):
        """Test multiple wikilinks are replaced"""
        content = "See [[First]] and [[Second]] notes"
        resolver = lambda target, alias: f"/notes/{target.lower()}"
        result = replace_wikilinks_with_markdown(content, resolver)
        assert result == "See [First](/notes/first) and [Second](/notes/second) notes"

    def test_resolver_returns_none(self):
        """Test wikilink kept unchanged when resolver returns None"""
        content = "Missing [[Unknown Note]] link"
        resolver = lambda target, alias: None
        result = replace_wikilinks_with_markdown(content, resolver)
        assert result == "Missing [[Unknown Note]] link"

    def test_mixed_resolved_and_unresolved(self):
        """Test mix of resolved and unresolved links"""
        def resolver(target, alias):
            if target == "Known":
                return "/notes/known"
            return None

        content = "[[Known]] and [[Unknown]] links"
        result = replace_wikilinks_with_markdown(content, resolver)
        assert result == "[Known](/notes/known) and [[Unknown]] links"

    def test_no_wikilinks(self):
        """Test content without wikilinks unchanged"""
        content = "Regular text without links"
        resolver = lambda target, alias: "/notes/test"
        result = replace_wikilinks_with_markdown(content, resolver)
        assert result == content


class TestValidateWikilinkSyntax:
    """Tests for validate_wikilink_syntax() function"""

    def test_valid_syntax_no_errors(self):
        """Test valid wikilinks return no errors"""
        content = "Valid [[Link One]] and [[Link Two]] here"
        errors = validate_wikilink_syntax(content)
        assert errors == []

    def test_empty_wikilink_error(self):
        """Test empty [[]] wikilink detected"""
        content = "Empty [[]] wikilink"
        errors = validate_wikilink_syntax(content)
        assert len(errors) == 1
        line_num, message = errors[0]
        assert line_num == 1
        assert "Empty wikilink" in message

    def test_unclosed_wikilink_error(self):
        """Test unclosed wikilink detected"""
        content = "Unclosed [[wikilink here"
        errors = validate_wikilink_syntax(content)
        assert len(errors) == 1
        line_num, message = errors[0]
        assert line_num == 1
        assert "Unclosed wikilink" in message

    def test_multiple_pipes_error(self):
        """Test multiple pipes detected"""
        content = "Bad [[Target|Alias|Extra]] link"
        errors = validate_wikilink_syntax(content)
        assert len(errors) == 1
        line_num, message = errors[0]
        assert line_num == 1
        assert "Multiple pipes" in message

    def test_multiple_errors_on_same_line(self):
        """Test multiple errors on same line"""
        content = "Empty [[]] and unclosed [[link"
        errors = validate_wikilink_syntax(content)
        assert len(errors) == 2

    def test_errors_on_different_lines(self):
        """Test errors reported with correct line numbers"""
        content = "Line 1\nLine 2 [[\nLine 3 [[]]"
        errors = validate_wikilink_syntax(content)
        assert len(errors) == 2
        line_nums = [err[0] for err in errors]
        assert 2 in line_nums  # Unclosed on line 2
        assert 3 in line_nums  # Empty on line 3

    def test_extra_closing_brackets(self):
        """Test extra closing brackets detected"""
        content = "Extra ]] brackets [[link]]"
        errors = validate_wikilink_syntax(content)
        assert len(errors) == 1
        assert "Unclosed wikilink" in errors[0][1]

    def test_empty_content_no_errors(self):
        """Test empty content returns no errors"""
        errors = validate_wikilink_syntax("")
        assert errors == []

    def test_single_pipe_valid(self):
        """Test single pipe (alias) is valid"""
        content = "Valid [[Target|Alias]] link"
        errors = validate_wikilink_syntax(content)
        assert errors == []


# Run tests with coverage
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=app.wikilink_parser", "--cov-report=term-missing"])
