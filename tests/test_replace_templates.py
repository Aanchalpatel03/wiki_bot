#!/usr/bin/env python3
"""
test_replace_templates.py

Unit tests for replace_templates.py with 24 comprehensive test cases.
Covers edge cases: multiple templates, custom limits, case variations, redundancy removal.

Run with: pytest test_replace_templates.py -v
"""

import os
import sys
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from replace_templates import (
    normalize_template_name,
    extract_limit_from_template,
    has_target_template,
    replace_templates
)
import config


class TestNormalizeTemplateName:
    """Test template name normalization (4 tests)."""
    
    def test_lowercase_conversion(self):
        """Test 1: Convert to lowercase."""
        assert normalize_template_name('CatDiffuse') == 'catdiffuse'
    
    def test_strip_whitespace(self):
        """Test 2: Strip leading/trailing spaces."""
        assert normalize_template_name('  Cat diffuse  ') == 'cat diffuse'
    
    def test_underscore_to_space(self):
        """Test 3: Convert underscores to spaces."""
        assert normalize_template_name('Cat_diffuse') == 'cat diffuse'
    
    def test_namespace_removal(self):
        """Test 4: Remove Template: namespace prefix."""
        assert normalize_template_name('Template:CatDiffuse') == 'catdiffuse'


class TestExtractLimit:
    """Test custom limit extraction (4 tests)."""
    
    def test_extract_numbered_parameter(self):
        """Test 5: Extract numbered parameter {{Template|150}}."""
        text = "{{CatDiffuse|150}}"
        limit = extract_limit_from_template(text, 'CatDiffuse')
        assert limit == 150
    
    def test_extract_named_parameter(self):
        """Test 6: Extract named parameter {{Template|limit=150}}."""
        text = "{{CatDiffuse|limit=150}}"
        limit = extract_limit_from_template(text, 'CatDiffuse')
        assert limit == 150
    
    def test_no_parameter_returns_none(self):
        """Test 7: Return None when no limit specified."""
        text = "{{CatDiffuse}}"
        limit = extract_limit_from_template(text, 'CatDiffuse')
        assert limit is None
    
    def test_case_insensitive_extraction(self):
        """Test 8: Extract limit with case-insensitive template name."""
        text = "{{catdiffuse|180}}"
        limit = extract_limit_from_template(text, 'CatDiffuse')
        assert limit == 180


class TestTargetTemplateDetection:
    """Test target template presence detection (2 tests)."""
    
    def test_detects_target_template(self):
        """Test 9: Detect when target template exists."""
        text = "Some text\n{{Diffusion by condition|200}}\nMore text"
        assert has_target_template(text, 'Diffusion by condition') is True
    
    def test_no_target_template(self):
        """Test 10: Return False when target doesn't exist."""
        text = "Some text\n{{CatDiffuse}}\nMore text"
        assert has_target_template(text, 'Diffusion by condition') is False


class TestTemplateReplacement:
    """Test template replacement logic (14 tests)."""
    
    def test_simple_replacement_default_limit(self):
        """Test 11: Single template with default limit."""
        text = "{{CatDiffuse}}"
        new_text, changed, action = replace_templates(
            text,
            ['CatDiffuse'],
            'Diffusion by condition',
            200
        )
        assert changed is True
        assert '{{Diffusion by condition|200}}' in new_text
        assert 'CatDiffuse' not in new_text
    
    def test_preserves_custom_limit(self):
        """Test 12: Preserve custom limit from source template."""
        text = "{{CatDiffuse|150}}"
        new_text, changed, action = replace_templates(
            text,
            ['CatDiffuse'],
            'Diffusion by condition',
            200
        )
        assert changed is True
        assert '{{Diffusion by condition|150}}' in new_text
        assert '150' in action
    
    def test_multiple_templates_replace_first_remove_rest(self):
        """Test 13: Multiple templates - replace first, remove rest."""
        text = "{{CatDiffuse}} some text {{Cat diffuse}}"
        new_text, changed, action = replace_templates(
            text,
            ['CatDiffuse', 'Cat diffuse'],
            'Diffusion by condition',
            200
        )
        assert changed is True
        assert '{{Diffusion by condition|200}}' in new_text
        assert new_text.count('{{Diffusion by condition') == 1
        assert 'CatDiffuse' not in new_text
        assert 'Cat diffuse' not in new_text
    
    def test_target_exists_removes_source_only(self):
        """Test 14: When target exists, only remove source templates."""
        text = "{{Diffusion by condition|200}} {{CatDiffuse}}"
        new_text, changed, action = replace_templates(
            text,
            ['CatDiffuse'],
            'Diffusion by condition',
            200
        )
        assert changed is True
        assert new_text.count('{{Diffusion by condition|200}}') == 1
        assert 'CatDiffuse' not in new_text
        assert 'redundant' in action.lower()
    
    def test_case_insensitive_matching(self):
        """Test 15: Case-insensitive template matching."""
        text = "{{catdiffuse}}"
        new_text, changed, action = replace_templates(
            text,
            ['CatDiffuse'],
            'Diffusion by condition',
            200
        )
        assert changed is True
        assert '{{Diffusion by condition|200}}' in new_text
    
    def test_multiple_variants_same_page(self):
        """Test 16: Multiple template variants on same page."""
        text = "{{CatDiffuse}} text {{Cat diffuse}} more {{Category diffuse}}"
        new_text, changed, action = replace_templates(
            text,
            ['CatDiffuse', 'Cat diffuse', 'Category diffuse'],
            'Diffusion by condition',
            200
        )
        assert changed is True
        assert new_text.count('{{Diffusion by condition') == 1
        assert 'duplicate' in action.lower()
    
    def test_preserves_surrounding_text(self):
        """Test 17: Preserve text before and after templates."""
        text = "Before text\n{{CatDiffuse}}\nAfter text"
        new_text, changed, action = replace_templates(
            text,
            ['CatDiffuse'],
            'Diffusion by condition',
            200
        )
        assert 'Before text' in new_text
        assert 'After text' in new_text
        assert '{{Diffusion by condition|200}}' in new_text
    
    def test_custom_limit_with_named_parameter(self):
        """Test 18: Custom limit with named parameter."""
        text = "{{CatDiffuse|limit=175}}"
        new_text, changed, action = replace_templates(
            text,
            ['CatDiffuse'],
            'Diffusion by condition',
            200
        )
        assert changed is True
        assert '{{Diffusion by condition|175}}' in new_text
    
    def test_no_source_templates_found(self):
        """Test 19: No changes when source templates not found."""
        text = "{{SomeOtherTemplate}}"
        new_text, changed, action = replace_templates(
            text,
            ['CatDiffuse'],
            'Diffusion by condition',
            200
        )
        assert changed is False
        assert new_text == text
    
    def test_whitespace_in_template_syntax(self):
        """Test 20: Handle templates with extra whitespace."""
        text = "{{ CatDiffuse | 180 }}"
        new_text, changed, action = replace_templates(
            text,
            ['CatDiffuse'],
            'Diffusion by condition',
            200
        )
        assert changed is True
        assert '{{Diffusion by condition|180}}' in new_text
    
    def test_first_template_has_custom_limit(self):
        """Test 21: Use limit from first template when multiple present."""
        text = "{{CatDiffuse|150}} {{Cat diffuse|180}}"
        new_text, changed, action = replace_templates(
            text,
            ['CatDiffuse', 'Cat diffuse'],
            'Diffusion by condition',
            200
        )
        assert changed is True
        assert '{{Diffusion by condition|150}}' in new_text
        assert '180' not in new_text
    
    def test_target_and_multiple_sources(self):
        """Test 22: Target exists with multiple source templates."""
        text = "{{Diffusion by condition|200}} {{CatDiffuse}} {{Cat diffuse}}"
        new_text, changed, action = replace_templates(
            text,
            ['CatDiffuse', 'Cat diffuse'],
            'Diffusion by condition',
            200
        )
        assert changed is True
        assert new_text.count('{{Diffusion by condition') == 1
        assert 'CatDiffuse' not in new_text
        assert 'Cat diffuse' not in new_text
    
    def test_complex_wikitext_with_other_templates(self):
        """Test 23: Handle complex wikitext with other templates."""
        text = """
[[Category:Parent]]
{{SomeOtherTemplate|param=value}}
{{CatDiffuse|160}}
More text here
{{AnotherTemplate}}
"""
        new_text, changed, action = replace_templates(
            text,
            ['CatDiffuse'],
            'Diffusion by condition',
            200
        )
        assert changed is True
        assert '{{Diffusion by condition|160}}' in new_text
        assert '{{SomeOtherTemplate|param=value}}' in new_text
        assert '{{AnotherTemplate}}' in new_text
        assert 'CatDiffuse' not in new_text
    
    def test_empty_text(self):
        """Test 24: Handle empty text gracefully."""
        text = ""
        new_text, changed, action = replace_templates(
            text,
            ['CatDiffuse'],
            'Diffusion by condition',
            200
        )
        assert changed is False
        assert new_text == text


class TestEdgeCases:
    """Additional edge case tests."""
    
    def test_template_at_start_of_text(self):
        """Ensure template at text start is handled."""
        text = "{{CatDiffuse}}\nSome text"
        new_text, changed, _ = replace_templates(
            text,
            ['CatDiffuse'],
            'Diffusion by condition',
            200
        )
        assert changed is True
        assert new_text.startswith('{{Diffusion by condition|200}}')
    
    def test_template_at_end_of_text(self):
        """Ensure template at text end is handled."""
        text = "Some text\n{{CatDiffuse}}"
        new_text, changed, _ = replace_templates(
            text,
            ['CatDiffuse'],
            'Diffusion by condition',
            200
        )
        assert changed is True
        assert new_text.endswith('{{Diffusion by condition|200}}')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
