"""
Training Results Report Generator.

This module generates HTML reports after model training with metrics,
feature importance, configuration details, and preprocessing information.
"""

from typing import Dict, Any
from datetime import datetime, timezone


def generate_training_report(
    output_path: str,
    job_id: str,
    problem_type: str,
    metrics: Dict[str, Any],
    feature_importance: Dict[str, float],
    training_config: Dict[str, Any],
    preprocessing_info: Dict[str, Any],
    dataset_info: Dict[str, Any]
) -> None:
    """
    Generate training results report after model training.
    
    Args:
        output_path: Path to save the HTML report
        job_id: Training job ID
        problem_type: 'classification' or 'regression'
        metrics: Dictionary of evaluation metrics
        feature_importance: Dictionary of feature importance
        training_config: Training configuration (time_budget, etc.)
        preprocessing_info: Info about preprocessing (dropped columns, etc.)
        dataset_info: Basic dataset info (rows, columns, target)
    """
    print("Generating training report...")
    
    try:
        report = TrainingReportGenerator(
            job_id=job_id,
            problem_type=problem_type,
            metrics=metrics,
            feature_importance=feature_importance,
            training_config=training_config,
            preprocessing_info=preprocessing_info,
            dataset_info=dataset_info
        )
        html = report.generate()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"Training report saved to: {output_path}")
        
    except Exception as e:
        print(f"Error generating training report: {str(e)}")
        generate_minimal_training_report(output_path, job_id, metrics, problem_type)


class TrainingReportGenerator:
    """Generate training results report with CSS-only visualizations"""
    
    def __init__(
        self,
        job_id: str,
        problem_type: str,
        metrics: Dict[str, Any],
        feature_importance: Dict[str, float],
        training_config: Dict[str, Any],
        preprocessing_info: Dict[str, Any],
        dataset_info: Dict[str, Any]
    ) -> None:
        self.job_id = job_id
        self.problem_type = problem_type
        self.metrics = metrics
        self.feature_importance = feature_importance
        self.training_config = training_config
        self.preprocessing_info = preprocessing_info
        self.dataset_info = dataset_info
    
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
            
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
            .grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }
            .grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; }
            
            .stat-box {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white; padding: 20px; border-radius: 8px; text-align: center;
            }
            .stat-box.green { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }
            .stat-box.orange { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
            .stat-box.blue { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
            .stat-box.gold { background: linear-gradient(135deg, #f7971e 0%, #ffd200 100%); }
            .stat-number { font-size: 2em; font-weight: bold; }
            .stat-label { font-size: 0.85em; opacity: 0.9; margin-top: 5px; }
            
            .metric-card {
                background: #f8f9fa; border-radius: 8px; padding: 15px;
                text-align: center; border: 1px solid #e9ecef;
            }
            .metric-value { font-size: 1.8em; font-weight: bold; color: #1a73e8; }
            .metric-label { font-size: 0.85em; color: #666; margin-top: 5px; }
            .metric-card.success .metric-value { color: #28a745; }
            .metric-card.warning .metric-value { color: #ffc107; }
            .metric-card.danger .metric-value { color: #dc3545; }
            
            table { width: 100%; border-collapse: collapse; margin: 10px 0; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
            th { background: #f8f9fa; font-weight: 600; color: #555; }
            tr:hover { background: #f8f9fa; }
            
            .bar-container { 
                background: #e9ecef; border-radius: 4px; height: 24px; 
                overflow: hidden; margin: 3px 0;
            }
            .bar { 
                height: 100%; border-radius: 4px; 
                display: flex; align-items: center; padding-left: 8px;
                font-size: 12px; color: white; font-weight: 500;
                transition: width 0.3s ease;
            }
            .bar.primary { background: linear-gradient(90deg, #667eea, #764ba2); }
            .bar.success { background: linear-gradient(90deg, #11998e, #38ef7d); }
            .bar.warning { background: linear-gradient(90deg, #f7971e, #ffd200); }
            .bar.info { background: linear-gradient(90deg, #4facfe, #00f2fe); }
            
            .info-box {
                background: #e3f2fd; border-left: 4px solid #1a73e8;
                padding: 15px; margin: 10px 0; border-radius: 0 8px 8px 0;
            }
            .success-box {
                background: #d4edda; border-left: 4px solid #28a745;
                padding: 15px; margin: 10px 0; border-radius: 0 8px 8px 0;
            }
            
            .badge {
                display: inline-block; padding: 4px 10px; border-radius: 12px;
                font-size: 0.8em; font-weight: 600;
            }
            .badge.classification { background: #e3f2fd; color: #1565c0; }
            .badge.regression { background: #f3e5f5; color: #7b1fa2; }
            .badge.model { background: #fff3e0; color: #e65100; }
            .badge.time { background: #e8f5e9; color: #2e7d32; }
            
            .feature-bar {
                display: flex; align-items: center; margin: 8px 0;
            }
            .feature-name {
                width: 200px; font-size: 0.9em; color: #333;
                white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
            }
            .feature-bar-container {
                flex: 1; margin-left: 10px;
            }
            .feature-value {
                width: 60px; text-align: right; font-size: 0.85em; color: #666;
                margin-left: 10px;
            }
            
            .config-table td:first-child { font-weight: 500; width: 40%; }
            .config-table td:last-child { color: #666; }
            
            @media (max-width: 768px) {
                .grid-2, .grid-3 { grid-template-columns: 1fr; }
                .feature-name { width: 120px; }
            }
        </style>
        """
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds into human-readable time"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    def _generate_header(self) -> str:
        """Generate report header"""
        training_time = self.metrics.get('training_time', 0)
        best_estimator = self.metrics.get('best_estimator', 'Unknown')
        
        return f"""
        <div class="card">
            <h2>🏆 Training Summary</h2>
            <div class="grid">
                <div class="stat-box green">
                    <div class="stat-number">✓</div>
                    <div class="stat-label">Training Completed</div>
                </div>
                <div class="stat-box blue">
                    <div class="stat-number">{self._format_time(training_time)}</div>
                    <div class="stat-label">Training Time</div>
                </div>
                <div class="stat-box orange">
                    <div class="stat-number" style="font-size: 1.2em;">{best_estimator}</div>
                    <div class="stat-label">Best Model</div>
                </div>
                <div class="stat-box gold">
                    <div class="stat-number">{self.preprocessing_info.get('feature_count', 'N/A')}</div>
                    <div class="stat-label">Features Used</div>
                </div>
            </div>
            <div style="margin-top: 20px;">
                <p><strong>Job ID:</strong> <code>{self.job_id}</code></p>
                <p><strong>Problem Type:</strong> <span class="badge {self.problem_type}">{self.problem_type.upper()}</span></p>
                <p><strong>Target Column:</strong> <code>{self.dataset_info.get('target_column', 'N/A')}</code></p>
            </div>
        </div>
        """
    
    def _generate_metrics(self) -> str:
        """Generate metrics section"""
        html = '<div class="card"><h2>📊 Model Performance Metrics</h2>'
        
        if self.problem_type == 'classification':
            metrics_to_show = [
                ('accuracy', 'Accuracy', 'success'),
                ('f1_score', 'F1 Score', 'success'),
                ('precision', 'Precision', 'info'),
                ('recall', 'Recall', 'info'),
            ]
        else:
            metrics_to_show = [
                ('r2_score', 'R² Score', 'success'),
                ('rmse', 'RMSE', 'warning'),
                ('mae', 'MAE', 'warning'),
            ]
        
        html += '<div class="grid">'
        for key, label, card_class in metrics_to_show:
            value = self.metrics.get(key, 0)
            if value is not None:
                if isinstance(value, (int, float)):
                    # Format based on metric type
                    if key in ['accuracy', 'f1_score', 'precision', 'recall', 'r2_score']:
                        formatted = f"{value:.2%}" if value <= 1 else f"{value:.4f}"
                    else:
                        formatted = f"{value:.4f}"
                else:
                    formatted = str(value)
            else:
                formatted = "N/A"
            
            html += f'''
            <div class="metric-card {card_class}">
                <div class="metric-value">{formatted}</div>
                <div class="metric-label">{label}</div>
            </div>
            '''
        html += '</div>'
        
        # Add interpretation
        if self.problem_type == 'classification':
            accuracy = self.metrics.get('accuracy', 0)
            if accuracy >= 0.9:
                html += '<div class="success-box">✓ <strong>Excellent performance!</strong> The model achieves over 90% accuracy.</div>'
            elif accuracy >= 0.7:
                html += '<div class="info-box">ℹ️ <strong>Good performance.</strong> Consider feature engineering or more training time for improvement.</div>'
            else:
                html += '<div class="info-box">⚠️ <strong>Moderate performance.</strong> The model may benefit from more data or different features.</div>'
        else:
            r2 = self.metrics.get('r2_score', 0)
            if r2 >= 0.8:
                html += '<div class="success-box">✓ <strong>Excellent fit!</strong> The model explains over 80% of the variance.</div>'
            elif r2 >= 0.5:
                html += '<div class="info-box">ℹ️ <strong>Moderate fit.</strong> Consider adding more features or increasing training time.</div>'
        
        html += '</div>'
        return html
    
    def _generate_feature_importance(self) -> str:
        """Generate feature importance section"""
        if not self.feature_importance:
            return ''
        
        # Sort by importance and get top 15
        sorted_features = sorted(
            self.feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        )[:15]
        
        if not sorted_features:
            return ''
        
        max_importance = max(v for _, v in sorted_features) if sorted_features else 1
        
        html = '<div class="card"><h2>📈 Feature Importance</h2>'
        html += '<p style="color: #666; margin-bottom: 20px;">Top features that most influence the model predictions:</p>'
        
        colors = ['primary', 'success', 'warning', 'info']
        for i, (feature, importance) in enumerate(sorted_features):
            pct = (importance / max_importance) * 100 if max_importance > 0 else 0
            color = colors[i % len(colors)]
            
            html += f'''
            <div class="feature-bar">
                <div class="feature-name" title="{feature}">{feature}</div>
                <div class="feature-bar-container">
                    <div class="bar-container">
                        <div class="bar {color}" style="width: {pct}%"></div>
                    </div>
                </div>
                <div class="feature-value">{importance:.4f}</div>
            </div>
            '''
        
        html += '</div>'
        return html
    
    def _generate_preprocessing_info(self) -> str:
        """Generate preprocessing information section"""
        html = '<div class="card"><h2>⚙️ Preprocessing Details</h2>'
        
        html += '<div class="grid-2">'
        
        # Features used
        html += '<div>'
        html += '<h3>Features Used</h3>'
        feature_columns = self.preprocessing_info.get('feature_columns', [])
        if feature_columns:
            html += '<ul style="margin: 0; padding-left: 20px; color: #666;">'
            for col in feature_columns:
                html += f'<li><code>{col}</code></li>'
            html += '</ul>'
        else:
            html += '<p style="color: #666;">No information available</p>'
        html += '</div>'
        
        # Dropped columns
        html += '<div>'
        html += '<h3>Excluded Columns</h3>'
        dropped_columns = self.preprocessing_info.get('dropped_columns', [])
        if dropped_columns:
            html += '<ul style="margin: 0; padding-left: 20px; color: #888;">'
            for col in dropped_columns:
                html += f'<li><code style="text-decoration: line-through;">{col}</code></li>'
            html += '</ul>'
        else:
            html += '<p style="color: #28a745;">✓ No columns were excluded</p>'
        html += '</div>'
        
        html += '</div></div>'
        return html
    
    def _generate_config_info(self) -> str:
        """Generate training configuration section"""
        html = '<div class="card"><h2>🔧 Training Configuration</h2>'
        
        html += '<table class="config-table">'
        
        config_items = [
            ('Time Budget', f"{self.training_config.get('time_budget', 'N/A')} seconds"),
            ('Dataset Rows', f"{self.dataset_info.get('rows', 'N/A'):,}"),
            ('Dataset Columns', str(self.dataset_info.get('columns', 'N/A'))),
            ('Training Set Size', f"{self.dataset_info.get('train_size', 'N/A'):,}" if isinstance(self.dataset_info.get('train_size'), int) else 'N/A'),
            ('Test Set Size', f"{self.dataset_info.get('test_size', 'N/A'):,}" if isinstance(self.dataset_info.get('test_size'), int) else 'N/A'),
            ('Best Estimator', self.metrics.get('best_estimator', 'N/A')),
        ]
        
        for label, value in config_items:
            html += f'<tr><td>{label}</td><td>{value}</td></tr>'
        
        html += '</table></div>'
        return html
    
    def generate(self) -> str:
        """Generate complete HTML report"""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Training Report - {self.job_id}</title>
            {self._get_css()}
        </head>
        <body>
            <div class="container">
                <h1>🤖 Model Training Report</h1>
                {self._generate_header()}
                {self._generate_metrics()}
                {self._generate_feature_importance()}
                {self._generate_preprocessing_info()}
                {self._generate_config_info()}
                
                <div class="card" style="text-align: center; color: #666;">
                    <p>Generated by AWS AutoML Lite</p>
                    <p style="font-size: 0.85em;">{timestamp}</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html


def generate_minimal_training_report(
    output_path: str,
    job_id: str,
    metrics: Dict[str, Any],
    problem_type: str
):
    """Minimal fallback report if main generator fails"""
    print("Generating minimal training report...")
    
    metrics_html = ''.join(
        f"<tr><td>{k}</td><td>{v}</td></tr>" 
        for k, v in metrics.items() if v is not None
    )
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Training Report - {job_id}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; }}
            th {{ background: #4CAF50; color: white; }}
        </style>
    </head>
    <body>
        <h1>Training Report</h1>
        <p><strong>Job ID:</strong> {job_id}</p>
        <p><strong>Problem Type:</strong> {problem_type}</p>
        <h2>Metrics</h2>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            {metrics_html}
        </table>
    </body>
    </html>
    """
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Minimal training report saved to: {output_path}")
