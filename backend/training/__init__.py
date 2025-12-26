"""
Training module for AWS AutoML Lite.

This module contains all components for automated machine learning training:
- core: Preprocessing, model training, ONNX export
- reports: EDA and training report generation
- utils: Shared detection utilities

Usage:
    from training.core.preprocessor import AutoPreprocessor
    from training.core.trainer import train_automl_model
    from training.core.exporter import export_model_to_onnx
    from training.reports.eda import generate_eda_report
    from training.reports.training import generate_training_report
    from training.utils.detection import detect_problem_type

Note: This module uses explicit imports to avoid loading heavy ML
dependencies (like FLAML) when only lightweight utilities are needed.
"""

__version__ = "1.1.0"
