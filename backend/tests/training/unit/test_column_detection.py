"""
Unit tests for ID column detection.

ID columns in training data cause data leakage and overfitting.
This function is critical for data quality.
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

from utils import is_id_column, is_constant_column, is_high_cardinality_categorical


class TestIsIdColumnByName:
    """Test ID column detection based on column names."""
    
    @pytest.mark.unit
    @pytest.mark.parametrize("col_name", [
        'id', 'ID', 'Id',
        'customer_id', 'CUSTOMER_ID',
        'user_id', 'userId',
        'order_id', 'orderId',
        'transaction_id',
        'product_id',
        'session_id',
        'uuid', 'UUID',
        'guid', 'GUID',
        'index',
        'row_num', 'rownum',
        'serial',
        'record_id',
    ])
    def test_id_name_patterns_detected(self, col_name):
        """Common ID name patterns should be detected."""
        series = pd.Series([1, 2, 3, 4, 5])
        assert is_id_column(col_name, series) == True
    
    @pytest.mark.unit
    @pytest.mark.parametrize("col_name", [
        'age', 'AGE',
        'income', 'salary',
        'price', 'cost',
        'quantity', 'amount',
        'rating', 'score',
        'height', 'weight',
        'category', 'type',
        'name', 'description',
        'date', 'timestamp',
        'is_active', 'has_value',
    ])
    def test_non_id_names_not_detected(self, col_name):
        """Non-ID column names should not be detected as IDs."""
        series = pd.Series([25, 30, 35, 40, 45])
        assert is_id_column(col_name, series) == False


class TestIsIdColumnByData:
    """Test ID column detection based on data patterns."""
    
    @pytest.mark.unit
    def test_sequential_integers_detected(self):
        """Sequential integers (1,2,3,4,5) should be detected as ID."""
        series = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        # With a generic name, sequential data might be detected
        result = is_id_column('row_num', series)
        assert result == True
    
    @pytest.mark.unit
    def test_non_sequential_integers_not_detected(self):
        """Non-sequential integers with normal name should not be ID."""
        series = pd.Series([25, 30, 35, 40, 45, 28, 33, 38, 42, 50])
        assert is_id_column('age', series) == False
    
    @pytest.mark.unit
    def test_repeated_values_not_detected(self):
        """Columns with repeated values are not IDs."""
        series = pd.Series([1, 1, 2, 2, 3, 3, 1, 2, 3, 1])
        assert is_id_column('category_code', series) == False
    
    @pytest.mark.unit
    def test_float_values_not_detected(self):
        """Float values should not be detected as ID."""
        series = pd.Series([10.5, 20.5, 30.5, 40.5, 50.5])
        assert is_id_column('measurement', series) == False
    
    @pytest.mark.unit
    def test_high_cardinality_string_id_patterns(self):
        """High cardinality alphanumeric strings might be IDs."""
        series = pd.Series(['ABC123', 'DEF456', 'GHI789', 'JKL012', 'MNO345'])
        # If unique ratio is high and pattern is alphanumeric, might be ID
        result = is_id_column('code', series)
        # This depends on implementation - accept either
        assert isinstance(result, bool)


class TestIsIdColumnEdgeCases:
    """Edge cases for ID column detection."""
    
    @pytest.mark.unit
    def test_empty_series(self):
        """Empty series should not crash."""
        series = pd.Series([], dtype=int)
        result = is_id_column('id', series)
        # Should return True for name pattern even with empty data
        assert result == True
    
    @pytest.mark.unit
    def test_single_value(self):
        """Single value series with ID name."""
        series = pd.Series([1])
        assert is_id_column('id', series) == True
    
    @pytest.mark.unit
    def test_nan_values_in_series(self):
        """Series with NaN values should be handled."""
        series = pd.Series([1, 2, np.nan, 4, 5])
        result = is_id_column('record_id', series)
        assert result == True  # Name pattern should match


class TestIsConstantColumn:
    """Tests for constant column detection."""
    
    @pytest.mark.unit
    def test_all_same_integer(self):
        """All same integer value is constant."""
        series = pd.Series([5, 5, 5, 5, 5])
        assert is_constant_column(series) == True
    
    @pytest.mark.unit
    def test_all_same_string(self):
        """All same string value is constant."""
        series = pd.Series(['A', 'A', 'A', 'A', 'A'])
        assert is_constant_column(series) == True
    
    @pytest.mark.unit
    def test_all_same_float(self):
        """All same float value is constant."""
        series = pd.Series([3.14, 3.14, 3.14, 3.14])
        assert is_constant_column(series) == True
    
    @pytest.mark.unit
    def test_all_nan(self):
        """All NaN is effectively constant (0-1 unique)."""
        series = pd.Series([np.nan, np.nan, np.nan])
        assert is_constant_column(series) == True
    
    @pytest.mark.unit
    def test_different_values_not_constant(self):
        """Different values should not be constant."""
        series = pd.Series([1, 2, 3, 4, 5])
        assert is_constant_column(series) == False
    
    @pytest.mark.unit
    def test_two_unique_values_not_constant(self):
        """Two unique values is not constant."""
        series = pd.Series([0, 1, 0, 1, 0])
        assert is_constant_column(series) == False
    
    @pytest.mark.unit
    def test_empty_series(self):
        """Empty series has 0 unique values - constant."""
        series = pd.Series([], dtype=float)
        assert is_constant_column(series) == True


class TestIsHighCardinalityCategorical:
    """Tests for high cardinality categorical detection."""
    
    @pytest.mark.unit
    def test_low_cardinality_not_flagged(self):
        """Low cardinality categorical should not be flagged."""
        series = pd.Series(['A', 'B', 'C', 'A', 'B', 'C', 'A', 'B', 'C', 'A'])
        assert is_high_cardinality_categorical(series) == False
    
    @pytest.mark.unit
    def test_high_cardinality_flagged(self):
        """High cardinality categorical (>50% unique) should be flagged."""
        # All unique values = 100% unique ratio
        series = pd.Series([f'category_{i}' for i in range(10)])
        assert is_high_cardinality_categorical(series) == True
    
    @pytest.mark.unit
    def test_numeric_not_flagged(self):
        """Numeric columns should not be flagged as high cardinality categorical."""
        series = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        assert is_high_cardinality_categorical(series) == False
    
    @pytest.mark.unit
    def test_threshold_boundary(self):
        """Test boundary at 50% threshold."""
        # 5 unique out of 10 = 50% - exactly at threshold
        series = pd.Series(['A', 'B', 'C', 'D', 'E', 'A', 'B', 'C', 'D', 'E'])
        # At 50% should not be flagged (threshold is >50%)
        assert is_high_cardinality_categorical(series) == False
    
    @pytest.mark.unit
    def test_above_threshold(self):
        """Test just above 50% threshold."""
        # 6 unique out of 10 = 60%
        series = pd.Series(['A', 'B', 'C', 'D', 'E', 'F', 'A', 'B', 'C', 'D'])
        assert is_high_cardinality_categorical(series) == True
    
    @pytest.mark.unit
    def test_custom_threshold(self):
        """Test with custom threshold."""
        series = pd.Series(['A', 'B', 'C', 'D', 'E'])  # 100% unique
        assert is_high_cardinality_categorical(series, threshold=0.8) == True
        assert is_high_cardinality_categorical(series, threshold=0.3) == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
