"""
Unit tests for the AutoPreprocessor class.
These tests focus on data transformation functions that don't require 
AWS services or ML model training.
"""

import pandas as pd
import numpy as np

# Import from new package structure (path setup in conftest.py)
from training.core.preprocessor import AutoPreprocessor


class TestHandleMissingValues:
    """Tests for handle_missing_values() method"""
    
    def test_fills_numeric_nan_with_median(self):
        """Numeric columns should have NaN filled with median"""
        preprocessor = AutoPreprocessor(target_column="target")
        df = pd.DataFrame({
            "age": [20, 30, np.nan, 40, 50],
            "target": [0, 1, 0, 1, 0]
        })
        
        result = preprocessor.handle_missing_values(df)
        
        # Median of [20, 30, 40, 50] = 35
        assert result["age"].iloc[2] == 35
        assert not result["age"].isnull().any()
    
    def test_fills_categorical_nan_with_mode(self):
        """Categorical columns should have NaN filled with mode"""
        preprocessor = AutoPreprocessor(target_column="target")
        df = pd.DataFrame({
            "color": ["red", "blue", "red", np.nan, "red"],
            "target": [0, 1, 0, 1, 0]
        })
        
        result = preprocessor.handle_missing_values(df)
        
        # Mode of ["red", "blue", "red", "red"] = "red"
        assert result["color"].iloc[3] == "red"
        assert not result["color"].isnull().any()
    
    def test_handles_all_nan_categorical_column(self):
        """Categorical column with all NaN should be filled with 'Unknown'"""
        preprocessor = AutoPreprocessor(target_column="target")
        df = pd.DataFrame({
            "empty_col": [np.nan, np.nan, np.nan],
            "target": [0, 1, 0]
        })
        df["empty_col"] = df["empty_col"].astype(object)
        
        result = preprocessor.handle_missing_values(df)
        
        # All values should be "Unknown" when mode is empty
        assert (result["empty_col"] == "Unknown").all()
    
    def test_preserves_original_dataframe(self):
        """Original DataFrame should not be modified"""
        preprocessor = AutoPreprocessor(target_column="target")
        df = pd.DataFrame({
            "value": [1, np.nan, 3],
            "target": [0, 1, 0]
        })
        original_nan_count = df["value"].isnull().sum()
        
        _ = preprocessor.handle_missing_values(df)
        
        # Original should still have NaN
        assert df["value"].isnull().sum() == original_nan_count
    
    def test_handles_no_missing_values(self):
        """Should work correctly when no missing values exist"""
        preprocessor = AutoPreprocessor(target_column="target")
        df = pd.DataFrame({
            "value": [1, 2, 3],
            "target": [0, 1, 0]
        })
        
        result = preprocessor.handle_missing_values(df)
        
        assert result["value"].tolist() == [1, 2, 3]


class TestEncodeCategorical:
    """Tests for encode_categorical() method"""
    
    def test_encodes_string_columns_to_integers(self):
        """String columns should be encoded to integers"""
        preprocessor = AutoPreprocessor(target_column="target")
        df = pd.DataFrame({
            "color": ["red", "blue", "green", "red"],
            "target": [0, 1, 0, 1]
        })
        
        result = preprocessor.encode_categorical(df)
        
        # Should be integers
        assert result["color"].dtype in [np.int32, np.int64]
        # Same original values should map to same encoded values
        assert result["color"].iloc[0] == result["color"].iloc[3]  # both "red"
    
    def test_stores_label_encoder(self):
        """Label encoder should be stored for each categorical column"""
        preprocessor = AutoPreprocessor(target_column="target")
        df = pd.DataFrame({
            "size": ["small", "medium", "large"],
            "target": [0, 1, 0]
        })
        
        preprocessor.encode_categorical(df)
        
        assert "size" in preprocessor.label_encoders
        assert hasattr(preprocessor.label_encoders["size"], "classes_")
    
    def test_tracks_categorical_columns(self):
        """Should track which columns are categorical"""
        preprocessor = AutoPreprocessor(target_column="target")
        df = pd.DataFrame({
            "category": ["A", "B", "C"],
            "numeric": [1.0, 2.0, 3.0],
            "target": [0, 1, 0]
        })
        
        preprocessor.encode_categorical(df)
        
        assert "category" in preprocessor.categorical_columns
        assert "numeric" not in preprocessor.categorical_columns
    
    def test_leaves_numeric_columns_unchanged(self):
        """Numeric columns should not be modified"""
        preprocessor = AutoPreprocessor(target_column="target")
        df = pd.DataFrame({
            "value": [1.5, 2.5, 3.5],
            "category": ["A", "B", "C"],
            "target": [0, 1, 0]
        })
        
        result = preprocessor.encode_categorical(df)
        
        assert result["value"].tolist() == [1.5, 2.5, 3.5]
    
    def test_handles_unseen_categories_in_transform_mode(self):
        """Unseen categories should be encoded as -1 when fit=False"""
        preprocessor = AutoPreprocessor(target_column="target")
        
        # First fit on known categories
        df_train = pd.DataFrame({
            "color": ["red", "blue"],
            "target": [0, 1]
        })
        preprocessor.encode_categorical(df_train, fit=True)
        
        # Then transform with unseen category
        df_test = pd.DataFrame({
            "color": ["red", "green"],  # "green" is unseen
            "target": [0, 1]
        })
        result = preprocessor.encode_categorical(df_test, fit=False)
        
        # "green" should be -1
        assert result["color"].iloc[1] == -1


class TestDetectUselessColumns:
    """Tests for detect_useless_columns() method"""
    
    def test_detects_id_column_by_name(self):
        """Columns with 'id' in name should be detected as useless"""
        preprocessor = AutoPreprocessor(target_column="target")
        df = pd.DataFrame({
            "customer_id": [1, 2, 3, 4, 5],
            "age": [25, 30, 35, 40, 45],
            "target": [0, 1, 0, 1, 0]
        })
        
        useless = preprocessor.detect_useless_columns(df)
        
        assert "customer_id" in useless
        assert "age" not in useless
    
    def test_detects_constant_column(self):
        """Columns with single value should be detected as useless"""
        preprocessor = AutoPreprocessor(target_column="target")
        # Use non-sequential, repeated values to avoid ID detection
        df = pd.DataFrame({
            "constant": [1, 1, 1, 1, 1],
            "varying": [10, 20, 10, 30, 20],  # Non-sequential with repeats
            "target": [0, 1, 0, 1, 0]
        })
        
        useless = preprocessor.detect_useless_columns(df)
        
        assert "constant" in useless
        assert "varying" not in useless
    
    def test_detects_high_cardinality_categorical(self):
        """Categorical columns with too many unique values should be detected"""
        preprocessor = AutoPreprocessor(target_column="target")
        # Create high cardinality column (>50% unique)
        df = pd.DataFrame({
            "unique_text": [f"value_{i}" for i in range(100)],
            "low_cardinality": ["A", "B"] * 50,
            "target": [0, 1] * 50
        })
        
        useless = preprocessor.detect_useless_columns(df)
        
        assert "unique_text" in useless
        assert "low_cardinality" not in useless
    
    def test_does_not_detect_target_as_useless(self):
        """Target column should never be marked as useless"""
        preprocessor = AutoPreprocessor(target_column="target")
        df = pd.DataFrame({
            "feature": [1, 2, 3, 4, 5],
            "target": [0, 0, 0, 0, 0]  # Constant, but it's the target
        })
        
        useless = preprocessor.detect_useless_columns(df)
        
        assert "target" not in useless
    
    def test_tracks_dropped_columns(self):
        """Dropped columns should be tracked in self.dropped_columns"""
        preprocessor = AutoPreprocessor(target_column="target")
        df = pd.DataFrame({
            "user_id": [1, 2, 3, 4, 5],
            "constant": [1, 1, 1, 1, 1],
            "feature": [10, 20, 30, 40, 50],
            "target": [0, 1, 0, 1, 0]
        })
        
        preprocessor.detect_useless_columns(df)
        
        assert len(preprocessor.dropped_columns) >= 2
        assert "user_id" in preprocessor.dropped_columns
        assert "constant" in preprocessor.dropped_columns


class TestDetectProblemType:
    """Tests for _detect_problem_type() method"""
    
    def test_delegates_to_utils_function(self):
        """Should use the shared detect_problem_type from utils"""
        preprocessor = AutoPreprocessor(target_column="target")
        
        classification_target = pd.Series([0, 1, 0, 1, 0])
        regression_target = pd.Series([1.5, 2.3, 3.7, 4.1, 5.9])
        
        assert preprocessor._detect_problem_type(classification_target) == "classification"
        assert preprocessor._detect_problem_type(regression_target) == "regression"
