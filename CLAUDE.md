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
Last updated: 2026-01-09
Status: All deployed and working

### Completed This Session:
1. **Committed and deployed** time-aware Browserless session management
2. **Updated Cloud Run API URL** across all frontend files
3. **Deployed backend** to Cloud Run (forkast-api-84498540486.us-central1.run.app)
4. **Deployed frontend** to Netlify (forkast-dashboard.netlify.app)
5. **Tested scraper in production** - Successfully scraped 56 items from Krystal UberEats in ~51 seconds

### Current State:
- Scraper fully functional with time-aware session management
- Krystal added as competitor with 56 menu items (11 categories)
- Production DB will reset on redeploy (SQLite limitation on Cloud Run)

### Next Steps:
- Add more competitors for richer market comparison data
- Consider Cloud SQL for persistent database
- Category auto-mapping returned 0 for Krystal - may need investigation
