import os
import sys
import boto3
import pandas as pd
from datetime import datetime
from io import StringIO
import traceback

from preprocessor import AutoPreprocessor
from eda import generate_eda_report
from model_trainer import train_automl_model


def main():
    """Main training script executed by AWS Batch"""
    
    # Get environment variables
    dataset_id = os.getenv('DATASET_ID')
    target_column = os.getenv('TARGET_COLUMN')
    job_id = os.getenv('JOB_ID')
    time_budget = int(os.getenv('TIME_BUDGET', '300'))
    s3_bucket_datasets = os.getenv('S3_BUCKET_DATASETS')
    s3_bucket_models = os.getenv('S3_BUCKET_MODELS')
    s3_bucket_reports = os.getenv('S3_BUCKET_REPORTS')
    dynamodb_jobs_table = os.getenv('DYNAMODB_JOBS_TABLE')
    aws_region = os.getenv('REGION', 'us-east-1')
    
    print(f"Starting training job: {job_id}")
    print(f"Dataset ID: {dataset_id}")
    print(f"Target column: {target_column}")
    print(f"Time budget: {time_budget}s")
    
    # Initialize AWS clients
    s3_client = boto3.client('s3', region_name=aws_region)
    dynamodb = boto3.resource('dynamodb', region_name=aws_region)
    jobs_table = dynamodb.Table(dynamodb_jobs_table)
    
    try:
        # Update job status to RUNNING
        update_job_status(jobs_table, job_id, 'running')
        
        # Step 1: Download dataset from S3
        print("Step 1: Downloading dataset from S3...")
        dataset_key = f"datasets/{dataset_id}/"
        
        # List objects in the dataset folder
        response = s3_client.list_objects_v2(
            Bucket=s3_bucket_datasets,
            Prefix=dataset_key
        )
        
        if 'Contents' not in response or len(response['Contents']) == 0:
            raise Exception(f"No files found in {dataset_key}")
        
        # Get the first CSV file
        csv_file = [obj for obj in response['Contents'] if obj['Key'].endswith('.csv')][0]
        csv_key = csv_file['Key']
        
        print(f"Downloading: {csv_key}")
        csv_obj = s3_client.get_object(Bucket=s3_bucket_datasets, Key=csv_key)
        df = pd.read_csv(csv_obj['Body'])
        
        print(f"Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")
        
        # Step 2: Generate EDA report
        print("Step 2: Generating EDA report...")
        report_path = f"/tmp/eda_report_{job_id}.html"
        generate_eda_report(df, target_column, report_path)
        
        # Upload report to S3
        report_key = f"reports/{job_id}/eda_report.html"
        s3_client.upload_file(report_path, s3_bucket_reports, report_key)
        report_s3_path = f"s3://{s3_bucket_reports}/{report_key}"
        print(f"EDA report uploaded to: {report_s3_path}")
        
        # Step 3: Preprocess data
        print("Step 3: Preprocessing data...")
        preprocessor = AutoPreprocessor(target_column)
        X_train, X_test, y_train, y_test, problem_type = preprocessor.preprocess(df)
        
        print(f"Problem type detected: {problem_type}")
        print(f"Training set: {X_train.shape}")
        print(f"Test set: {X_test.shape}")
        
        # Step 4: Train model
        print("Step 4: Training model with FLAML...")
        model, metrics, feature_importance = train_automl_model(
            X_train, X_test, y_train, y_test,
            problem_type=problem_type,
            time_budget=time_budget
        )
        
        print(f"Training completed!")
        print(f"Metrics: {metrics}")
        
        # Step 5: Save model to S3
        print("Step 5: Saving model...")
        import joblib
        model_local_path = f"/tmp/model_{job_id}.pkl"
        joblib.dump({
            'model': model,
            'preprocessor': preprocessor,
            'feature_importance': feature_importance,
            'problem_type': problem_type
        }, model_local_path)
        
        model_key = f"models/{job_id}/model.pkl"
        s3_client.upload_file(model_local_path, s3_bucket_models, model_key)
        model_s3_path = f"s3://{s3_bucket_models}/{model_key}"
        print(f"Model uploaded to: {model_s3_path}")
        
        # Step 6: Update job status to COMPLETED
        print("Step 6: Updating job status...")
        update_job_completion(
            jobs_table, job_id, 
            problem_type, model_s3_path, report_s3_path,
            metrics, feature_importance
        )
        
        print(f"Training job {job_id} completed successfully!")
        
    except Exception as e:
        error_msg = f"Training failed: {str(e)}"
        print(error_msg, file=sys.stderr)
        traceback.print_exc()
        
        # Update job status to FAILED
        update_job_status(
            jobs_table, job_id, 'failed',
            error_message=error_msg
        )
        sys.exit(1)


def update_job_status(table, job_id, status, error_message=None):
    """Update job status in DynamoDB"""
    now = datetime.utcnow().isoformat()
    update_expr = "SET #status = :status, updated_at = :updated_at"
    expr_attr_names = {'#status': 'status'}
    expr_attr_values = {
        ':status': status,
        ':updated_at': now
    }
    
    # Add started_at when job starts running
    if status == 'running':
        update_expr += ", started_at = :started_at"
        expr_attr_values[':started_at'] = now
    
    # Add completed_at when job finishes
    if status in ('completed', 'failed'):
        update_expr += ", completed_at = :completed_at"
        expr_attr_values[':completed_at'] = now
    
    if error_message:
        update_expr += ", error_message = :error_message"
        expr_attr_values[':error_message'] = error_message
    
    table.update_item(
        Key={'job_id': job_id},
        UpdateExpression=update_expr,
        ExpressionAttributeNames=expr_attr_names,
        ExpressionAttributeValues=expr_attr_values
    )


def update_job_completion(table, job_id, problem_type, model_path, report_path, metrics, feature_importance):
    """Update job with completion details"""
    from decimal import Decimal
    
    # Convert floats to Decimal for DynamoDB
    metrics_decimal = {k: Decimal(str(v)) if v is not None else None 
                      for k, v in metrics.items()}
    feature_importance_decimal = {k: Decimal(str(v)) 
                                  for k, v in feature_importance.items()}
    
    table.update_item(
        Key={'job_id': job_id},
        UpdateExpression="""
            SET #status = :status,
                updated_at = :updated_at,
                problem_type = :problem_type,
                model_path = :model_path,
                report_path = :report_path,
                metrics = :metrics,
                feature_importance = :feature_importance
        """,
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={
            ':status': 'completed',
            ':updated_at': datetime.utcnow().isoformat(),
            ':problem_type': problem_type,
            ':model_path': model_path,
            ':report_path': report_path,
            ':metrics': metrics_decimal,
            ':feature_importance': feature_importance_decimal
        }
    )


if __name__ == "__main__":
    main()
