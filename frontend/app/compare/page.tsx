'use client';

import { useState, useEffect, useMemo } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { listJobs, getJobDetails, JobDetails } from '@/lib/api';
import { formatDate } from '@/lib/utils';
import Header from '@/components/Header';

// Metrics to compare for classification
const CLASSIFICATION_METRICS = [
  { key: 'accuracy', label: 'Accuracy', format: 'percent' },
  { key: 'f1_score', label: 'F1 Score', format: 'percent' },
  { key: 'precision', label: 'Precision', format: 'percent' },
  { key: 'recall', label: 'Recall', format: 'percent' },
] as const;

// Metrics to compare for regression
const REGRESSION_METRICS = [
  { key: 'r2_score', label: 'R² Score', format: 'decimal' },
  { key: 'rmse', label: 'RMSE', format: 'decimal' },
  { key: 'mae', label: 'MAE', format: 'decimal' },
] as const;

type MetricKey = 'accuracy' | 'f1_score' | 'precision' | 'recall' | 'r2_score' | 'rmse' | 'mae';

function formatMetric(value: number | undefined, format: string): string {
  if (value === undefined || value === null) return 'N/A';
  if (format === 'percent') return `${(value * 100).toFixed(2)}%`;
  return value.toFixed(4);
}

function getBestValue(jobs: JobDetails[], metricKey: MetricKey): number | undefined {
  const values = jobs
    .map(j => j.metrics?.[metricKey as keyof typeof j.metrics])
    .filter((v): v is number => v !== undefined && v !== null);
  
  if (values.length === 0) return undefined;
  
  // For RMSE and MAE, lower is better
  if (metricKey === 'rmse' || metricKey === 'mae') {
    return Math.min(...values);
  }
  // For accuracy, F1, precision, recall, R2 - higher is better
  return Math.max(...values);
}

export default function ComparePage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  const [allJobs, setAllJobs] = useState<JobDetails[]>([]);
  const [selectedJobs, setSelectedJobs] = useState<JobDetails[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingSelected, setIsLoadingSelected] = useState(false);
  const [_error, setError] = useState<string | null>(null);

  // Get job IDs from URL params
  const jobIdsFromUrl = searchParams.get('jobs')?.split(',').filter(Boolean) || [];

  // Fetch all completed jobs for selection
  useEffect(() => {
    const fetchJobs = async () => {
      try {
        setIsLoading(true);
        const response = await listJobs(50); // Get up to 50 jobs
        // Filter only completed jobs
        const completedJobs = response.jobs.filter(j => j.status === 'completed');
        setAllJobs(completedJobs);
        setIsLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load jobs');
        setIsLoading(false);
      }
    };

    fetchJobs();
  }, []);

  // Fetch full details for selected jobs from URL
  useEffect(() => {
    if (jobIdsFromUrl.length === 0 || allJobs.length === 0) {
      setSelectedJobs([]);
      return;
    }

    const fetchSelectedJobs = async () => {
      setIsLoadingSelected(true);
      try {
        const jobPromises = jobIdsFromUrl.map(id => getJobDetails(id));
        const jobs = await Promise.all(jobPromises);
        setSelectedJobs(jobs.filter(j => j.status === 'completed'));
      } catch (err) {
        console.error('Failed to fetch selected jobs:', err);
      } finally {
        setIsLoadingSelected(false);
      }
    };

    fetchSelectedJobs();
  }, [jobIdsFromUrl.join(','), allJobs.length]);

  // Determine problem type (use first selected job's type)
  const problemType = selectedJobs[0]?.problem_type;
  const metrics = problemType === 'regression' ? REGRESSION_METRICS : CLASSIFICATION_METRICS;

  // Toggle job selection
  const toggleJob = (jobId: string) => {
    const currentIds = new Set(jobIdsFromUrl);
    
    if (currentIds.has(jobId)) {
      currentIds.delete(jobId);
    } else {
      // Max 4 jobs for comparison
      if (currentIds.size >= 4) {
        alert('You can compare up to 4 jobs at a time');
        return;
      }
      currentIds.add(jobId);
    }
    
    const newIds = Array.from(currentIds);
    const params = new URLSearchParams();
    if (newIds.length > 0) {
      params.set('jobs', newIds.join(','));
    }
    
    router.push(`/compare${newIds.length > 0 ? '?' + params.toString() : ''}`);
  };

  // Get all unique features across selected jobs
  const allFeatures = useMemo(() => {
    const featuresSet = new Set<string>();
    selectedJobs.forEach(job => {
      if (job.metrics?.feature_importance) {
        Object.keys(job.metrics.feature_importance).forEach(f => featuresSet.add(f));
      }
    });
    return Array.from(featuresSet).sort();
  }, [selectedJobs]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-zinc-900 transition-colors">
      <Header title="Compare Models" showBackToUpload />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Job Selection */}
        <div className="bg-white dark:bg-zinc-800 rounded-lg shadow dark:shadow-zinc-900/50 p-6 mb-6 transition-colors">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Select Jobs to Compare
            </h2>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              {selectedJobs.length}/4 selected
            </span>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 dark:border-indigo-400"></div>
            </div>
          ) : allJobs.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-600 dark:text-gray-400 mb-4">No completed training jobs found</p>
              <Link
                href="/"
                className="inline-block px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
              >
                Train a Model
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {allJobs.map((job) => {
                const isSelected = jobIdsFromUrl.includes(job.job_id);
                return (
                  <button
                    key={job.job_id}
                    onClick={() => toggleJob(job.job_id)}
                    className={`
                      p-4 rounded-lg border-2 text-left transition-all cursor-pointer
                      ${isSelected 
                        ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-950/30' 
                        : 'border-gray-200 dark:border-zinc-700 hover:border-indigo-300 dark:hover:border-indigo-700'
                      }
                    `}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-mono text-gray-900 dark:text-gray-100 truncate">
                          {job.job_id.substring(0, 12)}...
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                          {job.target_column} • {job.problem_type}
                        </p>
                        <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                          {job.created_at ? formatDate(job.created_at) : ''}
                        </p>
                      </div>
                      <div className={`
                        w-5 h-5 rounded-full border-2 flex items-center justify-center
                        ${isSelected 
                          ? 'border-indigo-500 bg-indigo-500' 
                          : 'border-gray-300 dark:border-zinc-600'
                        }
                      `}>
                        {isSelected && (
                          <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                        )}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Comparison Results */}
        {selectedJobs.length >= 2 && (
          <>
            {/* Metrics Comparison */}
            <div className="bg-white dark:bg-zinc-800 rounded-lg shadow dark:shadow-zinc-900/50 p-6 mb-6 transition-colors">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                📊 Metrics Comparison
              </h2>
              
              {isLoadingSelected ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full">
                    <thead>
                      <tr className="border-b border-gray-200 dark:border-zinc-700">
                        <th className="py-3 px-4 text-left text-sm font-medium text-gray-500 dark:text-gray-400">
                          Metric
                        </th>
                        {selectedJobs.map((job, idx) => (
                          <th key={job.job_id} className="py-3 px-4 text-center text-sm font-medium text-gray-900 dark:text-gray-100">
                            <div className="flex flex-col items-center">
                              <span className="text-indigo-600 dark:text-indigo-400">Model {idx + 1}</span>
                              <span className="text-xs text-gray-500 dark:text-gray-400 font-mono">
                                {job.job_id.substring(0, 8)}
                              </span>
                            </div>
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {metrics.map((metric) => {
                        const bestValue = getBestValue(selectedJobs, metric.key as MetricKey);
                        return (
                          <tr key={metric.key} className="border-b border-gray-100 dark:border-zinc-800">
                            <td className="py-3 px-4 text-sm font-medium text-gray-700 dark:text-gray-300">
                              {metric.label}
                            </td>
                            {selectedJobs.map((job) => {
                              const value = job.metrics?.[metric.key as keyof typeof job.metrics] as number | undefined;
                              const isBest = value !== undefined && value === bestValue;
                              return (
                                <td 
                                  key={job.job_id} 
                                  className={`py-3 px-4 text-center text-sm font-mono ${
                                    isBest 
                                      ? 'text-green-600 dark:text-green-400 font-bold' 
                                      : 'text-gray-900 dark:text-gray-100'
                                  }`}
                                >
                                  {formatMetric(value, metric.format)}
                                  {isBest && ' 🏆'}
                                </td>
                              );
                            })}
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Feature Importance Comparison */}
            {allFeatures.length > 0 && (
              <div className="bg-white dark:bg-zinc-800 rounded-lg shadow dark:shadow-zinc-900/50 p-6 transition-colors">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  📈 Feature Importance Comparison
                </h2>
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
                  Top features ranked by importance across selected models
                </p>
                
                <div className="overflow-x-auto">
                  <table className="min-w-full">
                    <thead>
                      <tr className="border-b border-gray-200 dark:border-zinc-700">
                        <th className="py-3 px-4 text-left text-sm font-medium text-gray-500 dark:text-gray-400">
                          Feature
                        </th>
                        {selectedJobs.map((job, idx) => (
                          <th key={job.job_id} className="py-3 px-4 text-center text-sm font-medium text-gray-900 dark:text-gray-100">
                            Model {idx + 1}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {allFeatures.slice(0, 15).map((feature) => (
                        <tr key={feature} className="border-b border-gray-100 dark:border-zinc-800">
                          <td className="py-2 px-4 text-sm font-medium text-gray-700 dark:text-gray-300 truncate max-w-[200px]" title={feature}>
                            {feature}
                          </td>
                          {selectedJobs.map((job) => {
                            const importance = job.metrics?.feature_importance?.[feature];
                            const maxImportance = Math.max(
                              ...selectedJobs
                                .map(j => j.metrics?.feature_importance?.[feature] || 0)
                            );
                            const barWidth = importance && maxImportance > 0 
                              ? (importance / maxImportance) * 100 
                              : 0;
                            
                            return (
                              <td key={job.job_id} className="py-2 px-4">
                                <div className="flex items-center gap-2">
                                  <div className="flex-1 bg-gray-100 dark:bg-zinc-700 rounded-full h-2 overflow-hidden">
                                    <div 
                                      className="bg-indigo-500 h-2 rounded-full transition-all"
                                      style={{ width: `${barWidth}%` }}
                                    />
                                  </div>
                                  <span className="text-xs text-gray-500 dark:text-gray-400 w-12 text-right font-mono">
                                    {importance !== undefined ? (importance * 100).toFixed(1) : '-'}
                                  </span>
                                </div>
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                
                {allFeatures.length > 15 && (
                  <p className="text-xs text-gray-400 dark:text-gray-500 mt-4 text-center">
                    Showing top 15 features of {allFeatures.length} total
                  </p>
                )}
              </div>
            )}
          </>
        )}

        {/* Empty selection state */}
        {selectedJobs.length < 2 && !isLoading && allJobs.length > 0 && (
          <div className="bg-white dark:bg-zinc-800 rounded-lg shadow dark:shadow-zinc-900/50 p-12 text-center transition-colors">
            <div className="text-6xl mb-4">📊</div>
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              Select at least 2 jobs to compare
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Click on the completed jobs above to select them for comparison
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
