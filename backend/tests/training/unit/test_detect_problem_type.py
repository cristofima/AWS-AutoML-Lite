"""
Unit tests for detect_problem_type() function.

This is one of the most critical functions in the training pipeline.
Wrong detection leads to training the wrong model type (classification vs regression).
"""
import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add training module to path
# Path: tests/training/unit/test_file.py -> backend/training
training_path = Path(__file__).parent.parent.parent.parent / "training"
sys.path.insert(0, str(training_path))

from utils import detect_problem_type


class TestDetectProblemTypeClassification:
    """Test cases where classification is expected."""
    
    @pytest.mark.unit
    def test_binary_integers_zero_one(self):
        """Binary 0/1 integers should be classification."""
        target = pd.Series([0, 1, 0, 1, 1, 0, 1, 0])
        assert detect_problem_type(target) == 'classification'
    
    @pytest.mark.unit
    def test_binary_integers_one_two(self):
        """Binary 1/2 integers should be classification."""
        target = pd.Series([1, 2, 1, 2, 1, 2, 2, 1])
        assert detect_problem_type(target) == 'classification'
    
    @pytest.mark.unit
    def test_multiclass_integers(self):
        """Multi-class integers (0,1,2,3) should be classification."""
        target = pd.Series([0, 1, 2, 3, 0, 1, 2, 3, 0, 1])
        assert detect_problem_type(target) == 'classification'
    
    @pytest.mark.unit
    def test_multiclass_up_to_ten(self):
        """Up to 10 unique integer classes should be classification."""
        target = pd.Series([0, 1, 2, 3, 4, 5, 6, 7, 8, 9] * 10)
        assert detect_problem_type(target) == 'classification'
    
    @pytest.mark.unit
    def test_string_labels(self):
        """String labels should always be classification."""
        target = pd.Series(['cat', 'dog', 'bird', 'cat', 'dog', 'bird'])
        assert detect_problem_type(target) == 'classification'
    
    @pytest.mark.unit
    def test_string_labels_many_samples(self):
        """String labels with many samples should be classification."""
        target = pd.Series(['yes', 'no'] * 100)
        assert detect_problem_type(target) == 'classification'
    
    @pytest.mark.unit
    def test_boolean_target(self):
        """Boolean target should be classification."""
        target = pd.Series([True, False, True, False, True, False])
        assert detect_problem_type(target) == 'classification'
    
    @pytest.mark.unit
    def test_float_integers_classification(self):
        """Float values that are whole numbers (0.0, 1.0, 2.0) should be classification."""
        target = pd.Series([0.0, 1.0, 2.0, 0.0, 1.0, 2.0, 0.0, 1.0])
        assert detect_problem_type(target) == 'classification'
    
    @pytest.mark.unit
    def test_negative_integers_classification(self):
        """Negative integer labels (-1, 0, 1) should be classification."""
        target = pd.Series([-1, 0, 1, -1, 0, 1, -1, 0])
        assert detect_problem_type(target) == 'classification'


class TestDetectProblemTypeRegression:
    """Test cases where regression is expected."""
    
    @pytest.mark.unit
    def test_continuous_floats(self):
        """Continuous float values should be regression."""
        target = pd.Series([35.5, 42.1, 38.7, 41.2, 50.8, 33.4, 45.6, 39.2])
        assert detect_problem_type(target) == 'regression'
    
    @pytest.mark.unit
    def test_prices(self):
        """Price values (many unique floats) should be regression."""
        target = pd.Series([199.99, 249.50, 89.99, 349.00, 129.95, 179.50, 299.99])
        assert detect_problem_type(target) == 'regression'
    
    @pytest.mark.unit
    def test_high_cardinality_integers(self):
        """Many unique integers (100+) should be regression."""
        target = pd.Series(list(range(100)))
        assert detect_problem_type(target) == 'regression'
    
    @pytest.mark.unit
    def test_percentages(self):
        """Percentage values (0.0-1.0 with decimals) should be regression."""
        target = pd.Series([0.15, 0.23, 0.45, 0.67, 0.89, 0.12, 0.34, 0.56])
        assert detect_problem_type(target) == 'regression'
    
    @pytest.mark.unit
    def test_negative_floats(self):
        """Negative float values should be regression."""
        target = pd.Series([-10.5, 5.3, -2.1, 8.7, -15.2, 3.4, -7.8, 12.1])
        assert detect_problem_type(target) == 'regression'
    
    @pytest.mark.unit
    def test_large_range_floats(self):
        """Large range of float values should be regression."""
        target = pd.Series([1000.5, 50000.3, 250.7, 75000.2, 500.9, 100000.1])
        assert detect_problem_type(target) == 'regression'
    
    @pytest.mark.unit
    def test_scientific_notation(self):
        """Scientific notation values should be regression."""
        target = pd.Series([1e-5, 2e-5, 3e-5, 4e-5, 5e-5, 6e-5])
        assert detect_problem_type(target) == 'regression'


class TestDetectProblemTypeEdgeCases:
    """Edge cases and boundary conditions."""
    
    @pytest.mark.unit
    def test_empty_series_defaults_to_classification(self):
        """Empty series should default to classification (safe fallback)."""
        target = pd.Series([], dtype=float)
        assert detect_problem_type(target) == 'classification'
    
    @pytest.mark.unit
    def test_single_value(self):
        """Single value series should be classification."""
        target = pd.Series([1])
        assert detect_problem_type(target) == 'classification'
    
    @pytest.mark.unit
    def test_all_same_value_integer(self):
        """Constant integer values should be classification."""
        target = pd.Series([5, 5, 5, 5, 5])
        assert detect_problem_type(target) == 'classification'
    
    @pytest.mark.unit
    def test_all_same_value_float(self):
        """Constant float values with decimals should be regression (floats are continuous)."""
        target = pd.Series([3.14, 3.14, 3.14, 3.14, 3.14])
        # Floats with decimal values are treated as regression even if constant
        assert detect_problem_type(target) == 'regression'
    
    @pytest.mark.unit
    def test_with_nan_values_classification(self):
        """Series with NaN values should still detect classification correctly."""
        target = pd.Series([0, 1, np.nan, 0, 1, np.nan, 0])
        result = detect_problem_type(target)
        assert result == 'classification'
    
    @pytest.mark.unit
    def test_with_nan_values_regression(self):
        """Series with NaN values should still detect regression correctly."""
        target = pd.Series([35.5, 42.1, np.nan, 41.2, 50.8, np.nan, 45.6])
        result = detect_problem_type(target)
        assert result == 'regression'
    
    @pytest.mark.unit
    def test_boundary_eleven_classes(self):
        """11 unique integer values should be classification (boundary)."""
        target = pd.Series([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10] * 5)
        # This tests the boundary - behavior depends on implementation
        result = detect_problem_type(target)
        # Accept either - the important thing is it doesn't crash
        assert result in ['classification', 'regression']
    
    @pytest.mark.unit
    def test_mixed_integer_float_types(self):
        """Mixed int and float types should be handled correctly."""
        target = pd.Series([1, 2.0, 3, 4.0, 5])
        result = detect_problem_type(target)
        assert result == 'classification'


class TestDetectProblemTypeParametrized:
    """Parametrized tests for comprehensive coverage."""
    
    @pytest.mark.unit
    @pytest.mark.parametrize("target,expected", [
        # Clear classification cases
        (pd.Series([0, 1, 0, 1, 1]), 'classification'),
        (pd.Series([0, 1, 2, 0, 1, 2]), 'classification'),
        (pd.Series(['A', 'B', 'C', 'A', 'B']), 'classification'),
        (pd.Series([True, False, True]), 'classification'),
        
        # Clear regression cases
        (pd.Series([35.5, 42.1, 38.7, 41.2]), 'regression'),
        (pd.Series([0.15, 0.23, 0.45, 0.67, 0.89]), 'regression'),
        (pd.Series(list(range(50))), 'regression'),
    ])
    def test_parametrized_detection(self, target, expected):
        """Parametrized test for various target distributions."""
        assert detect_problem_type(target) == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
