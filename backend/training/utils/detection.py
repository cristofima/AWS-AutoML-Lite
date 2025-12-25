"""
Shared utilities for the training module.

This module contains common functions used across preprocessing, EDA, and model training.
"""

import pandas as pd
import re


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


def detect_problem_type(y: pd.Series) -> str:
    """
    Detect if problem is classification or regression.
    
    This function uses heuristics to determine the problem type based on:
    - Data type (numeric vs categorical)
    - Number of unique values
    - Whether values are integer-like or continuous
    
    Classification indicators:
    - Non-numeric dtype (strings, categories)
    - Integer dtype with few unique values (<= 10)
    - Low unique ratio (< 5%) AND few unique values (< 20)
    
    Regression indicators:
    - Float dtype with decimal values
    - High unique ratio (>= 5%) for numeric data
    - Continuous-looking distribution
    
    Args:
        y: Target variable series
        
    Returns:
        'classification' or 'regression'
        
    Examples:
        >>> detect_problem_type(pd.Series([0, 1, 0, 1, 1, 0]))
        'classification'
        >>> detect_problem_type(pd.Series([35.5, 42.1, 38.7, 41.2]))
        'regression'
        >>> detect_problem_type(pd.Series(['cat', 'dog', 'bird']))
        'classification'
    """
    # Guard against empty target
    if len(y) == 0:
        return 'classification'  # Default fallback
    
    # Non-numeric target is always classification
    if not pd.api.types.is_numeric_dtype(y):
        return 'classification'
    
    n_unique = y.nunique()
    unique_ratio = n_unique / len(y)
    
    # Check if values are integer-like (no decimals)
    # This handles both int dtype and float dtype with .0 values
    try:
        is_integer_like = (y.dropna() == y.dropna().astype(int)).all()
    except (ValueError, TypeError):
        is_integer_like = False
    
    # Classification criteria:
    # 1. Integer-like values with few unique values (typical class labels: 0,1,2,...)
    if is_integer_like and n_unique <= 10:
        return 'classification'
    
    # 2. Low cardinality with low ratio - likely categorical encoded as numbers
    if n_unique < 20 and unique_ratio < 0.05:
        return 'classification'
    
    # Everything else is regression:
    # - Float values with decimals (scores, prices, measurements)
    # - High unique ratio (continuous distribution)
    # - Many unique values even if ratio is low
    return 'regression'


def is_id_column(col_name: str, series: pd.Series) -> bool:
    """
    Detect if a column is likely an ID/identifier column.
    
    Uses both name patterns and data characteristics to determine
    if a column is an identifier that should be excluded from training.
    
    Args:
        col_name: Name of the column
        series: Column data as pandas Series
        
    Returns:
        True if column appears to be an ID column
        
    Examples:
        >>> is_id_column('customer_id', pd.Series([1, 2, 3, 4, 5]))
        True
        >>> is_id_column('age', pd.Series([25, 30, 35, 40, 45]))
        False
    """
    col_lower = col_name.lower().strip()
    
    # Check name patterns
    for pattern in ID_PATTERNS:
        if re.search(pattern, col_lower):
            return True
    
    # Check data characteristics for numeric columns
    if pd.api.types.is_numeric_dtype(series):
        n_unique = series.nunique()
        n_total = len(series)
        
        # If all values are unique and sequential, likely an ID
        if n_unique == n_total:
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
            sample = series.dropna().head(100)
            # Check if values look like codes/IDs (alphanumeric patterns)
            if sample.apply(lambda x: bool(re.match(r'^[A-Za-z0-9\-_]+$', str(x)))).mean() > 0.9:
                return True
    
    return False


def is_constant_column(series: pd.Series) -> bool:
    """
    Detect if a column has only one unique value (constant).
    
    Args:
        series: Column data as pandas Series
        
    Returns:
        True if column has 0 or 1 unique values
    """
    return series.nunique() <= 1


def is_high_cardinality_categorical(series: pd.Series, threshold: float = 0.5) -> bool:
    """
    Detect categorical columns with too many unique values.
    
    High cardinality categorical columns often don't generalize well
    and can cause overfitting.
    
    Args:
        series: Column data as pandas Series
        threshold: Maximum ratio of unique values to total values (default 0.5)
        
    Returns:
        True if column is categorical with high cardinality
    """
    if series.dtype != 'object':
        return False
    
    n_unique = series.nunique()
    n_total = len(series)
    
    return n_unique / n_total > threshold
