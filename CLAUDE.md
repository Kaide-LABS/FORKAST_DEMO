# FORKAST DEMO - Project Instructions

## Project Overview
Forkast is a food delivery aggregation demo with:
- **Frontend**: Next.js app deployed on Netlify
- **Backend**: FastAPI on Google Cloud Run
- **Scraper**: UberEats scraper using Browserless.io for browser automation

## Current Priorities
1. Add more competitors to enrich market data
2. Consider Cloud SQL for persistent production database (SQLite resets on Cloud Run redeploy)
3. Add Chicken-focused competitors for that category comparison

## Known Issues / Context
- Browserless.io free tier has 60-second session limits - scraper must be time-aware
- Cloud Run URL changed to `forkast-api-84498540486.us-central1.run.app`
- AI category mapping uses autonomous semantic matching

## Architecture Decisions
- Using Browserless.io for headless browser automation (avoid local Chrome dependency)
- Frontend uses API proxy route (`/api/proxy`) to avoid CORS issues in browser
- Server-side code uses direct backend URL

## Deployment
- Frontend: `npx netlify deploy --prod` from `/frontend` directory
- Backend: `gcloud run deploy` from `/backend` directory

## Session Handoff Notes
Last updated: 2026-01-10
Status: Clerk authentication integrated, awaiting API keys

### Completed This Session:
1. **Implemented multi-tenancy** - Added `tenant_id` to all backend models and routers
2. **Integrated Clerk authentication** for the frontend:
   - Installed `@clerk/nextjs` package
   - Created `/sign-in` and `/sign-up` pages with Clerk components
   - Added `ClerkProvider` to root layout
   - Created middleware to protect authenticated routes
   - Added `UserButton` to Sidebar for user management
3. **Updated API proxy** to use Clerk user ID as tenant ID automatically
4. **Created server-config.ts** with `getServerApiHeaders()` for server-side auth
5. **Restructured app** using Next.js route groups: `(auth)` and `(dashboard)`

### Files Modified/Created:
- `src/middleware.ts` - NEW: Clerk route protection
- `src/app/layout.tsx` - Minimal root with ClerkProvider
- `src/app/(auth)/layout.tsx` - NEW: Auth pages layout (no sidebar)
- `src/app/(auth)/sign-in/[[...sign-in]]/page.tsx` - NEW
- `src/app/(auth)/sign-up/[[...sign-up]]/page.tsx` - NEW
- `src/app/(dashboard)/layout.tsx` - NEW: Dashboard with Sidebar
- `src/components/Sidebar.tsx` - Added UserButton
- `src/app/api/proxy/[...path]/route.ts` - Uses Clerk auth for tenant
- `src/lib/server-config.ts` - NEW: Server-side auth helpers
- `.env.example` - Added Clerk env vars

### Current State:
- Code is complete but **requires Clerk API keys to function**
- Build will fail until user creates Clerk account and adds keys

### Next Steps (User Action Required):
1. Create Clerk account at https://clerk.com
2. Get API keys from Clerk dashboard
3. Create `.env.local` with:
   ```
   NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
   CLERK_SECRET_KEY=sk_test_...
   NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
   NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
   NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/
   NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/
   ```
4. Add same env vars to Netlify for production
5. Test authentication flow locally
6. Deploy to Netlify
