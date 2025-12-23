'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { getJobDetails, JobDetails, downloadWithFilename, deployModel, makePrediction, PredictionResponse } from '@/lib/api';
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
  
  // Deploy state
  const [isDeploying, setIsDeploying] = useState(false);
  const [deployError, setDeployError] = useState<string | null>(null);
  
  // Prediction playground state
  const [featureInputs, setFeatureInputs] = useState<Record<string, string>>({});
  const [predictionResult, setPredictionResult] = useState<PredictionResponse | null>(null);
  const [isPredicting, setIsPredicting] = useState(false);
  const [predictionError, setPredictionError] = useState<string | null>(null);

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

  // Handle deploy/undeploy
  const handleDeploy = async (deploy: boolean) => {
    setIsDeploying(true);
    setDeployError(null);
    
    try {
      await deployModel(jobId, deploy);
      // Refresh job data
      const updatedJob = await getJobDetails(jobId);
      setJob(updatedJob);
      
      // Initialize feature inputs if deploying
      if (deploy && updatedJob.preprocessing_info?.feature_columns) {
        const initialInputs: Record<string, string> = {};
        updatedJob.preprocessing_info.feature_columns.forEach(col => {
          initialInputs[col] = '';
        });
        setFeatureInputs(initialInputs);
      }
    } catch (err) {
      setDeployError(err instanceof Error ? err.message : 'Failed to deploy model');
    } finally {
      setIsDeploying(false);
    }
  };

  // Handle prediction
  const handlePredict = async () => {
    if (!job?.preprocessing_info?.feature_columns) return;
    
    setIsPredicting(true);
    setPredictionError(null);
    setPredictionResult(null);
    
    try {
      // Convert string inputs to numbers where possible
      const features: Record<string, number | string> = {};
      for (const [key, value] of Object.entries(featureInputs)) {
        const numValue = parseFloat(value);
        features[key] = isNaN(numValue) ? value : numValue;
      }
      
      const result = await makePrediction(jobId, features);
      setPredictionResult(result);
    } catch (err) {
      setPredictionError(err instanceof Error ? err.message : 'Prediction failed');
    } finally {
      setIsPredicting(false);
    }
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
      <div className="min-h-screen bg-gray-50 dark:bg-zinc-900 transition-colors">
        <Header title="Training Results" showViewAllJobs />
        <div className="flex items-center justify-center" style={{ minHeight: 'calc(100vh - 80px)' }}>
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 dark:border-indigo-400 mx-auto mb-4"></div>
            <p className="text-gray-600 dark:text-gray-400">Loading results...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !job || !job.metrics) {
    const isNotFound = error?.toLowerCase().includes('not found') || error?.toLowerCase().includes('404');
    
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-zinc-900 transition-colors">
        <Header title="Training Results" showViewAllJobs />
        <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="bg-white dark:bg-zinc-800 rounded-lg shadow-lg dark:shadow-zinc-900/50 p-8 text-center transition-colors">
            <div className="text-6xl mb-4">{isNotFound ? '🔍' : '⚠️'}</div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              {isNotFound ? 'Job Not Found' : 'Unable to Load Results'}
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-2">
              {isNotFound 
                ? 'The training job you\'re looking for doesn\'t exist or may have been deleted.'
                : error || 'Results not available yet. The training may still be in progress.'}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-500 mb-6 font-mono">
              Job ID: {jobId}
            </p>
            
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <button
                onClick={() => router.push('/history')}
                className="py-2 px-6 bg-indigo-600 dark:bg-indigo-500 text-white rounded-lg hover:bg-indigo-700 dark:hover:bg-indigo-600 cursor-pointer transition-colors font-medium"
              >
                View All Jobs
              </button>
              <button
                onClick={() => router.push('/')}
                className="py-2 px-6 bg-gray-200 dark:bg-zinc-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-zinc-600 cursor-pointer transition-colors font-medium"
              >
                Start New Training
              </button>
            </div>
            
            {!isNotFound && (
              <button
                onClick={() => window.location.reload()}
                className="mt-4 text-sm text-indigo-600 dark:text-indigo-400 hover:underline cursor-pointer"
              >
                ↻ Try Again
              </button>
            )}
          </div>
        </main>
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

        {/* Model Deployment & Prediction Playground */}
        {job.onnx_model_download_url && (
          <div className="bg-white dark:bg-zinc-800 rounded-lg shadow dark:shadow-zinc-900/50 p-6 transition-colors">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">🚀 Model Deployment & Predictions</h3>
            
            {/* Deploy/Undeploy Button */}
            <div className="mb-6">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-gray-800 dark:text-gray-200">Serverless Inference</h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {job.deployed 
                      ? 'Model is deployed and ready for predictions' 
                      : 'Deploy your model to enable serverless predictions via API'}
                  </p>
                </div>
                <button
                  onClick={() => handleDeploy(!job.deployed)}
                  disabled={isDeploying}
                  className={`px-6 py-2 rounded-lg font-medium transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed ${
                    job.deployed
                      ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 hover:bg-red-200 dark:hover:bg-red-900/50 border border-red-300 dark:border-red-700'
                      : 'bg-green-600 dark:bg-green-500 text-white hover:bg-green-700 dark:hover:bg-green-600'
                  }`}
                >
                  {isDeploying ? (
                    <span className="flex items-center">
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      {job.deployed ? 'Undeploying...' : 'Deploying...'}
                    </span>
                  ) : (
                    <span>{job.deployed ? '⏹️ Undeploy Model' : '🚀 Deploy Model'}</span>
                  )}
                </button>
              </div>
              
              {deployError && (
                <div className="mt-3 p-3 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-lg">
                  <p className="text-sm text-red-700 dark:text-red-300">{deployError}</p>
                </div>
              )}
              
              {job.deployed && (
                <div className="mt-3 p-3 bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800 rounded-lg">
                  <p className="text-sm text-green-700 dark:text-green-300">
                    <strong>✅ Model Deployed</strong> — API Endpoint: <code className="bg-green-100 dark:bg-green-900/50 px-1 rounded">POST /predict/{job.job_id}</code>
                  </p>
                </div>
              )}
            </div>
            
            {/* Prediction Playground - Only show when deployed */}
            {job.deployed && job.preprocessing_info?.feature_columns && (
              <div className="border-t dark:border-zinc-700 pt-6">
                <h4 className="font-medium text-gray-800 dark:text-gray-200 mb-4">🎮 Prediction Playground</h4>
                
                <div className="grid md:grid-cols-2 gap-6">
                  {/* Input Form */}
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                      Enter values for each feature to test your model:
                    </p>
                    <div className="space-y-3 max-h-80 overflow-y-auto pr-2">
                      {job.preprocessing_info.feature_columns.map((col) => (
                        <div key={col}>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            {col}
                          </label>
                          <input
                            type="text"
                            value={featureInputs[col] || ''}
                            onChange={(e) => setFeatureInputs(prev => ({ ...prev, [col]: e.target.value }))}
                            placeholder={`Enter ${col}`}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-zinc-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 dark:bg-zinc-700 dark:text-white transition-colors"
                          />
                        </div>
                      ))}
                    </div>
                    
                    <button
                      onClick={handlePredict}
                      disabled={isPredicting || Object.values(featureInputs).every(v => v === '')}
                      className="mt-4 w-full py-2 px-4 bg-indigo-600 dark:bg-indigo-500 text-white rounded-lg font-medium hover:bg-indigo-700 dark:hover:bg-indigo-600 transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isPredicting ? (
                        <span className="flex items-center justify-center">
                          <svg className="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          Predicting...
                        </span>
                      ) : (
                        '🔮 Make Prediction'
                      )}
                    </button>
                  </div>
                  
                  {/* Results Panel */}
                  <div className="bg-gray-50 dark:bg-zinc-900/50 rounded-lg p-4">
                    <h5 className="font-medium text-gray-800 dark:text-gray-200 mb-3">Prediction Result</h5>
                    
                    {predictionError && (
                      <div className="p-3 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-lg">
                        <p className="text-sm text-red-700 dark:text-red-300">{predictionError}</p>
                      </div>
                    )}
                    
                    {predictionResult && (
                      <div className="space-y-4">
                        <div className="text-center py-4">
                          <div className="text-4xl font-bold text-indigo-600 dark:text-indigo-400">
                            {typeof predictionResult.prediction === 'number' 
                              ? predictionResult.prediction.toFixed(4)
                              : predictionResult.prediction}
                          </div>
                          <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                            {job.problem_type === 'classification' ? 'Predicted Class' : 'Predicted Value'}
                          </div>
                        </div>
                        
                        {predictionResult.probability !== undefined && (
                          <div className="text-center">
                            <div className="text-lg font-semibold text-gray-800 dark:text-gray-200">
                              {(predictionResult.probability * 100).toFixed(1)}%
                            </div>
                            <div className="text-xs text-gray-500 dark:text-gray-500">Confidence</div>
                          </div>
                        )}
                        
                        {predictionResult.probabilities && Object.keys(predictionResult.probabilities).length > 0 && (
                          <div className="border-t dark:border-zinc-700 pt-3">
                            <p className="text-xs text-gray-500 dark:text-gray-500 mb-2">Class Probabilities:</p>
                            <div className="space-y-1">
                              {Object.entries(predictionResult.probabilities)
                                .sort(([, a], [, b]) => b - a)
                                .map(([cls, prob]) => (
                                  <div key={cls} className="flex justify-between text-sm">
                                    <span className="text-gray-700 dark:text-gray-300">{cls}</span>
                                    <span className="font-medium text-gray-900 dark:text-gray-100">
                                      {(prob * 100).toFixed(1)}%
                                    </span>
                                  </div>
                                ))}
                            </div>
                          </div>
                        )}
                        
                        <div className="border-t dark:border-zinc-700 pt-3 text-xs text-gray-500 dark:text-gray-500">
                          <div className="flex justify-between">
                            <span>Inference Time:</span>
                            <span>{predictionResult.inference_time_ms.toFixed(1)} ms</span>
                          </div>
                          <div className="flex justify-between mt-1">
                            <span>Model Type:</span>
                            <span>{predictionResult.model_type}</span>
                          </div>
                        </div>
                      </div>
                    )}
                    
                    {!predictionResult && !predictionError && (
                      <div className="text-center py-8 text-gray-500 dark:text-gray-500">
                        <div className="text-3xl mb-2">🔮</div>
                        <p className="text-sm">Enter feature values and click &quot;Make Prediction&quot;</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
            
            {/* Cost comparison info */}
            <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 rounded-lg">
              <h5 className="font-medium text-blue-800 dark:text-blue-300 mb-2">💡 Serverless vs SageMaker</h5>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="font-medium text-blue-700 dark:text-blue-400">Lambda Inference (this)</p>
                  <ul className="text-blue-600 dark:text-blue-400 mt-1 space-y-1">
                    <li>• $0 idle cost</li>
                    <li>• ~$0.0001 per prediction</li>
                    <li>• 1-3s cold start</li>
                  </ul>
                </div>
                <div>
                  <p className="font-medium text-blue-700 dark:text-blue-400">SageMaker Endpoint</p>
                  <ul className="text-blue-600 dark:text-blue-400 mt-1 space-y-1">
                    <li>• ~$50-100/month idle</li>
                    <li>• ~$0.0001 per prediction</li>
                    <li>• No cold start</li>
                  </ul>
                </div>
              </div>
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
