'use client';

import { useEffect } from 'react';
import Link from 'next/link';

export default function TrainingError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Training page error:', error);
  }, [error]);

  const isJobNotFound = error.message?.includes('not found') || 
                         error.message?.includes('404');

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-zinc-900 flex items-center justify-center p-4 transition-colors">
      <div className="bg-white dark:bg-zinc-800 rounded-lg shadow-xl dark:shadow-zinc-900/50 p-8 max-w-lg w-full text-center transition-colors">
        <div className="text-6xl mb-4">
          {isJobNotFound ? '🔍' : '⚠️'}
        </div>
        
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          {isJobNotFound ? 'Training Job Not Found' : 'Error Loading Training Status'}
        </h1>
        
        <p className="text-gray-600 dark:text-gray-400 mb-6">
          {isJobNotFound 
            ? 'This training job may have been deleted or the ID is incorrect.'
            : 'We couldn\'t load the training status. Please try again.'
          }
        </p>

        {process.env.NODE_ENV === 'development' && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-lg text-left">
            <p className="text-sm font-mono text-red-700 dark:text-red-400 break-all">
              {error.message}
            </p>
          </div>
        )}

        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          {!isJobNotFound && (
            <button
              onClick={reset}
              className="px-6 py-3 bg-indigo-600 dark:bg-indigo-500 text-white rounded-lg font-medium hover:bg-indigo-700 dark:hover:bg-indigo-600 transition-colors cursor-pointer"
            >
              Try again
            </button>
          )}
          
          <Link
            href="/history"
            className="px-6 py-3 bg-gray-100 dark:bg-zinc-700 text-gray-700 dark:text-gray-200 rounded-lg font-medium hover:bg-gray-200 dark:hover:bg-zinc-600 transition-colors cursor-pointer text-center"
          >
            View All Jobs
          </Link>
          
          <Link
            href="/"
            className="px-6 py-3 border-2 border-indigo-600 dark:border-indigo-400 text-indigo-600 dark:text-indigo-400 rounded-lg font-medium hover:bg-indigo-50 dark:hover:bg-zinc-700 transition-colors cursor-pointer text-center"
          >
            New Training
          </Link>
        </div>
      </div>
    </div>
  );
}
