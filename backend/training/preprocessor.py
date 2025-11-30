import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from typing import Tuple


class AutoPreprocessor:
    """Automatic data preprocessing for AutoML"""
    
    def __init__(self, target_column: str):
        self.target_column = target_column
        self.label_encoders = {}
        self.scaler = StandardScaler()
        self.feature_columns = []
        self.numeric_columns = []
        self.categorical_columns = []
    
    def detect_problem_type(self, y: pd.Series) -> str:
        """Detect if problem is classification or regression"""
        # Check if target is numeric
        if pd.api.types.is_numeric_dtype(y):
            # If numeric, check unique values ratio
            unique_ratio = y.nunique() / len(y)
            
            # If less than 5% unique values or less than 20 unique values, likely classification
            if unique_ratio < 0.05 or y.nunique() < 20:
                return 'classification'
            else:
                return 'regression'
        else:
            # Non-numeric target is classification
            return 'classification'
    
    def handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values in the dataset"""
        df = df.copy()
        
        # For numeric columns, fill with median
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if df[col].isnull().any():
                df[col].fillna(df[col].median(), inplace=True)
        
        # For categorical columns, fill with mode
        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            if df[col].isnull().any():
                df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else 'Unknown', inplace=True)
        
        return df
    
    def encode_categorical(self, df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """Encode categorical variables"""
        df = df.copy()
        
        categorical_cols = df.select_dtypes(include=['object']).columns
        self.categorical_columns = list(categorical_cols)
        
        for col in categorical_cols:
            if fit:
                le = LabelEncoder()
                df[col] = le.fit_transform(df[col].astype(str))
                self.label_encoders[col] = le
            else:
                if col in self.label_encoders:
                    le = self.label_encoders[col]
                    # Handle unseen categories
                    df[col] = df[col].astype(str).apply(
                        lambda x: le.transform([x])[0] if x in le.classes_ else -1
                    )
        
        return df
    
    def preprocess(
        self, 
        df: pd.DataFrame, 
        test_size: float = 0.2
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, str]:
        """
        Complete preprocessing pipeline
        Returns: X_train, X_test, y_train, y_test, problem_type
        """
        # Separate features and target
        y = df[self.target_column].copy()
        X = df.drop(columns=[self.target_column]).copy()
        
        # Detect problem type
        problem_type = self.detect_problem_type(y)
        print(f"Detected problem type: {problem_type}")
        
        # Handle missing values
        X = self.handle_missing_values(X)
        
        # Store feature columns
        self.feature_columns = list(X.columns)
        self.numeric_columns = list(X.select_dtypes(include=[np.number]).columns)
        
        # Encode categorical features
        X = self.encode_categorical(X, fit=True)
        
        # Encode target if classification
        if problem_type == 'classification':
            if not pd.api.types.is_numeric_dtype(y):
                le = LabelEncoder()
                y = pd.Series(le.fit_transform(y.astype(str)), index=y.index)
                self.label_encoders['__target__'] = le
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y if problem_type == 'classification' else None
        )
        
        return X_train, X_test, y_train, y_test, problem_type
