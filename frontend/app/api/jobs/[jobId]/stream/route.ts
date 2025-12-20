/**
 * SSE (Server-Sent Events) endpoint for real-time job status updates
 * 
 * Streams job status updates every 3 seconds until the job completes or fails.
 * This replaces client-side polling with server-push updates.
 * 
 * Usage:
 *   const eventSource = new EventSource('/api/jobs/{jobId}/stream');
 *   eventSource.onmessage = (event) => {
 *     const job = JSON.parse(event.data);
 *     // Update UI with job status
 *   };
 */

import { NextRequest } from 'next/server';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Poll interval in milliseconds
const POLL_INTERVAL = 3000;

// Maximum stream duration (5 minutes)
const MAX_DURATION = 5 * 60 * 1000;

interface JobDetails {
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  [key: string]: unknown;
}

async function fetchJobDetails(jobId: string): Promise<JobDetails | null> {
  try {
    const response = await fetch(`${API_URL}/jobs/${jobId}`, {
      cache: 'no-store',
    });
    
    if (!response.ok) {
      console.error(`Failed to fetch job ${jobId}: ${response.status}`);
      return null;
    }
    
    return await response.json();
  } catch (error) {
    console.error(`Error fetching job ${jobId}:`, error);
    return null;
  }
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ jobId: string }> }
) {
  const { jobId } = await params;
  
  // Create a readable stream for SSE
  const encoder = new TextEncoder();
  const startTime = Date.now();
  
  const stream = new ReadableStream({
    async start(controller) {
      // Send initial connection message
      controller.enqueue(encoder.encode(`: connected\n\n`));
      
      let isStreamActive = true;
      
      const poll = async () => {
        while (isStreamActive) {
          // Check if max duration exceeded
          if (Date.now() - startTime > MAX_DURATION) {
            const timeoutEvent = `event: timeout\ndata: {"message": "Stream timeout after 5 minutes"}\n\n`;
            controller.enqueue(encoder.encode(timeoutEvent));
            controller.close();
            break;
          }
          
          // Fetch job status
          const job = await fetchJobDetails(jobId);
          
          if (!job) {
            const errorEvent = `event: error\ndata: {"message": "Failed to fetch job status"}\n\n`;
            controller.enqueue(encoder.encode(errorEvent));
            // Continue polling even on error
            await new Promise(resolve => setTimeout(resolve, POLL_INTERVAL));
            continue;
          }
          
          // Send job status as SSE data
          const dataEvent = `data: ${JSON.stringify(job)}\n\n`;
          controller.enqueue(encoder.encode(dataEvent));
          
          // Check if job is terminal state
          if (job.status === 'completed' || job.status === 'failed') {
            // Send one final event indicating stream end
            const doneEvent = `event: done\ndata: {"status": "${job.status}"}\n\n`;
            controller.enqueue(encoder.encode(doneEvent));
            controller.close();
            break;
          }
          
          // Wait before next poll
          await new Promise(resolve => setTimeout(resolve, POLL_INTERVAL));
        }
      };
      
      // Start polling
      poll().catch((error) => {
        console.error('SSE polling error:', error);
        const errorEvent = `event: error\ndata: {"message": "Stream error"}\n\n`;
        controller.enqueue(encoder.encode(errorEvent));
        controller.close();
      });
      
      // Handle client disconnect
      request.signal.addEventListener('abort', () => {
        isStreamActive = false;
      });
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache, no-transform',
      'Connection': 'keep-alive',
      'X-Accel-Buffering': 'no', // Disable nginx buffering
    },
  });
}
