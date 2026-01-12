import { auth } from '@/auth';
import { NextResponse, NextRequest } from 'next/server';

export default async function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  // Handle signout specially - fix Netlify Set-Cookie header ordering bug
  if (pathname.startsWith('/api/auth/signout')) {
    // @ts-expect-error auth returns Response, not NextResponse
    const resp: Response = await auth(req);

    // Remove all session cookies, then re-add one clear cookie
    const nonSessionCookies = resp.headers.getSetCookie().filter((cookie) => {
      return !cookie.startsWith('authjs.session-token') &&
             !cookie.startsWith('__Secure-authjs.session-token');
    });

    resp.headers.delete('Set-Cookie');

    for (const cookie of nonSessionCookies) {
      resp.headers.append('Set-Cookie', cookie);
    }

    // Add single clear cookie for both dev and prod
    resp.headers.append(
      'Set-Cookie',
      'authjs.session-token=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax'
    );
    resp.headers.append(
      'Set-Cookie',
      '__Secure-authjs.session-token=; Path=/; Max-Age=0; Secure; HttpOnly; SameSite=Lax'
    );

    return resp;
  }

  // Get auth state
  const session = await auth();
  const isLoggedIn = !!session;

  // Public routes that don't require authentication
  const publicRoutes = ['/sign-in', '/sign-up', '/api/auth'];
  const isPublicRoute = publicRoutes.some((route) => pathname.startsWith(route));

  // Allow API proxy for authenticated requests
  if (pathname.startsWith('/api/proxy')) {
    return NextResponse.next();
  }

  // Redirect to sign-in if not logged in and trying to access protected route
  if (!isLoggedIn && !isPublicRoute) {
    return NextResponse.redirect(new URL('/sign-in', req.url));
  }

  // Redirect to dashboard if logged in and trying to access auth pages
  if (isLoggedIn && (pathname === '/sign-in' || pathname === '/sign-up')) {
    return NextResponse.redirect(new URL('/', req.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    // Skip Next.js internals and static files
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    // Always run for API routes
    '/(api|trpc)(.*)',
  ],
};
