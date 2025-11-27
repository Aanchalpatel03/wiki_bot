#!/usr/bin/env python3
"""
test_category_diffusion_bot.py

Unit tests for category_diffusion_bot.py with mocked pywikibot API.
Covers file counting, boundary conditions (199/200/201), error handling.

Run with: pytest test_category_diffusion_bot.py -v
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock, patch, call

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from category_diffusion_bot import (
    count_files_in_category,
    get_subcategories,
    remove_category_from_parent,
    DIFFUSION_CATEGORY
)


class TestFileCounting:
    """Test file counting with various thresholds."""
    
    def test_count_zero_files(self):
        """Test category with no files."""
        mock_cat = Mock()
        mock_cat.members.return_value = []
        mock_cat.title.return_value = "Category:Empty"
        
        count = count_files_in_category(mock_cat, 200)
        assert count == 0
        mock_cat.members.assert_called_once_with(namespaces=[6], total=201)
    
    def test_count_below_threshold(self):
        """Test category with files below threshold."""
        mock_cat = Mock()
        mock_files = [Mock() for _ in range(150)]
        mock_cat.members.return_value = mock_files
        mock_cat.title.return_value = "Category:Small"
        
        count = count_files_in_category(mock_cat, 200)
        assert count == 150
    
    def test_count_at_boundary_199(self):
        """Test boundary condition: 199 files (below 200 threshold)."""
        mock_cat = Mock()
        mock_files = [Mock() for _ in range(199)]
        mock_cat.members.return_value = mock_files
        mock_cat.title.return_value = "Category:At199"
        
        count = count_files_in_category(mock_cat, 200)
        assert count == 199
    
    def test_count_at_boundary_200(self):
        """Test boundary condition: 200 files (at threshold)."""
        mock_cat = Mock()
        mock_files = [Mock() for _ in range(200)]
        mock_cat.members.return_value = mock_files
        mock_cat.title.return_value = "Category:At200"
        
        count = count_files_in_category(mock_cat, 200)
        assert count == 200
    
    def test_count_at_boundary_201(self):
        """Test boundary condition: 201 files (above threshold)."""
        mock_cat = Mock()
        mock_files = [Mock() for _ in range(201)]
        mock_cat.members.return_value = mock_files
        mock_cat.title.return_value = "Category:At201"
        
        count = count_files_in_category(mock_cat, 200)
        assert count == 201
    
    def test_count_short_circuit_large_category(self):
        """Test short-circuit behavior with large category."""
        mock_cat = Mock()
        # Simulate 500 files but should stop at 201
        mock_files = [Mock() for _ in range(500)]
        mock_cat.members.return_value = iter(mock_files)
        mock_cat.title.return_value = "Category:Large"
        
        count = count_files_in_category(mock_cat, 200)
        # Should stop at threshold + 1
        assert count == 201
    
    def test_count_custom_threshold_150(self):
        """Test with custom threshold of 150."""
        mock_cat = Mock()
        mock_files = [Mock() for _ in range(100)]
        mock_cat.members.return_value = mock_files
        mock_cat.title.return_value = "Category:Custom"
        
        count = count_files_in_category(mock_cat, 150)
        assert count == 100
        mock_cat.members.assert_called_once_with(namespaces=[6], total=151)
    
    def test_count_handles_exception(self):
        """Test error handling when counting fails."""
        mock_cat = Mock()
        mock_cat.members.side_effect = Exception("API Error")
        mock_cat.title.return_value = "Category:Error"
        
        count = count_files_in_category(mock_cat, 200)
        assert count == 0  # Should return 0 on error


class TestGetSubcategories:
    """Test fetching subcategories."""
    
    def test_get_subcategories_success(self):
        """Test successful subcategory fetching."""
        mock_parent = Mock()
        mock_subcats = [
            Mock(title=lambda: "Category:Sub1"),
            Mock(title=lambda: "Category:Sub2"),
            Mock(title=lambda: "Category:Sub3")
        ]
        mock_parent.members.return_value = mock_subcats
        
        with patch('category_diffusion_bot.pywikibot.Category') as mock_cat_class:
            mock_cat_class.side_effect = lambda x: x
            subcats = get_subcategories(mock_parent)
        
        assert len(subcats) == 3
        mock_parent.members.assert_called_once_with(namespaces=[14])
    
    def test_get_subcategories_empty(self):
        """Test when no subcategories exist."""
        mock_parent = Mock()
        mock_parent.members.return_value = []
        
        subcats = get_subcategories(mock_parent)
        assert len(subcats) == 0
    
    def test_get_subcategories_handles_error(self):
        """Test error handling when fetching subcategories."""
        mock_parent = Mock()
        mock_parent.members.side_effect = Exception("Network error")
        
        subcats = get_subcategories(mock_parent)
        assert len(subcats) == 0


class TestRemoveCategoryFromParent:
    """Test category removal logic."""
    
    @patch('category_diffusion_bot.pywikibot.Page')
    def test_remove_category_dry_run(self, mock_page_class):
        """Test removal in dry-run mode."""
        mock_cat = Mock()
        mock_cat.title.return_value = "Category:Test"
        mock_cat.site = Mock()
        
        mock_parent = Mock()
        mock_parent.title.return_value = "Category:Parent"
        
        mock_page = Mock()
        mock_page.get.return_value = "Some text\n[[Category:Parent]]\nMore text"
        mock_page_class.return_value = mock_page
        
        result = remove_category_from_parent(mock_cat, mock_parent, dry_run=True, threshold=200)
        
        assert result is True
        mock_page.save.assert_not_called()  # Should not save in dry-run
    
    @patch('category_diffusion_bot.pywikibot.Page')
    def test_remove_category_live(self, mock_page_class):
        """Test actual removal (live mode)."""
        mock_cat = Mock()
        mock_cat.title.return_value = "Category:Test"
        mock_cat.site = Mock()
        
        mock_parent = Mock()
        mock_parent.title.return_value = "Category:Parent"
        
        mock_page = Mock()
        mock_page.get.return_value = "Some text\n[[Category:Parent]]\nMore text"
        mock_page_class.return_value = mock_page
        
        result = remove_category_from_parent(mock_cat, mock_parent, dry_run=False, threshold=200)
        
        assert result is True
        mock_page.save.assert_called_once()
        # Check that category tag was removed
        assert "[[Category:Parent]]" not in mock_page.text
    
    @patch('category_diffusion_bot.pywikibot.Page')
    def test_remove_category_not_present(self, mock_page_class):
        """Test when category tag not present."""
        mock_cat = Mock()
        mock_cat.title.return_value = "Category:Test"
        mock_cat.site = Mock()
        
        mock_parent = Mock()
        mock_parent.title.return_value = "Category:Parent"
        
        mock_page = Mock()
        mock_page.get.return_value = "Some text without the category tag"
        mock_page_class.return_value = mock_page
        
        result = remove_category_from_parent(mock_cat, mock_parent, dry_run=False, threshold=200)
        
        assert result is False
        mock_page.save.assert_not_called()
    
    @patch('category_diffusion_bot.pywikibot.Page')
    def test_remove_category_with_pipe_syntax(self, mock_page_class):
        """Test removal with pipe syntax [[Category:Parent|Sort]]."""
        mock_cat = Mock()
        mock_cat.title.return_value = "Category:Test"
        mock_cat.site = Mock()
        
        mock_parent = Mock()
        mock_parent.title.return_value = "Category:Parent"
        
        mock_page = Mock()
        mock_page.get.return_value = "Some text\n[[Category:Parent|SortKey]]\nMore text"
        mock_page_class.return_value = mock_page
        
        result = remove_category_from_parent(mock_cat, mock_parent, dry_run=False, threshold=200)
        
        assert result is True
        mock_page.save.assert_called_once()
    
    @patch('category_diffusion_bot.pywikibot.Page')
    def test_remove_handles_no_page_error(self, mock_page_class):
        """Test handling of NoPageError."""
        from pywikibot.exceptions import NoPageError
        
        mock_cat = Mock()
        mock_cat.title.return_value = "Category:Missing"
        mock_cat.site = Mock()
        
        mock_parent = Mock()
        
        mock_page = Mock()
        mock_page.get.side_effect = NoPageError(Mock())
        mock_page_class.return_value = mock_page
        
        result = remove_category_from_parent(mock_cat, mock_parent, dry_run=False, threshold=200)
        
        assert result is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
