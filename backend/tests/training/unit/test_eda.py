"""Unit tests for eda.py

Tests the EDA report generation functionality.
Uses mocks to verify file writing without actual I/O.
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import mock_open, patch

# Import from new package structure (path setup in conftest.py)
from training.reports.eda import (
    generate_eda_report,
    generate_minimal_report,
    EDAReportGenerator
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def classification_df():
    """Sample classification dataset"""
    np.random.seed(42)
    return pd.DataFrame({
        "age": np.random.randint(18, 65, 100),
        "income": np.random.normal(50000, 15000, 100),
        "category": np.random.choice(["A", "B", "C"], 100),
        "target": np.random.choice([0, 1], 100)
    })


@pytest.fixture
def regression_df():
    """Sample regression dataset"""
    np.random.seed(42)
    return pd.DataFrame({
        "sqft": np.random.randint(500, 3000, 100),
        "bedrooms": np.random.randint(1, 5, 100),
        "location": np.random.choice(["urban", "suburban", "rural"], 100),
        "price": np.random.normal(300000, 100000, 100)
    })


@pytest.fixture
def df_with_missing():
    """Dataset with missing values"""
    df = pd.DataFrame({
        "feature1": [1, 2, np.nan, 4, 5, 6, 7, 8, 9, 10],
        "feature2": [np.nan, "A", "B", "A", np.nan, "C", "B", "A", "C", "A"],
        "target": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1]
    })
    return df


@pytest.fixture
def df_with_id_column():
    """Dataset with ID-like column"""
    return pd.DataFrame({
        "customer_id": range(1, 101),
        "age": np.random.randint(18, 65, 100),
        "score": np.random.random(100),
        "target": np.random.choice([0, 1], 100)
    })


@pytest.fixture
def imbalanced_df():
    """Dataset with class imbalance"""
    np.random.seed(42)
    return pd.DataFrame({
        "feature": np.random.normal(0, 1, 100),
        "target": [0] * 90 + [1] * 10  # 9:1 imbalance
    })


# =============================================================================
# Test EDAReportGenerator Initialization
# =============================================================================

class TestEDAReportGeneratorInit:
    """Tests for EDAReportGenerator initialization"""
    
    def test_initializes_with_dataframe(self, classification_df):
        """Generator initializes correctly with DataFrame"""
        generator = EDAReportGenerator(classification_df, "target")
        
        assert generator.df is not None
        assert generator.target_column == "target"
        assert generator.target is not None
        assert generator.features is not None
    
    def test_detects_classification_problem(self, classification_df):
        """Correctly detects classification problem type"""
        generator = EDAReportGenerator(classification_df, "target")
        
        assert generator.problem_type == "classification"
    
    def test_detects_regression_problem(self, regression_df):
        """Correctly detects regression problem type"""
        generator = EDAReportGenerator(regression_df, "price")
        
        assert generator.problem_type == "regression"
    
    def test_features_exclude_target(self, classification_df):
        """Features DataFrame excludes target column"""
        generator = EDAReportGenerator(classification_df, "target")
        
        assert "target" not in generator.features.columns
        assert len(generator.features.columns) == 3


# =============================================================================
# Test Column Analysis
# =============================================================================

class TestColumnAnalysis:
    """Tests for column analysis functionality"""
    
    def test_detects_id_columns(self, df_with_id_column):
        """ID columns are detected and marked for exclusion"""
        generator = EDAReportGenerator(df_with_id_column, "target")
        
        excluded_names = [col for col, _ in generator.excluded_columns]
        assert "customer_id" in excluded_names
    
    def test_detects_constant_columns(self):
        """Constant columns are detected and marked for exclusion"""
        df = pd.DataFrame({
            "constant": [1, 1, 1, 1, 1],
            "varying": [1, 2, 3, 4, 5],
            "target": [0, 1, 0, 1, 0]
        })
        
        generator = EDAReportGenerator(df, "target")
        
        excluded_names = [col for col, _ in generator.excluded_columns]
        assert "constant" in excluded_names
    
    def test_warns_about_missing_values(self, df_with_missing):
        """Generates warning for columns with missing values"""
        generator = EDAReportGenerator(df_with_missing, "target")
        
        missing_warnings = [w for w in generator.warnings if "Missing" in w]
        assert len(missing_warnings) > 0
    
    def test_warns_about_class_imbalance(self, imbalanced_df):
        """Generates warning for imbalanced classes"""
        generator = EDAReportGenerator(imbalanced_df, "target")
        
        imbalance_warnings = [w for w in generator.warnings if "imbalance" in w.lower()]
        assert len(imbalance_warnings) > 0


# =============================================================================
# Test HTML Generation
# =============================================================================

class TestHTMLGeneration:
    """Tests for HTML report generation"""
    
    def test_generate_returns_html_string(self, classification_df):
        """Generate method returns valid HTML string"""
        generator = EDAReportGenerator(classification_df, "target")
        
        html = generator.generate()
        
        assert isinstance(html, str)
        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "</html>" in html
    
    def test_html_contains_target_column(self, classification_df):
        """Generated HTML contains target column name"""
        generator = EDAReportGenerator(classification_df, "target")
        
        html = generator.generate()
        
        assert "target" in html
    
    def test_html_contains_problem_type_badge(self, classification_df):
        """Generated HTML contains problem type badge"""
        generator = EDAReportGenerator(classification_df, "target")
        
        html = generator.generate()
        
        assert "CLASSIFICATION" in html.upper()
    
    def test_html_contains_dataset_stats(self, classification_df):
        """Generated HTML contains dataset statistics"""
        generator = EDAReportGenerator(classification_df, "target")
        
        html = generator.generate()
        
        # Should contain row count (100)
        assert "100" in html
        # Should contain column count (4)
        assert "4" in html
    
    def test_html_contains_css_styles(self, classification_df):
        """Generated HTML contains CSS styles"""
        generator = EDAReportGenerator(classification_df, "target")
        
        html = generator.generate()
        
        assert "<style>" in html
        assert "</style>" in html
    
    def test_regression_html_contains_statistics(self, regression_df):
        """Regression report contains statistical summaries"""
        generator = EDAReportGenerator(regression_df, "price")
        
        html = generator.generate()
        
        # Should contain common stat terms
        assert "Mean" in html or "mean" in html
        assert "Std" in html or "std" in html


# =============================================================================
# Test generate_eda_report Function
# =============================================================================

class TestGenerateEDAReport:
    """Tests for the main generate_eda_report function"""
    
    def test_writes_file_to_output_path(self, classification_df):
        """Function writes HTML to the specified output path"""
        m = mock_open()
        
        with patch("builtins.open", m):
            generate_eda_report(
                df=classification_df,
                target_column="target",
                output_path="/tmp/eda_report.html"
            )
        
        # Verify file was opened for writing
        m.assert_called_once_with("/tmp/eda_report.html", 'w', encoding='utf-8')
        
        # Verify HTML was written
        handle = m()
        handle.write.assert_called_once()
        written_content = handle.write.call_args[0][0]
        assert "<!DOCTYPE html>" in written_content
    
    def test_handles_exception_with_fallback(self, classification_df):
        """Function falls back to minimal report on error"""
        with patch("training.reports.eda.EDAReportGenerator") as mock_generator:
            mock_generator.side_effect = Exception("Test error")
            
            m = mock_open()
            with patch("builtins.open", m):
                generate_eda_report(
                    df=classification_df,
                    target_column="target",
                    output_path="/tmp/eda_report.html"
                )
            
            # Should still write a file (minimal report)
            assert m.called


# =============================================================================
# Test generate_minimal_report Function
# =============================================================================

class TestGenerateMinimalReport:
    """Tests for the minimal fallback report generator"""
    
    def test_writes_minimal_html(self, classification_df):
        """Minimal report writes valid HTML"""
        m = mock_open()
        
        with patch("builtins.open", m):
            generate_minimal_report(
                df=classification_df,
                target_column="target",
                output_path="/tmp/minimal_eda.html"
            )
        
        m.assert_called_once_with("/tmp/minimal_eda.html", 'w', encoding='utf-8')
        
        written_content = m().write.call_args[0][0]
        assert "<!DOCTYPE html>" in written_content
        assert "EDA Report" in written_content
    
    def test_includes_row_count(self, classification_df):
        """Minimal report includes row count"""
        m = mock_open()
        
        with patch("builtins.open", m):
            generate_minimal_report(
                df=classification_df,
                target_column="target",
                output_path="/tmp/minimal.html"
            )
        
        written_content = m().write.call_args[0][0]
        assert "100" in written_content  # 100 rows
    
    def test_includes_column_info(self, classification_df):
        """Minimal report includes column information"""
        m = mock_open()
        
        with patch("builtins.open", m):
            generate_minimal_report(
                df=classification_df,
                target_column="target",
                output_path="/tmp/minimal.html"
            )
        
        written_content = m().write.call_args[0][0]
        assert "age" in written_content
        assert "income" in written_content


# =============================================================================
# Test Helper Methods
# =============================================================================

class TestHelperMethods:
    """Tests for helper methods in EDAReportGenerator"""
    
    def test_generate_histogram(self, classification_df):
        """_generate_histogram creates valid HTML"""
        generator = EDAReportGenerator(classification_df, "target")
        
        histogram_html = generator._generate_histogram(classification_df["age"])
        
        assert "mini-chart" in histogram_html
        assert "mini-bar" in histogram_html
    
    def test_generate_overview_contains_stats(self, classification_df):
        """_generate_overview contains dataset statistics"""
        generator = EDAReportGenerator(classification_df, "target")
        
        overview_html = generator._generate_overview()
        
        assert "100" in overview_html  # row count
        assert "Dataset Overview" in overview_html
    
    def test_generate_warnings_with_warnings(self, imbalanced_df):
        """_generate_warnings returns HTML when warnings exist"""
        generator = EDAReportGenerator(imbalanced_df, "target")
        
        warnings_html = generator._generate_warnings()
        
        assert "Preprocessing Notes" in warnings_html
    
    def test_generate_warnings_empty_when_no_issues(self):
        """_generate_warnings returns empty string when no warnings"""
        df = pd.DataFrame({
            "feature": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "target": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1]
        })
        
        generator = EDAReportGenerator(df, "target")
        
        # Clear any warnings/excluded for this test
        generator.warnings = []
        generator.excluded_columns = []
        
        warnings_html = generator._generate_warnings()
        
        assert warnings_html == ''
    
    def test_generate_column_info(self, classification_df):
        """_generate_column_info lists all columns"""
        generator = EDAReportGenerator(classification_df, "target")
        
        column_html = generator._generate_column_info()
        
        assert "age" in column_html
        assert "income" in column_html
        assert "category" in column_html
        assert "target" in column_html
    
    def test_generate_correlations_with_numeric(self, regression_df):
        """_generate_correlations works with numeric columns"""
        generator = EDAReportGenerator(regression_df, "price")
        
        corr_html = generator._generate_correlations()
        
        assert "Correlation" in corr_html
    
    def test_generate_correlations_empty_when_few_numeric(self):
        """_generate_correlations returns empty with <2 numeric columns"""
        df = pd.DataFrame({
            "category": ["A", "B", "C", "A", "B"],
            "type": ["X", "Y", "X", "Y", "X"],
            "target": ["yes", "no", "yes", "no", "yes"]
        })
        
        generator = EDAReportGenerator(df, "target")
        corr_html = generator._generate_correlations()
        
        assert corr_html == ''


# =============================================================================
# Test Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling"""
    
    def test_handles_empty_categorical_columns(self):
        """Report handles datasets with no categorical columns"""
        df = pd.DataFrame({
            "feature1": [1, 2, 3, 4, 5],
            "feature2": [1.1, 2.2, 3.3, 4.4, 5.5],
            "target": [0, 1, 0, 1, 0]
        })
        
        generator = EDAReportGenerator(df, "target")
        html = generator.generate()
        
        assert isinstance(html, str)
    
    def test_handles_empty_numeric_columns(self):
        """Report handles datasets with no numeric columns"""
        df = pd.DataFrame({
            "cat1": ["A", "B", "C", "A", "B"],
            "cat2": ["X", "Y", "X", "Y", "X"],
            "target": ["yes", "no", "yes", "no", "yes"]
        })
        
        generator = EDAReportGenerator(df, "target")
        html = generator.generate()
        
        assert isinstance(html, str)
    
    def test_handles_single_class(self):
        """Report handles single class in target"""
        df = pd.DataFrame({
            "feature": [1, 2, 3, 4, 5],
            "target": [1, 1, 1, 1, 1]  # Single class
        })
        
        generator = EDAReportGenerator(df, "target")
        html = generator.generate()
        
        assert isinstance(html, str)
    
    def test_handles_high_cardinality_categorical(self):
        """Report handles high cardinality categorical columns"""
        df = pd.DataFrame({
            "unique_ids": [f"id_{i}" for i in range(100)],
            "target": [0, 1] * 50
        })
        
        generator = EDAReportGenerator(df, "target")
        
        excluded_names = [col for col, _ in generator.excluded_columns]
        assert "unique_ids" in excluded_names
    
    def test_handles_all_nan_column(self):
        """Report handles columns with all NaN values"""
        df = pd.DataFrame({
            "all_nan": [np.nan] * 10,
            "normal": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "target": [0, 1] * 5
        })
        
        generator = EDAReportGenerator(df, "target")
        html = generator.generate()
        
        assert isinstance(html, str)
    
    def test_large_dataset_info(self):
        """Report handles larger datasets correctly"""
        np.random.seed(42)
        df = pd.DataFrame({
            "feature1": np.random.normal(0, 1, 10000),
            "feature2": np.random.choice(["A", "B", "C"], 10000),
            "target": np.random.choice([0, 1], 10000)
        })
        
        generator = EDAReportGenerator(df, "target")
        html = generator.generate()
        
        assert "10,000" in html or "10000" in html
