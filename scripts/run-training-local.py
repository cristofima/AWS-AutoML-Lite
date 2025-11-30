#!/usr/bin/env python3
"""
AutoML Training Local - Cross-platform (Windows/Linux/Mac)

Runs training in local Docker container (NOT AWS Batch).
Useful for development and testing.

Usage:
    python run-training-local.py <dataset-id> <target-column> [options]

Examples:
    python run-training-local.py abc123 Customer_Rating
    python run-training-local.py abc123 Customer_Rating --time-budget 120
    python run-training-local.py abc123 Customer_Rating --job-id my-test-job

Prerequisites:
    - Docker running
    - AWS CLI configured (for DynamoDB access)
    - .env file with AWS resource names
"""

import argparse
import json
import os
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def load_env_file(env_path: Path) -> dict:
    """Load environment variables from .env file."""
    env_vars = {}
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"').strip("'")
    return env_vars


def get_dataset_info(dataset_id: str, api_url: str) -> str:
    """Get dataset name from API."""
    try:
        url = f"{api_url}/datasets/{dataset_id}"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data.get('filename', dataset_id)
    except Exception:
        return dataset_id


def create_dynamodb_item(job_id: str, dataset_id: str, dataset_name: str, 
                         target_column: str, time_budget: int) -> dict:
    """Create DynamoDB item structure."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    
    return {
        "job_id": {"S": job_id},
        "dataset_id": {"S": dataset_id},
        "dataset_name": {"S": dataset_name},
        "target_column": {"S": target_column},
        "status": {"S": "pending"},
        "user_id": {"S": "default"},
        "created_at": {"S": now},
        "updated_at": {"S": now},
        "config": {
            "M": {
                "time_budget": {"N": str(time_budget)}
            }
        }
    }


def run_command(cmd: list, env: dict = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    
    return subprocess.run(cmd, env=full_env, check=check)


def main():
    parser = argparse.ArgumentParser(
        description='Run AutoML training in local Docker container',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run-training-local.py abc123 Customer_Rating
  python run-training-local.py abc123 Customer_Rating --time-budget 120
  python run-training-local.py abc123 Customer_Rating --job-id my-test-job
        """
    )
    
    parser.add_argument('dataset_id', help='Dataset ID to train on')
    parser.add_argument('target_column', help='Target column name for prediction')
    parser.add_argument('--job-id', '-j', 
                        default=f"local-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                        help='Job ID (default: auto-generated)')
    parser.add_argument('--time-budget', '-t', type=int, default=60,
                        help='Training time budget in seconds (default: 60)')
    parser.add_argument('--api-url', '-u', default='http://localhost:8000',
                        help='API URL for dataset info (default: http://localhost:8000)')
    parser.add_argument('--region', '-r', default='us-east-1',
                        help='AWS region (default: us-east-1)')
    
    args = parser.parse_args()
    
    # Find project root (where .env is)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    env_path = project_root / '.env'
    
    # Load environment variables
    env_vars = load_env_file(env_path)
    dynamo_table = env_vars.get('DYNAMODB_JOBS_TABLE') or os.environ.get('DYNAMODB_JOBS_TABLE')
    
    if not dynamo_table:
        print("❌ Error: DYNAMODB_JOBS_TABLE not set.")
        print(f"   Check .env file at: {env_path}")
        sys.exit(1)
    
    print("=" * 44)
    print("  AutoML Training - LOCAL Docker Test")
    print("=" * 44)
    print()
    print(f"📊 Dataset ID:    {args.dataset_id}")
    print(f"🎯 Target Column: {args.target_column}")
    print(f"📋 Job ID:        {args.job_id}")
    print(f"⏱️  Time Budget:   {args.time_budget}s")
    print(f"🗄️  DynamoDB:      {dynamo_table}")
    print()
    
    # Step 1: Get dataset info
    print("Step 1: Getting dataset info...")
    dataset_name = get_dataset_info(args.dataset_id, args.api_url)
    print(f"   Dataset: {dataset_name}")
    
    # Step 2: Create job record in DynamoDB
    print()
    print("Step 2: Creating job record in DynamoDB...")
    
    item = create_dynamodb_item(
        args.job_id, args.dataset_id, dataset_name,
        args.target_column, args.time_budget
    )
    item_json = json.dumps(item)
    
    try:
        result = subprocess.run(
            ['aws', 'dynamodb', 'put-item',
             '--table-name', dynamo_table,
             '--item', item_json,
             '--region', args.region],
            capture_output=True,
            text=True,
            check=True
        )
        print("   ✅ Job record created successfully")
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Error creating job record: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print("   ❌ Error: AWS CLI not found. Please install AWS CLI.")
        sys.exit(1)
    
    # Step 3: Run training container
    print()
    print("Step 3: Starting training container...")
    print()
    
    # Set environment variables for docker-compose
    container_env = {
        'DATASET_ID': args.dataset_id,
        'TARGET_COLUMN': args.target_column,
        'JOB_ID': args.job_id,
        'TIME_BUDGET': str(args.time_budget),
    }
    
    # Add all env vars from .env file
    container_env.update(env_vars)
    
    try:
        # Change to project root for docker-compose
        os.chdir(project_root)
        
        result = run_command(
            ['docker-compose', '--profile', 'training', 'run', '--rm', 'training'],
            env=container_env,
            check=False
        )
        
        if result.returncode == 0:
            print()
            print("=" * 44)
            print("  ✅ Training completed successfully!")
            print("=" * 44)
            print()
            print("View results:")
            print(f"  Frontend: http://localhost:3000/results/{args.job_id}")
            print(f"  API:      {args.api_url}/jobs/{args.job_id}")
        else:
            print()
            print("=" * 44)
            print("  ❌ Training failed!")
            print("=" * 44)
            print()
            print("Check the logs above for errors.")
            print("Job status in DynamoDB may show 'failed' with error message.")
            sys.exit(1)
            
    except FileNotFoundError:
        print("❌ Error: docker-compose not found. Please install Docker.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Training interrupted by user.")
        sys.exit(1)


if __name__ == '__main__':
    main()
