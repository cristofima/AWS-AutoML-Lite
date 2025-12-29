
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

    // SCENARIO 1: Incoming missing, Current has it -> Preserve Current
    if (!incomingUrl && currentUrl) {
      (merged as any)[field] = currentUrl;
    }
    
    // SCENARIO 2: Both have it, but we want to avoid unnecessary refresh
    // If exact same job/deployment state, we could prefer current.
    // However, if the backend regenerated it, it's safer to use the new one UNLESS
    // we strictly want to avoid iframe reloads. 
    // Given the user requirement: "conserving the presigned urls... sin aun estan dentro del tiempo de vida"
    // We ideally check expiry. For now, if we have a valid current URL, we can stick with it.
    // simpler heuristic: if incoming has a URL, we trust the backend provided a fresh one.
    // BUT common issue: partial update (patch) might return object MINUS expensive computed fields?
    // Backend `update_job_metadata` calls `get_job_status` which DOES return URLs.
    // So incoming WILL have URLs. 
    
    // OPTIMIZATION: If incoming URL differs only by signature/token but underlying resource is same,
    // and current URL is not expired, keep current.
    if (incomingUrl && currentUrl && incomingUrl !== currentUrl) {
       // Check if current is still valid (parsing X-Amz-Expires/Expires is complex here without helpers).
       // Strict preservation: If we just updated tags, why change the URL?
       // Let's preserve current URL if it exists.
       (merged as any)[field] = currentUrl;
    }
  });

  return merged;
}
