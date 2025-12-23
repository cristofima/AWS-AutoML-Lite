'use client';

import { DatasetMetadata } from '@/lib/api';

interface ColumnStatsDisplayProps {
  metadata: DatasetMetadata;
  selectedColumn?: string;
}

export default function ColumnStatsDisplay({ metadata, selectedColumn }: ColumnStatsDisplayProps) {
  // Calculate overall dataset statistics
  const totalColumns = metadata.columns.length;
  const numericColumns = Object.values(metadata.column_types).filter(t => t === 'numeric').length;
  const categoricalColumns = Object.values(metadata.column_types).filter(t => t === 'categorical').length;
  
  // Calculate missing values summary
  const columnsWithMissing = metadata.column_stats 
    ? Object.entries(metadata.column_stats).filter(([_, stats]) => stats.missing > 0)
    : [];
  
  // Get selected column stats
  const selectedStats = selectedColumn && metadata.column_stats 
    ? metadata.column_stats[selectedColumn] 
    : null;
  const selectedType = selectedColumn ? metadata.column_types[selectedColumn] : null;

  return (
    <div className="space-y-4">
      {/* Dataset Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-gray-50 dark:bg-zinc-900/50 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-gray-900 dark:text-white">
            {metadata.row_count.toLocaleString()}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">Rows</div>
        </div>
        <div className="bg-gray-50 dark:bg-zinc-900/50 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-gray-900 dark:text-white">
            {totalColumns}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">Columns</div>
        </div>
        <div className="bg-blue-50 dark:bg-blue-950/30 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
            {numericColumns}
          </div>
          <div className="text-xs text-blue-600 dark:text-blue-400">Numeric</div>
        </div>
        <div className="bg-purple-50 dark:bg-purple-950/30 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
            {categoricalColumns}
          </div>
          <div className="text-xs text-purple-600 dark:text-purple-400">Categorical</div>
        </div>
      </div>

      {/* Missing Values Warning */}
      {columnsWithMissing.length > 0 && (
        <div className="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-lg p-3">
          <div className="flex items-start gap-2">
            <span className="text-amber-500">⚠️</span>
            <div>
              <p className="text-sm font-medium text-amber-800 dark:text-amber-300">
                {columnsWithMissing.length} column{columnsWithMissing.length > 1 ? 's' : ''} with missing values
              </p>
              <p className="text-xs text-amber-700 dark:text-amber-400 mt-1">
                Missing values will be handled automatically during training (imputation).
              </p>
              <div className="mt-2 flex flex-wrap gap-1">
                {columnsWithMissing.slice(0, 5).map(([col, stats]) => (
                  <span 
                    key={col}
                    className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-amber-100 dark:bg-amber-900/50 text-amber-700 dark:text-amber-300"
                  >
                    {col}: {stats.missing_pct.toFixed(1)}%
                  </span>
                ))}
                {columnsWithMissing.length > 5 && (
                  <span className="text-xs text-amber-600 dark:text-amber-400">
                    +{columnsWithMissing.length - 5} more
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Selected Column Details */}
      {selectedColumn && selectedStats && (
        <div className="bg-indigo-50 dark:bg-indigo-950/30 border border-indigo-200 dark:border-indigo-800 rounded-lg p-4">
          <h4 className="text-sm font-semibold text-indigo-900 dark:text-indigo-300 mb-3 flex items-center gap-2">
            <span>📊</span> Target Column: {selectedColumn}
          </h4>
          
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-lg font-bold text-indigo-700 dark:text-indigo-300">
                {selectedStats.unique.toLocaleString()}
              </div>
              <div className="text-xs text-indigo-600 dark:text-indigo-400">Unique Values</div>
            </div>
            <div>
              <div className="text-lg font-bold text-indigo-700 dark:text-indigo-300">
                {selectedStats.missing}
              </div>
              <div className="text-xs text-indigo-600 dark:text-indigo-400">Missing</div>
            </div>
            <div>
              <div className={`text-lg font-bold ${
                selectedType === 'numeric' 
                  ? 'text-blue-600 dark:text-blue-400' 
                  : 'text-purple-600 dark:text-purple-400'
              }`}>
                {selectedType === 'numeric' ? '🔢' : '📝'}
              </div>
              <div className="text-xs text-indigo-600 dark:text-indigo-400">
                {selectedType === 'numeric' ? 'Numeric' : 'Categorical'}
              </div>
            </div>
          </div>

          {/* Unique Ratio Visualization */}
          <div className="mt-4">
            <div className="flex justify-between text-xs text-indigo-600 dark:text-indigo-400 mb-1">
              <span>Unique Value Ratio</span>
              <span>{((selectedStats.unique / metadata.row_count) * 100).toFixed(1)}%</span>
            </div>
            <div className="h-2 bg-indigo-200 dark:bg-indigo-900 rounded-full overflow-hidden">
              <div 
                className="h-full bg-indigo-600 dark:bg-indigo-400 rounded-full transition-all duration-300"
                style={{ width: `${Math.min((selectedStats.unique / metadata.row_count) * 100, 100)}%` }}
              />
            </div>
            <p className="text-xs text-indigo-500 dark:text-indigo-400 mt-1">
              {selectedStats.unique <= 10 
                ? '✓ Low cardinality - good for classification'
                : selectedStats.unique / metadata.row_count < 0.05
                  ? '✓ Moderate cardinality - likely classification'
                  : '✓ High cardinality - likely regression'
              }
            </p>
          </div>
        </div>
      )}

      {/* Column Types Distribution */}
      <div className="bg-gray-50 dark:bg-zinc-900/50 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
          Column Types Distribution
        </h4>
        <div className="space-y-2">
          {numericColumns > 0 && (
            <div>
              <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400 mb-1">
                <span>🔢 Numeric</span>
                <span>{numericColumns} ({((numericColumns / totalColumns) * 100).toFixed(0)}%)</span>
              </div>
              <div className="h-2 bg-gray-200 dark:bg-zinc-700 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-blue-500 dark:bg-blue-400 rounded-full"
                  style={{ width: `${(numericColumns / totalColumns) * 100}%` }}
                />
              </div>
            </div>
          )}
          {categoricalColumns > 0 && (
            <div>
              <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400 mb-1">
                <span>📝 Categorical</span>
                <span>{categoricalColumns} ({((categoricalColumns / totalColumns) * 100).toFixed(0)}%)</span>
              </div>
              <div className="h-2 bg-gray-200 dark:bg-zinc-700 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-purple-500 dark:bg-purple-400 rounded-full"
                  style={{ width: `${(categoricalColumns / totalColumns) * 100}%` }}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
