// API Client for AWS AutoML Lite
// Centralized API calls to backend

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface UploadResponse {
  dataset_id: string;
  upload_url: string;
  expires_in: number;
}

export interface ColumnStats {
  unique: number;
  missing: number;
  missing_pct: number;
}

export interface DatasetMetadata {
  dataset_id: string;
  filename: string;
  file_size: number;
  uploaded_at: string;
  columns: string[];
  row_count: number;
  column_types: Record<string, string>;
  column_stats?: Record<string, ColumnStats>;
  problem_type?: 'classification' | 'regression';
}

export interface TrainRequest {
  dataset_id: string;
  target_column: string;
  config?: {
    time_budget?: number;
    estimator_list?: string[];
  };
}

export interface TrainResponse {
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  estimated_time: number;
}

export interface TrainingMetrics {
  accuracy?: number;
  f1_score?: number;
  precision?: number;
  recall?: number;
  r2_score?: number;
  rmse?: number;
  mae?: number;
  feature_importance?: Record<string, number>;
}

export interface JobDetails {
  job_id: string;
  dataset_id?: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  target_column?: string;
  problem_type?: 'classification' | 'regression';
  dataset_name?: string;
  created_at?: string;
  updated_at?: string;
  started_at?: string;
  completed_at?: string;
  metrics?: TrainingMetrics;
  model_download_url?: string;
  onnx_model_download_url?: string;
  report_download_url?: string;  // Backward compatibility (EDA report)
  eda_report_download_url?: string;
  training_report_download_url?: string;
  error_message?: string;
}

export interface JobListResponse {
  jobs: JobDetails[];
  next_token?: string;
}

// Health check
export async function checkHealth(): Promise<{ status: string; service: string }> {
  const response = await fetch(`${API_URL}/health`);
  if (!response.ok) throw new Error('Health check failed');
  return response.json();
}

// Request presigned URL for CSV upload
export async function requestUploadUrl(filename: string): Promise<UploadResponse> {
  const response = await fetch(`${API_URL}/upload`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filename }),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to request upload URL');
  }
  
  return response.json();
}

// Upload CSV file to presigned URL
export async function uploadFile(uploadUrl: string, file: File): Promise<void> {
  const response = await fetch(uploadUrl, {
    method: 'PUT',
    headers: { 'Content-Type': 'text/csv' },
    body: file,
  });
  
  if (!response.ok) {
    throw new Error('Failed to upload file to S3');
  }
}

// Confirm upload and analyze dataset
export async function confirmUpload(datasetId: string): Promise<DatasetMetadata> {
  const response = await fetch(`${API_URL}/datasets/${datasetId}/confirm`, {
    method: 'POST',
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to confirm upload');
  }
  
  return response.json();
}

// Start training job
export async function startTraining(request: TrainRequest): Promise<TrainResponse> {
  const response = await fetch(`${API_URL}/train`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to start training');
  }
  
  return response.json();
}

// Get job status and results
export async function getJobDetails(jobId: string): Promise<JobDetails> {
  const response = await fetch(`${API_URL}/jobs/${jobId}`);
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get job details');
  }
  
  return response.json();
}

// List all training jobs
export async function listJobs(limit = 10, nextToken?: string): Promise<JobListResponse> {
  const params = new URLSearchParams({ limit: limit.toString() });
  if (nextToken) params.append('next_token', nextToken);
  
  const response = await fetch(`${API_URL}/jobs?${params}`);
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to list jobs');
  }
  
  return response.json();
}

// Complete workflow: Upload + Confirm
export async function uploadAndConfirm(file: File): Promise<DatasetMetadata> {
  // Step 1: Request upload URL
  const { dataset_id, upload_url } = await requestUploadUrl(file.name);
  
  // Step 2: Upload file to S3
  await uploadFile(upload_url, file);
  
  // Step 3: Confirm and analyze
  const metadata = await confirmUpload(dataset_id);
  
  return metadata;
}

// Get dataset metadata
export async function getDatasetMetadata(datasetId: string): Promise<DatasetMetadata> {
  const response = await fetch(`${API_URL}/datasets/${datasetId}`);
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get dataset metadata');
  }
  
  return response.json();
}

// Delete a job and all associated data
export async function deleteJob(jobId: string, deleteData: boolean = true): Promise<{ message: string; job_id: string; deleted_resources: string[] }> {
  const response = await fetch(`${API_URL}/jobs/${jobId}?delete_data=${deleteData}`, {
    method: 'DELETE',
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to delete job');
  }
  
  return response.json();
}

// Download file with custom filename
export async function downloadWithFilename(url: string, filename: string): Promise<void> {
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error('Download failed');
    
    const blob = await response.blob();
    const blobUrl = window.URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    window.URL.revokeObjectURL(blobUrl);
  } catch (error) {
    // Fallback: open in new tab
    window.open(url, '_blank');
  }
}
