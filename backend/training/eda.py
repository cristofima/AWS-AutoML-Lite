import pandas as pd
import sweetviz as sv


def generate_eda_report(df: pd.DataFrame, target_column: str, output_path: str):
    """
    Generate automated EDA report using Sweetviz
    
    Args:
        df: Input dataframe
        target_column: Name of the target column
        output_path: Path to save the HTML report
    """
    try:
        print("Generating EDA report with Sweetviz...")
        
        # Create Sweetviz report
        report = sv.analyze(
            df,
            target_feat=target_column,
            pairwise_analysis='auto'
        )
        
        # Save report
        report.show_html(
            filepath=output_path,
            open_browser=False,
            layout='vertical'
        )
        
        print(f"EDA report saved to: {output_path}")
        
    except Exception as e:
        print(f"Error generating EDA report: {str(e)}")
        # Generate basic report as fallback
        generate_basic_report(df, target_column, output_path)


def generate_basic_report(df: pd.DataFrame, target_column: str, output_path: str):
    """
    Generate basic EDA report as fallback
    """
    print("Generating basic EDA report...")
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>EDA Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #333; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #4CAF50; color: white; }}
            .section {{ margin-top: 30px; }}
        </style>
    </head>
    <body>
        <h1>Exploratory Data Analysis Report</h1>
        
        <div class="section">
            <h2>Dataset Overview</h2>
            <p><strong>Rows:</strong> {df.shape[0]}</p>
            <p><strong>Columns:</strong> {df.shape[1]}</p>
            <p><strong>Target Column:</strong> {target_column}</p>
        </div>
        
        <div class="section">
            <h2>Column Information</h2>
            <table>
                <tr>
                    <th>Column</th>
                    <th>Type</th>
                    <th>Missing</th>
                    <th>Unique Values</th>
                </tr>
    """
    
    for col in df.columns:
        missing_pct = (df[col].isnull().sum() / len(df)) * 100
        unique_count = df[col].nunique()
        html += f"""
                <tr>
                    <td>{col}</td>
                    <td>{df[col].dtype}</td>
                    <td>{missing_pct:.2f}%</td>
                    <td>{unique_count}</td>
                </tr>
        """
    
    html += """
            </table>
        </div>
        
        <div class="section">
            <h2>Statistical Summary</h2>
            <pre>{}</pre>
        </div>
    </body>
    </html>
    """.format(df.describe().to_html())
    
    with open(output_path, 'w') as f:
        f.write(html)
    
    print(f"Basic EDA report saved to: {output_path}")
