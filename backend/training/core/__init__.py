"""
Core ML components: preprocessing, training, and ONNX export.

Usage:
    from training.core.preprocessor import AutoPreprocessor
    from training.core.trainer import train_automl_model
    from training.core.exporter import export_model_to_onnx

Note: Uses explicit imports to avoid loading heavy ML dependencies
(FLAML, skl2onnx) when only preprocessing is needed.
"""
