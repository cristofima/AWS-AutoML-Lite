import pandas as pd
import numpy as np
from typing import List, Tuple
import re


def generate_eda_report(df: pd.DataFrame, target_column: str, output_path: str):
    """
    Generate comprehensive EDA report with pure HTML/CSS (no external dependencies).
    
    Args:
        df: Input dataframe
        target_column: Name of the target column
        output_path: Path to save the HTML report
    """
    print("Generating comprehensive EDA report...")
    
    try:
        report = EDAReportGenerator(df, target_column)
        html = report.generate()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"EDA report saved to: {output_path}")
        
    except Exception as e:
        print(f"Error generating EDA report: {str(e)}")
        # Fallback to minimal report
        generate_minimal_report(df, target_column, output_path)


class EDAReportGenerator:
    """Generate comprehensive EDA report with CSS-only visualizations"""
    
    # Common ID column patterns
    ID_PATTERNS = [
        r'^id$', r'_id$', r'^id_', r'^uuid$', r'^guid$',
        r'order.*id', r'customer.*id', r'user.*id', r'transaction.*id',
        r'^index$', r'^row.*num', r'^serial', r'^record.*id',
    ]
    
    def __init__(self, df: pd.DataFrame, target_column: str):
        self.df = df
        self.target_column = target_column
        self.target = df[target_column]
        self.features = df.drop(columns=[target_column])
        self.problem_type = self._detect_problem_type()
        self.warnings: List[str] = []
        self.excluded_columns: List[Tuple[str, str]] = []
        
        # Analyze columns
        self._analyze_columns()
    
    def _detect_problem_type(self) -> str:
        """Detect if classification or regression"""
        # Guard against empty target
        if len(self.target) == 0:
            return 'classification'  # Default fallback
        
        if pd.api.types.is_numeric_dtype(self.target):
            unique_ratio = self.target.nunique() / len(self.target)
            if unique_ratio < 0.05 or self.target.nunique() < 20:
                return 'classification'
            return 'regression'
        return 'classification'
    
    def _is_id_column(self, col_name: str, series: pd.Series) -> bool:
        """Check if column is likely an ID"""
        col_lower = col_name.lower().strip()
        for pattern in self.ID_PATTERNS:
            if re.search(pattern, col_lower):
                return True
        
        # Check if all unique and sequential
        if pd.api.types.is_numeric_dtype(series):
            if series.nunique() == len(series):
                sorted_vals = series.sort_values()
                if (sorted_vals.diff().dropna() == 1).all():
                    return True
        
        # High cardinality string column
        if series.dtype == 'object':
            if series.nunique() / len(series) > 0.95:
                return True
        
        return False
    
    def _analyze_columns(self):
        """Analyze and categorize columns"""
        for col in self.features.columns:
            series = self.features[col]
            
            # Check for ID columns
            if self._is_id_column(col, series):
                self.excluded_columns.append((col, "ID/Identifier column"))
                continue
            
            # Check for constant columns
            if series.nunique() <= 1:
                self.excluded_columns.append((col, "Constant value (no variance)"))
                continue
            
            # Check for high cardinality categorical
            if series.dtype == 'object' and series.nunique() / len(series) > 0.5:
                self.excluded_columns.append((col, f"High cardinality ({series.nunique()} unique values)"))
        
        # Add warnings
        missing_cols = [col for col in self.df.columns if self.df[col].isnull().any()]
        if missing_cols:
            self.warnings.append(f"Missing values detected in {len(missing_cols)} column(s)")
        
        if self.problem_type == 'classification':
            class_counts = self.target.value_counts()
            if len(class_counts) > 0 and class_counts.min() > 0:
                imbalance_ratio = class_counts.max() / class_counts.min()
                if imbalance_ratio > 3:
                    self.warnings.append(f"Class imbalance detected (ratio: {imbalance_ratio:.1f}:1)")
    
    def _get_css(self) -> str:
        """Return CSS styles"""
        return """
        <style>
            * { box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                margin: 0; padding: 20px; background: #f5f7fa; color: #333;
            }
            .container { max-width: 1200px; margin: 0 auto; }
            h1 { color: #1a73e8; border-bottom: 3px solid #1a73e8; padding-bottom: 10px; }
            h2 { color: #333; margin-top: 30px; }
            h3 { color: #555; margin-top: 20px; }
            
            .card {
                background: white; border-radius: 8px; padding: 20px;
                margin: 15px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 15px; }
            .grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }
            
            .stat-box {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white; padding: 20px; border-radius: 8px; text-align: center;
            }
            .stat-box.green { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }
            .stat-box.orange { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
            .stat-box.blue { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
            .stat-number { font-size: 2.5em; font-weight: bold; }
            .stat-label { font-size: 0.9em; opacity: 0.9; margin-top: 5px; }
            
            table { width: 100%; border-collapse: collapse; margin: 10px 0; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
            th { background: #f8f9fa; font-weight: 600; color: #555; }
            tr:hover { background: #f8f9fa; }
            
            .bar-container { 
                background: #e9ecef; border-radius: 4px; height: 20px; 
                overflow: hidden; margin: 3px 0;
            }
            .bar { 
                height: 100%; border-radius: 4px; 
                display: flex; align-items: center; padding-left: 8px;
                font-size: 11px; color: white; font-weight: 500;
                transition: width 0.3s ease;
            }
            .bar.primary { background: linear-gradient(90deg, #667eea, #764ba2); }
            .bar.success { background: linear-gradient(90deg, #11998e, #38ef7d); }
            .bar.warning { background: linear-gradient(90deg, #f093fb, #f5576c); }
            .bar.info { background: linear-gradient(90deg, #4facfe, #00f2fe); }
            
            .warning-box {
                background: #fff3cd; border-left: 4px solid #ffc107;
                padding: 15px; margin: 10px 0; border-radius: 0 8px 8px 0;
            }
            .warning-box.danger {
                background: #f8d7da; border-left-color: #dc3545;
            }
            .warning-box.info {
                background: #d1ecf1; border-left-color: #17a2b8;
            }
            
            .badge {
                display: inline-block; padding: 3px 8px; border-radius: 12px;
                font-size: 0.8em; font-weight: 500;
            }
            .badge.classification { background: #e3f2fd; color: #1565c0; }
            .badge.regression { background: #f3e5f5; color: #7b1fa2; }
            .badge.numeric { background: #e8f5e9; color: #2e7d32; }
            .badge.categorical { background: #fff3e0; color: #e65100; }
            .badge.excluded { background: #ffebee; color: #c62828; }
            
            .correlation-cell {
                text-align: center; font-weight: 500;
            }
            .corr-high-pos { background: #c8e6c9; color: #1b5e20; }
            .corr-med-pos { background: #dcedc8; color: #33691e; }
            .corr-low { background: #fff; }
            .corr-med-neg { background: #ffcdd2; color: #b71c1c; }
            .corr-high-neg { background: #ef9a9a; color: #b71c1c; }
            
            .mini-chart { display: flex; align-items: flex-end; height: 40px; gap: 2px; }
            .mini-bar { background: #667eea; border-radius: 2px 2px 0 0; min-width: 8px; }
            
            @media (max-width: 768px) {
                .grid-2 { grid-template-columns: 1fr; }
            }
        </style>
        """
    
    def _generate_overview(self) -> str:
        """Generate dataset overview section"""
        n_rows, n_cols = self.df.shape
        n_numeric = len(self.df.select_dtypes(include=[np.number]).columns)
        n_categorical = len(self.df.select_dtypes(include=['object', 'category']).columns)
        memory_mb = self.df.memory_usage(deep=True).sum() / 1024 / 1024
        
        problem_badge = f'<span class="badge {self.problem_type}">{self.problem_type.upper()}</span>'
        
        return f"""
        <div class="card">
            <h2>📊 Dataset Overview</h2>
            <div class="grid">
                <div class="stat-box">
                    <div class="stat-number">{n_rows:,}</div>
                    <div class="stat-label">Total Rows</div>
                </div>
                <div class="stat-box green">
                    <div class="stat-number">{n_cols}</div>
                    <div class="stat-label">Total Columns</div>
                </div>
                <div class="stat-box orange">
                    <div class="stat-number">{n_numeric}</div>
                    <div class="stat-label">Numeric Features</div>
                </div>
                <div class="stat-box blue">
                    <div class="stat-number">{n_categorical}</div>
                    <div class="stat-label">Categorical Features</div>
                </div>
            </div>
            <div style="margin-top: 20px;">
                <p><strong>Target Column:</strong> <code>{self.target_column}</code></p>
                <p><strong>Problem Type:</strong> {problem_badge}</p>
                <p><strong>Memory Usage:</strong> {memory_mb:.2f} MB</p>
            </div>
        </div>
        """
    
    def _generate_target_analysis(self) -> str:
        """Generate target variable analysis"""
        html = '<div class="card"><h2>🎯 Target Variable Analysis</h2>'
        
        if self.problem_type == 'classification':
            class_counts = self.target.value_counts()
            total = len(self.target)
            
            html += '<h3>Class Distribution</h3><table><tr><th>Class</th><th>Count</th><th>Percentage</th><th>Distribution</th></tr>'
            
            colors = ['primary', 'success', 'warning', 'info']
            for i, (cls, count) in enumerate(class_counts.items()):
                pct = count / total * 100
                color = colors[i % len(colors)]
                html += f'''
                <tr>
                    <td><strong>{cls}</strong></td>
                    <td>{count:,}</td>
                    <td>{pct:.1f}%</td>
                    <td>
                        <div class="bar-container">
                            <div class="bar {color}" style="width: {pct}%">{pct:.1f}%</div>
                        </div>
                    </td>
                </tr>
                '''
            html += '</table>'
            
            # Class balance warning
            imbalance = class_counts.max() / class_counts.min()
            if imbalance > 3:
                html += f'<div class="warning-box danger">⚠️ <strong>Class Imbalance Detected:</strong> Ratio is {imbalance:.1f}:1. Consider using stratified sampling or class weights.</div>'
            elif imbalance > 1.5:
                html += f'<div class="warning-box">⚠️ <strong>Slight Class Imbalance:</strong> Ratio is {imbalance:.1f}:1.</div>'
            else:
                html += '<div class="warning-box info">✓ Classes are reasonably balanced.</div>'
        
        else:  # Regression
            stats = self.target.describe()
            html += f'''
            <div class="grid-2">
                <div>
                    <h3>Statistics</h3>
                    <table>
                        <tr><td>Mean</td><td><strong>{stats["mean"]:.4f}</strong></td></tr>
                        <tr><td>Std Dev</td><td>{stats["std"]:.4f}</td></tr>
                        <tr><td>Min</td><td>{stats["min"]:.4f}</td></tr>
                        <tr><td>25%</td><td>{stats["25%"]:.4f}</td></tr>
                        <tr><td>Median</td><td>{stats["50%"]:.4f}</td></tr>
                        <tr><td>75%</td><td>{stats["75%"]:.4f}</td></tr>
                        <tr><td>Max</td><td>{stats["max"]:.4f}</td></tr>
                    </table>
                </div>
                <div>
                    <h3>Distribution Shape</h3>
                    {self._generate_histogram(self.target)}
                </div>
            </div>
            '''
            
            # Skewness check
            skew = self.target.skew()
            if abs(skew) > 1:
                html += f'<div class="warning-box">⚠️ <strong>High Skewness ({skew:.2f}):</strong> Consider log transformation for better model performance.</div>'
        
        html += '</div>'
        return html
    
    def _generate_histogram(self, series: pd.Series, bins: int = 20) -> str:
        """Generate a CSS-only histogram"""
        counts, edges = np.histogram(series.dropna(), bins=bins)
        max_count = max(counts) if max(counts) > 0 else 1
        
        html = '<div class="mini-chart">'
        for count in counts:
            height = int((count / max_count) * 40)
            html += f'<div class="mini-bar" style="height: {max(height, 2)}px;"></div>'
        html += '</div>'
        return html
    
    def _generate_warnings(self) -> str:
        """Generate warnings section"""
        if not self.warnings and not self.excluded_columns:
            return ''
        
        html = '<div class="card"><h2>⚠️ Preprocessing Notes</h2>'
        
        if self.excluded_columns:
            html += '<h3>Columns to be Excluded from Training</h3>'
            html += '<table><tr><th>Column</th><th>Reason</th></tr>'
            for col, reason in self.excluded_columns:
                html += f'<tr><td><code>{col}</code> <span class="badge excluded">EXCLUDED</span></td><td>{reason}</td></tr>'
            html += '</table>'
        
        if self.warnings:
            html += '<h3>Warnings</h3>'
            for warning in self.warnings:
                html += f'<div class="warning-box">{warning}</div>'
        
        html += '</div>'
        return html
    
    def _generate_column_info(self) -> str:
        """Generate column information table"""
        html = '<div class="card"><h2>📋 Column Details</h2>'
        html += '<table><tr><th>Column</th><th>Type</th><th>Missing</th><th>Unique</th><th>Sample Values</th></tr>'
        
        for col in self.df.columns:
            series = self.df[col]
            dtype = str(series.dtype)
            missing_pct = series.isnull().sum() / len(series) * 100
            unique = series.nunique()
            
            # Type badge
            if pd.api.types.is_numeric_dtype(series):
                type_badge = '<span class="badge numeric">numeric</span>'
            else:
                type_badge = '<span class="badge categorical">categorical</span>'
            
            # Sample values
            sample = series.dropna().head(3).tolist()
            sample_str = ', '.join([str(s)[:20] for s in sample])
            
            # Missing indicator
            missing_class = 'style="color: #dc3545; font-weight: bold;"' if missing_pct > 5 else ''
            
            # Excluded indicator
            excluded = any(col == ex[0] for ex in self.excluded_columns)
            excluded_badge = ' <span class="badge excluded">EXCLUDED</span>' if excluded else ''
            
            html += f'''
            <tr>
                <td><code>{col}</code>{excluded_badge}</td>
                <td>{type_badge}</td>
                <td {missing_class}>{missing_pct:.1f}%</td>
                <td>{unique:,}</td>
                <td style="font-size: 0.85em; color: #666;">{sample_str}...</td>
            </tr>
            '''
        
        html += '</table></div>'
        return html
    
    def _generate_correlations(self) -> str:
        """Generate correlation analysis for numeric columns"""
        numeric_df = self.df.select_dtypes(include=[np.number])
        
        if len(numeric_df.columns) < 2:
            return ''
        
        # Correlation with target (if target is numeric)
        html = '<div class="card"><h2>📈 Correlation Analysis</h2>'
        
        if self.target_column in numeric_df.columns:
            correlations = numeric_df.corr()[self.target_column].drop(self.target_column).sort_values(key=abs, ascending=False)
            
            html += '<h3>Correlation with Target</h3>'
            html += '<table><tr><th>Feature</th><th>Correlation</th><th>Strength</th></tr>'
            
            for feat, corr in correlations.head(10).items():
                # Color based on correlation
                if corr > 0.5:
                    css_class = 'corr-high-pos'
                    strength = 'Strong Positive'
                elif corr > 0.3:
                    css_class = 'corr-med-pos'
                    strength = 'Moderate Positive'
                elif corr < -0.5:
                    css_class = 'corr-high-neg'
                    strength = 'Strong Negative'
                elif corr < -0.3:
                    css_class = 'corr-med-neg'
                    strength = 'Moderate Negative'
                else:
                    css_class = 'corr-low'
                    strength = 'Weak'
                
                html += f'''
                <tr>
                    <td><code>{feat}</code></td>
                    <td class="correlation-cell {css_class}">{corr:.3f}</td>
                    <td>{strength}</td>
                </tr>
                '''
            
            html += '</table>'
        
        html += '</div>'
        return html
    
    def _generate_categorical_summary(self) -> str:
        """Generate summary of categorical columns"""
        cat_cols = self.df.select_dtypes(include=['object', 'category']).columns
        
        if len(cat_cols) == 0:
            return ''
        
        html = '<div class="card"><h2>🏷️ Categorical Features Summary</h2>'
        
        for col in cat_cols[:10]:  # Limit to first 10
            series = self.df[col]
            value_counts = series.value_counts().head(5)
            total = len(series)
            
            html += f'<h3><code>{col}</code> <span style="font-weight: normal; color: #666;">({series.nunique()} unique)</span></h3>'
            html += '<div style="margin-bottom: 20px;">'
            
            colors = ['primary', 'success', 'warning', 'info', 'primary']
            for i, (val, count) in enumerate(value_counts.items()):
                pct = count / total * 100
                color = colors[i % len(colors)]
                html += f'''
                <div style="margin: 5px 0;">
                    <div style="display: flex; justify-content: space-between; font-size: 0.9em;">
                        <span>{str(val)[:30]}</span>
                        <span>{count:,} ({pct:.1f}%)</span>
                    </div>
                    <div class="bar-container">
                        <div class="bar {color}" style="width: {min(pct, 100)}%"></div>
                    </div>
                </div>
                '''
            
            if series.nunique() > 5:
                html += f'<p style="color: #666; font-size: 0.85em;">... and {series.nunique() - 5} more values</p>'
            
            html += '</div>'
        
        html += '</div>'
        return html
    
    def _generate_numeric_summary(self) -> str:
        """Generate summary statistics for numeric columns"""
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) == 0:
            return ''
        
        html = '<div class="card"><h2>🔢 Numeric Features Summary</h2>'
        html += '<table><tr><th>Feature</th><th>Mean</th><th>Std</th><th>Min</th><th>Median</th><th>Max</th><th>Distribution</th></tr>'
        
        for col in numeric_cols:
            if col == self.target_column:
                continue
            
            series = self.df[col]
            html += f'''
            <tr>
                <td><code>{col}</code></td>
                <td>{series.mean():.2f}</td>
                <td>{series.std():.2f}</td>
                <td>{series.min():.2f}</td>
                <td>{series.median():.2f}</td>
                <td>{series.max():.2f}</td>
                <td>{self._generate_histogram(series, bins=15)}</td>
            </tr>
            '''
        
        html += '</table></div>'
        return html
    
    def generate(self) -> str:
        """Generate complete HTML report"""
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>EDA Report - {self.target_column}</title>
            {self._get_css()}
        </head>
        <body>
            <div class="container">
                <h1>📊 Exploratory Data Analysis Report</h1>
                {self._generate_overview()}
                {self._generate_target_analysis()}
                {self._generate_warnings()}
                {self._generate_correlations()}
                {self._generate_column_info()}
                {self._generate_categorical_summary()}
                {self._generate_numeric_summary()}
                
                <div class="card" style="text-align: center; color: #666;">
                    <p>Generated by AWS AutoML Lite</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html


def generate_minimal_report(df: pd.DataFrame, target_column: str, output_path: str):
    """Minimal fallback report if main generator fails"""
    print("Generating minimal fallback report...")
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>EDA Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; }}
            th {{ background: #4CAF50; color: white; }}
        </style>
    </head>
    <body>
        <h1>EDA Report</h1>
        <p><strong>Rows:</strong> {df.shape[0]:,} | <strong>Columns:</strong> {df.shape[1]} | <strong>Target:</strong> {target_column}</p>
        <h2>Column Info</h2>
        <table>
            <tr><th>Column</th><th>Type</th><th>Missing %</th><th>Unique</th></tr>
            {''.join(f"<tr><td>{col}</td><td>{df[col].dtype}</td><td>{df[col].isnull().mean()*100:.1f}%</td><td>{df[col].nunique()}</td></tr>" for col in df.columns)}
        </table>
        <h2>Statistics</h2>
        {df.describe().to_html()}
    </body>
    </html>
    """
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Minimal report saved to: {output_path}")
