/**
 * Custom hook for job status polling
 * 
 * Polls the backend API for job status updates at a configurable interval.
 * Automatically stops polling when job reaches a terminal state (completed/failed).
 * 
 * Note: This hook was originally designed for SSE but SSE is not compatible
 * with AWS Amplify's Lambda@Edge (30s timeout). Polling is the reliable solution
 * for serverless platforms.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { JobDetails, getJobDetails } from './api';

interface UseJobPollingOptions {
  /** Enable polling (default: true) */
  enabled?: boolean;
  /** Polling interval in ms (default: 5000) */
  pollingInterval?: number;
  /** Callback when job completes */
  onComplete?: (job: JobDetails) => void;
  /** Callback when job fails */
  onError?: (error: string) => void;
}

interface UseJobPollingResult {
  /** Current job data */
  job: JobDetails | null;
  /** Loading state (initial fetch) */
  isLoading: boolean;
  /** Error message if any */
  error: string | null;
  /** Manually refresh job status */
  refresh: () => Promise<void>;
}

export function useJobPolling(
  jobId: string,
  options: UseJobPollingOptions = {}
): UseJobPollingResult {
  const {
    enabled = true,
    pollingInterval = 5000,
    onComplete,
    onError,
  } = options;

  const [job, setJob] = useState<JobDetails | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const onCompleteRef = useRef(onComplete);
  const onErrorRef = useRef(onError);

  // Keep callbacks up to date
  onCompleteRef.current = onComplete;
  onErrorRef.current = onError;

  // Cleanup function
  const cleanup = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  }, []);

  const refresh = useCallback(async () => {
    try {
      const jobData = await getJobDetails(jobId);
      setJob(jobData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch job');
    }
  }, [jobId]);

  // Setup polling
  useEffect(() => {
    if (!enabled || !jobId) return;

    const poll = async () => {
      try {
        const jobData = await getJobDetails(jobId);
        setJob(jobData);
        setIsLoading(false);
        setError(null);

        // Handle terminal states
        if (jobData.status === 'completed') {
          cleanup();
          onCompleteRef.current?.(jobData);
        } else if (jobData.status === 'failed') {
          cleanup();
          onErrorRef.current?.(jobData.error_message || 'Training failed');
        }
      } catch (err) {
        setIsLoading(false);
        setError(err instanceof Error ? err.message : 'Failed to fetch job');
        // Don't stop polling on transient errors
      }
    };

    // Initial fetch
    poll();

    // Start polling
    pollingIntervalRef.current = setInterval(poll, pollingInterval);

    return cleanup;
  }, [jobId, enabled, pollingInterval, cleanup]);

  return {
    job,
    isLoading,
    error,
    refresh,
  };
}
