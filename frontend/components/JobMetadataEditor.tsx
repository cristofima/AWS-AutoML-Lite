'use client';

import { useState, useRef, useEffect } from 'react';
import { updateJobMetadata, JobDetails } from '@/lib/api';

interface JobMetadataEditorProps {
  job: JobDetails;
  onUpdate: (updatedJob: JobDetails) => void;
  compact?: boolean;  // For use in tables/lists
}

export default function JobMetadataEditor({ job, onUpdate, compact = false }: JobMetadataEditorProps) {
  const [isEditingTags, setIsEditingTags] = useState(false);
  const [isEditingNotes, setIsEditingNotes] = useState(false);
  const [tags, setTags] = useState<string[]>(job.tags || []);
  const [notes, setNotes] = useState(job.notes || '');
  const [newTag, setNewTag] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const tagInputRef = useRef<HTMLInputElement>(null);
  const notesInputRef = useRef<HTMLTextAreaElement>(null);

  // Focus input when editing starts
  useEffect(() => {
    if (isEditingTags && tagInputRef.current) {
      tagInputRef.current.focus();
    }
  }, [isEditingTags]);

  useEffect(() => {
    if (isEditingNotes && notesInputRef.current) {
      notesInputRef.current.focus();
    }
  }, [isEditingNotes]);

  const handleAddTag = () => {
    const trimmedTag = newTag.trim().toLowerCase();
    if (trimmedTag && !tags.includes(trimmedTag) && tags.length < 10) {
      setTags([...tags, trimmedTag]);
      setNewTag('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter(t => t !== tagToRemove));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag();
    }
  };

  const handleSaveTags = async () => {
    setIsSaving(true);
    setError(null);
    try {
      const updatedJob = await updateJobMetadata(job.job_id, { tags });
      onUpdate(updatedJob);
      setIsEditingTags(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save tags');
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveNotes = async () => {
    setIsSaving(true);
    setError(null);
    try {
      const updatedJob = await updateJobMetadata(job.job_id, { notes: notes || undefined });
      onUpdate(updatedJob);
      setIsEditingNotes(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save notes');
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancelTags = () => {
    setTags(job.tags || []);
    setNewTag('');
    setIsEditingTags(false);
    setError(null);
  };

  const handleCancelNotes = () => {
    setNotes(job.notes || '');
    setIsEditingNotes(false);
    setError(null);
  };

  // Compact view for history table
  if (compact) {
    return (
      <div className="flex flex-wrap gap-1">
        {tags.length > 0 ? (
          tags.map(tag => (
            <span
              key={tag}
              className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300"
            >
              {tag}
            </span>
          ))
        ) : (
          <span className="text-xs text-gray-400 dark:text-gray-500">No tags</span>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Tags Section */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">Tags</h4>
          {!isEditingTags && (
            <button
              onClick={() => setIsEditingTags(true)}
              className="text-xs text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 cursor-pointer"
            >
              ✏️ Edit
            </button>
          )}
        </div>

        {isEditingTags ? (
          <div className="space-y-2">
            <div className="flex flex-wrap gap-1 mb-2">
              {tags.map(tag => (
                <span
                  key={tag}
                  className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300"
                >
                  {tag}
                  <button
                    onClick={() => handleRemoveTag(tag)}
                    className="ml-1 text-indigo-500 hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-200 cursor-pointer"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
            
            <div className="flex gap-2">
              <input
                ref={tagInputRef}
                type="text"
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Add tag..."
                maxLength={50}
                className="flex-1 px-3 py-1.5 text-sm border border-gray-300 dark:border-zinc-600 rounded-lg bg-white dark:bg-zinc-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 focus:border-transparent"
              />
              <button
                onClick={handleAddTag}
                disabled={!newTag.trim() || tags.length >= 10}
                className="px-3 py-1.5 text-sm bg-gray-100 dark:bg-zinc-600 text-gray-700 dark:text-gray-200 rounded-lg hover:bg-gray-200 dark:hover:bg-zinc-500 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
              >
                Add
              </button>
            </div>
            
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {tags.length}/10 tags • Press Enter to add
            </p>
            
            <div className="flex gap-2 mt-2">
              <button
                onClick={handleSaveTags}
                disabled={isSaving}
                className="px-3 py-1.5 text-sm bg-indigo-600 dark:bg-indigo-500 text-white rounded-lg hover:bg-indigo-700 dark:hover:bg-indigo-600 disabled:opacity-50 cursor-pointer"
              >
                {isSaving ? 'Saving...' : 'Save'}
              </button>
              <button
                onClick={handleCancelTags}
                disabled={isSaving}
                className="px-3 py-1.5 text-sm bg-gray-100 dark:bg-zinc-600 text-gray-700 dark:text-gray-200 rounded-lg hover:bg-gray-200 dark:hover:bg-zinc-500 cursor-pointer"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div className="flex flex-wrap gap-1">
            {tags.length > 0 ? (
              tags.map(tag => (
                <span
                  key={tag}
                  className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300"
                >
                  {tag}
                </span>
              ))
            ) : (
              <span className="text-sm text-gray-400 dark:text-gray-500">No tags added</span>
            )}
          </div>
        )}
      </div>

      {/* Notes Section */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">Notes</h4>
          {!isEditingNotes && (
            <button
              onClick={() => setIsEditingNotes(true)}
              className="text-xs text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 cursor-pointer"
            >
              ✏️ Edit
            </button>
          )}
        </div>

        {isEditingNotes ? (
          <div className="space-y-2">
            <textarea
              ref={notesInputRef}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add notes about this training run..."
              maxLength={1000}
              rows={3}
              className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-zinc-600 rounded-lg bg-white dark:bg-zinc-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 focus:border-transparent resize-none"
            />
            
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {notes.length}/1000 characters
            </p>
            
            <div className="flex gap-2">
              <button
                onClick={handleSaveNotes}
                disabled={isSaving}
                className="px-3 py-1.5 text-sm bg-indigo-600 dark:bg-indigo-500 text-white rounded-lg hover:bg-indigo-700 dark:hover:bg-indigo-600 disabled:opacity-50 cursor-pointer"
              >
                {isSaving ? 'Saving...' : 'Save'}
              </button>
              <button
                onClick={handleCancelNotes}
                disabled={isSaving}
                className="px-3 py-1.5 text-sm bg-gray-100 dark:bg-zinc-600 text-gray-700 dark:text-gray-200 rounded-lg hover:bg-gray-200 dark:hover:bg-zinc-500 cursor-pointer"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {notes || <span className="text-gray-400 dark:text-gray-500">No notes added</span>}
          </p>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/30 p-2 rounded">
          {error}
        </div>
      )}
    </div>
  );
}
