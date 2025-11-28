// Utility functions for the frontend

export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

export function formatDuration(startDate: string, endDate: string): string {
  const start = new Date(startDate).getTime();
  const end = new Date(endDate).getTime();
  const duration = Math.floor((end - start) / 1000); // seconds
  
  if (duration < 60) return `${duration}s`;
  if (duration < 3600) return `${Math.floor(duration / 60)}m ${duration % 60}s`;
  return `${Math.floor(duration / 3600)}h ${Math.floor((duration % 3600) / 60)}m`;
}

export function getStatusColor(status: string): string {
  switch (status) {
    case 'completed':
      return 'text-green-600 bg-green-50';
    case 'running':
      return 'text-blue-600 bg-blue-50';
    case 'pending':
      return 'text-yellow-600 bg-yellow-50';
    case 'failed':
      return 'text-red-600 bg-red-50';
    default:
      return 'text-gray-600 bg-gray-50';
  }
}

export function getStatusIcon(status: string): string {
  switch (status) {
    case 'completed':
      return '✓';
    case 'running':
      return '⟳';
    case 'pending':
      return '○';
    case 'failed':
      return '✗';
    default:
      return '?';
  }
}

export function validateCSV(file: File): { valid: boolean; error?: string } {
  // Check file type
  if (!file.name.toLowerCase().endsWith('.csv')) {
    return { valid: false, error: 'File must be a CSV file' };
  }
  
  // Check file size (max 100MB)
  const maxSize = 100 * 1024 * 1024; // 100MB
  if (file.size > maxSize) {
    return { valid: false, error: 'File size must be less than 100MB' };
  }
  
  return { valid: true };
}

export function formatMetric(value: number, decimals = 4): string {
  return value.toFixed(decimals);
}

export function getProblemTypeIcon(problemType: string): string {
  return problemType === 'classification' ? '📊' : '📈';
}

export function getProblemTypeDescription(problemType: string): string {
  return problemType === 'classification' 
    ? 'Predicting categories or classes'
    : 'Predicting continuous numerical values';
}
