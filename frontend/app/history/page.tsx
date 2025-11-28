'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { listJobs, JobDetails } from '@/lib/api';
import { getStatusColor, getStatusIcon, formatDate } from '@/lib/utils';

export default function HistoryPage() {
  const router = useRouter();
  const [jobs, setJobs] = useState<JobDetails[]>([]);
  const [nextToken, setNextToken] = useState<string | undefined>();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>('all');

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

  const filteredJobs = filter === 'all' 
    ? jobs 
    : jobs.filter(job => job.status === filter);

  const handleJobClick = (job: JobDetails) => {
    if (job.status === 'completed') {
      router.push(`/results/${job.job_id}`);
    } else if (job.status === 'running' || job.status === 'pending') {
      router.push(`/training/${job.job_id}`);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">Training History</h1>
            <Link
              href="/"
              className="text-sm text-indigo-600 hover:text-indigo-700 font-medium"
            >
              ← Back to Upload
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Filters */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="flex space-x-2 overflow-x-auto">
            {['all', 'completed', 'running', 'pending', 'failed'].map((status) => (
              <button
                key={status}
                onClick={() => setFilter(status)}
                className={`
                  px-4 py-2 rounded-lg font-medium text-sm whitespace-nowrap transition-colors
                  ${filter === status
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }
                `}
              >
                {status.charAt(0).toUpperCase() + status.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Loading State */}
        {isLoading && jobs.length === 0 && (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading training history...</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            <p className="text-sm">{error}</p>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && filteredJobs.length === 0 && (
          <div className="bg-white rounded-lg shadow-lg p-12 text-center">
            <div className="text-6xl mb-4">📋</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              {filter === 'all' ? 'No Training Jobs Yet' : `No ${filter} Jobs`}
            </h3>
            <p className="text-gray-600 mb-6">
              {filter === 'all' 
                ? 'Start by uploading a CSV file to train your first model'
                : `No jobs with status "${filter}" found`
              }
            </p>
            {filter === 'all' && (
              <Link
                href="/"
                className="inline-block px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
              >
                Upload Dataset
              </Link>
            )}
          </div>
        )}

        {/* Jobs Table */}
        {!isLoading && filteredJobs.length > 0 && (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Job ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Target Column
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Problem Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created At
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredJobs.map((job) => (
                  <tr
                    key={job.job_id}
                    className="hover:bg-gray-50 cursor-pointer transition-colors"
                    onClick={() => handleJobClick(job)}
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-mono text-gray-900">
                        {job.job_id.substring(0, 8)}...
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {job.target_column}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {job.problem_type.charAt(0).toUpperCase() + job.problem_type.slice(1)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(job.status)}`}>
                        {getStatusIcon(job.status)} {job.status.charAt(0).toUpperCase() + job.status.slice(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(job.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {job.status === 'completed' ? (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            router.push(`/results/${job.job_id}`);
                          }}
                          className="text-indigo-600 hover:text-indigo-900 font-medium"
                        >
                          View Results
                        </button>
                      ) : job.status === 'running' || job.status === 'pending' ? (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            router.push(`/training/${job.job_id}`);
                          }}
                          className="text-blue-600 hover:text-blue-900 font-medium"
                        >
                          View Status
                        </button>
                      ) : (
                        <span className="text-gray-400">No actions</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Load More */}
        {nextToken && !isLoading && (
          <div className="text-center mt-6">
            <button
              onClick={() => fetchJobs(nextToken)}
              className="px-6 py-3 bg-white border-2 border-indigo-600 text-indigo-600 rounded-lg font-medium hover:bg-indigo-50 transition-colors"
            >
              Load More
            </button>
          </div>
        )}

        {/* Stats */}
        <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-4 text-center">
            <div className="text-2xl font-bold text-gray-900">{jobs.length}</div>
            <div className="text-sm text-gray-600">Total Jobs</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4 text-center">
            <div className="text-2xl font-bold text-green-600">
              {jobs.filter(j => j.status === 'completed').length}
            </div>
            <div className="text-sm text-gray-600">Completed</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4 text-center">
            <div className="text-2xl font-bold text-blue-600">
              {jobs.filter(j => j.status === 'running').length}
            </div>
            <div className="text-sm text-gray-600">Running</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4 text-center">
            <div className="text-2xl font-bold text-red-600">
              {jobs.filter(j => j.status === 'failed').length}
            </div>
            <div className="text-sm text-gray-600">Failed</div>
          </div>
        </div>
      </main>
    </div>
  );
}
