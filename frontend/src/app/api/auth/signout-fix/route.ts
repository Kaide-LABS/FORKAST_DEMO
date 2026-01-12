import { NextResponse } from 'next/server';

/**
 * Custom signout endpoint that properly clears session cookies.
 *
 * Workaround for Netlify bug where Set-Cookie headers are reversed,
 * causing NextAuth's dual-cookie signout to fail.
 *
 * See: https://github.com/nextauthjs/next-auth/issues/12909
 */
export async function POST() {
  const response = NextResponse.json({ success: true });

  // Clear all possible session cookie variants
  const cookieOptions = 'Path=/; Max-Age=0; HttpOnly; SameSite=Lax';
  const secureCookieOptions = `${cookieOptions}; Secure`;

  // Standard cookies (development)
  response.headers.append('Set-Cookie', `authjs.session-token=; ${cookieOptions}`);
  response.headers.append('Set-Cookie', `authjs.callback-url=; ${cookieOptions}`);
  response.headers.append('Set-Cookie', `authjs.csrf-token=; ${cookieOptions}`);

  // Secure cookies (production HTTPS)
  response.headers.append('Set-Cookie', `__Secure-authjs.session-token=; ${secureCookieOptions}`);
  response.headers.append('Set-Cookie', `__Secure-authjs.callback-url=; ${secureCookieOptions}`);
  response.headers.append('Set-Cookie', `__Host-authjs.csrf-token=; ${secureCookieOptions}`);

  return response;
}
