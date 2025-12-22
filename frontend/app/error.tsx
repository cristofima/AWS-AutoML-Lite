'use client';

import { useEffect } from 'react';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to console (in production, send to error reporting service)
    console.error('Application error:', error);
  }, [error]);

  // Check if it's a network/API error
  const isNetworkError = error.message?.includes('fetch') || 
                         error.message?.includes('network') ||
                         error.message?.includes('Failed to');

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-zinc-900 flex items-center justify-center p-4 transition-colors">
      <div className="bg-white dark:bg-zinc-800 rounded-lg shadow-xl dark:shadow-zinc-900/50 p-8 max-w-lg w-full text-center transition-colors">
        <div className="text-6xl mb-4">
          {isNetworkError ? '🌐' : '⚠️'}
        </div>
        
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          {isNetworkError ? 'Connection Error' : 'Something went wrong'}
        </h1>
        
        <p className="text-gray-600 dark:text-gray-400 mb-6">
          {isNetworkError 
            ? 'Unable to connect to the server. Please check your internet connection and try again.'
            : 'An unexpected error occurred. Our team has been notified.'
          }
        </p>

        {/* Error details for debugging (only in development) */}
        {process.env.NODE_ENV === 'development' && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-lg text-left">
            <p className="text-sm font-mono text-red-700 dark:text-red-400 break-all">
              {error.message}
            </p>
            {error.digest && (
              <p className="text-xs text-red-500 dark:text-red-500 mt-2">
                Error ID: {error.digest}
              </p>
            )}
          </div>
        )}

        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <button
            onClick={reset}
            className="px-6 py-3 bg-indigo-600 dark:bg-indigo-500 text-white rounded-lg font-medium hover:bg-indigo-700 dark:hover:bg-indigo-600 transition-colors cursor-pointer"
          >
            Try again
          </button>
          
          <button
            onClick={() => window.location.href = '/'}
            className="px-6 py-3 bg-gray-100 dark:bg-zinc-700 text-gray-700 dark:text-gray-200 rounded-lg font-medium hover:bg-gray-200 dark:hover:bg-zinc-600 transition-colors cursor-pointer"
          >
            Go to Home
          </button>
        </div>

        {/* Helpful tips */}
        {isNetworkError && (
          <div className="mt-8 text-left">
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Troubleshooting tips:
            </h3>
            <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
              <li>• Check your internet connection</li>
              <li>• Verify the API server is running</li>
              <li>• Try refreshing the page</li>
              <li>• Clear your browser cache</li>
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
