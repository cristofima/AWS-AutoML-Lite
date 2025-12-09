import pandas as pd
import numpy as np
import re
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from typing import Tuple, List

# Feature-engine for robust feature selection
from feature_engine.selection import DropConstantFeatures, DropDuplicateFeatures


class AutoPreprocessor:
    """Automatic data preprocessing for AutoML"""
    
    # Common patterns for ID/identifier columns (case insensitive)
    ID_PATTERNS = [
        r'^id$',
        r'_id$',
        r'^id_',
        r'_id_',
        r'^uuid$',
        r'^guid$',
        r'order.*id',
        r'customer.*id',
        r'user.*id',
        r'transaction.*id',
        r'product.*id',
        r'session.*id',
        r'^index$',
        r'^row.*num',
        r'^serial',
        r'^record.*id',
    ]
    
    def __init__(self, target_column: str):
        self.target_column = target_column
        self.label_encoders = {}
        self.scaler = StandardScaler()
        self.feature_columns = []
        self.numeric_columns = []
        self.categorical_columns = []
        self.dropped_columns = []  # Track dropped columns for reporting
    
    def detect_id_column(self, col_name: str, series: pd.Series) -> bool:
        """
        Detect if a column is likely an ID/identifier column.
        Uses both name patterns and data characteristics.
        """
        col_lower = col_name.lower().strip()
        
        # Check name patterns
        for pattern in self.ID_PATTERNS:
            if re.search(pattern, col_lower):
                return True
        
        # Check data characteristics for numeric columns
        if pd.api.types.is_numeric_dtype(series):
            n_unique = series.nunique()
            n_total = len(series)
            
            # If all values are unique and sequential, likely an ID
            if n_unique == n_total:
                # Check if values are sequential integers
                if series.dtype in ['int64', 'int32', 'int']:
                    sorted_vals = series.sort_values()
                    is_sequential = (sorted_vals.diff().dropna() == 1).all()
                    if is_sequential:
                        return True
        
        # Check for string columns that look like IDs (high cardinality)
        if series.dtype == 'object':
            n_unique = series.nunique()
            n_total = len(series)
            
            # If almost all values are unique, likely an ID
            if n_unique / n_total > 0.95:
                # Additional check: IDs often have consistent format
                sample = series.dropna().head(100)
                # Check if values look like codes/IDs (alphanumeric patterns)
                if sample.apply(lambda x: bool(re.match(r'^[A-Za-z0-9\-_]+$', str(x)))).mean() > 0.9:
                    return True
        
        return False
    
    def detect_constant_column(self, series: pd.Series) -> bool:
        """Detect if a column has only one unique value (constant)"""
        return series.nunique() <= 1
    
    def detect_high_cardinality_categorical(self, series: pd.Series, threshold: float = 0.5) -> bool:
        """
        Detect categorical columns with too many unique values.
        These often don't generalize well and can cause overfitting.
        """
        if series.dtype != 'object':
            return False
        
        n_unique = series.nunique()
        n_total = len(series)
        
        # If more than 50% unique values, too high cardinality
        return n_unique / n_total > threshold
    
    def detect_useless_columns_with_feature_engine(self, df: pd.DataFrame) -> Tuple[List[str], dict]:
        """
        Use feature-engine to detect constant and duplicate columns.
        Returns tuple of (columns_to_drop, reasons_dict)
        """
        cols_to_drop = []
        reasons = {}
        
        # Prepare dataframe without target
        X = df.drop(columns=[self.target_column], errors='ignore')
        
        try:
            # Detect constant features (columns with single unique value)
            constant_detector = DropConstantFeatures(tol=0.98, missing_values='ignore')
            constant_detector.fit(X)
            constant_cols = constant_detector.features_to_drop_
            for col in constant_cols:
                cols_to_drop.append(col)
                reasons[col] = "constant or quasi-constant (>98% same value)"
            
            # Detect duplicate columns
            X_no_constant = X.drop(columns=constant_cols, errors='ignore')
            if len(X_no_constant.columns) > 1:
                duplicate_detector = DropDuplicateFeatures(missing_values='ignore')
                duplicate_detector.fit(X_no_constant)
                duplicate_cols = duplicate_detector.features_to_drop_
                for col in duplicate_cols:
                    if col not in cols_to_drop:
                        cols_to_drop.append(col)
                        reasons[col] = "duplicate of another column"
        except Exception as e:
            print(f"⚠️  Feature-engine detection warning: {e}")
        
        return cols_to_drop, reasons

    def detect_useless_columns(self, df: pd.DataFrame) -> List[str]:
        """
        Detect columns that should be excluded from training:
        1. ID columns (unique identifiers) - custom detection
        2. Constant columns (no variance) - feature-engine
        3. Duplicate columns - feature-engine
        4. High cardinality categorical columns - custom detection
        """
        useless_cols = []
        reasons = {}
        
        # Step 1: Use feature-engine for constant and duplicate detection
        fe_cols, fe_reasons = self.detect_useless_columns_with_feature_engine(df)
        useless_cols.extend(fe_cols)
        reasons.update(fe_reasons)
        
        # Step 2: Custom detection for IDs and high cardinality
        for col in df.columns:
            # Skip if already marked or is target
            if col in useless_cols or col == self.target_column:
                continue
            
            series = df[col]
            
            # Check for ID columns (name patterns + data characteristics)
            if self.detect_id_column(col, series):
                useless_cols.append(col)
                reasons[col] = "identifier/ID column"
                continue
            
            # Check for high cardinality categorical
            if series.dtype == 'object':
                if self.detect_high_cardinality_categorical(series, threshold=0.5):
                    useless_cols.append(col)
                    reasons[col] = f"high cardinality categorical ({series.nunique()} unique values)"
                    continue
        
        # Log dropped columns
        if useless_cols:
            print(f"\n🔍 Detected {len(useless_cols)} column(s) to exclude from training:")
            for col in useless_cols:
                print(f"   - '{col}': {reasons[col]}")
            print()
        
        self.dropped_columns = useless_cols
        return useless_cols
    
    def detect_problem_type(self, y: pd.Series) -> str:
        """Detect if problem is classification or regression"""
        # Guard against empty target
        if len(y) == 0:
            return 'classification'  # Default fallback
        
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
        
        # Detect and remove useless columns (IDs, constants, high cardinality)
        useless_cols = self.detect_useless_columns(df)
        if useless_cols:
            # Only drop columns that exist in X (target is already removed)
            cols_to_drop = [col for col in useless_cols if col in X.columns]
            if cols_to_drop:
                X = X.drop(columns=cols_to_drop)
                print(f"✂️  Removed {len(cols_to_drop)} column(s): {cols_to_drop}")
        
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
        
        print(f"📊 Training with {len(self.feature_columns)} features: {self.feature_columns}")
        
        return X_train, X_test, y_train, y_test, problem_type
