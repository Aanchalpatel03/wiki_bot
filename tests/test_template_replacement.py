#!/usr/bin/env python3
"""
Unit tests for replace_catdiffuse.py template replacement logic.

Run with: pytest test_template_replacement.py -v
"""

import pytest
import sys
import os

# Add parent directory to path to import the main script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from replace_catdiffuse import (
    normalize_template_name,
    find_and_replace_templates
)


class TestNormalizeTemplateName:
    """Test template name normalization."""
    
    def test_lowercase(self):
        assert normalize_template_name('CatDiffuse') == 'catdiffuse'
    
    def test_strip_spaces(self):
        assert normalize_template_name('  CatDiffuse  ') == 'catdiffuse'
    
    def test_mixed_case(self):
        assert normalize_template_name('CaTdIfFuSe') == 'catdiffuse'


class TestFindAndReplaceTemplates:
    """Test template replacement logic."""
    
    def test_simple_replacement(self):
        """Test basic template replacement without parameters."""
        text = "{{CatDiffuse}}"
        new_text, changed, detected_threshold = find_and_replace_templates(
            text, 
            ['CatDiffuse'], 
            'Diffusion by condition', 
            200
        )
        assert changed
        assert 'Diffusion by condition' in new_text
        assert 'threshold=200' in new_text
        assert 'CatDiffuse' not in new_text
        assert detected_threshold is None  # No threshold in original template
    
    def test_replacement_with_existing_params(self):
        """Test replacement preserving existing parameters."""
        text = "{{CatDiffuse|param1=value1|param2=value2}}"
        new_text, changed, detected_threshold = find_and_replace_templates(
            text, 
            ['CatDiffuse'], 
            'Diffusion by condition', 
            200
        )
        assert changed
        assert 'Diffusion by condition' in new_text
        assert 'param1=value1' in new_text
        assert 'param2=value2' in new_text
        assert 'threshold=200' in new_text
        assert detected_threshold is None
    
    def test_no_replacement_when_not_found(self):
        """Test that text is unchanged when template not found."""
        text = "{{SomeOtherTemplate}}"
        new_text, changed, detected_threshold = find_and_replace_templates(
            text, 
            ['CatDiffuse'], 
            'Diffusion by condition', 
            200
        )
        assert not changed
        assert new_text == text
        assert detected_threshold is None
    
    def test_multiple_templates_in_text(self):
        """Test replacement when multiple instances exist."""
        text = "{{CatDiffuse}}\nSome text\n{{CatDiffuse}}"
        new_text, changed, detected_threshold = find_and_replace_templates(
            text, 
            ['CatDiffuse'], 
            'Diffusion by condition', 
            200
        )
        assert changed
        # Both instances should be replaced
        assert new_text.count('Diffusion by condition') == 2
        assert 'CatDiffuse' not in new_text
        assert detected_threshold is None
    
    def test_case_insensitive_matching(self):
        """Test that matching is case-insensitive."""
        text = "{{catdiffuse}}"
        new_text, changed, detected_threshold = find_and_replace_templates(
            text, 
            ['CatDiffuse'], 
            'Diffusion by condition', 
            200
        )
        assert changed
        assert 'Diffusion by condition' in new_text
        assert detected_threshold is None
    
    def test_multiple_source_templates(self):
        """Test replacing multiple different source templates."""
        text = "{{CatDiffuse}} and {{CatDiffuse2}}"
        new_text, changed, detected_threshold = find_and_replace_templates(
            text, 
            ['CatDiffuse', 'CatDiffuse2'], 
            'Diffusion by condition', 
            200
        )
        assert changed
        assert new_text.count('Diffusion by condition') == 2
        assert 'CatDiffuse' not in new_text
        assert detected_threshold is None
    
    def test_preserve_surrounding_text(self):
        """Test that surrounding text is preserved."""
        text = "Header text\n{{CatDiffuse}}\nFooter text"
        new_text, changed, detected_threshold = find_and_replace_templates(
            text, 
            ['CatDiffuse'], 
            'Diffusion by condition', 
            200
        )
        assert changed
        assert 'Header text' in new_text
        assert 'Footer text' in new_text
        assert 'Diffusion by condition' in new_text
        assert detected_threshold is None
    
    def test_threshold_parameter_not_duplicated(self):
        """Test that threshold parameter is not added if already present."""
        text = "{{CatDiffuse|threshold=150}}"
        new_text, changed, detected_threshold = find_and_replace_templates(
            text, 
            ['CatDiffuse'], 
            'Diffusion by condition', 
            200
        )
        assert changed
        # Should preserve existing threshold value
        assert 'threshold=150' in new_text
        # Count threshold occurrences - should only appear once
        assert new_text.count('threshold=') == 1
        # Should detect the existing threshold
        assert detected_threshold == 150
    
    def test_complex_wikitext(self):
        """Test replacement in complex wikitext with other templates."""
        text = """
[[Category:Something]]
{{OtherTemplate|param=value}}
{{CatDiffuse}}
Some category description.
[[File:Example.jpg]]
"""
        new_text, changed, detected_threshold = find_and_replace_templates(
            text, 
            ['CatDiffuse'], 
            'Diffusion by condition', 
            200
        )
        assert changed
        assert 'Diffusion by condition' in new_text
        assert 'CatDiffuse' not in new_text
        # Other content should be preserved
        assert '[[Category:Something]]' in new_text
        assert '{{OtherTemplate|param=value}}' in new_text
        assert '[[File:Example.jpg]]' in new_text
        assert detected_threshold is None
    
    def test_custom_threshold_value(self):
        """Test that custom threshold value is correctly applied."""
        text = "{{CatDiffuse}}"
        new_text, changed, detected_threshold = find_and_replace_templates(
            text, 
            ['CatDiffuse'], 
            'Diffusion by condition', 
            500
        )
        assert changed
        assert 'threshold=500' in new_text
        assert detected_threshold is None
    
    def test_no_preserve_params(self):
        """Test replacement without preserving parameters."""
        text = "{{CatDiffuse|param1=value1}}"
        new_text, changed, detected_threshold = find_and_replace_templates(
            text, 
            ['CatDiffuse'], 
            'Diffusion by condition', 
            200,
            preserve_params=False
        )
        assert changed
        assert 'Diffusion by condition' in new_text
        assert 'param1=value1' not in new_text
        assert 'threshold=200' in new_text
        assert detected_threshold is None


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_text(self):
        """Test with empty text."""
        text = ""
        new_text, changed, detected_threshold = find_and_replace_templates(
            text, 
            ['CatDiffuse'], 
            'Diffusion by condition', 
            200
        )
        assert not changed
        assert new_text == ""
        assert detected_threshold is None
    
    def test_template_with_namespace_prefix(self):
        """Test template with explicit namespace prefix."""
        text = "{{Template:CatDiffuse}}"
        new_text, changed, detected_threshold = find_and_replace_templates(
            text, 
            ['CatDiffuse'], 
            'Diffusion by condition', 
            200
        )
        assert changed
        assert 'Diffusion by condition' in new_text
        assert detected_threshold is None
    
    def test_whitespace_in_template_name(self):
        """Test template with whitespace in name."""
        text = "{{CatDiffuse }}"
        new_text, changed, detected_threshold = find_and_replace_templates(
            text, 
            ['CatDiffuse'], 
            'Diffusion by condition', 
            200
        )
        assert changed
        assert 'Diffusion by condition' in new_text
        assert detected_threshold is None
    
    def test_detected_threshold_from_template(self):
        """Test that threshold is detected from existing template parameter."""
        text = "{{CatDiffuse|threshold=300}}"
        new_text, changed, detected_threshold = find_and_replace_templates(
            text, 
            ['CatDiffuse'], 
            'Diffusion by condition', 
            200
        )
        assert changed
        assert 'Diffusion by condition' in new_text
        # Should preserve the 300 threshold from original
        assert 'threshold=300' in new_text
        assert detected_threshold == 300
    
    def test_detected_threshold_with_other_params(self):
        """Test threshold detection with other parameters present."""
        text = "{{CatDiffuse|param1=value1|threshold=250|param2=value2}}"
        new_text, changed, detected_threshold = find_and_replace_templates(
            text, 
            ['CatDiffuse'], 
            'Diffusion by condition', 
            200
        )
        assert changed
        assert 'Diffusion by condition' in new_text
        assert 'threshold=250' in new_text
        assert 'param1=value1' in new_text
        assert 'param2=value2' in new_text
        assert detected_threshold == 250


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
