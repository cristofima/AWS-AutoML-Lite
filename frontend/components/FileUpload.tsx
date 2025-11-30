'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { uploadAndConfirm } from '@/lib/api';
import { validateCSV, formatBytes } from '@/lib/utils';

export default function FileUpload() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      const validation = validateCSV(droppedFile);
      if (!validation.valid) {
        setError(validation.error || 'Invalid file');
        return;
      }
      setFile(droppedFile);
      setError(null);
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      const validation = validateCSV(selectedFile);
      if (!validation.valid) {
        setError(validation.error || 'Invalid file');
        return;
      }
      setFile(selectedFile);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    setError(null);

    try {
      const metadata = await uploadAndConfirm(file);
      
      // Redirect to configuration page
      router.push(`/configure/${metadata.dataset_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload file');
      setIsUploading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Drag & Drop Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          border-2 border-dashed rounded-lg p-12 text-center transition-colors
          ${isDragging ? 'border-indigo-500 bg-indigo-50' : 'border-gray-300 hover:border-gray-400'}
          ${file ? 'bg-gray-50' : ''}
        `}
      >
        {!file ? (
          <>
            <div className="text-5xl mb-4">📁</div>
            <p className="text-lg font-medium text-gray-700 mb-2">
              Drag and drop your CSV file here
            </p>
            <p className="text-sm text-gray-500 mb-4">or</p>
            <label className="inline-block">
              <input
                type="file"
                accept=".csv"
                onChange={handleFileSelect}
                className="hidden"
              />
              <span className="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 cursor-pointer inline-block">
                Browse Files
              </span>
            </label>
            <p className="text-xs text-gray-500 mt-4">
              Maximum file size: 100MB
            </p>
          </>
        ) : (
          <div className="space-y-3">
            <div className="text-5xl">✅</div>
            <div>
              <p className="font-medium text-gray-900">{file.name}</p>
              <p className="text-sm text-gray-500">{formatBytes(file.size)}</p>
            </div>
            <button
              onClick={() => setFile(null)}
              className="text-sm text-red-600 hover:text-red-700"
            >
              Remove file
            </button>
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          <p className="text-sm">{error}</p>
        </div>
      )}

      {/* Upload Button */}
      {file && (
        <button
          onClick={handleUpload}
          disabled={isUploading}
          className={`
            w-full py-3 px-6 rounded-lg font-medium text-white
            ${isUploading 
              ? 'bg-gray-400 cursor-not-allowed' 
              : 'bg-indigo-600 hover:bg-indigo-700'
            }
            transition-colors
          `}
        >
          {isUploading ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Uploading and analyzing...
            </span>
          ) : (
            'Continue to Configuration'
          )}
        </button>
      )}
    </div>
  );
}
