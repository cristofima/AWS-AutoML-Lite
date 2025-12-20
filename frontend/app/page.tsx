import FileUpload from '@/components/FileUpload';
import Header from '@/components/Header';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-zinc-900 dark:to-zinc-800 transition-colors">
      <Header showViewHistory />

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
            Train ML Models in Minutes
          </h2>
          <p className="text-xl text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
            Upload your CSV file, select a target column, and let AutoML find the best model for you. 
            No coding required.
          </p>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-6 mb-12">
          <div className="bg-white dark:bg-zinc-800 rounded-lg p-6 shadow-sm dark:shadow-zinc-900/50 transition-colors">
            <div className="text-3xl mb-3">📤</div>
            <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Easy Upload</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Drag and drop your CSV file or click to browse
            </p>
          </div>
          <div className="bg-white dark:bg-zinc-800 rounded-lg p-6 shadow-sm dark:shadow-zinc-900/50 transition-colors">
            <div className="text-3xl mb-3">🤖</div>
            <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Auto Detection</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Automatically detects problem type and preprocesses data
            </p>
          </div>
          <div className="bg-white dark:bg-zinc-800 rounded-lg p-6 shadow-sm dark:shadow-zinc-900/50 transition-colors">
            <div className="text-3xl mb-3">📊</div>
            <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Full Reports</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Get metrics, feature importance, and EDA reports
            </p>
          </div>
        </div>

        {/* Upload Section */}
        <div className="bg-white dark:bg-zinc-800 rounded-lg shadow-lg dark:shadow-zinc-900/50 p-8 transition-colors">
          <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Upload Your Dataset</h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Supported format: CSV files (max 100MB)
          </p>
          <FileUpload />
        </div>

        {/* Info Section */}
        <div className="mt-8 bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 rounded-lg p-6 transition-colors">
          <h4 className="font-semibold text-blue-900 dark:text-blue-300 mb-2">💡 How it works</h4>
          <ol className="list-decimal list-inside space-y-2 text-sm text-blue-800 dark:text-blue-400">
            <li>Upload your CSV file with labeled data</li>
            <li>Select the target column you want to predict</li>
            <li>We'll automatically detect the problem type and train multiple models</li>
            <li>Download your trained model and view detailed metrics</li>
          </ol>
        </div>
      </main>

      {/* Footer */}
      <footer className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 mt-12">
        <div className="text-center text-gray-600 dark:text-gray-400 text-sm">
          <p>Built with FastAPI, FLAML, and AWS Batch</p>
          <p className="mt-1">~$10-25/month operational cost</p>
        </div>
      </footer>
    </div>
  );
}
