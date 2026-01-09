# FORKAST DEMO - Project Instructions

## Project Overview
Forkast is a food delivery aggregation demo with:
- **Frontend**: Next.js app deployed on Netlify
- **Backend**: FastAPI on Google Cloud Run
- **Scraper**: UberEats scraper using Browserless.io for browser automation

## Current Priorities
1. Complete any uncommitted changes and deploy
2. Test scraper reliability with Browserless session management
3. Ensure production API URLs are correctly configured

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
Last updated: 2026-01-09
Status: Session ending - uncommitted changes present

### Uncommitted Changes:
1. **backend/scraper/ubereats_scraper.py** - Added time-aware session management:
   - Checks remaining Browserless session time before actions
   - Skips cookie banner dismissal if < 15s remaining
   - Reduces or skips scrolling if < 10-20s remaining
   - Prioritizes getting content quickly when time is critical

2. **frontend/netlify.toml, route.ts, config.ts** - Updated Cloud Run API URL:
   - Changed from `forkast-api-249426017768.us-central1.run.app` and `forkast-api-6utnmdj4rq-uc.a.run.app`
   - To new URL: `forkast-api-84498540486.us-central1.run.app`

### Next Steps:
- Review uncommitted changes
- Commit if changes are correct
- Deploy frontend to Netlify with updated API URL
- Test scraper with Browserless session time management
