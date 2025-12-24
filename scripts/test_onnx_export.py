#!/usr/bin/env python3
"""Test script to verify ONNX export functionality locally.

This script creates a simple sklearn model and tests the ONNX export
without needing the full training pipeline.

Usage:
    pip install scikit-learn skl2onnx onnx onnxruntime pandas numpy
    python scripts/test_onnx_export.py
"""

import sys
import tempfile
from pathlib import Path

# Add training module to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "training"))

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.datasets import make_classification, make_regression


def test_classifier_export():
    """Test ONNX export for a classification model."""
    print("\n" + "=" * 60)
    print("Testing ONNX export for CLASSIFIER")
    print("=" * 60)
    
    # Create sample classification data
    X, y = make_classification(
        n_samples=100,
        n_features=10,
        n_informative=5,
        n_redundant=2,
        random_state=42
    )
    
    # Convert to DataFrame (like real training pipeline)
    feature_names = [f"feature_{i}" for i in range(X.shape[1])]
    X_df = pd.DataFrame(X, columns=feature_names)
    
    # Train a simple model
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X_df, y)
    
    print(f"✓ Model trained: {type(model).__name__}")
    print(f"  - Features: {X_df.shape[1]}")
    print(f"  - Classes: {len(np.unique(y))}")
    
    # Test ONNX export
    from onnx_exporter import export_model_to_onnx
    
    with tempfile.TemporaryDirectory() as tmpdir:
        onnx_path = Path(tmpdir) / "classifier_model.onnx"
        
        success = export_model_to_onnx(
            model=model,
            X_sample=X_df,
            output_path=str(onnx_path),
            model_name="test_classifier"
        )
        
        if success:
            print(f"\n✓ ONNX export successful!")
            print(f"  - File size: {onnx_path.stat().st_size / 1024:.1f} KB")
            
            # Test inference with ONNX Runtime
            test_onnx_inference(onnx_path, X_df.iloc[:5])
            return True
        else:
            print(f"\n✗ ONNX export failed!")
            return False


def test_regressor_export():
    """Test ONNX export for a regression model."""
    print("\n" + "=" * 60)
    print("Testing ONNX export for REGRESSOR")
    print("=" * 60)
    
    # Create sample regression data
    X, y = make_regression(
        n_samples=100,
        n_features=8,
        n_informative=5,
        random_state=42
    )
    
    # Convert to DataFrame
    feature_names = [f"feature_{i}" for i in range(X.shape[1])]
    X_df = pd.DataFrame(X, columns=feature_names)
    
    # Train a simple model
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    model.fit(X_df, y)
    
    print(f"✓ Model trained: {type(model).__name__}")
    print(f"  - Features: {X_df.shape[1]}")
    
    # Test ONNX export
    from onnx_exporter import export_model_to_onnx
    
    with tempfile.TemporaryDirectory() as tmpdir:
        onnx_path = Path(tmpdir) / "regressor_model.onnx"
        
        success = export_model_to_onnx(
            model=model,
            X_sample=X_df,
            output_path=str(onnx_path),
            model_name="test_regressor"
        )
        
        if success:
            print(f"\n✓ ONNX export successful!")
            print(f"  - File size: {onnx_path.stat().st_size / 1024:.1f} KB")
            
            # Test inference with ONNX Runtime
            test_onnx_inference(onnx_path, X_df.iloc[:5])
            return True
        else:
            print(f"\n✗ ONNX export failed!")
            return False


def test_onnx_inference(onnx_path: Path, X_sample: pd.DataFrame):
    """Test that the ONNX model can make predictions."""
    print("\nTesting ONNX inference...")
    
    try:
        import onnxruntime as rt
        
        # Create inference session
        sess = rt.InferenceSession(
            str(onnx_path),
            providers=["CPUExecutionProvider"]
        )
        
        # Prepare input
        input_name = sess.get_inputs()[0].name
        X_array = X_sample.values.astype(np.float32)
        
        # Run inference
        outputs = sess.run(None, {input_name: X_array})
        
        print(f"✓ ONNX inference successful!")
        print(f"  - Input shape: {X_array.shape}")
        print(f"  - Output shapes: {[o.shape for o in outputs]}")
        print(f"  - Sample predictions: {outputs[0][:3]}")
        
    except Exception as e:
        print(f"✗ ONNX inference failed: {e}")


def main():
    """Run all ONNX export tests."""
    print("=" * 60)
    print("AWS AutoML Lite - ONNX Export Test Suite")
    print("=" * 60)
    
    # Check dependencies
    try:
        import sklearn
        import onnx
        import skl2onnx
        import onnxruntime
        
        print(f"\nDependencies OK:")
        print(f"  - scikit-learn: {sklearn.__version__}")
        print(f"  - onnx: {onnx.__version__}")
        print(f"  - skl2onnx: {skl2onnx.__version__}")
        print(f"  - onnxruntime: {onnxruntime.__version__}")
        
    except ImportError as e:
        print(f"\n✗ Missing dependency: {e}")
        print("\nInstall with:")
        print("  pip install scikit-learn skl2onnx onnx onnxruntime pandas numpy")
        sys.exit(1)
    
    # Run tests
    results = []
    
    results.append(("Classifier", test_classifier_export()))
    results.append(("Regressor", test_regressor_export()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("All tests passed! ONNX export is working correctly.")
    else:
        print("Some tests failed. Check the output above for details.")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
