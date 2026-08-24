# Frontend Architecture - AI Buying Signal Intelligence

## Current Architecture
The application is currently built as a single-file React prototype (`final_ai-buying-signal-intelligence.jsx`). It uses client-side state for routing and data management. Data is deterministically generated on the client-side via a mock data generator (`generateLeads`), meaning there is no current backend integration or asynchronous data fetching. The UI is built using inline styles and plain CSS variables without external UI libraries or component frameworks (e.g., Tailwind, Material UI).

## Folder Structure
Currently, the entire application lives in a single file within the frontend directory:
```text
frontend/
└── final_ai-buying-signal-intelligence.jsx
```

## Page / Component Dependency Map
- **App (Shell)**
  - Sidebar Navigation
  - **OverviewPage**
    - `StatCard`, `SectionTitle`, `SourceCardsVerticalSlider`, `SourceLogoBadge`, `LinkBtn`, `Chip`, `LeadTable`
  - **LeadsPage**
    - `SectionTitle`, `FilterBar`, `Chip`, `LinkBtn`, `LeadTable`
  - **SourceIntelPage**
    - `SectionTitle`, `StatCard`, `LinkBtn`, `LeadTable`
    - Sub-components: `Bar`, Source x Industry Matrix Table
  - **CompaniesPage**
    - `SectionTitle`, Company Table, `Panel`
    - Sub-components: `Bar`
  - **LeadIntelPage**
    - `LinkBtn`, `SignalBars`, `TierBadge`, `SourceTag`, `Panel`, `IntentCell`
- **Shared Components**
  - `SignalBars`, `IntentCell`, `TierBadge`, `SourceTag`, `SourceIcon`, `SourceLogoBadge`
  - `SourceCardsVerticalSlider`, `Chip`, `StatCard`, `SectionTitle`, `LinkBtn`, `Panel`
  - `LeadTable`
  - `FilterBar`

## Current Data Flow
1. On `App` mount, `generateLeads()` creates a static array of mock leads deterministically using a custom seeded RNG (`mulberry32`).
2. The `leads` array and `nav` object are passed down as props to the active page component (determined by the `page` state).
3. The `LeadsPage` uses `applyFilters` to filter and sort the leads entirely on the client side.
4. Aggregations (like `sourceStats`, `industryStats`, `matrix`) are calculated synchronously inside page components (`OverviewPage`, `SourceIntelPage`, `CompaniesPage`) by mapping and reducing the `leads` array.
5. `selectedLeadId` is tracked in `App` state to pass a single lead to `LeadIntelPage`.

## Mock Data Locations
- **`SOURCES` array:** Static list of 9 sources (Reddit, Hacker News, X, etc.)
- **`TECHNOLOGIES` array:** Static list of 12 tech keywords (RAG, LLM, etc.)
- **`SIGNAL_TYPES` array:** Static list of 8 signal types.
- **`COMPANIES` array:** Static list of 35 companies with their industries and countries.
- **`generateLeads()` function:** Uses the above constants, `PAIN_PHRASES`, and `NEED_PHRASES` to build the list of leads.
- **RNG:** Custom `mulberry32` pseudo-random number generator for deterministic mock generation.

## Expected Lead Object Shape
```typescript
interface Lead {
  id: string; // e.g., "LEAD-1000"
  company: string;
  industry: string;
  country: string;
  source: string; // Source ID (e.g., "reddit")
  signalType: string;
  technology: string;
  businessPain: string;
  detectedNeed: string;
  intentScore: number; // 0-99
  tierLabel: string; // "HOT" | "HIGH" | "MEDIUM" | "LOW"
  aiSummary: string;
  iosysService: string;
  publishedDate: Date; // or ISO string in real API
  daysAgo: number;
  status: string; // "New" | "Reviewed" | "Contacted" | "Qualified"
  originalSnippet: string;
  originalUrl: string;
  explicitRequirement: boolean;
  recentSignal: boolean;
  contactEmail: string | null;
}
```

## Expected Source Object Shape
```typescript
interface Source {
  id: string; // e.g., "reddit"
  name: string; // e.g., "Reddit"
  tag: string; // e.g., "RDT"
}
```

## Expected Company Object Shape
```typescript
interface Company {
  name: string; // e.g., "Northwind Health Systems"
  industry: string; // e.g., "Healthcare"
  country: string; // e.g., "United States"
}
```

## Expected Analytics Object Shape
*(Currently implicitly calculated, will need dedicated structure from backend for scale)*
```typescript
interface SourceAnalytics {
  id: string;
  count: number;
  hotCount: number;
  avgIntent: number;
}

interface AnalyticsOverview {
  totalSignals: number;
  hotLeads: number;
  highIntent: number;
  newToday: number;
  totalCompanies: number;
  topIndustries: Array<{ industry: string, count: number }>;
  sourceStats: Array<SourceAnalytics>;
}
```

## API Calls That Will Eventually Be Required
1. **`GET /api/leads`**: Fetch leads with server-side pagination, sorting, and filtering.
2. **`GET /api/leads/:id`**: Fetch detailed view for a single lead, including related signals.
3. **`GET /api/analytics/overview`**: Fetch aggregated metrics for the dashboard.
4. **`GET /api/analytics/sources`**: Fetch metrics and distributions specific to sources.
5. **`GET /api/analytics/companies`**: Fetch aggregated company intelligence and activity.
6. **`PATCH /api/leads/:id`**: Update lead status (e.g., from "New" to "Contacted").
7. **`GET /api/metadata`**: Fetch dynamic list of valid sources, industries, countries, and technologies for filter dropdowns.

## Components That Should Remain Unchanged
Pure presentational and UI components should remain unchanged to preserve the intended aesthetic and design language:
- `SignalBars`
- `IntentCell`
- `TierBadge`
- `SourceTag`
- `SourceIcon`
- `SourceLogoBadge`
- `Chip`
- `StatCard`
- `SectionTitle`
- `Panel`
- Custom `Bar` implementations in analytics pages.

## Components That Will Need Backend Integration
These components handle data, state, or side-effects and will require refactoring:
- **`App`**: Will need React Context or global state (Zustand/Redux) and data fetching hooks (e.g., React Query/SWR) to replace `generateLeads()`.
- **`LeadsPage` & `LeadTable`**: Needs to accept server-side paginated data rather than filtering a large client-side array.
- **`FilterBar`**: Needs to sync state with URL query parameters to support link sharing and trigger server fetches.
- **`OverviewPage`, `SourceIntelPage`, `CompaniesPage`**: Will need to fetch pre-calculated analytics from the backend instead of computing heavy aggregations on the client side.
- **`LeadIntelPage`**: Will need to fetch individual lead details asynchronously by `id`.

## Other Technical Details
- **Styling:** The app uses inline styles and plain CSS variables injected into the DOM via `<style>` tag.
- **Routing:** Built manually with `useState`. Will likely need upgrading to a real router (e.g., React Router, or Next.js file-based routing) for deep linking.
- **Loading / Error States:** Completely absent. Implementing asynchronous backend connections will require adding skeletons, spinners, and error boundaries.
