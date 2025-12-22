'use client';

import { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { listJobs, deleteJob, JobDetails } from '@/lib/api';
import { getStatusColor, getStatusIcon, formatDate } from '@/lib/utils';
import Header from '@/components/Header';

export default function HistoryPage() {
  const router = useRouter();
  const [jobs, setJobs] = useState<JobDetails[]>([]);
  const [nextToken, setNextToken] = useState<string | undefined>();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>('all');
  const [tagFilter, setTagFilter] = useState<string>('');  // New: filter by tag
  const [deletingJobId, setDeletingJobId] = useState<string | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState<string | null>(null);

  // Get all unique tags from jobs
  const allTags = useMemo(() => {
    const tags = new Set<string>();
    jobs.forEach(job => {
      job.tags?.forEach(tag => tags.add(tag));
    });
    return Array.from(tags).sort();
  }, [jobs]);

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async (token?: string) => {
    try {
      setIsLoading(true);
      const response = await listJobs(20, token);
      
      if (token) {
        setJobs(prev => [...prev, ...response.jobs]);
      } else {
        setJobs(response.jobs);
      }
      
      setNextToken(response.next_token);
      setIsLoading(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load jobs');
      setIsLoading(false);
    }
  };

  const handleDeleteJob = async (jobId: string) => {
    setDeletingJobId(jobId);
    setShowDeleteModal(null);
    
    try {
      await deleteJob(jobId, true);
      // Remove job from local state
      setJobs(prev => prev.filter(j => j.job_id !== jobId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete job');
    } finally {
      setDeletingJobId(null);
    }
  };

  const filteredJobs = useMemo(() => {
    let result = jobs;
    
    // Filter by status
    if (filter !== 'all') {
      result = result.filter(job => job.status === filter);
    }
    
    // Filter by tag
    if (tagFilter) {
      result = result.filter(job => job.tags?.includes(tagFilter));
    }
    
    return result;
  }, [jobs, filter, tagFilter]);

  const handleJobClick = (job: JobDetails) => {
    if (job.status === 'completed') {
      router.push(`/results/${job.job_id}`);
    } else if (job.status === 'running' || job.status === 'pending') {
      router.push(`/training/${job.job_id}`);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-zinc-900 transition-colors">
      <Header title="Training History" showBackToUpload showCompare />

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Filters */}
        <div className="bg-white dark:bg-zinc-800 rounded-lg shadow dark:shadow-zinc-900/50 p-4 mb-6 transition-colors">
          <div className="flex flex-col sm:flex-row gap-4">
            {/* Status Filter */}
            <div className="flex-1">
              <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">Status</label>
              <div className="flex space-x-2 overflow-x-auto">
                {['all', 'completed', 'running', 'pending', 'failed'].map((status) => (
                  <button
                    key={status}
                    onClick={() => setFilter(status)}
                    className={`
                      px-4 py-2 rounded-lg font-medium text-sm whitespace-nowrap transition-colors cursor-pointer
                      ${filter === status
                        ? 'bg-indigo-600 dark:bg-indigo-500 text-white'
                        : 'bg-gray-100 dark:bg-zinc-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-zinc-600'
                      }
                    `}
                  >
                    {status.charAt(0).toUpperCase() + status.slice(1)}
                  </button>
                ))}
              </div>
            </div>
            
            {/* Tag Filter */}
            {allTags.length > 0 && (
              <div className="sm:w-48">
                <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">Filter by Tag</label>
                <select
                  value={tagFilter}
                  onChange={(e) => setTagFilter(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-zinc-600 bg-white dark:bg-zinc-700 text-gray-700 dark:text-gray-200 text-sm focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 focus:border-transparent cursor-pointer"
                >
                  <option value="">All tags</option>
                  {allTags.map(tag => (
                    <option key={tag} value={tag}>{tag}</option>
                  ))}
                </select>
              </div>
            )}
          </div>
        </div>

        {/* Loading State */}
        {isLoading && jobs.length === 0 && (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 dark:border-indigo-400 mx-auto mb-4"></div>
            <p className="text-gray-600 dark:text-gray-400">Loading training history...</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg">
            <p className="text-sm">{error}</p>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && filteredJobs.length === 0 && (
          <div className="bg-white dark:bg-zinc-800 rounded-lg shadow-lg dark:shadow-zinc-900/50 p-12 text-center transition-colors">
            <div className="text-6xl mb-4">📋</div>
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              {filter === 'all' ? 'No Training Jobs Yet' : `No ${filter} Jobs`}
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              {filter === 'all' 
                ? 'Start by uploading a CSV file to train your first model'
                : `No jobs with status "${filter}" found`
              }
            </p>
            {filter === 'all' && (
              <Link
                href="/"
                className="inline-block px-6 py-3 bg-indigo-600 dark:bg-indigo-500 text-white rounded-lg hover:bg-indigo-700 dark:hover:bg-indigo-600 transition-colors cursor-pointer"
              >
                Upload Dataset
              </Link>
            )}
          </div>
        )}

        {/* Jobs Table */}
        {!isLoading && filteredJobs.length > 0 && (
          <div className="bg-white dark:bg-zinc-800 rounded-lg shadow dark:shadow-zinc-900/50 overflow-hidden transition-colors">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-zinc-700">
              <thead className="bg-gray-50 dark:bg-zinc-900/50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Job ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Target Column
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Problem Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Tags
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Created At
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-zinc-800 divide-y divide-gray-200 dark:divide-zinc-700">
                {filteredJobs.map((job) => (
                  <tr
                    key={job.job_id}
                    className="hover:bg-gray-50 dark:hover:bg-zinc-700/50 cursor-pointer transition-colors"
                    onClick={() => handleJobClick(job)}
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-mono text-gray-900 dark:text-gray-100">
                        {job.job_id.substring(0, 8)}...
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {job.target_column || 'N/A'}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900 dark:text-gray-100">
                        {job.problem_type ? job.problem_type.charAt(0).toUpperCase() + job.problem_type.slice(1) : 'N/A'}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-wrap gap-1 max-w-[150px]">
                        {job.tags && job.tags.length > 0 ? (
                          job.tags.slice(0, 3).map(tag => (
                            <span
                              key={tag}
                              className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300"
                            >
                              {tag}
                            </span>
                          ))
                        ) : (
                          <span className="text-xs text-gray-400 dark:text-gray-500">—</span>
                        )}
                        {job.tags && job.tags.length > 3 && (
                          <span className="text-xs text-gray-500 dark:text-gray-400">+{job.tags.length - 3}</span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(job.status)}`}>
                        {getStatusIcon(job.status)} {job.status.charAt(0).toUpperCase() + job.status.slice(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {job.created_at ? formatDate(job.created_at) : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className="flex items-center space-x-2">
                        {job.status === 'completed' ? (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              router.push(`/results/${job.job_id}`);
                            }}
                            className="text-indigo-600 dark:text-indigo-400 hover:text-indigo-900 dark:hover:text-indigo-300 font-medium cursor-pointer"
                          >
                            View Results
                          </button>
                        ) : job.status === 'running' || job.status === 'pending' ? (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              router.push(`/training/${job.job_id}`);
                            }}
                            className="text-blue-600 dark:text-blue-400 hover:text-blue-900 dark:hover:text-blue-300 font-medium cursor-pointer"
                          >
                            View Status
                          </button>
                        ) : null}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setShowDeleteModal(job.job_id);
                          }}
                          disabled={deletingJobId === job.job_id}
                          className="text-red-600 dark:text-red-400 hover:text-red-900 dark:hover:text-red-300 font-medium disabled:opacity-50 cursor-pointer disabled:cursor-not-allowed"
                        >
                          {deletingJobId === job.job_id ? 'Deleting...' : '🗑️'}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Delete Confirmation Modal */}
        {showDeleteModal && (
          <div className="fixed inset-0 bg-gray-900/50 dark:bg-black/70 backdrop-blur-sm flex items-center justify-center z-50">
            <div className="bg-white dark:bg-zinc-800 rounded-lg p-6 max-w-md w-full mx-4 shadow-xl transition-colors">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Delete Training Job?</h3>
              
              {/* Job Details */}
              {(() => {
                const jobToDelete = jobs.find(j => j.job_id === showDeleteModal);
                return jobToDelete ? (
                  <div className="bg-gray-50 dark:bg-zinc-900/50 rounded-lg p-4 mb-4 border border-gray-200 dark:border-zinc-700">
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">Job ID:</span>
                        <p className="font-mono text-gray-900 dark:text-gray-100">{jobToDelete.job_id.substring(0, 12)}...</p>
                      </div>
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">Target:</span>
                        <p className="font-medium text-gray-900 dark:text-gray-100">{jobToDelete.target_column || 'N/A'}</p>
                      </div>
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">Type:</span>
                        <p className="text-gray-900 dark:text-gray-100">{jobToDelete.problem_type ? jobToDelete.problem_type.charAt(0).toUpperCase() + jobToDelete.problem_type.slice(1) : 'N/A'}</p>
                      </div>
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">Status:</span>
                        <p className="text-gray-900 dark:text-gray-100">{jobToDelete.status.charAt(0).toUpperCase() + jobToDelete.status.slice(1)}</p>
                      </div>
                    </div>
                  </div>
                ) : null;
              })()}

              <p className="text-gray-600 dark:text-gray-400 mb-3">
                This will permanently delete all associated data:
              </p>
              <ul className="text-sm text-gray-600 dark:text-gray-400 mb-4 list-disc list-inside">
                <li>Trained model file (.pkl)</li>
                <li>EDA report (.html)</li>
                <li>Original dataset (CSV)</li>
                <li>Job metadata</li>
              </ul>
              <p className="text-red-600 dark:text-red-400 text-sm font-medium mb-4">
                ⚠️ This action cannot be undone.
              </p>
              <div className="flex space-x-3">
                <button
                  onClick={() => setShowDeleteModal(null)}
                  className="flex-1 py-2 px-4 border border-gray-300 dark:border-zinc-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-zinc-700 cursor-pointer transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleDeleteJob(showDeleteModal)}
                  className="flex-1 py-2 px-4 bg-red-600 dark:bg-red-500 text-white rounded-lg hover:bg-red-700 dark:hover:bg-red-600 cursor-pointer transition-colors"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Load More */}
        {nextToken && !isLoading && (
          <div className="text-center mt-6">
            <button
              onClick={() => fetchJobs(nextToken)}
              className="px-6 py-3 bg-white dark:bg-zinc-800 border-2 border-indigo-600 dark:border-indigo-400 text-indigo-600 dark:text-indigo-400 rounded-lg font-medium hover:bg-indigo-50 dark:hover:bg-zinc-700 transition-colors cursor-pointer"
            >
              Load More
            </button>
          </div>
        )}

        {/* Stats */}
        <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-zinc-800 rounded-lg shadow dark:shadow-zinc-900/50 p-4 text-center transition-colors">
            <div className="text-2xl font-bold text-gray-900 dark:text-white">{jobs.length}</div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Total Jobs</div>
          </div>
          <div className="bg-white dark:bg-zinc-800 rounded-lg shadow dark:shadow-zinc-900/50 p-4 text-center transition-colors">
            <div className="text-2xl font-bold text-green-600 dark:text-green-400">
              {jobs.filter(j => j.status === 'completed').length}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Completed</div>
          </div>
          <div className="bg-white dark:bg-zinc-800 rounded-lg shadow dark:shadow-zinc-900/50 p-4 text-center transition-colors">
            <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {jobs.filter(j => j.status === 'running').length}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Running</div>
          </div>
          <div className="bg-white dark:bg-zinc-800 rounded-lg shadow dark:shadow-zinc-900/50 p-4 text-center transition-colors">
            <div className="text-2xl font-bold text-red-600 dark:text-red-400">
              {jobs.filter(j => j.status === 'failed').length}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Failed</div>
          </div>
        </div>
      </main>
    </div>
  );
}
