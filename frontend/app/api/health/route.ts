/**
 * Health check endpoint for Amplify
 * Returns 200 OK immediately without any heavy processing
 */
export async function GET() {
  return Response.json({ status: 'ok' }, { status: 200 });
}
