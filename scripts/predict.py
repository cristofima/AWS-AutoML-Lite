#!/usr/bin/env python3
"""
AWS AutoML Lite - Model Prediction Script

Use this script to make predictions with models trained by AWS AutoML Lite.

Usage:
    # Single prediction with JSON input
    python predict.py model.pkl '{"Age": 35, "City": "Istanbul", "Product_Category": "Electronics"}'
    
    # Batch predictions from CSV file
    python predict.py model.pkl --input data.csv --output predictions.csv
    
    # Single prediction from JSON file
    python predict.py model.pkl --json input.json
    
    # Show model info
    python predict.py model.pkl --info

Requirements (same as training container):
    pip install pandas scikit-learn joblib flaml[automl] lightgbm feature-engine

Author: AWS AutoML Lite
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import joblib
    import pandas as pd
    import numpy as np
except ImportError as e:
    print(f"Error: Missing required package.")
    print(f"Run: pip install pandas scikit-learn joblib flaml[automl] lightgbm feature-engine")
    print(f"Details: {e}")
    sys.exit(1)


def load_model(model_path: str) -> dict:
    """Load the trained model package from a .pkl file."""
    path = Path(model_path)
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    if not path.suffix == '.pkl':
        raise ValueError(f"Expected .pkl file, got: {path.suffix}")
    
    model_package = joblib.load(path)
    
    # Validate model package structure
    required_keys = ['model', 'preprocessor', 'problem_type']
    for key in required_keys:
        if key not in model_package:
            raise ValueError(f"Invalid model package: missing '{key}'")
    
    return model_package


def show_model_info(model_package: dict) -> None:
    """Display information about the loaded model."""
    print("\n" + "=" * 60)
    print("📦 MODEL INFORMATION")
    print("=" * 60)
    
    # Problem type
    problem_type = model_package.get('problem_type', 'Unknown')
    print(f"\n🎯 Problem Type: {problem_type.upper()}")
    
    # Preprocessor info
    preprocessor = model_package.get('preprocessor')
    if preprocessor:
        print(f"\n📋 Features ({len(preprocessor.feature_columns)}):")
        for i, col in enumerate(preprocessor.feature_columns, 1):
            print(f"   {i}. {col}")
        
        if hasattr(preprocessor, 'dropped_columns') and preprocessor.dropped_columns:
            print(f"\n⚠️  Excluded columns: {preprocessor.dropped_columns}")
        
        if hasattr(preprocessor, 'categorical_columns') and preprocessor.categorical_columns:
            print(f"\n🏷️  Categorical columns: {preprocessor.categorical_columns}")
        
        # Show target labels if classification
        if '__target__' in preprocessor.label_encoders:
            le = preprocessor.label_encoders['__target__']
            print(f"\n🎯 Target classes: {list(le.classes_)}")
    
    # Feature importance
    feature_importance = model_package.get('feature_importance', {})
    if feature_importance:
        print(f"\n📈 Top 10 Feature Importance:")
        sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]
        max_imp = max(v for _, v in sorted_features) if sorted_features else 1
        for i, (feat, imp) in enumerate(sorted_features, 1):
            bar_len = int((imp / max_imp) * 30) if max_imp > 0 else 0
            bar = "█" * bar_len
            print(f"   {i:2}. {feat:<30} {imp:.4f} {bar}")
    
    # Model type
    model = model_package.get('model')
    if model:
        best_estimator = getattr(model, 'best_estimator', 'Unknown')
        print(f"\n🤖 Best Estimator: {best_estimator}")
    
    # Generate sample JSON input
    if preprocessor and preprocessor.feature_columns:
        print(f"\n📝 Sample input JSON:")
        sample = {}
        for col in preprocessor.feature_columns[:5]:
            if col in preprocessor.categorical_columns:
                sample[col] = "<category>"
            else:
                sample[col] = 0.0
        if len(preprocessor.feature_columns) > 5:
            sample["..."] = "..."
        print(f"   {json.dumps(sample, indent=2)}")
    
    print("\n" + "=" * 60)


def generate_sample_input(model_package: dict, output_path: str = None) -> dict:
    """
    Generate a sample input JSON based on the model's required features.
    Detects feature types and provides appropriate placeholder values.
    """
    preprocessor = model_package.get('preprocessor')
    if not preprocessor or not preprocessor.feature_columns:
        raise ValueError("Model does not contain feature information")
    
    sample = {}
    categorical_cols = getattr(preprocessor, 'categorical_columns', [])
    label_encoders = getattr(preprocessor, 'label_encoders', {})
    
    for col in preprocessor.feature_columns:
        if col in categorical_cols:
            # Get actual category values from label encoder if available
            if col in label_encoders:
                le = label_encoders[col]
                # Use first category as example
                sample[col] = str(le.classes_[0]) if len(le.classes_) > 0 else "category"
            else:
                sample[col] = "category"
        else:
            # Numeric - use 0.0 as placeholder
            sample[col] = 0.0
    
    # Save to file if path provided
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(sample, f, indent=4)
        print(f"✅ Sample input saved to: {output_path}")
        print(f"   Features: {len(sample)}")
        print(f"\n📝 Edit the file with your actual values before running predictions.")
    
    return sample


def prepare_input(data: pd.DataFrame, preprocessor) -> pd.DataFrame:
    """
    Prepare input data for prediction using the saved preprocessor.
    Uses the same logic as training but for inference.
    """
    df = data.copy()
    
    # Ensure all required columns are present
    missing_cols = set(preprocessor.feature_columns) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Select only feature columns in the correct order
    df = df[preprocessor.feature_columns]
    
    # Handle missing values (same as training)
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if df[col].isnull().any():
            df[col].fillna(df[col].median(), inplace=True)
    
    categorical_cols = df.select_dtypes(include=['object']).columns
    for col in categorical_cols:
        if df[col].isnull().any():
            df[col].fillna('Unknown', inplace=True)
    
    # Encode categorical columns using saved encoders
    for col in df.columns:
        if col in preprocessor.label_encoders:
            le = preprocessor.label_encoders[col]
            # Handle unseen categories gracefully
            df[col] = df[col].astype(str).apply(
                lambda x: le.transform([x])[0] if x in le.classes_ else -1
            )
    
    return df


def decode_prediction(prediction, preprocessor, problem_type):
    """Decode prediction back to original label if applicable."""
    if problem_type == 'classification' and '__target__' in preprocessor.label_encoders:
        le = preprocessor.label_encoders['__target__']
        try:
            return le.inverse_transform([int(prediction)])[0]
        except (ValueError, IndexError):
            return prediction
    return prediction


def predict_single(model_package: dict, input_data: dict) -> dict:
    """Make prediction for a single input."""
    model = model_package['model']
    preprocessor = model_package['preprocessor']
    problem_type = model_package['problem_type']
    
    # Convert to DataFrame
    df = pd.DataFrame([input_data])
    
    # Prepare data
    X = prepare_input(df, preprocessor)
    
    # Predict
    prediction = model.predict(X)[0]
    
    result = {
        'prediction': float(prediction) if problem_type == 'regression' else int(prediction),
        'problem_type': problem_type
    }
    
    # Decode label for classification
    if problem_type == 'classification':
        result['prediction_label'] = decode_prediction(prediction, preprocessor, problem_type)
    
    # Add probabilities for classification
    if problem_type == 'classification' and hasattr(model, 'predict_proba'):
        try:
            probas = model.predict_proba(X)[0]
            # Get class labels
            if '__target__' in preprocessor.label_encoders:
                le = preprocessor.label_encoders['__target__']
                class_labels = le.classes_
            else:
                class_labels = [f"class_{i}" for i in range(len(probas))]
            
            result['probabilities'] = {str(label): float(p) for label, p in zip(class_labels, probas)}
            result['confidence'] = float(max(probas))
        except Exception:
            pass
    
    return result


def predict_batch(model_package: dict, input_path: str, output_path: str) -> None:
    """Make predictions for a batch of inputs from CSV."""
    model = model_package['model']
    preprocessor = model_package['preprocessor']
    problem_type = model_package['problem_type']
    
    # Load input data
    print(f"📂 Loading input data from: {input_path}")
    df = pd.read_csv(input_path)
    print(f"   Loaded {len(df)} rows")
    
    # Prepare data
    print("⚙️  Preprocessing data...")
    X = prepare_input(df, preprocessor)
    
    # Predict
    print("🔮 Making predictions...")
    predictions = model.predict(X)
    
    # Add predictions to original dataframe
    df['prediction'] = predictions
    
    # Decode predictions if classification
    if problem_type == 'classification':
        df['prediction_label'] = [
            decode_prediction(p, preprocessor, problem_type) 
            for p in predictions
        ]
    
    # Add probabilities for classification
    if problem_type == 'classification' and hasattr(model, 'predict_proba'):
        try:
            probas = model.predict_proba(X)
            df['confidence'] = probas.max(axis=1)
        except Exception:
            pass
    
    # Save results
    df.to_csv(output_path, index=False)
    print(f"✅ Predictions saved to: {output_path}")
    print(f"   Total predictions: {len(predictions)}")


def main():
    parser = argparse.ArgumentParser(
        description='Make predictions with AWS AutoML Lite trained models',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show model information
  python predict.py model.pkl --info
  
  # Generate sample input JSON from model
  python predict.py model.pkl --generate-sample sample_input.json
  
  # Single prediction with inline JSON
  python predict.py model.pkl '{"Age": 35, "City": "Istanbul"}'
  
  # Single prediction from JSON file
  python predict.py model.pkl --json input.json
  
  # Batch predictions from CSV
  python predict.py model.pkl --input test_data.csv --output predictions.csv
        """
    )
    
    parser.add_argument('model', help='Path to the model .pkl file')
    parser.add_argument('json_input', nargs='?', help='JSON string with input features for single prediction')
    parser.add_argument('--json', '-j', help='JSON file with input features for single prediction')
    parser.add_argument('--input', '-i', help='Input CSV file for batch predictions')
    parser.add_argument('--output', '-o', default='predictions.csv', help='Output CSV file (default: predictions.csv)')
    parser.add_argument('--info', action='store_true', help='Show model information and exit')
    parser.add_argument('--generate-sample', '-g', metavar='FILE', help='Generate sample input JSON file based on model features')
    
    args = parser.parse_args()
    
    try:
        # Load model
        print(f"🔄 Loading model from: {args.model}")
        model_package = load_model(args.model)
        print("✅ Model loaded successfully!")
        
        # Show info and exit
        if args.info:
            show_model_info(model_package)
            return
        
        # Generate sample input file
        if args.generate_sample:
            generate_sample_input(model_package, args.generate_sample)
            return
        
        # Batch prediction from CSV
        if args.input:
            predict_batch(model_package, args.input, args.output)
            return
        
        # Single prediction from JSON file
        if args.json:
            json_path = Path(args.json)
            if not json_path.exists():
                print(f"❌ JSON file not found: {args.json}")
                sys.exit(1)
            with open(json_path) as f:
                input_data = json.load(f)
            
            result = predict_single(model_package, input_data)
            print_prediction_result(input_data, result)
            return
        
        # Single prediction from inline JSON
        if args.json_input:
            try:
                input_data = json.loads(args.json_input)
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON input: {e}")
                sys.exit(1)
            
            result = predict_single(model_package, input_data)
            print_prediction_result(input_data, result)
            return
        
        # No input provided, show info
        show_model_info(model_package)
        print("\n💡 Tip: Provide JSON input for prediction or use --input for batch mode")
        print("   Example: python predict.py model.pkl '{\"Age\": 35, \"City\": \"Istanbul\"}'")
        print("   Or:      python predict.py model.pkl --json input.json")
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def print_prediction_result(input_data: dict, result: dict) -> None:
    """Print formatted prediction result."""
    print("\n" + "=" * 40)
    print("🔮 PREDICTION RESULT")
    print("=" * 40)
    print(f"\n📊 Input: {json.dumps(input_data, indent=2)}")
    
    if result['problem_type'] == 'classification':
        print(f"\n🎯 Prediction: {result.get('prediction_label', result['prediction'])}")
    else:
        print(f"\n🎯 Prediction: {result['prediction']:.4f}")
    
    if 'confidence' in result:
        print(f"   Confidence: {result['confidence']:.2%}")
    
    if 'probabilities' in result:
        print(f"\n📈 Class Probabilities:")
        for cls, prob in sorted(result['probabilities'].items(), key=lambda x: x[1], reverse=True):
            bar_len = int(prob * 30)
            bar = "█" * bar_len
            print(f"   {cls}: {prob:.4f} {bar}")
    
    print()


if __name__ == '__main__':
    main()
