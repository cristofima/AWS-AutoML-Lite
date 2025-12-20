'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ThemeToggle } from './ThemeToggle';

interface HeaderProps {
  title?: string;
  showBackToUpload?: boolean;
  showViewHistory?: boolean;
  showViewAllJobs?: boolean;
  showCompare?: boolean;
}

export default function Header({ 
  title,
  showBackToUpload = false,
  showViewHistory = false,
  showViewAllJobs = false,
  showCompare = false,
}: HeaderProps) {
  const pathname = usePathname();
  const isHomePage = pathname === '/';

  return (
    <header className="bg-white dark:bg-zinc-900 shadow-sm dark:shadow-zinc-800/50 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center justify-between">
          {isHomePage ? (
            // Home page: show full branding
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center shadow-sm">
                <span className="text-2xl">⚡</span>
              </div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">AWS AutoML Lite</h1>
            </div>
          ) : (
            // Other pages: show logo + page title
            <div className="flex items-center space-x-4">
              <Link href="/" className="flex items-center space-x-2 hover:opacity-80 transition-opacity">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center shadow-sm">
                  <span className="text-lg">⚡</span>
                </div>
                <span className="text-lg font-semibold text-gray-700 dark:text-gray-300 hidden sm:inline">AutoML Lite</span>
              </Link>
              {title && (
                <>
                  <span className="text-gray-300 dark:text-gray-600">|</span>
                  <h1 className="text-xl font-bold text-gray-900 dark:text-white">{title}</h1>
                </>
              )}
            </div>
          )}

          {/* Navigation links + Dark Mode Toggle */}
          <div className="flex items-center space-x-4">
            <nav className="flex items-center space-x-4">
              {showViewHistory && (
                <Link 
                  href="/history" 
                  className="text-sm text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300 font-medium"
                >
                  View History →
                </Link>
              )}
              {showCompare && (
                <Link
                  href="/compare"
                  className="text-sm text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300 font-medium"
                >
                  📊 Compare Models
                </Link>
              )}
              {showBackToUpload && (
                <Link
                  href="/"
                  className="text-sm text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300 font-medium"
                >
                  ← Back to Upload
                </Link>
              )}
              {showViewAllJobs && (
                <Link
                  href="/history"
                  className="text-sm text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300 font-medium"
                >
                  View All Jobs →
                </Link>
              )}
            </nav>
            <ThemeToggle />
          </div>
        </div>
      </div>
    </header>
  );
}
