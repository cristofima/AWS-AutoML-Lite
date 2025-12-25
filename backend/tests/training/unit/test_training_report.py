"""Unit tests for training_report.py

Tests the HTML report generation for training results.
Uses mocks to verify file writing without actual I/O.
"""
import pytest
from unittest.mock import mock_open, patch

# Import from new package structure (path setup in conftest.py)
from training.reports.training import (
    generate_training_report,
    generate_minimal_training_report,
    TrainingReportGenerator
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def sample_metrics():
    """Sample metrics for classification model"""
    return {
        "accuracy": 0.92,
        "f1_score": 0.89,
        "precision": 0.91,
        "recall": 0.87,
        "training_time": 125.5,
        "best_estimator": "RandomForestClassifier"
    }


@pytest.fixture
def sample_regression_metrics():
    """Sample metrics for regression model"""
    return {
        "r2": 0.85,
        "rmse": 15.23,
        "mae": 12.45,
        "mse": 231.95,
        "training_time": 180.0,
        "best_estimator": "LGBMRegressor"
    }


@pytest.fixture
def sample_feature_importance():
    """Sample feature importance dictionary"""
    return {
        "feature_a": 0.35,
        "feature_b": 0.25,
        "feature_c": 0.20,
        "feature_d": 0.12,
        "feature_e": 0.08
    }


@pytest.fixture
def sample_training_config():
    """Sample training configuration"""
    return {
        "time_budget": 300,
        "estimators": ["rf", "lgbm", "extra_tree"],
        "metric": "accuracy"
    }


@pytest.fixture
def sample_preprocessing_info():
    """Sample preprocessing information"""
    return {
        "dropped_columns": ["id", "customer_id"],
        "categorical_columns": ["category", "type"],
        "numeric_columns": ["age", "income", "score"],
        "label_encoders": {"category": "LabelEncoder", "type": "LabelEncoder"}
    }


@pytest.fixture
def sample_dataset_info():
    """Sample dataset information"""
    return {
        "rows": 1000,
        "columns": 10,
        "target_column": "target",
        "problem_type": "classification"
    }


# =============================================================================
# Test TrainingReportGenerator Class
# =============================================================================

class TestTrainingReportGenerator:
    """Tests for the TrainingReportGenerator class"""
    
    def test_initializes_with_all_parameters(
        self,
        sample_metrics,
        sample_feature_importance,
        sample_training_config,
        sample_preprocessing_info,
        sample_dataset_info
    ):
        """Generator initializes correctly with all parameters"""
        generator = TrainingReportGenerator(
            job_id="test-job-123",
            problem_type="classification",
            metrics=sample_metrics,
            feature_importance=sample_feature_importance,
            training_config=sample_training_config,
            preprocessing_info=sample_preprocessing_info,
            dataset_info=sample_dataset_info
        )
        
        assert generator.job_id == "test-job-123"
        assert generator.problem_type == "classification"
        assert generator.metrics == sample_metrics
        assert generator.feature_importance == sample_feature_importance
    
    def test_generate_returns_html_string(
        self,
        sample_metrics,
        sample_feature_importance,
        sample_training_config,
        sample_preprocessing_info,
        sample_dataset_info
    ):
        """Generate method returns valid HTML string"""
        generator = TrainingReportGenerator(
            job_id="test-job-123",
            problem_type="classification",
            metrics=sample_metrics,
            feature_importance=sample_feature_importance,
            training_config=sample_training_config,
            preprocessing_info=sample_preprocessing_info,
            dataset_info=sample_dataset_info
        )
        
        html = generator.generate()
        
        assert isinstance(html, str)
        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "</html>" in html
    
    def test_html_contains_job_id(
        self,
        sample_metrics,
        sample_feature_importance,
        sample_training_config,
        sample_preprocessing_info,
        sample_dataset_info
    ):
        """Generated HTML contains the job ID"""
        generator = TrainingReportGenerator(
            job_id="unique-job-abc123",
            problem_type="classification",
            metrics=sample_metrics,
            feature_importance=sample_feature_importance,
            training_config=sample_training_config,
            preprocessing_info=sample_preprocessing_info,
            dataset_info=sample_dataset_info
        )
        
        html = generator.generate()
        
        assert "unique-job-abc123" in html
    
    def test_html_contains_metrics(
        self,
        sample_metrics,
        sample_feature_importance,
        sample_training_config,
        sample_preprocessing_info,
        sample_dataset_info
    ):
        """Generated HTML contains metric values"""
        generator = TrainingReportGenerator(
            job_id="test-job",
            problem_type="classification",
            metrics=sample_metrics,
            feature_importance=sample_feature_importance,
            training_config=sample_training_config,
            preprocessing_info=sample_preprocessing_info,
            dataset_info=sample_dataset_info
        )
        
        html = generator.generate()
        
        # Check accuracy is present (92% or 0.92)
        assert "92" in html or "0.92" in html
    
    def test_html_contains_feature_importance(
        self,
        sample_metrics,
        sample_feature_importance,
        sample_training_config,
        sample_preprocessing_info,
        sample_dataset_info
    ):
        """Generated HTML contains feature importance data"""
        generator = TrainingReportGenerator(
            job_id="test-job",
            problem_type="classification",
            metrics=sample_metrics,
            feature_importance=sample_feature_importance,
            training_config=sample_training_config,
            preprocessing_info=sample_preprocessing_info,
            dataset_info=sample_dataset_info
        )
        
        html = generator.generate()
        
        assert "feature_a" in html
        assert "feature_b" in html
    
    def test_format_time_seconds(
        self,
        sample_metrics,
        sample_feature_importance,
        sample_training_config,
        sample_preprocessing_info,
        sample_dataset_info
    ):
        """_format_time correctly formats seconds"""
        generator = TrainingReportGenerator(
            job_id="test",
            problem_type="classification",
            metrics=sample_metrics,
            feature_importance=sample_feature_importance,
            training_config=sample_training_config,
            preprocessing_info=sample_preprocessing_info,
            dataset_info=sample_dataset_info
        )
        
        assert generator._format_time(45.5) == "45.5s"
        assert generator._format_time(125) == "2m 5s"
        assert generator._format_time(3725) == "1h 2m"


# =============================================================================
# Test generate_training_report Function
# =============================================================================

class TestGenerateTrainingReport:
    """Tests for the main generate_training_report function"""
    
    def test_writes_file_to_output_path(
        self,
        sample_metrics,
        sample_feature_importance,
        sample_training_config,
        sample_preprocessing_info,
        sample_dataset_info
    ):
        """Function writes HTML to the specified output path"""
        m = mock_open()
        
        with patch("builtins.open", m):
            generate_training_report(
                output_path="/tmp/report.html",
                job_id="test-job",
                problem_type="classification",
                metrics=sample_metrics,
                feature_importance=sample_feature_importance,
                training_config=sample_training_config,
                preprocessing_info=sample_preprocessing_info,
                dataset_info=sample_dataset_info
            )
        
        # Verify file was opened for writing
        m.assert_called_once_with("/tmp/report.html", 'w', encoding='utf-8')
        
        # Verify HTML was written
        handle = m()
        handle.write.assert_called_once()
        written_content = handle.write.call_args[0][0]
        assert "<!DOCTYPE html>" in written_content
    
    def test_handles_exception_with_fallback(
        self,
        sample_metrics,
        sample_feature_importance,
        sample_training_config,
        sample_preprocessing_info,
        sample_dataset_info
    ):
        """Function falls back to minimal report on error"""
        # Mock TrainingReportGenerator to raise an exception
        with patch("training.reports.training.TrainingReportGenerator") as mock_generator:
            mock_generator.side_effect = Exception("Test error")
            
            m = mock_open()
            with patch("builtins.open", m):
                generate_training_report(
                    output_path="/tmp/report.html",
                    job_id="test-job",
                    problem_type="classification",
                    metrics=sample_metrics,
                    feature_importance=sample_feature_importance,
                    training_config=sample_training_config,
                    preprocessing_info=sample_preprocessing_info,
                    dataset_info=sample_dataset_info
                )
            
            # Should still write a file (minimal report)
            assert m.called


# =============================================================================
# Test generate_minimal_training_report Function
# =============================================================================

class TestGenerateMinimalTrainingReport:
    """Tests for the minimal fallback report generator"""
    
    def test_writes_minimal_html(self):
        """Minimal report writes valid HTML"""
        m = mock_open()
        
        with patch("builtins.open", m):
            generate_minimal_training_report(
                output_path="/tmp/minimal.html",
                job_id="minimal-job",
                metrics={"accuracy": 0.85, "f1_score": 0.82},
                problem_type="classification"
            )
        
        m.assert_called_once_with("/tmp/minimal.html", 'w', encoding='utf-8')
        
        written_content = m().write.call_args[0][0]
        assert "<!DOCTYPE html>" in written_content
        assert "minimal-job" in written_content
        assert "classification" in written_content
    
    def test_includes_all_metrics(self):
        """Minimal report includes all provided metrics"""
        m = mock_open()
        
        metrics = {
            "accuracy": 0.90,
            "precision": 0.88,
            "recall": 0.85
        }
        
        with patch("builtins.open", m):
            generate_minimal_training_report(
                output_path="/tmp/minimal.html",
                job_id="test",
                metrics=metrics,
                problem_type="classification"
            )
        
        written_content = m().write.call_args[0][0]
        assert "accuracy" in written_content
        assert "precision" in written_content
        assert "recall" in written_content
    
    def test_handles_empty_metrics(self):
        """Minimal report handles empty metrics dictionary"""
        m = mock_open()
        
        with patch("builtins.open", m):
            generate_minimal_training_report(
                output_path="/tmp/minimal.html",
                job_id="test",
                metrics={},
                problem_type="regression"
            )
        
        # Should still write the file
        m.assert_called_once()
    
    def test_handles_none_values_in_metrics(self):
        """Minimal report skips None values in metrics"""
        m = mock_open()
        
        metrics = {
            "accuracy": 0.90,
            "auc": None,  # Should be skipped
            "f1_score": 0.85
        }
        
        with patch("builtins.open", m):
            generate_minimal_training_report(
                output_path="/tmp/minimal.html",
                job_id="test",
                metrics=metrics,
                problem_type="classification"
            )
        
        written_content = m().write.call_args[0][0]
        assert "accuracy" in written_content
        assert "f1_score" in written_content


# =============================================================================
# Test Regression Reports
# =============================================================================

class TestRegressionReport:
    """Tests specific to regression problem type"""
    
    def test_regression_report_contains_r2(
        self,
        sample_regression_metrics,
        sample_feature_importance,
        sample_training_config,
        sample_preprocessing_info,
        sample_dataset_info
    ):
        """Regression report contains R² metric"""
        generator = TrainingReportGenerator(
            job_id="regression-job",
            problem_type="regression",
            metrics=sample_regression_metrics,
            feature_importance=sample_feature_importance,
            training_config=sample_training_config,
            preprocessing_info=sample_preprocessing_info,
            dataset_info=sample_dataset_info
        )
        
        html = generator.generate()
        
        # R2 should be present
        assert "0.85" in html or "85" in html
    
    def test_regression_badge_in_html(
        self,
        sample_regression_metrics,
        sample_feature_importance,
        sample_training_config,
        sample_preprocessing_info,
        sample_dataset_info
    ):
        """Regression report shows regression badge"""
        generator = TrainingReportGenerator(
            job_id="regression-job",
            problem_type="regression",
            metrics=sample_regression_metrics,
            feature_importance=sample_feature_importance,
            training_config=sample_training_config,
            preprocessing_info=sample_preprocessing_info,
            dataset_info=sample_dataset_info
        )
        
        html = generator.generate()
        
        assert "regression" in html.lower()


# =============================================================================
# Test Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling"""
    
    def test_empty_feature_importance(
        self,
        sample_metrics,
        sample_training_config,
        sample_preprocessing_info,
        sample_dataset_info
    ):
        """Report handles empty feature importance"""
        generator = TrainingReportGenerator(
            job_id="test",
            problem_type="classification",
            metrics=sample_metrics,
            feature_importance={},
            training_config=sample_training_config,
            preprocessing_info=sample_preprocessing_info,
            dataset_info=sample_dataset_info
        )
        
        html = generator.generate()
        assert isinstance(html, str)
        assert "<!DOCTYPE html>" in html
    
    def test_empty_preprocessing_info(
        self,
        sample_metrics,
        sample_feature_importance,
        sample_training_config,
        sample_dataset_info
    ):
        """Report handles empty preprocessing info"""
        generator = TrainingReportGenerator(
            job_id="test",
            problem_type="classification",
            metrics=sample_metrics,
            feature_importance=sample_feature_importance,
            training_config=sample_training_config,
            preprocessing_info={},
            dataset_info=sample_dataset_info
        )
        
        html = generator.generate()
        assert isinstance(html, str)
    
    def test_special_characters_in_job_id(
        self,
        sample_metrics,
        sample_feature_importance,
        sample_training_config,
        sample_preprocessing_info,
        sample_dataset_info
    ):
        """Report handles special characters in job ID"""
        generator = TrainingReportGenerator(
            job_id="job-123_test<special>",
            problem_type="classification",
            metrics=sample_metrics,
            feature_importance=sample_feature_importance,
            training_config=sample_training_config,
            preprocessing_info=sample_preprocessing_info,
            dataset_info=sample_dataset_info
        )
        
        # Should not raise an exception
        html = generator.generate()
        assert isinstance(html, str)
    
    def test_very_long_feature_names(
        self,
        sample_metrics,
        sample_training_config,
        sample_preprocessing_info,
        sample_dataset_info
    ):
        """Report handles very long feature names"""
        long_features = {
            "this_is_a_very_long_feature_name_that_might_break_layout_" * 3: 0.5,
            "another_extremely_long_feature_name_for_testing_purposes": 0.3,
            "short": 0.2
        }
        
        generator = TrainingReportGenerator(
            job_id="test",
            problem_type="classification",
            metrics=sample_metrics,
            feature_importance=long_features,
            training_config=sample_training_config,
            preprocessing_info=sample_preprocessing_info,
            dataset_info=sample_dataset_info
        )
        
        html = generator.generate()
        assert isinstance(html, str)
