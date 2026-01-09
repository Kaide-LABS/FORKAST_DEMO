import { NextRequest, NextResponse } from 'next/server';

// Use local backend for development, production backend otherwise
// Use 127.0.0.1 instead of localhost to avoid IPv6 issues
const BACKEND_URL = process.env.NODE_ENV === 'development'
  ? 'http://127.0.0.1:8000'
  : 'https://forkast-api-84498540486.us-central1.run.app';

// Endpoints that require trailing slash for POST/PUT to avoid 307 redirects
// Only exact matches - NOT paths with IDs after them
const TRAILING_SLASH_ENDPOINTS = [
  'api/v1/competitors',
  'api/v1/alerts',
];

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  const pathStr = path.join('/');
  const searchParams = request.nextUrl.searchParams.toString();
  const url = `${BACKEND_URL}/${pathStr}${searchParams ? `?${searchParams}` : ''}`;

  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('Proxy GET error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch from backend' },
      { status: 500 }
    );
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  let pathStr = path.join('/');

  // Add trailing slash ONLY for exact endpoint matches (e.g., api/v1/competitors)
  // NOT for paths with IDs (e.g., api/v1/scraping/trigger/123)
  const needsTrailingSlash = TRAILING_SLASH_ENDPOINTS.includes(pathStr);
  if (needsTrailingSlash && !pathStr.endsWith('/')) {
    pathStr += '/';
  }

  // Include query parameters for POST requests
  const searchParams = request.nextUrl.searchParams.toString();
  const url = `${BACKEND_URL}/${pathStr}${searchParams ? `?${searchParams}` : ''}`;

  try {
    const body = await request.json().catch(() => null);

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: body ? JSON.stringify(body) : undefined,
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('Proxy POST error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch from backend' },
      { status: 500 }
    );
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  let pathStr = path.join('/');

  // Add trailing slash ONLY for exact endpoint matches
  const needsTrailingSlash = TRAILING_SLASH_ENDPOINTS.includes(pathStr);
  if (needsTrailingSlash && !pathStr.endsWith('/')) {
    pathStr += '/';
  }

  // Include query parameters for PUT requests
  const searchParams = request.nextUrl.searchParams.toString();
  const url = `${BACKEND_URL}/${pathStr}${searchParams ? `?${searchParams}` : ''}`;

  try {
    const body = await request.json().catch(() => null);

    const response = await fetch(url, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: body ? JSON.stringify(body) : undefined,
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('Proxy PUT error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch from backend' },
      { status: 500 }
    );
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  const pathStr = path.join('/');
  const url = `${BACKEND_URL}/${pathStr}`;

  try {
    const response = await fetch(url, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // DELETE might return 204 No Content
    if (response.status === 204) {
      return new NextResponse(null, { status: 204 });
    }

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('Proxy DELETE error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch from backend' },
      { status: 500 }
    );
  }
}
