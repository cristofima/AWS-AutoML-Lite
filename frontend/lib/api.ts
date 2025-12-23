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
  tags?: string[];  // Custom labels for filtering
  notes?: string;   // User notes for experiment tracking
  deployed?: boolean;  // Whether the model is deployed for inference
  preprocessing_info?: PreprocessingInfo;  // Feature info for inference
}

export interface JobUpdateRequest {
  tags?: string[];
  notes?: string;
}

export interface NumericStats {
  min: number;
  max: number;
  is_integer: boolean;
}

export interface PreprocessingInfo {
  feature_columns?: string[];
  feature_count?: number;
  dropped_columns?: string[];
  dropped_count?: number;
  feature_types?: Record<string, 'numeric' | 'categorical'>;
  categorical_mappings?: Record<string, Record<string, number>>;
  numeric_stats?: Record<string, NumericStats>;
  numeric_columns?: string[];
  categorical_columns?: string[];
  target_mapping?: Record<string, string>;  // encoded_value -> original_label
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

// Update job metadata (tags and notes)
export async function updateJobMetadata(jobId: string, updates: JobUpdateRequest): Promise<JobDetails> {
  const response = await fetch(`${API_URL}/jobs/${jobId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to update job metadata');
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

// Deploy/Undeploy interfaces
export interface DeployResponse {
  job_id: string;
  deployed: boolean;
  message: string;
}

// Prediction interfaces
export interface PredictionInput {
  features: Record<string, number | string>;
}

export interface PredictionResponse {
  job_id: string;
  prediction: number | string;
  probability?: number;
  probabilities?: Record<string, number>;
  inference_time_ms: number;
  model_type: string;
}

export interface FeatureInfo {
  type: 'numeric' | 'categorical';
  input_type: 'number' | 'select';
  allowed_values?: string[];
}

export interface PredictionInfo {
  job_id: string;
  problem_type: 'classification' | 'regression';
  target_column: string;
  dataset_name: string;
  feature_columns: string[];
  feature_count: number;
  feature_info: Record<string, FeatureInfo>;
  model_type: string;
  deployed: boolean;
  example_request: {
    features: Record<string, string | number>;
  };
}

// Deploy or undeploy a model
export async function deployModel(jobId: string, deploy: boolean): Promise<DeployResponse> {
  const response = await fetch(`${API_URL}/jobs/${jobId}/deploy`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ deploy }),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to deploy model');
  }
  
  return response.json();
}

// Make a prediction with a deployed model
export async function makePrediction(jobId: string, features: Record<string, number | string>): Promise<PredictionResponse> {
  const response = await fetch(`${API_URL}/predict/${jobId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ features }),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Prediction failed');
  }
  
  return response.json();
}

// Get prediction info for a deployed model
export async function getPredictionInfo(jobId: string): Promise<PredictionInfo> {
  const response = await fetch(`${API_URL}/predict/${jobId}/info`);
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get prediction info');
  }
  
  return response.json();
}
