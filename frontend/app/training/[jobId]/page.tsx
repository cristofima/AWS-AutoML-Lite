'use client';

import { useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { JobDetails } from '@/lib/api';
import { useJobSSE } from '@/lib/useJobSSE';
import { getStatusColor, getStatusIcon, formatDuration, formatDateTime } from '@/lib/utils';
import Header from '@/components/Header';

export default function TrainingPage() {
  const router = useRouter();
  const params = useParams();
  const jobId = params.jobId as string;

  // Use SSE for real-time updates
  const { job, isLoading, error, sseStatus, isUsingSSE } = useJobSSE(jobId, {
    enabled: true,
    fallbackToPolling: true,
    pollingInterval: 5000,
    onComplete: (completedJob: JobDetails) => {
      // Redirect to results when job completes
      router.push(`/results/${completedJob.job_id}`);
    },
  });

  // Redirect to results when job completes
  useEffect(() => {
    if (job?.status === 'completed') {
      router.push(`/results/${jobId}`);
    }
  }, [job?.status, jobId, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-zinc-900 flex items-center justify-center transition-colors">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 dark:border-indigo-400 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading training status...</p>
        </div>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-zinc-900 flex items-center justify-center transition-colors">
        <div className="bg-white dark:bg-zinc-800 rounded-lg shadow-lg dark:shadow-zinc-900/50 p-8 max-w-md transition-colors">
          <div className="text-red-500 text-5xl mb-4">⚠️</div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Error</h2>
          <p className="text-gray-600 dark:text-gray-400 mb-4">{error || 'Job not found'}</p>
          <button
            onClick={() => router.push('/')}
            className="w-full py-2 px-4 bg-indigo-600 dark:bg-indigo-500 text-white rounded-lg hover:bg-indigo-700 dark:hover:bg-indigo-600 cursor-pointer transition-colors"
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
      <div className="min-h-screen bg-gray-50 dark:bg-zinc-900 flex items-center justify-center transition-colors">
        <div className="text-center">
          <div className="text-5xl mb-4">✅</div>
          <p className="text-gray-600 dark:text-gray-400">Training complete! Redirecting to results...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-zinc-900 transition-colors">
      <Header title="Training in Progress" showViewAllJobs />

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white dark:bg-zinc-800 rounded-lg shadow-lg dark:shadow-zinc-900/50 p-8 transition-colors">
          {/* Status */}
          <div className="text-center mb-8">
            <div className="text-6xl mb-4">
              {job.status === 'running' ? '⚙️' : '⏳'}
            </div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              {job.status === 'running' ? 'Training Model...' : 'Preparing Training...'}
            </h2>
            <div className={`inline-block px-4 py-2 rounded-full text-sm font-medium ${getStatusColor(job.status)}`}>
              {getStatusIcon(job.status)} {job.status.charAt(0).toUpperCase() + job.status.slice(1)}
            </div>
          </div>

          {/* Progress Animation */}
          <div className="mb-8">
            <div className="w-full bg-gray-200 dark:bg-zinc-700 rounded-full h-2 overflow-hidden">
              <div className="bg-indigo-600 dark:bg-indigo-500 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400 text-center mt-2">
              This may take a few minutes depending on dataset size and time budget
            </p>
            {/* SSE Status Indicator */}
            <div className="flex items-center justify-center gap-2 mt-2">
              <span className={`inline-block w-2 h-2 rounded-full ${
                sseStatus === 'connected' ? 'bg-green-500 animate-pulse' :
                sseStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' :
                sseStatus === 'error' ? 'bg-red-500' : 'bg-gray-400'
              }`}></span>
              <span className="text-xs text-gray-500 dark:text-gray-500">
                {isUsingSSE ? 'Real-time updates' : 'Polling for updates'} • {sseStatus}
              </span>
            </div>
          </div>

          {/* Job Info */}
          <div className="bg-gray-50 dark:bg-zinc-900/50 rounded-lg p-6 space-y-4">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Training Details</h3>
            
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600 dark:text-gray-400">Job ID:</span>
                <p className="font-mono text-gray-900 dark:text-gray-100 text-xs mt-1">{job.job_id}</p>
              </div>
              <div>
                <span className="text-gray-600 dark:text-gray-400">Dataset:</span>
                <p className="font-mono text-gray-900 dark:text-gray-100 text-xs mt-1">{job.dataset_name || job.dataset_id || 'Loading...'}</p>
              </div>
              <div>
                <span className="text-gray-600 dark:text-gray-400">Target Column:</span>
                <p className="font-medium text-gray-900 dark:text-gray-100 mt-1">{job.target_column || 'Loading...'}</p>
              </div>
              <div>
                <span className="text-gray-600 dark:text-gray-400">Problem Type:</span>
                <p className="font-medium text-gray-900 dark:text-gray-100 mt-1">
                  {job.problem_type ? job.problem_type.charAt(0).toUpperCase() + job.problem_type.slice(1) : 'Detecting...'}
                </p>
              </div>
              <div>
                <span className="text-gray-600 dark:text-gray-400">Started At:</span>
                <p className="text-gray-900 dark:text-gray-100 mt-1">
                  {job.started_at ? formatDateTime(job.started_at) : 'Not started'}
                </p>
              </div>
              <div>
                <span className="text-gray-600 dark:text-gray-400">Elapsed Time:</span>
                <p className="text-gray-900 dark:text-gray-100 mt-1">
                  {job.started_at ? formatDuration(job.started_at) : 'N/A'}
                </p>
              </div>
            </div>
          </div>

          {/* What's Happening */}
          <div className="mt-8 bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 rounded-lg p-6 transition-colors">
            <h4 className="font-semibold text-blue-900 dark:text-blue-300 mb-3">🔄 What's happening now:</h4>
            <ul className="space-y-2 text-sm text-blue-800 dark:text-blue-400">
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
              className="flex-1 py-3 px-6 border-2 border-gray-300 dark:border-zinc-600 rounded-lg font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-zinc-700 transition-colors cursor-pointer"
            >
              View All Jobs
            </button>
            <button
              onClick={() => window.location.reload()}
              className="flex-1 py-3 px-6 bg-indigo-600 dark:bg-indigo-500 text-white rounded-lg font-medium hover:bg-indigo-700 dark:hover:bg-indigo-600 transition-colors cursor-pointer"
            >
              Refresh Status
            </button>
          </div>

          {/* Failed State */}
          {job.status === 'failed' && (
            <div className="mt-8 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-lg p-6 transition-colors">
              <h4 className="font-semibold text-red-900 dark:text-red-300 mb-2">❌ Training Failed</h4>
              <p className="text-sm text-red-800 dark:text-red-400">
                {job.error_message || 'An unknown error occurred during training'}
              </p>
              <button
                onClick={() => router.push('/')}
                className="mt-4 px-4 py-2 bg-red-600 dark:bg-red-500 text-white rounded-lg hover:bg-red-700 dark:hover:bg-red-600 cursor-pointer transition-colors"
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
