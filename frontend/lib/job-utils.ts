
import { JobDetails } from './api';

/**
 * Merges incoming JobDetails with current JobDetails, preserving existing presigned URLs
 * from the current state if they are missing or "refreshed" in the incoming state.
 * 
 * This prevents UI flicker for large files/downloads when only metadata (tags/notes) changes.
 * 
 * Strategy:
 * 1. Use incoming job as the base (it has latest status, tags, etc.)
 * 2. For each URL field:
 *    - If incoming has it -> Accept it (or optionally prefer current if still valid)
 *    - If incoming is missing it but current has it -> Keep current (preservation)
 */
export function mergeJobPreservingUrls(current: JobDetails | null, incoming: JobDetails): JobDetails {
  if (!current) return incoming;

  // Clone incoming to avoid mutation
  const merged = { ...incoming };

  // List of URL fields to preserve
  const urlFields: (keyof JobDetails)[] = [
    'model_download_url',
    'onnx_model_download_url',
    'eda_report_download_url',
    'training_report_download_url',
    'report_download_url',
  ];

  urlFields.forEach((field) => {
    const currentUrl = current[field] as string | undefined;
    const incomingUrl = incoming[field] as string | undefined;

    // Preserve current URL only if incoming is missing (e.g. partial updates)
    // If incoming has a URL, we trust it's newer/valid and let it overwrite.
    if (!incomingUrl && currentUrl) {
      (merged as any)[field] = currentUrl;
    }
  });

  return merged;
}
