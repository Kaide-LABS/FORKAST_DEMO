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
Last updated: 2026-01-12
Status: Sign out fix for Netlify deployed

### Completed This Session:
1. **Fixed sign out functionality (initial)** - NextAuth v5 issue where `signOut({ callbackUrl })` doesn't properly clear client session state. Fixed by using `redirect: false` + manual `router.push()` + `router.refresh()`.
2. **Fixed sign out on Netlify (production)** - Netlify has a bug where Set-Cookie headers are returned in reversed order, preventing session clearing. Added manual cookie expiration before signOut call.
3. **Updated global CLAUDE.md** - Added repo indexing step to session handoff protocol.
4. **Deployed to Netlify** - Live at https://forkast-dashboard.netlify.app
5. **Pushed to GitHub** - commits 0c418a5, a34dc93

### Key Files:
- `src/components/Sidebar.tsx` - Sign out button with Netlify-compatible handler (lines 19-27)

### Known Issue (Netlify):
Netlify returns Set-Cookie headers in reversed order (violates RFC 6265). Workaround: manually clear `authjs.session-token` and `__Secure-authjs.session-token` cookies before calling signOut.

### Current State:
- **Frontend**: https://forkast-dashboard.netlify.app (with auth)
- **Backend**: https://forkast-api-84498540486.us-central1.run.app
- Sign in and sign out both working correctly in production

### Next Steps:
- Add more competitors for richer data
- Consider Cloud SQL for persistent database
- Optional: Add Google/GitHub OAuth providers to NextAuth
