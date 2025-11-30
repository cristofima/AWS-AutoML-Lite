'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { getJobDetails, JobDetails } from '@/lib/api';
import { formatMetric, getProblemTypeIcon } from '@/lib/utils';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function ResultsPage() {
  const router = useRouter();
  const params = useParams();
  const jobId = params.jobId as string;

  const [job, setJob] = useState<JobDetails | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchResults = async () => {
      try {
        const jobData = await getJobDetails(jobId);
        
        if (jobData.status !== 'completed') {
          router.push(`/training/${jobId}`);
          return;
        }
        
        setJob(jobData);
        setIsLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load results');
        setIsLoading(false);
      }
    };

    fetchResults();
  }, [jobId, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading results...</p>
        </div>
      </div>
    );
  }

  if (error || !job || !job.metrics) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md">
          <div className="text-red-500 text-5xl mb-4">⚠️</div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Error</h2>
          <p className="text-gray-600 mb-4">{error || 'Results not available'}</p>
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

  // Prepare feature importance data for chart
  const featureImportanceData = job.metrics.feature_importance
    ? Object.entries(job.metrics.feature_importance)
        .sort(([, a], [, b]) => b - a)
        .slice(0, 10)
        .map(([name, value]) => ({ name, importance: value }))
    : [];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">Training Results</h1>
            <Link
              href="/history"
              className="text-sm text-indigo-600 hover:text-indigo-700 font-medium"
            >
              View All Jobs →
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Success Banner */}
        <div className="bg-green-50 border-2 border-green-200 rounded-lg p-6">
          <div className="flex items-center">
            <div className="text-5xl mr-4">✅</div>
            <div>
              <h2 className="text-xl font-bold text-green-900 mb-1">Training Completed Successfully!</h2>
              <p className="text-green-700">
                Your model has been trained and is ready to download
              </p>
            </div>
          </div>
        </div>

        {/* Job Info */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Job Information</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Problem Type:</span>
              <p className="font-medium text-gray-900 mt-1">
                {getProblemTypeIcon(job.problem_type)} {job.problem_type.charAt(0).toUpperCase() + job.problem_type.slice(1)}
              </p>
            </div>
            <div>
              <span className="text-gray-600">Target Column:</span>
              <p className="font-medium text-gray-900 mt-1">{job.target_column}</p>
            </div>
            <div>
              <span className="text-gray-600">Completed At:</span>
              <p className="text-gray-900 mt-1">
                {job.completed_at ? new Date(job.completed_at).toLocaleString() : 'N/A'}
              </p>
            </div>
            <div>
              <span className="text-gray-600">Job ID:</span>
              <p className="font-mono text-xs text-gray-900 mt-1">{job.job_id}</p>
            </div>
          </div>
        </div>

        {/* Metrics */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Model Performance</h3>
          
          {job.problem_type === 'classification' ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              {job.metrics.accuracy !== undefined && (
                <div className="text-center">
                  <div className="text-3xl font-bold text-indigo-600">
                    {formatMetric(job.metrics.accuracy * 100, 2)}%
                  </div>
                  <div className="text-sm text-gray-600 mt-1">Accuracy</div>
                </div>
              )}
              {job.metrics.f1_score !== undefined && (
                <div className="text-center">
                  <div className="text-3xl font-bold text-indigo-600">
                    {formatMetric(job.metrics.f1_score, 3)}
                  </div>
                  <div className="text-sm text-gray-600 mt-1">F1 Score</div>
                </div>
              )}
              {job.metrics.precision !== undefined && (
                <div className="text-center">
                  <div className="text-3xl font-bold text-indigo-600">
                    {formatMetric(job.metrics.precision, 3)}
                  </div>
                  <div className="text-sm text-gray-600 mt-1">Precision</div>
                </div>
              )}
              {job.metrics.recall !== undefined && (
                <div className="text-center">
                  <div className="text-3xl font-bold text-indigo-600">
                    {formatMetric(job.metrics.recall, 3)}
                  </div>
                  <div className="text-sm text-gray-600 mt-1">Recall</div>
                </div>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {job.metrics.r2_score !== undefined && (
                <div className="text-center">
                  <div className="text-3xl font-bold text-indigo-600">
                    {formatMetric(job.metrics.r2_score, 4)}
                  </div>
                  <div className="text-sm text-gray-600 mt-1">R² Score</div>
                </div>
              )}
              {job.metrics.rmse !== undefined && (
                <div className="text-center">
                  <div className="text-3xl font-bold text-indigo-600">
                    {formatMetric(job.metrics.rmse, 4)}
                  </div>
                  <div className="text-sm text-gray-600 mt-1">RMSE</div>
                </div>
              )}
              {job.metrics.mae !== undefined && (
                <div className="text-center">
                  <div className="text-3xl font-bold text-indigo-600">
                    {formatMetric(job.metrics.mae, 4)}
                  </div>
                  <div className="text-sm text-gray-600 mt-1">MAE</div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Feature Importance */}
        {featureImportanceData.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Feature Importance (Top 10)</h3>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={featureImportanceData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="name" type="category" width={120} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="importance" fill="#4f46e5" name="Importance" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Download Section */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Download Results</h3>
          <div className="grid md:grid-cols-2 gap-4">
            {job.model_download_url && (
              <a
                href={job.model_download_url}
                className="flex items-center justify-center space-x-2 px-6 py-4 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
              >
                <span className="text-2xl">📦</span>
                <span className="font-medium">Download Model (.pkl)</span>
              </a>
            )}
            {job.report_download_url && (
              <a
                href={job.report_download_url}
                className="flex items-center justify-center space-x-2 px-6 py-4 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                <span className="text-2xl">📊</span>
                <span className="font-medium">Download EDA Report (.html)</span>
              </a>
            )}
          </div>
          <p className="text-sm text-gray-600 mt-4">
            💡 Use the .pkl file to make predictions in your Python application with joblib or pickle
          </p>
        </div>

        {/* Actions */}
        <div className="flex space-x-4">
          <button
            onClick={() => router.push('/')}
            className="flex-1 py-3 px-6 border-2 border-indigo-600 text-indigo-600 rounded-lg font-medium hover:bg-indigo-50 transition-colors"
          >
            Train Another Model
          </button>
          <button
            onClick={() => router.push('/history')}
            className="flex-1 py-3 px-6 bg-gray-600 text-white rounded-lg font-medium hover:bg-gray-700 transition-colors"
          >
            View All Jobs
          </button>
        </div>
      </main>
    </div>
  );
}
