# AWS AutoML Lite - Resource Verification Script
# Verifies all deployed AWS resources are accessible and healthy

param(
    [switch]$Detailed = $false
)

Write-Host "`n🔍 AWS AutoML Lite - Resource Verification" -ForegroundColor Cyan
Write-Host ("="*70) -ForegroundColor Cyan

$ErrorCount = 0
$WarningCount = 0

# Function to test resource
function Test-Resource {
    param($Name, $Command, $ExpectedPattern = $null)
    
    Write-Host "`n📋 Checking $Name..." -ForegroundColor Yellow
    try {
        $result = Invoke-Expression $Command 2>&1
        if ($LASTEXITCODE -eq 0) {
            if ($ExpectedPattern -and $result -notmatch $ExpectedPattern) {
                Write-Host "  ⚠️  Found but unexpected result" -ForegroundColor Yellow
                $script:WarningCount++
                if ($Detailed) { Write-Host "  Output: $result" -ForegroundColor Gray }
            } else {
                Write-Host "  ✅ OK" -ForegroundColor Green
                if ($Detailed) { Write-Host "  Output: $result" -ForegroundColor Gray }
            }
        } else {
            Write-Host "  ❌ FAILED" -ForegroundColor Red
            Write-Host "  Error: $result" -ForegroundColor Red
            $script:ErrorCount++
        }
    } catch {
        Write-Host "  ❌ ERROR: $($_.Exception.Message)" -ForegroundColor Red
        $script:ErrorCount++
    }
}

# 1. API Gateway Health Check
Write-Host "`n🌐 API Gateway Tests" -ForegroundColor Magenta
Test-Resource "API Health Endpoint" `
    "curl -s https://sirpi54231.execute-api.us-east-1.amazonaws.com/dev/health" `
    "healthy"

Test-Resource "API Gateway Exists" `
    "aws apigateway get-rest-api --rest-api-id sirpi54231 --query 'name' --output text" `
    "automl-lite-dev-api"

# 2. Lambda Function
Write-Host "`n⚡ Lambda Function Tests" -ForegroundColor Magenta
Test-Resource "Lambda Function" `
    "aws lambda get-function --function-name automl-lite-dev-api --query 'Configuration.FunctionName' --output text" `
    "automl-lite-dev-api"

Test-Resource "Lambda Runtime" `
    "aws lambda get-function --function-name automl-lite-dev-api --query 'Configuration.Runtime' --output text" `
    "python3.11"

# 3. S3 Buckets
Write-Host "`n📦 S3 Bucket Tests" -ForegroundColor Magenta
Test-Resource "Datasets Bucket" `
    "aws s3 ls s3://automl-lite-dev-datasets-835503570883/"

Test-Resource "Models Bucket" `
    "aws s3 ls s3://automl-lite-dev-models-835503570883/"

Test-Resource "Reports Bucket" `
    "aws s3 ls s3://automl-lite-dev-reports-835503570883/"

Test-Resource "Terraform State Bucket" `
    "aws s3 ls s3://automl-lite-terraform-state-835503570883/"

# 4. DynamoDB Tables
Write-Host "`n🗄️  DynamoDB Table Tests" -ForegroundColor Magenta
Test-Resource "Datasets Table" `
    "aws dynamodb describe-table --table-name automl-lite-dev-datasets --query 'Table.TableStatus' --output text" `
    "ACTIVE"

Test-Resource "Training Jobs Table" `
    "aws dynamodb describe-table --table-name automl-lite-dev-training-jobs --query 'Table.TableStatus' --output text" `
    "ACTIVE"

Test-Resource "Terraform Locks Table" `
    "aws dynamodb describe-table --table-name automl-lite-terraform-locks --query 'Table.TableStatus' --output text" `
    "ACTIVE"

# 5. AWS Batch
Write-Host "`n🔄 AWS Batch Tests" -ForegroundColor Magenta
Test-Resource "Batch Compute Environment" `
    "aws batch describe-compute-environments --compute-environments automl-lite-dev-compute --query 'computeEnvironments[0].status' --output text" `
    "VALID"

Test-Resource "Batch Job Queue" `
    "aws batch describe-job-queues --job-queues automl-lite-dev-training-queue --query 'jobQueues[0].state' --output text" `
    "ENABLED"

Test-Resource "Batch Job Definition" `
    "aws batch describe-job-definitions --job-definition-name automl-lite-dev-training-job --status ACTIVE --query 'jobDefinitions[0].status' --output text" `
    "ACTIVE"

# 6. ECR Repository
Write-Host "`n🐳 ECR Repository Tests" -ForegroundColor Magenta
Test-Resource "ECR Repository" `
    "aws ecr describe-repositories --repository-names automl-lite-training --query 'repositories[0].repositoryName' --output text" `
    "automl-lite-training"

$imageCount = aws ecr list-images --repository-name automl-lite-training --query 'length(imageIds)' --output text 2>$null
if ($imageCount -eq "0") {
    Write-Host "`n  ⚠️  No container images pushed yet" -ForegroundColor Yellow
    Write-Host "  Run: docker build and push to ECR" -ForegroundColor Gray
    $script:WarningCount++
} else {
    Write-Host "`n  ✅ $imageCount image(s) in repository" -ForegroundColor Green
}

# 7. CloudWatch Log Groups
Write-Host "`n📊 CloudWatch Log Groups Tests" -ForegroundColor Magenta
Test-Resource "Lambda Log Group" `
    "aws logs describe-log-groups --log-group-name-prefix /aws/lambda/automl-lite-dev-api --query 'logGroups[0].logGroupName' --output text" `
    "/aws/lambda/automl-lite-dev-api"

Test-Resource "Batch Log Group" `
    "aws logs describe-log-groups --log-group-name-prefix /aws/batch/automl-lite-dev-training --query 'logGroups[0].logGroupName' --output text" `
    "/aws/batch/automl-lite-dev-training"

Test-Resource "API Gateway Log Group" `
    "aws logs describe-log-groups --log-group-name-prefix /aws/apigateway/automl-lite-dev --query 'logGroups[0].logGroupName' --output text" `
    "/aws/apigateway/automl-lite-dev"

# 8. IAM Roles
Write-Host "`n🔐 IAM Role Tests" -ForegroundColor Magenta
Test-Resource "Lambda Execution Role" `
    "aws iam get-role --role-name automl-lite-dev-lambda-exec-role --query 'Role.RoleName' --output text" `
    "automl-lite-dev-lambda-exec-role"

Test-Resource "Batch Job Role" `
    "aws iam get-role --role-name automl-lite-dev-batch-job-role --query 'Role.RoleName' --output text" `
    "automl-lite-dev-batch-job-role"

# 9. Resource Tags
Write-Host "`n🏷️  Resource Tagging Tests" -ForegroundColor Magenta
$taggedResources = aws resourcegroupstaggingapi get-resources `
    --tag-filters Key=Project,Values=AWS-AutoML-Lite `
    --region us-east-1 `
    --query 'length(ResourceTagMappingList)' `
    --output text 2>$null

if ($taggedResources -gt 0) {
    Write-Host "  ✅ Found $taggedResources tagged resources" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  No tagged resources found (may be tagging delay)" -ForegroundColor Yellow
    $script:WarningCount++
}

# Summary
Write-Host "`n" + ("="*70) -ForegroundColor Cyan
Write-Host "📊 Verification Summary" -ForegroundColor Cyan
Write-Host ("="*70) -ForegroundColor Cyan

if ($ErrorCount -eq 0 -and $WarningCount -eq 0) {
    Write-Host "`n🎉 All resources verified successfully!" -ForegroundColor Green
    Write-Host "✅ Infrastructure is ready for use" -ForegroundColor Green
} elseif ($ErrorCount -eq 0) {
    Write-Host "`n⚠️  Verification completed with warnings: $WarningCount" -ForegroundColor Yellow
    Write-Host "Most resources are operational" -ForegroundColor Yellow
} else {
    Write-Host "`n❌ Verification failed!" -ForegroundColor Red
    Write-Host "Errors: $ErrorCount | Warnings: $WarningCount" -ForegroundColor Red
    Write-Host "Check the errors above and verify AWS credentials" -ForegroundColor Red
}

Write-Host "`n📚 Next Steps:" -ForegroundColor Cyan
if ($imageCount -eq "0") {
    Write-Host "  1. Build and push training container to ECR" -ForegroundColor Yellow
    Write-Host "     cd backend/training" -ForegroundColor Gray
    Write-Host "     docker build -t automl-training:latest ." -ForegroundColor Gray
    Write-Host "     # Login and push to ECR" -ForegroundColor Gray
}
Write-Host "  2. Test API endpoints" -ForegroundColor White
Write-Host "  3. Run end-to-end workflow test" -ForegroundColor White
Write-Host "  4. Configure frontend with API URL" -ForegroundColor White
Write-Host ""
