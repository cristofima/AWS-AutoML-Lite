'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { getJobDetails, JobDetails } from '@/lib/api';
import { getStatusColor, getStatusIcon, formatDuration, formatDateTime } from '@/lib/utils';

export default function TrainingPage() {
  const router = useRouter();
  const params = useParams();
  const jobId = params.jobId as string;

  const [job, setJob] = useState<JobDetails | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Redirect to results when job completes
  useEffect(() => {
    if (job?.status === 'completed') {
      router.push(`/results/${jobId}`);
    }
  }, [job?.status, jobId, router]);

  useEffect(() => {
    const fetchJobStatus = async () => {
      try {
        const jobData = await getJobDetails(jobId);
        setJob(jobData);
        setIsLoading(false);

        // If job is still running or pending, poll every 5 seconds
        if (jobData.status === 'running' || jobData.status === 'pending') {
          const interval = setInterval(async () => {
            const updated = await getJobDetails(jobId);
            setJob(updated);

            // Stop polling if completed or failed
            if (updated.status === 'completed' || updated.status === 'failed') {
              clearInterval(interval);
            }
          }, 5000);

          return () => clearInterval(interval);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load job status');
        setIsLoading(false);
      }
    };

    fetchJobStatus();
  }, [jobId]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading training status...</p>
        </div>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md">
          <div className="text-red-500 text-5xl mb-4">⚠️</div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Error</h2>
          <p className="text-gray-600 mb-4">{error || 'Job not found'}</p>
          <button
            onClick={() => router.push('/')}
            className="w-full py-2 px-4 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            Go Home
          </button>
        </div>
      </div>
    );
  }

  // Show loading while redirecting to results
  if (job?.status === 'completed') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-5xl mb-4">✅</div>
          <p className="text-gray-600">Training complete! Redirecting to results...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <h1 className="text-2xl font-bold text-gray-900">Training in Progress</h1>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow-lg p-8">
          {/* Status */}
          <div className="text-center mb-8">
            <div className="text-6xl mb-4">
              {job.status === 'running' ? '⚙️' : '⏳'}
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              {job.status === 'running' ? 'Training Model...' : 'Preparing Training...'}
            </h2>
            <div className={`inline-block px-4 py-2 rounded-full text-sm font-medium ${getStatusColor(job.status)}`}>
              {getStatusIcon(job.status)} {job.status.charAt(0).toUpperCase() + job.status.slice(1)}
            </div>
          </div>

          {/* Progress Animation */}
          <div className="mb-8">
            <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
              <div className="bg-indigo-600 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
            </div>
            <p className="text-sm text-gray-600 text-center mt-2">
              This may take a few minutes depending on dataset size and time budget
            </p>
          </div>

          {/* Job Info */}
          <div className="bg-gray-50 rounded-lg p-6 space-y-4">
            <h3 className="font-semibold text-gray-900 mb-4">Training Details</h3>
            
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Job ID:</span>
                <p className="font-mono text-gray-900 text-xs mt-1">{job.job_id}</p>
              </div>
              <div>
                <span className="text-gray-600">Dataset:</span>
                <p className="font-mono text-gray-900 text-xs mt-1">{job.dataset_name || job.dataset_id || 'Loading...'}</p>
              </div>
              <div>
                <span className="text-gray-600">Target Column:</span>
                <p className="font-medium text-gray-900 mt-1">{job.target_column || 'Loading...'}</p>
              </div>
              <div>
                <span className="text-gray-600">Problem Type:</span>
                <p className="font-medium text-gray-900 mt-1">
                  {job.problem_type ? job.problem_type.charAt(0).toUpperCase() + job.problem_type.slice(1) : 'Detecting...'}
                </p>
              </div>
              <div>
                <span className="text-gray-600">Started At:</span>
                <p className="text-gray-900 mt-1">
                  {job.started_at ? formatDateTime(job.started_at) : 'Not started'}
                </p>
              </div>
              <div>
                <span className="text-gray-600">Elapsed Time:</span>
                <p className="text-gray-900 mt-1">
                  {job.started_at ? formatDuration(job.started_at) : 'N/A'}
                </p>
              </div>
            </div>
          </div>

          {/* What's Happening */}
          <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h4 className="font-semibold text-blue-900 mb-3">🔄 What's happening now:</h4>
            <ul className="space-y-2 text-sm text-blue-800">
              <li>✓ Downloading your dataset from S3</li>
              <li>✓ Generating exploratory data analysis (EDA) report</li>
              <li className={job.status === 'running' ? 'font-bold' : ''}>
                {job.status === 'running' ? '⚙️' : '○'} Training multiple ML models with FLAML
              </li>
              <li>○ Evaluating model performance with cross-validation</li>
              <li>○ Selecting best model and saving to S3</li>
            </ul>
          </div>

          {/* Actions */}
          <div className="mt-8 flex space-x-4">
            <button
              onClick={() => router.push('/history')}
              className="flex-1 py-3 px-6 border-2 border-gray-300 rounded-lg font-medium text-gray-700 hover:bg-gray-50 transition-colors"
            >
              View All Jobs
            </button>
            <button
              onClick={() => window.location.reload()}
              className="flex-1 py-3 px-6 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors"
            >
              Refresh Status
            </button>
          </div>

          {/* Failed State */}
          {job.status === 'failed' && (
            <div className="mt-8 bg-red-50 border border-red-200 rounded-lg p-6">
              <h4 className="font-semibold text-red-900 mb-2">❌ Training Failed</h4>
              <p className="text-sm text-red-800">
                {job.error_message || 'An unknown error occurred during training'}
              </p>
              <button
                onClick={() => router.push('/')}
                className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
              >
                Start New Training
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
