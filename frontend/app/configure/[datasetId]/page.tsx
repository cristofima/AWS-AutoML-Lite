'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { DatasetMetadata, startTraining, getDatasetMetadata } from '@/lib/api';
import { getProblemTypeIcon, getProblemTypeDescription } from '@/lib/utils';
import Header from '@/components/Header';

export default function ConfigurePage() {
  const router = useRouter();
  const params = useParams();
  const datasetId = params.datasetId as string;

  const [metadata, setMetadata] = useState<DatasetMetadata | null>(null);
  const [selectedTarget, setSelectedTarget] = useState<string>('');
  const [timeBudget, setTimeBudget] = useState<number>(300);
  const [isLoading, setIsLoading] = useState(true);
  const [isStarting, setIsStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Detect problem type based on column type
  const detectProblemType = (columnName: string): 'classification' | 'regression' => {
    if (!metadata) return 'regression';
    const columnType = metadata.column_types[columnName];
    return columnType === 'categorical' ? 'classification' : 'regression';
  };

  useEffect(() => {
    const fetchMetadata = async () => {
      try {
        const data = await getDatasetMetadata(datasetId);
        setMetadata(data);
        setIsLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load dataset metadata');
        setIsLoading(false);
      }
    };

    fetchMetadata();
  }, [datasetId]);

  const handleStartTraining = async () => {
    if (!selectedTarget) {
      setError('Please select a target column');
      return;
    }

    setIsStarting(true);
    setError(null);

    try {
      const response = await startTraining({
        dataset_id: datasetId,
        target_column: selectedTarget,
        config: {
          time_budget: timeBudget,
        },
      });

      // Redirect to training status page
      router.push(`/training/${response.job_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start training');
      setIsStarting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dataset information...</p>
        </div>
      </div>
    );
  }

  if (error && !metadata) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-500 text-4xl mb-4">❌</div>
          <p className="text-gray-900 font-medium mb-2">Failed to load dataset</p>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => router.push('/')}
            className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 cursor-pointer"
          >
            Back to Home
          </button>
        </div>
      </div>
    );
  }

  const columns = metadata?.columns || [];
  const columnTypes = metadata?.column_types || {};
  const detectedProblemType = selectedTarget ? detectProblemType(selectedTarget) : null;

  return (
    <div className="min-h-screen bg-gray-50">
      <Header title="Configure Training" showBackToUpload />

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow-lg p-8 space-y-8">
          {/* Dataset Info */}
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Dataset Information</h2>
            <div className="bg-gray-50 rounded-lg p-4 space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Dataset ID:</span>
                <span className="font-mono text-gray-900">{datasetId}</span>
              </div>
              {metadata && (
                <>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Filename:</span>
                    <span className="text-gray-900">{metadata.filename}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Rows:</span>
                    <span className="text-gray-900">{metadata.row_count.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Columns:</span>
                    <span className="text-gray-900">{columns.length}</span>
                  </div>
                </>
              )}
              <div className="flex justify-between">
                <span className="text-gray-600">Status:</span>
                <span className="text-green-600">✓ Uploaded and analyzed</span>
              </div>
            </div>
          </div>

          {/* Column Selection */}
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Select Target Column</h2>
            <p className="text-gray-600 mb-4">
              Choose the column you want to predict. We'll automatically detect if it's a classification or regression problem.
            </p>

            <div className="space-y-3 max-h-96 overflow-y-auto">
              {columns.map((column) => (
                <label
                  key={column}
                  className={`flex items-center p-4 border-2 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors ${
                    selectedTarget === column ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200'
                  }`}
                >
                  <input
                    type="radio"
                    name="target"
                    value={column}
                    checked={selectedTarget === column}
                    onChange={(e) => setSelectedTarget(e.target.value)}
                    className="w-4 h-4 text-indigo-600"
                  />
                  <div className="ml-3 flex-1">
                    <div className="font-medium text-gray-900">{column}</div>
                    <div className="text-sm text-gray-500">
                      Type: {columnTypes[column] || 'unknown'}
                    </div>
                  </div>
                  <div className="text-xs px-2 py-1 rounded bg-gray-200 text-gray-700">
                    {columnTypes[column] === 'categorical' ? 'Classification' : 'Regression'}
                  </div>
                </label>
              ))}

              {columns.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  No columns found in dataset
                </div>
              )}

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm text-blue-800">
                  💡 <strong>Tip:</strong> Select a column that contains the values you want to predict. 
                  Make sure it has no missing values or they will be handled automatically.
                </p>
              </div>
            </div>
          </div>

          {/* Problem Type Detection */}
          {selectedTarget && detectedProblemType && (
            <div className="bg-indigo-50 border-2 border-indigo-200 rounded-lg p-6">
              <div className="flex items-start">
                <div className="text-4xl mr-4">{getProblemTypeIcon(detectedProblemType)}</div>
                <div>
                  <h3 className="text-lg font-semibold text-indigo-900 mb-2">
                    Detected Problem Type: {detectedProblemType === 'classification' ? 'Classification' : 'Regression'}
                  </h3>
                  <p className="text-indigo-700 text-sm">
                    {getProblemTypeDescription(detectedProblemType)}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Advanced Settings */}
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Training Configuration</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Time Budget (seconds)
                </label>
                <input
                  type="number"
                  value={timeBudget}
                  onChange={(e) => setTimeBudget(parseInt(e.target.value))}
                  min="60"
                  max="3600"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Recommended: 300 seconds for small datasets, 600-1800 for larger ones
                </p>
              </div>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              <p className="text-sm">{error}</p>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex space-x-4">
            <button
              onClick={() => router.push('/')}
              className="flex-1 py-3 px-6 border-2 border-gray-300 rounded-lg font-medium text-gray-700 hover:bg-gray-50 transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              onClick={handleStartTraining}
              disabled={!selectedTarget || isStarting}
              className={`
                flex-1 py-3 px-6 rounded-lg font-medium text-white cursor-pointer
                ${!selectedTarget || isStarting
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-indigo-600 hover:bg-indigo-700'
                }
                transition-colors
              `}
            >
              {isStarting ? 'Starting Training...' : 'Start Training'}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
