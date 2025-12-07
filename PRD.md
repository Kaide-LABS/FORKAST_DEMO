# Product Requirements Document
## Competitive Intelligence Dashboard for Forkast
**Version:** 1.0  
**Date:** December 7, 2025  
**Author:** Hafeedh (Development Partner)  
**Target Delivery:** 7-Day Sprint  

---

## Executive Summary

This PRD outlines the development of a **Competitive Intelligence Dashboard**—a minimum viable product (MVP) designed to demonstrate immediate value to Forkast's **Starter tier** ($99/mo) customer segment. The dashboard addresses a critical pain point identified in restaurant operations: the inability to systematically monitor competitor pricing strategies in real-time across third-party delivery platforms.

By automating competitive benchmarking, this tool transforms a labor-intensive manual process (requiring 3-5 hours weekly per location) into an always-on intelligence layer, enabling restaurant operators to make data-driven pricing decisions without the cognitive overhead of manual surveillance.

**Strategic Alignment:**
- Directly supports Forkast's "land and expand" go-to-market strategy
- Provides pure visibility without requiring pricing execution authority (reduces adoption friction)
- Generates valuable competitive data that feeds into future Value-Based Pricing algorithms
- Demonstrates technical capability in data ingestion—a known bottleneck in restaurant tech stacks

---

## Problem Statement

### Primary User Pain Points

**Restaurant Operator (Primary Persona: Independent/Small Chain Owner)**
> "I know my competitors are changing prices on DoorDash, but I have no systematic way to track what they're doing. By the time I manually check their menus, I'm already behind the market."

**Specific Problems:**
1. **Manual Surveillance Burden:** Operators currently check competitor menus manually, sporadically, and inconsistently
2. **Blind Pricing Decisions:** Price changes are made based on intuition or cost increases, not competitive positioning
3. **Platform Fragmentation:** Competitors may price differently across DoorDash vs. Uber Eats vs. in-store
4. **Reactive Posture:** Discover competitors dropped prices only after losing sales volume
5. **Time Poverty:** Operators lack bandwidth to perform consistent competitive analysis

### Market Context (from Research)
- **Dynamic pricing backlash:** Customers perceive "surge pricing" negatively (Wendy's backlash, Reddit sentiment)
- **Competitive intelligence is table stakes:** Forkast's Starter tier explicitly promises "competitor benchmarking"
- **Trust through transparency:** Operators need to see the competitive landscape before making pricing changes

---

## Solution Overview

### Product Vision
A **passive intelligence dashboard** that continuously monitors competitor pricing across delivery platforms, surfaces meaningful changes, and provides clear visual context for positioning decisions—all without requiring the operator to execute pricing changes (de-risking adoption).

### Core Value Proposition
**"Know exactly where you stand in your market—automatically—so you can price with confidence, not guesswork."**

### Key Differentiators
1. **Multi-platform aggregation:** Unified view across DoorDash, Uber Eats (vs. manual per-platform checking)
2. **Temporal intelligence:** Historical tracking reveals pricing patterns (e.g., "Competitor X drops prices every Tuesday 3-6pm")
3. **Zero-friction setup:** No POS integration required for MVP—just competitor identification
4. **Explainable insights:** Every metric includes context (e.g., "You're 12% above market average on burgers")

---

## User Stories & Use Cases

### Primary User Stories

**US-1: Competitive Benchmarking**
```
As a restaurant operator,
I want to see my competitors' current prices for similar menu items,
So that I can ensure my pricing is competitive without being arbitrarily low.
```

**US-2: Price Change Alerts**
```
As a restaurant operator,
I want to be notified when competitors change their prices significantly,
So that I can react quickly to market movements without constant manual checking.
```

**US-3: Positioning Analysis**
```
As a restaurant operator,
I want to understand whether I'm positioned as "premium," "value," or "mid-market" relative to competitors,
So that I can align my pricing strategy with my brand positioning.
```

**US-4: Category-Level Insights**
```
As a restaurant operator,
I want to see competitive positioning by menu category (appetizers, entrees, drinks),
So that I can identify where I'm over/under-priced strategically.
```

**US-5: Historical Trend Analysis**
```
As a restaurant operator,
I want to see how competitor prices have changed over the past 30 days,
So that I can identify patterns (e.g., weekend pricing, happy hour strategies).
```

### Real-World Use Case Scenarios

**Scenario 1: New Competitor Opens**
- **Trigger:** New burger restaurant opens within 1-mile radius
- **User Action:** Adds competitor to monitoring list via simple form
- **System Response:** Begins scraping competitor's DoorDash/Uber Eats menu within 24 hours
- **Outcome:** Operator sees new competitor is pricing burgers 15% lower—decides to emphasize quality differentiators rather than match price

**Scenario 2: Silent Price War**
- **Trigger:** Competitor drops appetizer prices by 20%
- **System Response:** Dashboard shows alert: "⚠️ Competitor X reduced Loaded Nachos from $12.99 → $9.99"
- **User Action:** Operator reviews positioning, decides to bundle appetizers with drinks instead of matching
- **Outcome:** Maintains margin while remaining competitive through bundling strategy

**Scenario 3: Market-Wide Inflation Response**
- **Trigger:** Three competitors increase entree prices by 8-12% same week
- **System Response:** Dashboard shows trend: "Market average for pasta dishes increased 10% this week"
- **User Action:** Operator increases own prices by 9%, feeling confident it's market-justified
- **Outcome:** Preserves margins without fear of losing competitiveness

---

## Functional Requirements

### Phase 1: MVP (7-Day Sprint)

#### FR-1: Competitor Configuration
**Priority:** P0 (Blocker)

- **FR-1.1:** User can add competitors by name + location (e.g., "Burger Shack, 123 Main St, Austin TX")
- **FR-1.2:** System validates competitor exists on DoorDash and/or Uber Eats
- **FR-1.3:** User can specify competitor's "concept type" (burger joint, pizza, casual dining) for better comparison
- **FR-1.4:** Support 3-10 competitors per client location (MVP limitation)

**Acceptance Criteria:**
```
GIVEN I am a restaurant operator
WHEN I enter a competitor name and address
THEN the system finds their DoorDash/Uber Eats listings
AND confirms I want to track this competitor
AND begins daily scraping within 24 hours
```

#### FR-2: Automated Web Scraping
**Priority:** P0 (Blocker)

- **FR-2.1:** Scrape DoorDash restaurant pages for menu items and prices (daily at 6am local time)
- **FR-2.2:** Scrape Uber Eats restaurant pages for menu items and prices (daily at 6am local time)
- **FR-2.3:** Extract: Item Name, Category, Price, Description, Availability Status
- **FR-2.4:** Store historical data (minimum 30 days retention for MVP)
- **FR-2.5:** Handle common scraping challenges:
  - Rate limiting (throttle requests)
  - Dynamic rendering (use Playwright for JS-heavy pages)
  - Menu structure variations
  - Temporary unavailability (retry logic)

**Technical Constraints:**
- Respect robots.txt (legal compliance)
- User-agent rotation to avoid blocks
- Error logging for failed scrapes
- Maximum 100 items per competitor (MVP scope)

#### FR-3: Price Comparison Dashboard
**Priority:** P0 (Blocker)

- **FR-3.1:** **Home View:** Show high-level competitive positioning
  - Card: "Your Average Price vs. Market" (e.g., "+8% above market")
  - Card: "Items Tracked" (e.g., "47 of your items matched to competitors")
  - Card: "Price Changes This Week" (e.g., "3 competitors adjusted prices")
  
- **FR-3.2:** **Category View:** Break down positioning by menu section
  - Table showing: [Your Category] | [Your Avg Price] | [Market Avg] | [Price Delta %]
  - Visual indicator: Green (below market), Yellow (at market), Red (above market)
  
- **FR-3.3:** **Item-Level Comparison:** Detailed competitive grid
  - Table: [Your Item] | [Your Price] | [Comp A Price] | [Comp B Price] | [Market Avg] | [Your Position]
  - Sortable by: price delta, category, competitor
  - Search/filter functionality

**UI/UX Requirements:**
- Clean, professional design (not gamified—matches Chokshi's consulting background)
- Mobile-responsive (operators check on phones during shifts)
- Export to CSV for analysis in Excel

#### FR-4: Price Change Alerts
**Priority:** P1 (High)

- **FR-4.1:** Detect significant price changes (>5% increase/decrease)
- **FR-4.2:** Dashboard notification badge (e.g., "3 new alerts")
- **FR-4.3:** Alert detail view:
  - What changed: "Competitor X increased Margherita Pizza $14 → $16 (+14%)"
  - When: "Detected on Dec 7, 2025"
  - Context: "You're still 5% below this item"
- **FR-4.4:** Mark alerts as "acknowledged" to clear badge

**Future (Post-MVP):** Email/SMS notifications

#### FR-5: Historical Trend Visualization
**Priority:** P1 (High)

- **FR-5.1:** Line chart showing price movements over 30 days
  - X-axis: Date
  - Y-axis: Price
  - Multiple lines: Your item + up to 3 competitor items
- **FR-5.2:** Identify patterns:
  - Day-of-week pricing (e.g., "Competitor drops prices Tuesdays")
  - Promotional periods (sustained price drops)
- **FR-5.3:** Tooltip on hover showing exact price and date

#### FR-6: Menu Item Matching
**Priority:** P1 (High)

**Challenge:** Competitor's "Classic Burger" vs. your "House Burger"—are they comparable?

- **FR-6.1:** Manual matching interface (MVP):
  - Show your menu items on left
  - Show competitor items on right
  - Drag-and-drop or button to link items
  - Store matches in database
- **FR-6.2:** Smart suggestions (AI-assisted for post-MVP):
  - Use simple keyword matching for MVP (e.g., "burger" → "burger")
  - Future: Claude API to analyze descriptions and suggest matches

**Example:**
```
Your Item: "Signature Beef Burger - $13.99"
Suggested Match: Competitor A's "Classic Cheeseburger - $12.99" (85% confidence)
```

### Phase 2: Future Enhancements (Post-Demo)

#### FR-7: Client Menu Upload
- Import operator's own menu (CSV/PDF)
- Automatically map to competitor items for instant comparison

#### FR-8: Multi-Location Support
- Dashboard for chains with 3-10 locations
- Aggregate insights across locations
- Location-specific competitor sets

#### FR-9: Advanced Analytics
- Seasonal trend detection (summer vs. winter pricing)
- Demand elasticity hints (when competitors lower price, do they sell more?)
- Market share estimation (based on review volume as proxy)

#### FR-10: Pricing Recommendations
- "Consider raising your Margherita Pizza by $1.50—you're 18% below market and demand is strong"
- Bridge to Forkast's Core/Pro tiers (upsell path)

---

## Technical Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     CLIENT LAYER                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │   Next.js Frontend (React)                          │   │
│  │   - Dashboard UI                                    │   │
│  │   - Data visualization (Recharts/Chart.js)          │   │
│  │   - Responsive design (Tailwind CSS)                │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ REST API
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   APPLICATION LAYER                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │   Python FastAPI Backend                            │   │
│  │   - API endpoints (/competitors, /prices, /alerts)  │   │
│  │   - Business logic                                  │   │
│  │   - Authentication (simple API key for MVP)         │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    DATA LAYER                               │
│  ┌────────────────────┐      ┌─────────────────────────┐   │
│  │   PostgreSQL       │      │   Redis Cache           │   │
│  │   - Competitors    │      │   - Recent scrapes      │   │
│  │   - Menu items     │      │   - Rate limiting       │   │
│  │   - Price history  │      └─────────────────────────┘   │
│  │   - Alerts         │                                     │
│  └────────────────────┘                                     │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  SCRAPING LAYER                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │   Python Scraping Service                           │   │
│  │   - Playwright (JS rendering)                       │   │
│  │   - BeautifulSoup (HTML parsing)                    │   │
│  │   - Scheduled jobs (APScheduler)                    │   │
│  │   - Retry logic & error handling                    │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

#### Frontend
- **Framework:** Next.js 14 (React 18)
- **Styling:** Tailwind CSS
- **Charts:** Recharts or Chart.js
- **State Management:** React Context API (sufficient for MVP)
- **HTTP Client:** Axios
- **Hosting:** Vercel (free tier for demo)

#### Backend
- **API Framework:** FastAPI (Python 3.11+)
- **Web Scraping:**
  - Playwright (for DoorDash/Uber Eats dynamic content)
  - BeautifulSoup4 (HTML parsing)
- **Task Scheduling:** APScheduler (for daily scrapes)
- **Authentication:** Simple API key (JWT for post-MVP)
- **Hosting:** Railway / Render (free tier with limitations)

#### Database
- **Primary DB:** PostgreSQL 15
  - Heroku Postgres (free tier: 10K rows) OR
  - Supabase (generous free tier)
- **Caching:** Redis (optional for MVP, Upstash free tier)

#### DevOps
- **Version Control:** GitHub
- **CI/CD:** GitHub Actions (automated deploy on push to main)
- **Monitoring:** Sentry (error tracking)
- **Logging:** Python logging → stdout (Railway/Render handles aggregation)

### Data Models

#### Competitor
```python
class Competitor(Base):
    id: UUID (PK)
    name: str (e.g., "Joe's Pizza")
    location: str (e.g., "123 Main St, Austin TX")
    concept_type: str (e.g., "pizza", "burger")
    doordash_url: str (nullable)
    ubereats_url: str (nullable)
    scraping_enabled: bool (default: True)
    last_scraped_at: datetime (nullable)
    created_at: datetime
    updated_at: datetime
```

#### MenuItem
```python
class MenuItem(Base):
    id: UUID (PK)
    competitor_id: UUID (FK)
    platform: str (enum: "doordash", "ubereats")
    name: str (e.g., "Margherita Pizza")
    category: str (e.g., "Pizza", "Appetizers")
    description: str (nullable)
    current_price: Decimal (2 decimal places)
    is_available: bool
    menu_position: int (order on menu)
    created_at: datetime
    updated_at: datetime
```

#### PriceHistory
```python
class PriceHistory(Base):
    id: UUID (PK)
    menu_item_id: UUID (FK)
    price: Decimal
    recorded_at: datetime
    change_percentage: Decimal (nullable, calculated)
    
    # Composite index on (menu_item_id, recorded_at) for fast time-series queries
```

#### Alert
```python
class Alert(Base):
    id: UUID (PK)
    menu_item_id: UUID (FK)
    alert_type: str (enum: "price_increase", "price_decrease", "new_item", "item_removed")
    old_value: str (e.g., "$12.99")
    new_value: str (e.g., "$14.99")
    change_percentage: Decimal
    is_acknowledged: bool (default: False)
    created_at: datetime
```

#### ClientMenuItem (for future manual matching)
```python
class ClientMenuItem(Base):
    id: UUID (PK)
    client_id: UUID (FK, future multi-tenancy)
    name: str
    category: str
    current_price: Decimal
    matched_items: JSONB (array of competitor menu_item_ids)
```

### API Endpoints

#### Competitors
```
GET    /api/v1/competitors              # List all tracked competitors
POST   /api/v1/competitors              # Add new competitor
GET    /api/v1/competitors/{id}         # Get competitor details
PUT    /api/v1/competitors/{id}         # Update competitor
DELETE /api/v1/competitors/{id}         # Stop tracking competitor
```

#### Menu Items & Prices
```
GET    /api/v1/competitors/{id}/menu    # Get current menu for competitor
GET    /api/v1/items/{id}/history       # Price history for specific item
GET    /api/v1/comparison               # Compare all competitors (main dashboard data)
```

#### Alerts
```
GET    /api/v1/alerts                   # Get recent alerts (unacknowledged first)
POST   /api/v1/alerts/{id}/acknowledge  # Mark alert as read
GET    /api/v1/alerts/stats             # Count of unread alerts
```

#### Scraping (Admin)
```
POST   /api/v1/scrape/trigger/{competitor_id}  # Manual trigger scrape
GET    /api/v1/scrape/status                   # Last scrape times, success rates
```

### Scraping Strategy

#### Target Platforms

**DoorDash**
- **URL Pattern:** `https://www.doordash.com/store/{restaurant-slug}`
- **Rendering:** JavaScript-heavy (React app) → requires Playwright
- **Selectors (as of Dec 2025):**
  - Menu items: `[data-testid="menu-item-card"]` or similar
  - Item name: `.MenuItem__title` or `h3` within card
  - Price: `[data-testid="price"]` or similar
- **Challenges:**
  - Frequent DOM structure changes (use flexible selectors)
  - Anti-bot detection (rotate user agents, add delays)
  - Menu sections dynamically loaded (scroll to load all)

**Uber Eats**
- **URL Pattern:** `https://www.ubereats.com/store/{restaurant-slug}`
- **Rendering:** JavaScript-heavy → requires Playwright
- **Selectors:**
  - Items typically in `<ul>` or grid containers
  - Prices in spans with specific classes
- **Challenges:**
  - Similar to DoorDash
  - May require location cookie/IP matching

#### Scraping Schedule
- **Frequency:** Daily at 6:00 AM local time (captures overnight price changes)
- **Duration:** ~5-10 seconds per restaurant (rate limited)
- **Retries:** Up to 3 attempts with exponential backoff (2s, 4s, 8s)

#### Error Handling
```python
# Pseudo-code
try:
    scrape_competitor(competitor_id)
except ScrapingError as e:
    log_error(competitor_id, str(e))
    if failure_count >= 3:
        send_notification_to_admin("Scraper failing for X")
        disable_competitor_temporarily(competitor_id)
```

#### Rate Limiting
- **Between requests:** 2-5 second randomized delay
- **User agent rotation:** Pool of 10+ realistic user agents
- **Respect robots.txt:** Check before first scrape (document any violations for legal review)

### Deployment Architecture (MVP)

```
┌─────────────────────┐
│   Vercel (Frontend) │  ← Next.js static/SSR
│   - Auto-deploy     │
│   - CDN edge cache  │
└─────────────────────┘
          ▲
          │ HTTPS
          ▼
┌─────────────────────┐
│  Railway/Render     │  ← FastAPI + Scraper
│  (Backend)          │
│  - Single dyno/pod  │
│  - APScheduler      │
└─────────────────────┘
          ▲
          │
          ▼
┌─────────────────────┐
│  Supabase/Heroku    │  ← PostgreSQL
│  (Database)         │
│  - Automated backup │
└─────────────────────┘
```

**Estimated Monthly Cost (MVP):**
- Vercel: Free
- Railway/Render: Free tier (with limits) or ~$5/mo
- Database: Free tier (Supabase) or ~$5/mo
- **Total: $0-10/mo** (scalable to $50-100/mo production)

---

## Success Metrics

### Product Metrics (Measure during demo)

**Engagement:**
- Dashboard views per day (target: 3-5 daily active checks)
- Time spent on dashboard (target: >2 minutes per session)
- Alert acknowledgment rate (target: >70% within 24 hours)

**Data Quality:**
- Scrape success rate (target: >95% successful daily scrapes)
- Item match accuracy (manual validation: >80% correct auto-suggestions)
- Price change detection latency (target: <24 hours)

**User Value:**
- Number of competitive insights surfaced (target: 5-10 meaningful alerts per week)
- Pricing decisions influenced (qualitative feedback)
- Time saved vs. manual checking (estimate: 3 hours/week → 5 minutes/week)

### Technical Metrics

**Performance:**
- API response time p95: <500ms
- Scraper execution time: <30 seconds per competitor
- Database query performance: <100ms for dashboard views

**Reliability:**
- Uptime: >99% (excluding scheduled maintenance)
- Error rate: <1% of API requests
- Data freshness: All competitor data <24 hours old

### Demo Success Criteria (Pitch Meeting)

**Must-Have for Demo:**
1. ✅ Live dashboard showing 3-5 real competitors (Austin burger joints as example)
2. ✅ Historical price data spanning 7-14 days (show trends are tracked)
3. ✅ At least 1-2 real price change alerts generated
4. ✅ Clean, professional UI (no bugs, fast loading)
5. ✅ Mobile-responsive (Chokshi may check on phone during pitch)

**Nice-to-Have for Demo:**
1. 🎯 Automated scraper running successfully (show logs/status page)
2. 🎯 Comparison across DoorDash + Uber Eats (multi-platform)
3. 🎯 Downloadable CSV export (for further analysis)

---

## Project Timeline & Milestones

### 7-Day Sprint Breakdown

#### Day 1: Foundation
**Focus:** Setup + Data Architecture

- [ ] Initialize Next.js + FastAPI project repos
- [ ] Set up PostgreSQL database (Supabase)
- [ ] Define data models + create migrations
- [ ] Basic authentication (API key)
- [ ] Hello World: Frontend calls Backend successfully

**Deliverable:** Deployed skeleton (empty dashboard, API responds to ping)

#### Day 2: Scraping Core
**Focus:** Prove we can extract data

- [ ] Implement DoorDash scraper (Playwright)
- [ ] Implement Uber Eats scraper (Playwright)
- [ ] Test with 2-3 real restaurants (Austin market)
- [ ] Store scraped data in database
- [ ] Add error handling + logging

**Deliverable:** Python script successfully scrapes 3 competitors, data in DB

#### Day 3: Backend API
**Focus:** Serve data to frontend

- [ ] Implement `/api/v1/competitors` endpoints (CRUD)
- [ ] Implement `/api/v1/comparison` endpoint (main dashboard data)
- [ ] Implement `/api/v1/alerts` endpoints
- [ ] Price history calculation logic
- [ ] API documentation (Swagger auto-generated by FastAPI)

**Deliverable:** All API endpoints functional, testable via Postman

#### Day 4: Frontend Dashboard (Part 1)
**Focus:** Home view + basic visualization

- [ ] Home view cards (price positioning, items tracked)
- [ ] Competitor list page (add/remove competitors)
- [ ] Basic table showing item-level comparison
- [ ] Responsive layout (mobile + desktop)

**Deliverable:** Navigable dashboard with real data displayed

#### Day 5: Frontend Dashboard (Part 2)
**Focus:** Visualizations + alerts

- [ ] Historical price trend chart (Recharts line chart)
- [ ] Category breakdown view
- [ ] Alert notification system (badge + list)
- [ ] Search/filter functionality on item table

**Deliverable:** Full-featured dashboard, visually polished

#### Day 6: Automation + Polish
**Focus:** Scheduled scraping + UX refinement

- [ ] Implement APScheduler for daily scrapes (6am job)
- [ ] Alert generation logic (detect >5% price changes)
- [ ] Loading states, error messages (UX polish)
- [ ] CSV export functionality
- [ ] Mobile testing + fixes

**Deliverable:** System runs autonomously, generates alerts automatically

#### Day 7: Demo Prep + Documentation
**Focus:** Make it pitch-perfect

- [ ] Seed demo database with compelling data (Austin burger market)
- [ ] Create demo video/walkthrough (2-3 minute Loom)
- [ ] Write deployment guide + README
- [ ] Security review (no API keys exposed, input validation)
- [ ] Final testing on staging environment

**Deliverable:** Production-ready demo + pitch materials

### Contingency Planning

**If Behind Schedule:**
- **Drop:** Multi-platform scraping (DoorDash only for MVP)
- **Drop:** Historical trends (focus on current snapshot)
- **Simplify:** Manual competitor URL input (skip auto-discovery)

**If Ahead of Schedule:**
- **Add:** Email alerts (SendGrid integration)
- **Add:** AI-powered item matching (Claude API)
- **Add:** Basic pricing recommendations

---

## Non-Functional Requirements

### Security

**MVP Security:**
- API key authentication (rotate post-demo)
- Input validation on all endpoints (prevent SQL injection)
- HTTPS only (enforced by Vercel/Railway)
- No sensitive data logged

**Future Production Security:**
- OAuth 2.0 / JWT authentication
- Role-based access control (RBAC)
- Data encryption at rest
- GDPR/CCPA compliance (if storing user data)

### Performance

**Response Times:**
- Dashboard initial load: <2 seconds
- API queries: <500ms
- Scraper per-restaurant: <30 seconds

**Scalability (Future):**
- Design for 100 clients × 10 competitors = 1,000 restaurants
- Database partitioning by client_id (when multi-tenant)
- Background job queue (Celery) if APScheduler insufficient

### Compliance & Legal

**Web Scraping Legality:**
- ⚠️ **Critical:** Web scraping sits in legal gray area
- **Best Practices:**
  - Respect robots.txt
  - Don't overwhelm servers (rate limiting)
  - Scrape publicly available data only (no login required)
  - Use data for internal analysis, not republishing
  - Monitor ToS changes (DoorDash/Uber Eats may prohibit scraping)

**Recommendation:** 
- Include legal disclaimer in demo pitch
- Suggest official API partnerships as roadmap item (DoorDash/Uber Eats have partner programs)
- Frame MVP as "technical proof of concept" pending legal review

### Data Retention

**MVP Policy:**
- Price history: 30 days (sufficient for trend detection)
- Alerts: 90 days
- Competitor profiles: Indefinite (or until user deletes)

**Future Policy:**
- Configurable retention per client
- Automated data archival to cold storage (S3)

---

## Risks & Mitigations

### High-Priority Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Scrapers blocked by anti-bot systems** | 🔴 High (no data = no product) | Medium | • User agent rotation<br>• Realistic delays between requests<br>• Fallback to manual data entry for demo<br>• Long-term: pursue official API partnerships |
| **DOM structure changes break scrapers** | 🟡 Medium (requires maintenance) | High | • Flexible CSS selectors (avoid brittle XPath)<br>• Automated monitoring for scrape failures<br>• Quick-fix process documented |
| **Legal cease-and-desist from platform** | 🔴 High (product shutdown) | Low-Medium | • Legal review before scaling<br>• Frame as technical POC in pitch<br>• Roadmap includes official API integrations |
| **Insufficient demo data in 7 days** | 🟡 Medium (weak demo) | Low | • Seed database with realistic mock data<br>• Run scrapers 2-3 days early to build history |
| **Chokshi prioritizes other features** | 🟡 Medium (wasted effort) | Medium | • Pre-demo alignment call (validate this is valuable)<br>• Show competitor analysis (Sauce has this feature) |

### Low-Priority Risks

- **Competitor restaurant closed:** Alert user, mark inactive
- **Menu item name mismatches:** Manual mapping UI mitigates
- **Time zone handling errors:** Use UTC internally, display local time
- **Multi-location restaurants:** Scope to single location for MVP

---

## Future Roadmap (Post-Demo)

### Phase 2: Enhanced Intelligence (Weeks 2-4)
- AI-powered menu item matching (Claude API)
- Email/SMS alerts
- Multi-location support for chains
- Promotional detection (identify coupon codes, limited-time offers)

### Phase 3: Actionable Insights (Months 2-3)
- Price recommendation engine: "Consider raising X by $Y because..."
- Seasonal trend analysis: "Your competitors raise prices 10% in summer"
- Demand elasticity estimation (correlate reviews with prices)

### Phase 4: Strategic Positioning (Months 3-6)
- Market share estimation (review volume as proxy)
- Customer sentiment analysis (scrape reviews for quality/value mentions)
- Competitive moat identification: "Competitor X can't compete on appetizers"

### Phase 5: Integration & Scale (Months 6-12)
- POS integration (pull client's menu automatically)
- Automated price sync (push recommendations to POS)
- API partnerships (official DoorDash/Uber Eats data feeds)
- White-label offering for POS vendors

---

## Appendix A: Sample Data Structures

### Example API Response: `/api/v1/comparison`

```json
{
  "client": {
    "name": "Your Restaurant",
    "location": "Austin, TX",
    "avg_price": 13.45,
    "market_position": "+8%"
  },
  "competitors": [
    {
      "id": "uuid-123",
      "name": "Burger Palace",
      "avg_price": 12.20,
      "price_delta": "-9.3%",
      "last_updated": "2025-12-07T06:00:00Z"
    },
    {
      "id": "uuid-456",
      "name": "Grill House",
      "avg_price": 14.80,
      "price_delta": "+10.0%",
      "last_updated": "2025-12-07T06:00:00Z"
    }
  ],
  "category_breakdown": [
    {
      "category": "Burgers",
      "client_avg": 14.99,
      "market_avg": 13.75,
      "delta": "+9.0%",
      "items_compared": 5
    },
    {
      "category": "Appetizers",
      "client_avg": 8.99,
      "market_avg": 9.50,
      "delta": "-5.4%",
      "items_compared": 8
    }
  ],
  "alerts": [
    {
      "id": "alert-789",
      "type": "price_decrease",
      "competitor": "Burger Palace",
      "item": "Classic Cheeseburger",
      "old_price": 13.99,
      "new_price": 11.99,
      "change": "-14.3%",
      "detected_at": "2025-12-06T06:00:00Z",
      "is_acknowledged": false
    }
  ]
}
```

### Example Scraper Output (Internal)

```python
# Scraped from DoorDash
{
  "restaurant_name": "Burger Palace",
  "platform": "doordash",
  "scraped_at": "2025-12-07T06:05:23Z",
  "menu_items": [
    {
      "name": "Classic Cheeseburger",
      "category": "Burgers",
      "price": 11.99,
      "description": "1/4 lb beef patty, American cheese, lettuce, tomato",
      "is_available": true,
      "position": 1
    },
    {
      "name": "Bacon BBQ Burger",
      "category": "Burgers",
      "price": 13.99,
      "description": "1/3 lb beef, crispy bacon, BBQ sauce, onion rings",
      "is_available": true,
      "position": 2
    },
    {
      "name": "Loaded Fries",
      "category": "Sides",
      "price": 6.99,
      "description": "Crispy fries topped with cheese, bacon, jalapeños",
      "is_available": true,
      "position": 12
    }
  ]
}
```

---

## Appendix B: Competitive Analysis

### How This Compares to Existing Solutions

| Feature | **Our MVP** | Sauce | Juicer | Manual Process |
|---------|-------------|-------|--------|----------------|
| **Price Tracking** | ✅ Automated (DoorDash/UE) | ✅ Automated | ❌ (pivoted away) | ❌ Manual |
| **Historical Trends** | ✅ 30 days | ✅ Extensive | N/A | ❌ No |
| **Alert System** | ✅ Real-time | ✅ Email alerts | N/A | ❌ No |
| **POS Integration** | ❌ Future | ✅ Yes (Chowly) | ❌ Dropped | N/A |
| **Price Execution** | ❌ View-only (MVP) | ✅ Auto-adjust | ❌ Dropped | Manual |
| **Setup Time** | ⚡ <10 minutes | ~2 hours | N/A | Continuous |
| **Cost** | Free (demo) | $300+/mo | N/A | Staff time |

**Differentiation:**
- **Lower friction:** No POS integration needed (Sauce requires Chowly integration)
- **Transparency:** View-only reduces adoption fear (vs. automated price changes)
- **Speed:** Operational in <24 hours vs. weeks for full integration
- **Cost:** Accessible to independent operators (not just chains)

---

## Appendix C: Demo Script (for Pitch Meeting)

### 3-Minute Demo Flow

**1. Set the Scene (30 sec)**
> "Imagine you're Joe, owner of Joe's Burger Shack in Austin. You know your competitors are constantly adjusting prices on DoorDash, but checking manually takes hours every week—and you still miss changes."

**2. Dashboard Overview (60 sec)**
> [Pull up live dashboard]
> "This is your competitive intelligence dashboard. At a glance, you see:
> - You're currently 8% above market average—not bad, but let's investigate.
> - You have 47 menu items being tracked across 5 competitors.
> - There are 3 new alerts this week—price changes you need to know about."

**3. Drill into Alerts (45 sec)**
> [Click on alerts]
> "Here's what changed: Burger Palace dropped their classic cheeseburger from $14 to $12—a 14% decrease. 
> This happened yesterday. You're now $2 more expensive on a similar item.
> You can decide: match them, emphasize quality, or bundle with fries to offset."

**4. Historical Context (30 sec)**
> [Show trend chart]
> "Look at this 30-day trend. Burger Palace consistently drops prices on Tuesdays around 3pm—they're running a stealth happy hour.
> You could counter-program or lean into premium positioning during their discount window."

**5. Category Breakdown (15 sec)**
> [Show category view]
> "At the category level: your burgers are 9% above market, but your appetizers are 5% below. Strategic insight: you have room to raise appetizer prices."

**6. Value Proposition Close (10 sec)**
> "All of this data—collected automatically, updated daily—replaces 3-4 hours of manual checking per week. And this is just the visibility layer. Imagine what we build next."

---

## Conclusion

This PRD defines a **focused, achievable MVP** designed to demonstrate immediate value to Forkast while respecting the 7-day delivery constraint. The Competitive Intelligence Dashboard addresses a validated pain point (manual competitor surveillance), aligns with Forkast's Starter tier go-to-market strategy, and establishes technical credibility in data ingestion—a foundational capability for future Value-Based Pricing features.

**Key Strengths of This Approach:**
1. **Low Friction:** No POS integration required for initial adoption
2. **High Visibility:** Generates tangible insights within 24 hours of setup
3. **Strategic Alignment:** Feeds data into Forkast's long-term pricing algorithms
4. **Scalable Foundation:** Architecture supports expansion to automated pricing recommendations

**Next Steps:**
1. Schedule alignment call with Kiran Chokshi to validate priorities
2. Begin Day 1 development (foundation + data architecture)
3. Provide daily progress updates (async Slack/email)
4. Deliver demo + walkthrough by Day 7

---

**Document Control:**
- **Version:** 1.0  
- **Last Updated:** December 7, 2025  
- **Owner:** Hafeedh (Development Partner)  
- **Stakeholder:** Forkast (Kiran Chokshi, Founder)  
- **Review Cycle:** Update after demo feedback
