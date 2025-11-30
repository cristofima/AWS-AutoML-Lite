# Setup Terraform S3 Backend with DynamoDB State Locking
# This script creates the necessary AWS resources for Terraform remote state management

param(
    [string]$Region = "us-east-1",
    [string]$AccountId = ""
)

Write-Host "🚀 Setting up Terraform S3 Backend..." -ForegroundColor Cyan

# Get AWS Account ID if not provided
if ([string]::IsNullOrEmpty($AccountId)) {
    Write-Host "Getting AWS Account ID..." -ForegroundColor Yellow
    $AccountId = (aws sts get-caller-identity --query Account --output text)
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to get AWS Account ID. Make sure AWS CLI is configured." -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Account ID: $AccountId" -ForegroundColor Green
}

$BucketName = "automl-lite-terraform-state-$AccountId"
$TableName = "automl-lite-terraform-locks"

# Step 1: Create S3 bucket for state
Write-Host "`n📦 Creating S3 bucket: $BucketName" -ForegroundColor Yellow
aws s3api create-bucket --bucket $BucketName --region $Region 2>$null

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Bucket created successfully" -ForegroundColor Green
} else {
    Write-Host "⚠️  Bucket might already exist, continuing..." -ForegroundColor Yellow
}

# Step 2: Enable versioning on the bucket
Write-Host "`n🔄 Enabling versioning on bucket..." -ForegroundColor Yellow
aws s3api put-bucket-versioning `
    --bucket $BucketName `
    --versioning-configuration Status=Enabled `
    --region $Region

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Versioning enabled" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to enable versioning" -ForegroundColor Red
}

# Step 3: Enable encryption
Write-Host "`n🔒 Enabling server-side encryption..." -ForegroundColor Yellow
aws s3api put-bucket-encryption `
    --bucket $BucketName `
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            },
            "BucketKeyEnabled": true
        }]
    }' `
    --region $Region

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Encryption enabled" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to enable encryption" -ForegroundColor Red
}

# Step 4: Block public access
Write-Host "`n🚫 Blocking public access..." -ForegroundColor Yellow
aws s3api put-public-access-block `
    --bucket $BucketName `
    --public-access-block-configuration '{
        "BlockPublicAcls": true,
        "IgnorePublicAcls": true,
        "BlockPublicPolicy": true,
        "RestrictPublicBuckets": true
    }' `
    --region $Region

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Public access blocked" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to block public access" -ForegroundColor Red
}

# Step 5: Add lifecycle policy (optional - keep last 30 state versions)
Write-Host "`n♻️  Adding lifecycle policy..." -ForegroundColor Yellow
aws s3api put-bucket-lifecycle-configuration `
    --bucket $BucketName `
    --lifecycle-configuration '{
        "Rules": [{
            "Id": "DeleteOldVersions",
            "Status": "Enabled",
            "NoncurrentVersionExpiration": {
                "NoncurrentDays": 30
            }
        }]
    }' `
    --region $Region

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Lifecycle policy added" -ForegroundColor Green
} else {
    Write-Host "⚠️  Failed to add lifecycle policy" -ForegroundColor Yellow
}

# Step 6: Create DynamoDB table for state locking
Write-Host "`n🔐 Creating DynamoDB table: $TableName" -ForegroundColor Yellow
aws dynamodb create-table `
    --table-name $TableName `
    --attribute-definitions AttributeName=LockID,AttributeType=S `
    --key-schema AttributeName=LockID,KeyType=HASH `
    --billing-mode PAY_PER_REQUEST `
    --region $Region `
    --tags Key=Project,Value=AWS-AutoML-Lite Key=ManagedBy,Value=Terraform Key=Purpose,Value=StateLocking 2>$null

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ DynamoDB table created successfully" -ForegroundColor Green
    Write-Host "⏳ Waiting for table to become active..." -ForegroundColor Yellow
    aws dynamodb wait table-exists --table-name $TableName --region $Region
    Write-Host "✅ Table is active" -ForegroundColor Green
} else {
    Write-Host "⚠️  Table might already exist, continuing..." -ForegroundColor Yellow
}

# Step 7: Enable point-in-time recovery for DynamoDB
Write-Host "`n🔄 Enabling point-in-time recovery for DynamoDB..." -ForegroundColor Yellow
aws dynamodb update-continuous-backups `
    --table-name $TableName `
    --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true `
    --region $Region

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Point-in-time recovery enabled" -ForegroundColor Green
} else {
    Write-Host "⚠️  Failed to enable point-in-time recovery" -ForegroundColor Yellow
}

# Summary
Write-Host "`n" + ("="*70) -ForegroundColor Cyan
Write-Host "✅ TERRAFORM BACKEND SETUP COMPLETE" -ForegroundColor Green
Write-Host ("="*70) -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Configuration Summary:" -ForegroundColor Cyan
Write-Host "  • S3 Bucket: $BucketName" -ForegroundColor White
Write-Host "  • DynamoDB Table: $TableName" -ForegroundColor White
Write-Host "  • Region: $Region" -ForegroundColor White
Write-Host "  • Encryption: AES256 (enabled)" -ForegroundColor White
Write-Host "  • Versioning: Enabled" -ForegroundColor White
Write-Host "  • State Locking: Enabled" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Update main.tf backend configuration if needed" -ForegroundColor White
Write-Host "  2. Run: terraform init -reconfigure" -ForegroundColor White
Write-Host "  3. Migrate existing state (if any): terraform init -migrate-state" -ForegroundColor White
Write-Host ""
Write-Host "📚 Backend Configuration in main.tf:" -ForegroundColor Cyan
Write-Host "  backend `"s3`" {" -ForegroundColor Gray
Write-Host "    bucket         = `"$BucketName`"" -ForegroundColor Gray
Write-Host "    key            = `"automl-lite/terraform.tfstate`"" -ForegroundColor Gray
Write-Host "    region         = `"$Region`"" -ForegroundColor Gray
Write-Host "    encrypt        = true" -ForegroundColor Gray
Write-Host "    dynamodb_table = `"$TableName`"" -ForegroundColor Gray
Write-Host "  }" -ForegroundColor Gray
Write-Host ""
