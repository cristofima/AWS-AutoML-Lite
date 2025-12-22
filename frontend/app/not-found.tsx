import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-zinc-900 flex items-center justify-center p-4 transition-colors">
      <div className="bg-white dark:bg-zinc-800 rounded-lg shadow-xl dark:shadow-zinc-900/50 p-8 max-w-lg w-full text-center transition-colors">
        <div className="text-6xl mb-4">🔍</div>
        
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          Page Not Found
        </h1>
        
        <p className="text-gray-600 dark:text-gray-400 mb-6">
          The page you&apos;re looking for doesn&apos;t exist or has been moved.
        </p>

        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            href="/"
            className="px-6 py-3 bg-indigo-600 dark:bg-indigo-500 text-white rounded-lg font-medium hover:bg-indigo-700 dark:hover:bg-indigo-600 transition-colors cursor-pointer text-center"
          >
            Go to Home
          </Link>
          
          <Link
            href="/history"
            className="px-6 py-3 bg-gray-100 dark:bg-zinc-700 text-gray-700 dark:text-gray-200 rounded-lg font-medium hover:bg-gray-200 dark:hover:bg-zinc-600 transition-colors cursor-pointer text-center"
          >
            View History
          </Link>
        </div>

        {/* Quick links */}
        <div className="mt-8 pt-6 border-t border-gray-200 dark:border-zinc-700">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Popular pages:
          </h3>
          <div className="flex flex-wrap gap-2 justify-center">
            <Link
              href="/"
              className="px-3 py-1.5 text-sm bg-gray-100 dark:bg-zinc-700 text-gray-600 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-zinc-600 transition-colors"
            >
              📤 Upload Dataset
            </Link>
            <Link
              href="/history"
              className="px-3 py-1.5 text-sm bg-gray-100 dark:bg-zinc-700 text-gray-600 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-zinc-600 transition-colors"
            >
              📋 Training History
            </Link>
            <Link
              href="/compare"
              className="px-3 py-1.5 text-sm bg-gray-100 dark:bg-zinc-700 text-gray-600 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-zinc-600 transition-colors"
            >
              📊 Compare Models
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
