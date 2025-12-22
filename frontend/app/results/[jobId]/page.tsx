'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { getJobDetails, JobDetails, downloadWithFilename } from '@/lib/api';
import { formatMetric, getProblemTypeIcon, formatDateTime } from '@/lib/utils';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import Header from '@/components/Header';
import JobMetadataEditor from '@/components/JobMetadataEditor';

export default function ResultsPage() {
  const router = useRouter();
  const params = useParams();
  const jobId = params.jobId as string;

  const [job, setJob] = useState<JobDetails | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copiedDocker, setCopiedDocker] = useState(false);
  const [copiedPython, setCopiedPython] = useState(false);

  const handleCopyDocker = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopiedDocker(true);
    setTimeout(() => setCopiedDocker(false), 2000);
  };

  const handleCopyPython = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopiedPython(true);
    setTimeout(() => setCopiedPython(false), 2000);
  };

  // Generate Docker commands for model prediction (extracted to avoid duplication)
  const getDockerCommands = (jobId: string) => {
    const modelFile = `model_${jobId.slice(0, 8)}.pkl`;
    return `# Build prediction container (one time)
docker build -f scripts/Dockerfile.predict -t automl-predict .

# Show model info and required features
docker run --rm -v \${PWD}:/data automl-predict /data/${modelFile} --info

# Generate sample input JSON (auto-detects features)
docker run --rm -v \${PWD}:/data automl-predict /data/${modelFile} -g /data/sample_input.json

# Edit sample_input.json with your values, then predict
docker run --rm -v \${PWD}:/data automl-predict /data/${modelFile} --json /data/sample_input.json

# Batch predictions from CSV
docker run --rm -v \${PWD}:/data automl-predict /data/${modelFile} -i /data/test.csv -o /data/predictions.csv`;
  };

  useEffect(() => {
    const fetchResults = async () => {
      try {
        const jobData = await getJobDetails(jobId);
        
        if (jobData.status !== 'completed') {
          router.push(`/training/${jobId}`);
          return;
        }
        
        setJob(jobData);
        setIsLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load results');
        setIsLoading(false);
      }
    };

    fetchResults();
  }, [jobId, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-zinc-900 flex items-center justify-center transition-colors">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 dark:border-indigo-400 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading results...</p>
        </div>
      </div>
    );
  }

  if (error || !job || !job.metrics) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-zinc-900 flex items-center justify-center transition-colors">
        <div className="bg-white dark:bg-zinc-800 rounded-lg shadow-lg dark:shadow-zinc-900/50 p-8 max-w-md transition-colors">
          <div className="text-red-500 text-5xl mb-4">⚠️</div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Error</h2>
          <p className="text-gray-600 dark:text-gray-400 mb-4">{error || 'Results not available'}</p>
          <button
            onClick={() => router.push('/')}
            className="w-full py-2 px-4 bg-indigo-600 dark:bg-indigo-500 text-white rounded-lg hover:bg-indigo-700 dark:hover:bg-indigo-600 cursor-pointer transition-colors"
          >
            Go Home
          </button>
        </div>
      </div>
    );
  }

  // Prepare feature importance data for chart
  const featureImportanceData = job.metrics.feature_importance
    ? Object.entries(job.metrics.feature_importance)
        .sort(([, a], [, b]) => b - a)
        .slice(0, 10)
        .map(([name, value]) => ({ name, importance: value }))
    : [];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-zinc-900 transition-colors">
      <Header title="Training Results" showViewAllJobs />

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Success Banner */}
        <div className="bg-green-50 dark:bg-green-950/30 border-2 border-green-200 dark:border-green-800 rounded-lg p-6 transition-colors">
          <div className="flex items-center">
            <div className="text-5xl mr-4">✅</div>
            <div>
              <h2 className="text-xl font-bold text-green-900 dark:text-green-300 mb-1">Training Completed Successfully!</h2>
              <p className="text-green-700 dark:text-green-400">
                Your model has been trained and is ready to download
              </p>
            </div>
          </div>
        </div>

        {/* Job Info */}
        <div className="bg-white dark:bg-zinc-800 rounded-lg shadow dark:shadow-zinc-900/50 p-6 transition-colors">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Job Information</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-600 dark:text-gray-400">Problem Type:</span>
              <p className="font-medium text-gray-900 dark:text-gray-100 mt-1">
                {job.problem_type ? (
                  <>{getProblemTypeIcon(job.problem_type)} {job.problem_type.charAt(0).toUpperCase() + job.problem_type.slice(1)}</>
                ) : 'N/A'}
              </p>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">Target Column:</span>
              <p className="font-medium text-gray-900 dark:text-gray-100 mt-1">{job.target_column || 'N/A'}</p>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">Completed At:</span>
              <p className="text-gray-900 dark:text-gray-100 mt-1">
                {job.completed_at ? formatDateTime(job.completed_at) : 'N/A'}
              </p>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">Job ID:</span>
              <p className="font-mono text-xs text-gray-900 dark:text-gray-100 mt-1">{job.job_id}</p>
            </div>
          </div>
          
          {/* Tags & Notes Section */}
          <div className="mt-6 pt-6 border-t border-gray-200 dark:border-zinc-700">
            <JobMetadataEditor 
              job={job} 
              onUpdate={(updatedJob) => setJob(updatedJob)} 
            />
          </div>
        </div>

        {/* Metrics */}
        <div className="bg-white dark:bg-zinc-800 rounded-lg shadow dark:shadow-zinc-900/50 p-6 transition-colors">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Model Performance</h3>
          
          {job.problem_type === 'classification' ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              {job.metrics.accuracy !== undefined && (
                <div className="text-center">
                  <div className="text-3xl font-bold text-indigo-600 dark:text-indigo-400">
                    {formatMetric(job.metrics.accuracy * 100, 2)}%
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">Accuracy</div>
                </div>
              )}
              {job.metrics.f1_score !== undefined && (
                <div className="text-center">
                  <div className="text-3xl font-bold text-indigo-600 dark:text-indigo-400">
                    {formatMetric(job.metrics.f1_score, 3)}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">F1 Score</div>
                </div>
              )}
              {job.metrics.precision !== undefined && (
                <div className="text-center">
                  <div className="text-3xl font-bold text-indigo-600 dark:text-indigo-400">
                    {formatMetric(job.metrics.precision, 3)}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">Precision</div>
                </div>
              )}
              {job.metrics.recall !== undefined && (
                <div className="text-center">
                  <div className="text-3xl font-bold text-indigo-600 dark:text-indigo-400">
                    {formatMetric(job.metrics.recall, 3)}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">Recall</div>
                </div>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {job.metrics.r2_score !== undefined && (
                <div className="text-center">
                  <div className="text-3xl font-bold text-indigo-600 dark:text-indigo-400">
                    {formatMetric(job.metrics.r2_score, 4)}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">R² Score</div>
                </div>
              )}
              {job.metrics.rmse !== undefined && (
                <div className="text-center">
                  <div className="text-3xl font-bold text-indigo-600 dark:text-indigo-400">
                    {formatMetric(job.metrics.rmse, 4)}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">RMSE</div>
                </div>
              )}
              {job.metrics.mae !== undefined && (
                <div className="text-center">
                  <div className="text-3xl font-bold text-indigo-600 dark:text-indigo-400">
                    {formatMetric(job.metrics.mae, 4)}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">MAE</div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Feature Importance */}
        {featureImportanceData.length > 0 && (
          <div className="bg-white dark:bg-zinc-800 rounded-lg shadow dark:shadow-zinc-900/50 p-6 transition-colors">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Feature Importance (Top 10)</h3>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={featureImportanceData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="text-gray-200 dark:text-zinc-700" />
                  <XAxis type="number" stroke="currentColor" className="text-gray-600 dark:text-gray-400" />
                  <YAxis dataKey="name" type="category" width={120} stroke="currentColor" className="text-gray-600 dark:text-gray-400" />
                  <Tooltip contentStyle={{ backgroundColor: 'var(--card-bg)', borderColor: 'var(--card-border)' }} />
                  <Legend />
                  <Bar dataKey="importance" fill="#6366f1" name="Importance" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Download Section */}
        <div className="bg-white dark:bg-zinc-800 rounded-lg shadow dark:shadow-zinc-900/50 p-6 transition-colors">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Download Results</h3>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {job.model_download_url && (
              <button
                onClick={() => downloadWithFilename(job.model_download_url!, `model_${job.job_id.slice(0, 8)}.pkl`)}
                className="flex items-center justify-center space-x-2 px-6 py-4 bg-indigo-600 dark:bg-indigo-500 text-white rounded-lg hover:bg-indigo-700 dark:hover:bg-indigo-600 transition-colors cursor-pointer"
              >
                <span className="text-2xl">📦</span>
                <span className="font-medium">Download Model (.pkl)</span>
              </button>
            )}
            {job.onnx_model_download_url && (
              <button
                onClick={() => downloadWithFilename(job.onnx_model_download_url!, `model_${job.job_id.slice(0, 8)}.onnx`)}
                className="flex items-center justify-center space-x-2 px-6 py-4 bg-orange-600 dark:bg-orange-500 text-white rounded-lg hover:bg-orange-700 dark:hover:bg-orange-600 transition-colors cursor-pointer"
                title="ONNX format for cross-platform inference (C#, JavaScript, Rust, etc.)"
              >
                <span className="text-2xl">⚡</span>
                <span className="font-medium">Download Model (.onnx)</span>
              </button>
            )}
            {(job.eda_report_download_url || job.report_download_url) && (
              <button
                onClick={() => downloadWithFilename(
                  job.eda_report_download_url || job.report_download_url!, 
                  `eda_report_${job.job_id.slice(0, 8)}.html`
                )}
                className="flex items-center justify-center space-x-2 px-6 py-4 bg-green-600 dark:bg-green-500 text-white rounded-lg hover:bg-green-700 dark:hover:bg-green-600 transition-colors cursor-pointer"
              >
                <span className="text-2xl">📊</span>
                <span className="font-medium">EDA Report (.html)</span>
              </button>
            )}
            {job.training_report_download_url && (
              <button
                onClick={() => downloadWithFilename(
                  job.training_report_download_url!, 
                  `training_report_${job.job_id.slice(0, 8)}.html`
                )}
                className="flex items-center justify-center space-x-2 px-6 py-4 bg-purple-600 dark:bg-purple-500 text-white rounded-lg hover:bg-purple-700 dark:hover:bg-purple-600 transition-colors cursor-pointer"
              >
                <span className="text-2xl">🏆</span>
                <span className="font-medium">Training Report (.html)</span>
              </button>
            )}
          </div>
          
          {/* ONNX info tooltip */}
          {job.onnx_model_download_url && (
            <div className="mt-4 p-3 bg-orange-50 dark:bg-orange-950/30 border border-orange-200 dark:border-orange-800 rounded-lg">
              <p className="text-sm text-orange-800 dark:text-orange-300">
                <strong>💡 ONNX Format:</strong> Use for cross-platform inference in C#, JavaScript, Rust, Java, and more. 
                Run with <a href="https://onnxruntime.ai/" target="_blank" rel="noopener noreferrer" className="underline hover:no-underline">ONNX Runtime</a>.
              </p>
            </div>
          )}
        </div>

        {/* How to Use Your Model Section */}
        <div className="bg-white dark:bg-zinc-800 rounded-lg shadow dark:shadow-zinc-900/50 p-6 transition-colors">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">🚀 How to Use Your Model</h3>
          
          {/* Docker Method - Recommended */}
          <div className="mb-6">
            <div className="flex items-center mb-3">
              <span className="bg-green-100 dark:bg-green-900/50 text-green-800 dark:text-green-300 text-xs font-medium px-2 py-1 rounded mr-2">Recommended</span>
              <h4 className="font-medium text-gray-800 dark:text-gray-200">🐳 Using Docker (No setup required)</h4>
            </div>
            <div className="relative">
              <pre className="bg-gray-900 text-gray-100 rounded-lg p-4 overflow-x-auto text-sm font-mono">
                <code>{getDockerCommands(job.job_id)}</code>
              </pre>
              <button
                onClick={() => handleCopyDocker(getDockerCommands(job.job_id))}
                className={`absolute top-2 right-2 px-3 py-1 text-xs rounded transition-all cursor-pointer ${
                  copiedDocker 
                    ? 'bg-green-600 text-white' 
                    : 'bg-gray-700 hover:bg-gray-600 text-gray-200'
                }`}
              >
                {copiedDocker ? '✓ Copied!' : '📋 Copy'}
              </button>
            </div>
          </div>

          {/* Python Method - Alternative */}
          <div className="border-t dark:border-zinc-700 pt-4">
            <div className="flex items-center mb-3">
              <span className="bg-gray-100 dark:bg-zinc-700 text-gray-600 dark:text-gray-300 text-xs font-medium px-2 py-1 rounded mr-2">Alternative</span>
              <h4 className="font-medium text-gray-800 dark:text-gray-200">🐍 Using Python directly</h4>
            </div>
            <div className="p-4 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-lg mb-3">
              <p className="text-sm text-amber-800 dark:text-amber-300">
                <strong>⚠️ Note:</strong> Requires installing ML dependencies (~500MB): <code className="bg-amber-100 dark:bg-amber-900/50 px-1 rounded">pip install flaml[automl] lightgbm feature-engine scikit-learn pandas joblib</code>
              </p>
            </div>
            <details className="group">
              <summary className="cursor-pointer text-sm text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 font-medium">
                Show Python code →
              </summary>
              <div className="relative mt-3">
                <pre className="bg-gray-900 text-gray-100 rounded-lg p-4 overflow-x-auto text-sm font-mono">
                  <code>{`import joblib
import pandas as pd

# Load the model package
model_package = joblib.load('model_${job.job_id.slice(0, 8)}.pkl')

model = model_package['model']
preprocessor = model_package['preprocessor']
print(f"Features: {preprocessor.feature_columns}")

# Prepare your data
new_data = pd.DataFrame([{
    # Add your features here
}])

# Predict
X = new_data[preprocessor.feature_columns]
predictions = model.predict(X)
print(f"Predictions: {predictions}")`}</code>
                </pre>
                <button
                  onClick={() => {
                    const code = `import joblib
import pandas as pd

# Load the model package
model_package = joblib.load('model_${job.job_id.slice(0, 8)}.pkl')

model = model_package['model']
preprocessor = model_package['preprocessor']
print(f"Features: {preprocessor.feature_columns}")

# Prepare your data
new_data = pd.DataFrame([{
    # Add your features here
}])

# Predict
X = new_data[preprocessor.feature_columns]
predictions = model.predict(X)
print(f"Predictions: {predictions}")`;
                    handleCopyPython(code);
                  }}
                  className={`absolute top-2 right-2 px-3 py-1 text-xs rounded transition-all cursor-pointer ${
                    copiedPython 
                      ? 'bg-green-600 text-white' 
                      : 'bg-gray-700 hover:bg-gray-600 text-gray-200'
                  }`}
                >
                  {copiedPython ? '✓ Copied!' : '📋 Copy'}
                </button>
              </div>
            </details>
          </div>
        </div>

        {/* Actions */}
        <div className="flex space-x-4">
          <button
            onClick={() => router.push('/')}
            className="flex-1 py-3 px-6 border-2 border-indigo-600 dark:border-indigo-400 text-indigo-600 dark:text-indigo-400 rounded-lg font-medium hover:bg-indigo-50 dark:hover:bg-indigo-950/30 transition-colors cursor-pointer"
          >
            Train Another Model
          </button>
          <button
            onClick={() => router.push('/history')}
            className="flex-1 py-3 px-6 bg-gray-600 dark:bg-zinc-700 text-white rounded-lg font-medium hover:bg-gray-700 dark:hover:bg-zinc-600 transition-colors cursor-pointer"
          >
            View All Jobs
          </button>
        </div>
      </main>
    </div>
  );
}
