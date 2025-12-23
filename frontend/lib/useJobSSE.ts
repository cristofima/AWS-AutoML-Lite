/**
 * Custom hook for Server-Sent Events (SSE) job status updates
 * 
 * Uses EventSource to receive real-time job status updates from the server.
 * Falls back to polling if SSE is not supported or fails.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { JobDetails, getJobDetails } from './api';

export type SSEStatus = 'connecting' | 'connected' | 'error' | 'closed';

interface UseJobSSEOptions {
  /** Enable SSE streaming (default: true) */
  enabled?: boolean;
  /** Fallback to polling if SSE fails (default: true) */
  fallbackToPolling?: boolean;
  /** Polling interval in ms when using fallback (default: 5000) */
  pollingInterval?: number;
  /** Callback when job completes */
  onComplete?: (job: JobDetails) => void;
  /** Callback when job fails */
  onError?: (error: string) => void;
}

interface UseJobSSEResult {
  /** Current job data */
  job: JobDetails | null;
  /** Loading state (initial fetch) */
  isLoading: boolean;
  /** Error message if any */
  error: string | null;
  /** SSE connection status */
  sseStatus: SSEStatus;
  /** Whether using SSE or fallback polling */
  isUsingSSE: boolean;
  /** Manually refresh job status */
  refresh: () => Promise<void>;
}

export function useJobSSE(
  jobId: string,
  options: UseJobSSEOptions = {}
): UseJobSSEResult {
  const {
    enabled = true,
    fallbackToPolling = true,
    pollingInterval = 5000,
    onComplete,
    onError,
  } = options;

  const [job, setJob] = useState<JobDetails | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sseStatus, setSseStatus] = useState<SSEStatus>('connecting');
  const [isUsingSSE, setIsUsingSSE] = useState(true);
  
  const eventSourceRef = useRef<EventSource | null>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const onCompleteRef = useRef(onComplete);
  const onErrorRef = useRef(onError);

  // Keep callbacks up to date
  onCompleteRef.current = onComplete;
  onErrorRef.current = onError;

  const refresh = useCallback(async () => {
    try {
      const jobData = await getJobDetails(jobId);
      setJob(jobData);
      setError(null);
      return;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch job');
    }
  }, [jobId]);

  // Cleanup function
  const cleanup = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  }, []);

  // Start polling fallback
  const startPolling = useCallback(() => {
    setIsUsingSSE(false);
    
    const poll = async () => {
      try {
        const jobData = await getJobDetails(jobId);
        setJob(jobData);
        setIsLoading(false);
        setError(null);

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
        cleanup(); // Stop polling on persistent error
      }
    };

    // Initial fetch
    poll();

    // Start polling
    pollingIntervalRef.current = setInterval(poll, pollingInterval);
  }, [jobId, pollingInterval, cleanup]);

  // Setup SSE connection
  useEffect(() => {
    if (!enabled || !jobId) return;

    // Check if EventSource is supported
    if (typeof EventSource === 'undefined') {
      console.warn('EventSource not supported, falling back to polling');
      if (fallbackToPolling) {
        startPolling();
      }
      return cleanup;
    }

    // Create EventSource connection
    const eventSource = new EventSource(`/api/jobs/${jobId}/stream`);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setSseStatus('connected');
      setIsUsingSSE(true);
    };

    eventSource.onmessage = (event) => {
      try {
        const jobData: JobDetails = JSON.parse(event.data);
        setJob(jobData);
        setIsLoading(false);
        setError(null);

        // Handle terminal states
        if (jobData.status === 'completed') {
          cleanup();
          setSseStatus('closed');
          onCompleteRef.current?.(jobData);
        } else if (jobData.status === 'failed') {
          cleanup();
          setSseStatus('closed');
          onErrorRef.current?.(jobData.error_message || 'Training failed');
        }
      } catch (err) {
        console.error('Failed to parse SSE message:', err);
      }
    };

    eventSource.addEventListener('done', () => {
      cleanup();
      setSseStatus('closed');
    });

    eventSource.addEventListener('timeout', () => {
      console.warn('SSE stream timed out, switching to polling');
      cleanup();
      setSseStatus('closed');
      if (fallbackToPolling) {
        startPolling();
      }
    });

    eventSource.onerror = (err) => {
      console.error('SSE error:', err);
      setSseStatus('error');
      
      // Close the failed connection
      eventSource.close();
      eventSourceRef.current = null;

      // Fallback to polling
      if (fallbackToPolling) {
        console.log('SSE failed, falling back to polling');
        startPolling();
      } else {
        setError('Real-time connection failed');
        setIsLoading(false);
      }
    };

    return cleanup;
  }, [jobId, enabled, fallbackToPolling, cleanup, startPolling]);

  return {
    job,
    isLoading,
    error,
    sseStatus,
    isUsingSSE,
    refresh,
  };
}
