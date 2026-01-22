# Content-to-Domain Mapping Strategy

**Version:** 1.0.0  
**Date:** 2026-01-19  
**Author:** Jannice Wang  
**Status:** Baseline Strategy  
**Scope:** UXI, DIRAC, Omnivoltaic Company-Wide

---

## Executive Summary

This document defines the strategic mapping between content organization and domain structure for Omnivoltaic's digital ecosystem. It establishes three distinct information flow dimensions and their corresponding domain architecture, serving as the baseline for all future domain-related decisions across UXI interfaces and broader company infrastructure.

---

## Strategic Context

### Brand Hierarchy

- **Omnivoltaic** = Group company and master brand (registered trademark)
- **OVES** = Omnivoltaic Energy Solutions (primary operating company)
- **OVK** = Omnivoltaic Kenya (regional trading entity)
- **OVT** = Omnivoltaic Togo (regional trading entity)
- **OVN** = Omnivoltaic Nigeria (future regional entity)
- **OVE** = Omnivoltaic Ethiopia (future regional entity)

**Key Principle:** Omnivoltaic is the central brand identity. Regional trading companies (OVK, OVT, etc.) operate under Omnivoltaic and do not establish independent brand recognition.

### Business Model Context

1. **Products:** Centrally managed under Omnivoltaic, sourced from single MRP system
2. **B2B Operations:** Regionally aligned through trading companies (OV[X])
3. **B2C Commerce:** Country-specific shopping aligned with Odoo COMPANY structure
4. **Platform Services:** Cross-cutting capabilities that transcend regions and solutions

---

## Three Information Flow Dimensions

### Dimension 1: Solutions Flow (Use-Case Driven)

```
Company → Solutions → Products
```

**Logic:** Products are designed to solve specific use-case scenarios, not organized by geography.

**Example Flow:**
- Customer need: "I need urban delivery transportation"
- Solution: E-Mobility
- Products: E-bikes, e-motos, battery swap infrastructure

**Target Audience:** End users, partners, distributors seeking solutions to specific business problems

---

### Dimension 2: Regional Commercial Flow (B2B Structure)

```
Company → OV[X] → Services/Capabilities
```

**Logic:** B2B commercial operations are regionally aligned through trading companies.

**Example Flow:**
- Partner interest: "I want to work with Omnivoltaic in Kenya"
- Entity: OVK (Omnivoltaic Kenya)
- Services: Installation, maintenance, training, fleet management

**Target Audience:** B2B customers, partners, distributors within specific countries

---

### Dimension 3: Enterprise Capabilities (Cross-Cutting)

```
Company → [Capability Domains]
```

**Logic:** Platform capabilities that serve all regions and solutions without geographic or use-case boundaries.

**Example Capabilities:**
- Documentation (docs.omnivoltaic.com)
- Asset Management (assets.omnivoltaic.com)
- Enterprise Platform (enterprise.omnivoltaic.com)

**Target Audience:** Internal teams, partners, enterprise customers across all regions

---

## Domain Architecture

### Tier 1: Corporate Hub

**Domain:** `omnivoltaic.com`

**Purpose:** Central entry point and brand headquarters

**Content:**
- Company overview (about, vision, mission)
- Investor relations
- Careers
- Press/media
- Navigation to:
  - Solutions (Dimension 1)
  - Regional offices (Dimension 2)
  - Enterprise capabilities (Dimension 3)

**Implementation:** `apps/corporate/omnivoltaic/`

---

### Tier 2A: Solutions (Dimension 1 - Use-Case Driven)

#### Path-Based Structure (Recommended)

```
omnivoltaic.com/solutions/[solution-name]
```

**Solution Categories (Use-Case Scenarios):**

1. **E-Mobility** (`/solutions/mobility`)
   - Personal transport (e-bikes, e-motos)
   - Commercial fleets (delivery, taxi)
   - Battery swap infrastructure
   - Products aligned to mobility use-case

2. **Cross-Grid** (`/solutions/cross-grid`)
   - Hybrid solar + grid systems
   - Grid-tied solutions
   - Backup power systems
   - Products aligned to grid integration use-case

3. **Energy Access** (`/solutions/energy-access`)
   - Home lighting & power
   - Productive use applications (sewing, pumps)
   - Small business power
   - Products aligned to off-grid use-case

4. **Commercial & Industrial** (`/solutions/commercial`)
   - Mini-grids
   - C&I solar systems
   - Cold storage
   - Products aligned to commercial use-case

5. **PayGo Financing** (`/solutions/financing`)
   - Consumer PayGo models
   - Asset financing
   - Products with financing options

**Note:** "Mobility" and "Cross-Grid" are examples of use-case scenarios. Products are organized under these scenarios based on their primary application context.

**Key Characteristic:** Products appear within solution contexts, showing how they solve specific use-cases. The same product may appear in multiple solutions if it serves different scenarios.

**Target Audience:**
- B2B customers seeking solutions
- Partners evaluating product portfolios
- Distributors understanding market positioning

**Implementation:** `apps/solutions/` (can be modular for future subdomain split if needed)

**Alternative Structure:** Subdomain-based (e.g., `mobility.omnivoltaic.com`) if independent deployment per solution becomes necessary.

---

### Tier 2B: Regional Operations (Dimension 2 - B2B Commercial)

**Pattern:** `ov[x].omnivoltaic.com`

**Deployed Sites:**
- `ovk.omnivoltaic.com` - Omnivoltaic Kenya
- `ovt.omnivoltaic.com` - Omnivoltaic Togo
- `ovn.omnivoltaic.com` - Omnivoltaic Nigeria (future)
- `ove.omnivoltaic.com` - Omnivoltaic Ethiopia (future)

**Content Per Regional Site:**
- About OV[X] (local team, offices, history)
- Services & Capabilities
  - Installation services
  - Maintenance & support
  - Training programs
  - Fleet management
  - Custom integration
- Partner programs
- Local case studies
- Contact & locations
- Link to regional B2C shop (shops.omnivoltaic.com/[country])

**Key Characteristic:** Focus on **services and capabilities**, NOT product catalogs. Products live in Solutions (Tier 2A).

**Target Audience:**
- B2B customers in specific countries
- Local partners and distributors
- Institutional buyers (governments, NGOs)

**Implementation:** `apps/regional/ovk/`, `apps/regional/ovt/`, etc.

---

### Tier 2C: B2C E-Commerce (Regional Shopping)

**Pattern:** `shops.omnivoltaic.com/[country]`

**Structure:**
```
shops.omnivoltaic.com/          → E-commerce hub (country selector)
shops.omnivoltaic.com/kenya/    → Kenya shop (OVK inventory)
shops.omnivoltaic.com/togo/     → Togo shop (OVT inventory)
shops.omnivoltaic.com/nigeria/  → Nigeria shop (OVN - future)
shops.omnivoltaic.com/ethiopia/ → Ethiopia shop (OVE - future)
```

**Category Structure Within Each Country:**
```
shops.omnivoltaic.com/kenya/
  ├─ /                    → Kenya shop homepage
  ├─ /mobility/           → E-bikes, e-motos, accessories
  ├─ /solar/              → Solar home systems, batteries
  ├─ /appliances/         → Solar appliances, lights
  ├─ /financing/          → PayGo options
  ├─ /cart/               → Shopping cart
  ├─ /checkout/           → Checkout flow
  └─ /account/            → Customer account management
```

**Design Inspiration:** Amazon (category-first navigation) + Tesla (clean product pages with rich media)

**Key Features:**
- Country/region selector prominent in header
- Category-first navigation within each country shop
- Unified cart across categories within a country
- PayGo financing options integrated at checkout
- Rich product pages with media, specs, reviews

**Backend Alignment:**
- `shops.omnivoltaic.com/kenya` → Odoo COMPANY = OVK
- `shops.omnivoltaic.com/togo` → Odoo COMPANY = OVT
- Single MRP product catalog, filtered by country availability
- Country-specific pricing, inventory, checkout

**Target Audience:** End consumers purchasing products online

**Implementation:** `apps/commerce/shops/` (single Next.js app with country routing)

---

### Tier 3: Enterprise Capabilities (Dimension 3 - Cross-Cutting)

**Pattern:** `[capability].omnivoltaic.com`

#### 3A: Documentation Platform

**Domain:** `docs.omnivoltaic.com/[topic]`

**Status:** EXISTING - NO CHANGES

**Content:**
- Internal documentation
- API references
- Technical guides
- Process documentation
- Organized by topic, not region or solution

**Characteristics:**
- Serves all regions
- Serves all solutions
- Topic-based organization
- Internal/technical audience

---

#### 3B: Asset Management Platform

**Domain:** `assets.omnivoltaic.com`

**Status:** EXISTING - NO CHANGES

**Content:**
- Fleet tracking (all regions)
- IoT device management
- Performance analytics
- Maintenance scheduling
- Asset utilization reporting

**Characteristics:**
- Cross-regional visibility
- Real-time data platform
- Internal teams + partners with asset management needs

**Implementation:** `apps/platforms/assets/`

---

#### 3C: Enterprise Platform (Odoo Portal)

**Domain:** `enterprise.omnivoltaic.com`

**Status:** NEW - Portal to Odoo ERP

**Purpose:** Unified portal interface to Odoo backend with role-based access for both internal and external users

**User Personas:**

**Internal Users (Sales Reps, Operations):**
- Sales Order (SO) creation
- Invoice management
- Quote generation
- Customer account management
- Training administration
- Reporting & analytics

**External Users (B2B Clients, Partners):**
- View orders & invoices
- Submit purchase orders
- Track shipments
- Access training materials
- View account status
- Request quotes

**Technical Architecture:**
- Frontend: Next.js ISR application in `apps/platforms/enterprise/`
- Backend: Direct integration with Odoo API
- Authentication: Odoo SSO or federated auth
- Data: Real-time sync with Odoo (no BFF caching for transactional data)

**Key Capabilities:**
- **Order Management:** SO creation, modification, approval workflows
- **Financial Operations:** Invoice generation, payment tracking, credit limits
- **Training Portal:** Course catalog, enrollment, completion tracking
- **Partner Management:** Partner onboarding, contract management, performance metrics
- **Customer Self-Service:** Order history, invoice download, support tickets

**Implementation:** `apps/platforms/enterprise/` (portal UI) + Odoo API integration

---

### Tier 4: Partner Franchisee Sites

**Pattern:** Custom domains OR branded subdomains

**Examples:**
- `kenya_moto.com` (custom domain)
- `kenyamoto.omnivoltaic.com` (branded subdomain - optional)

**Platform Strategy:**
- Franchisees receive white-label ABS platform infrastructure
- Choose between custom domain (full white-label) or Omnivoltaic-branded subdomain
- Integrated e-commerce capabilities
- Backend connects to Omnivoltaic product catalog + local inventory
- Multi-tenant architecture

**Implementation:** `apps/franchisee/platform/` (multi-tenant with domain-based routing)

---

## dirac-uxi Monorepo Structure

### Recommended Organization

```
apps/isr/
├── omnivoltaic/                  → www.omnivoltaic.com (was: apps/isr/company)
│   └── Corporate hub + navigation to dimensions
│
├── mobility/                      → mobility.omnivoltaic.com (EXISTING)
│   └── E-mobility solution site with products
│
├── [other-solutions]/             → [solution].omnivoltaic.com
│   └── Future solution sites (cross-grid, energy-access, etc.)
│   └── OR path-based under omnivoltaic.com/solutions/
│
apps/regional/                     → DIMENSION 2A
├── ovk/                          → ovk.omnivoltaic.com
├── ovt/                          → ovt.omnivoltaic.com
├── ovn/                          → ovn.omnivoltaic.com (future)
├── ove/                          → ove.omnivoltaic.com (future)
└── shared/                       → Shared regional components

apps/commerce/                     → DIMENSION 2B
└── shops/                        → shops.omnivoltaic.com
    └── Multi-country routing (kenya, togo, nigeria, ethiopia)

apps/platforms/                    → DIMENSION 3
├── docs/                         → docs.omnivoltaic.com (EXISTING)
├── assets/                       → assets.omnivoltaic.com (EXISTING)
└── enterprise/                   → enterprise.omnivoltaic.com (Odoo Portal)

apps/franchisee/
└── platform/                     → Multi-tenant franchisee platform
    └── Deployed to custom domains (kenya_moto.com, etc.)
```

---

## Cross-Repository Implications

### DIRAC-Wide Impacts

**dirac-uxi (This Repository):**
- Implements all user-facing web interfaces
- BFF layer serves content to all domains
- Shared component libraries (@dirac/uxi-blocks)
- ISR strategy for offline resilience

**dirac-fed (Federation Layer):**
- GraphQL schema must support multi-dimensional content queries
- Regional filtering for commerce and regional sites
- Solution-based content organization
- Cross-cutting capability data access

**dirac-abs (Accounting/Business Systems):**
- Odoo COMPANY structure aligns with regional sites
- Single MRP system serves all shops
- Asset management data feeds assets.omnivoltaic.com
- Enterprise platform may integrate with ABS data

**dirac-ats (AfterSale Transaction System):**
- Service requests may originate from regional sites
- Warranty data accessible across all domains
- Customer portal integration with enterprise.omnivoltaic.com

---

### Company-Wide Implications

#### Marketing & Communications
- **Brand consistency:** All digital properties under omnivoltaic.com
- **Regional autonomy:** OV[X] sites can have localized content while maintaining brand
- **Solution-based messaging:** Marketing materials organized by use-case, not product SKU

#### Sales & Business Development
- **B2B flow:** Partners directed to regional OV[X] sites for services/capabilities
- **B2C flow:** Consumers directed to shops.omnivoltaic.com/[country]
- **Solution selling:** Sales teams reference omnivoltaic.com/solutions/ for portfolio presentation

#### Operations & Logistics
- **Inventory management:** Country-specific availability reflected in shops
- **Asset tracking:** Centralized in assets.omnivoltaic.com across all regions
- **Service delivery:** Regional teams manage through OV[X] sites

#### Technology & IT
- **DNS management:** Subdomain strategy requires coordination
- **SSL certificates:** Wildcard certificate for *.omnivoltaic.com
- **CDN configuration:** Country-specific caching for shops.omnivoltaic.com
- **Authentication:** Shared SSO across platforms (enterprise.omnivoltaic.com, assets.omnivoltaic.com)

#### Finance & Legal
- **Compliance:** Country-specific legal requirements in shops.omnivoltaic.com/[country]
- **Payment processing:** Regional payment gateways per shop
- **Tax handling:** Country-specific tax calculations in e-commerce
- **Data residency:** Regional data storage requirements for B2C commerce

---

## Decision Framework

### When to Add a New Subdomain

**Ask:**
1. **Which dimension does this serve?**
   - Solution (use-case driven)
   - Regional (geography driven)
   - Enterprise capability (cross-cutting)
   - Franchisee (independent entity)

2. **Does it fit existing structure?**
   - Can it be a path under an existing domain?
   - Does it require independent deployment?
   - Does it serve a distinct audience?

3. **What is the organizational boundary?**
   - Product team ownership?
   - Regional team ownership?
   - Platform team ownership?

**Decision Matrix:**

| If it's... | Then it should be... | Example |
|------------|---------------------|---------|
| A new solution/use-case | Path under /solutions/ OR new subdomain if large | omnivoltaic.com/solutions/coldchain |
| A new regional entity | New ov[x].omnivoltaic.com subdomain | ovn.omnivoltaic.com |
| A new country shop | Path under shops.omnivoltaic.com | shops.omnivoltaic.com/uganda |
| A new platform capability | New [name].omnivoltaic.com | monitoring.omnivoltaic.com |
| A franchisee | Custom domain or branded subdomain | partner.omnivoltaic.com |

---

## Open Questions & Future Considerations

### 1. Solutions: Path vs Subdomain?

**✅ RESOLVED:** Subdomain-based (e.g., `mobility.omnivoltaic.com`)

**Current Implementation:**
- `apps/isr/mobility/` → `mobility.omnivoltaic.com` (EXISTING)
- Future solutions will follow same pattern: `[solution].omnivoltaic.com`
- Each solution site is independent Next.js ISR app

**Rationale:**
- Independent deployment per solution team
- Clear ownership boundaries
- Dedicated branding per solution
- Matches current `apps/isr/mobility` structure

**Note:** Corporate site (`www.omnivoltaic.com`) provides navigation hub to all solution subdomains

---

### 2. Enterprise Platform Scope

**✅ RESOLVED:** Odoo Portal with dual user personas

**Internal Users:** Sales reps, operations teams (SO creation, invoicing, training admin)
**External Users:** B2B clients, partners (order viewing, quote requests, training access)

**Technical Note:** Real-time Odoo API integration, no BFF caching for transactional data

---

### 3. Product Catalog Organization

**Base Case:** Products are aligned to solution sites based on use-case scenarios

**CMS Implementation:**
- Backend CMS (Odoo) uses **category/collection** taxonomy
- Collections define which products appear on which solution sites
- Primary collection = solution alignment (e.g., "E-Mobility Products", "Cross-Grid Products")
- Products can belong to multiple collections (same product in different contexts)

**Content Presentation Strategies:**

**Strategy 1: Solution-Aligned Collections (Primary)**
```
mobility.omnivoltaic.com/products/
  └── Filtered by collection: "E-Mobility Products"
  
cross-grid.omnivoltaic.com/products/
  └── Filtered by collection: "Cross-Grid Products"
```

**Strategy 2: Cross-Cutting Collections (Secondary)**

Products can also be featured in context-specific collections across sites:

**Example: "New from Omnivoltaic" Collection**
- Landing page: `omnivoltaic.com/new-products`
- Features: Recently launched products across all solutions
- CMS: Collection tagged with `new_launch` + date range filter

**Example: "PayGo Available" Collection**
- Featured on: `omnivoltaic.com/solutions/financing`
- Features: All products with PayGo financing options
- CMS: Collection tagged with `paygo_enabled`

**Example: "Bestsellers" Collection**
- Featured on: `omnivoltaic.com/bestsellers`
- Features: Top-selling products across categories
- CMS: Collection based on sales volume metrics

**CMS Tagging Strategy:**
```
Product in Odoo:
├── Primary Collection: "E-Mobility Products" → mobility.omnivoltaic.com
├── Secondary Collections:
│   ├── "New from Omnivoltaic" → /new-products landing
│   ├── "PayGo Available" → /solutions/financing
│   └── "Featured: Battery Tech" → /featured/batteries
└── Attributes:
    ├── launch_date: 2025-12-01
    ├── paygo_enabled: true
    └── featured_category: batteries
```

**Key Principle:** Collections are flexible presentation layers on top of the product catalog. Same product can appear in multiple contexts without data duplication.

**Implementation:**
- BFF queries Odoo collections via GraphQL
- Frontend components filter/render based on collection membership
- Collections managed by marketing team in Odoo CMS

---

### 4. Multi-Language Strategy

**Current:** Not addressed in domain structure

**Future Consideration:**
- Path-based language routing? (`shops.omnivoltaic.com/kenya/en`, `/kenya/sw`)
- Language subdomain? (`en.omnivoltaic.com`, `fr.omnivoltaic.com`)
- Language parameter? (`shops.omnivoltaic.com/kenya?lang=en`)

**Recommendation:** Path-based for SEO and simplicity, but requires planning

---

### 5. Mobile Apps vs Web

**Current:** This document focuses on web domains

**Future Consideration:**
- Do mobile apps follow same information architecture?
- Deep linking strategy to web domains?
- App-specific content that doesn't map to web?

---

## Implementation Roadmap

### Phase 1: Foundation (Current)
- ✅ Define domain strategy (this document)
- ⏳ Rename/restructure existing apps in dirac-uxi
- ⏳ Deploy omnivoltaic.com corporate hub
- ⏳ Deploy ovk.omnivoltiac.com (Kenya regional B2B)

### Phase 2: Solutions & Commerce (Q1 2026)
- ⏳ Implement solutions structure (path-based)
- ⏳ Launch shops.omnivoltaic.com/kenya (B2C)
- ⏳ Launch shops.omnivoltaic.com/togo (B2C)
- ⏳ Deploy ovt.omnivoltaic.com (Togo regional B2B)

### Phase 3: Platform Expansion (Q2 2026)
- ⏳ Implement enterprise.omnivoltaic.com (Odoo Portal)
- ⏳ Expand to additional regions (OVN, OVE)
- ⏳ Additional country shops (Nigeria, Ethiopia)
- ⏳ Deploy additional solution sites (cross-grid, energy-access)

### Phase 4: Franchisee & Advanced (Q3-Q4 2026)
- ⏳ Launch franchisee platform (multi-tenant)
- ⏳ Onboard first franchisee partners
- ⏳ Implement cross-cutting product collections ("New from Omnivoltaic", etc.)
- ⏳ Implement multi-language support

---

## Maintenance & Updates

### Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.1 | 2026-01-19 | Jannice Wang | Clarifications: Solutions subdomain-based, Enterprise=Odoo Portal, Product collections strategy, Current app mappings |
| 1.0.0 | 2026-01-19 | Jannice Wang | Initial baseline strategy |

### Review Schedule

- **Quarterly Review:** Assess if domain structure is serving business needs
- **Annual Review:** Major strategic reassessment
- **Ad-hoc Review:** When new business units or products are launched

### Change Process

1. **Proposal:** Document proposed change with rationale
2. **Impact Analysis:** Assess cross-repository and company-wide implications
3. **Stakeholder Review:** Marketing, Sales, Ops, IT, Legal
4. **Decision:** Executive approval for company-wide changes
5. **Update Document:** Version bump and change log
6. **Communicate:** Notify all affected teams

---

## Contact & Ownership

**Document Owner:** UXI Team (dirac-uxi)  
**Primary Contact:** Jannice Wang  
**Cross-Functional Stakeholders:**
- Marketing & Communications
- Sales & Business Development
- Operations
- Technology & IT
- Finance & Legal

**Repository:** `dirac-uxi/docs/applications/content-to-domain.md`  
**Related Documents:**
- `content-architecture.md` - Content organization strategy
- `ISR-OFFLINE-RESILIENCE.md` - Offline resilience patterns
- `dirac-uxi/BFF-Contracts-ISR.md` - BFF contract specifications

---

## Appendix: Quick Reference

### Domain Mapping Table

| Domain | Purpose | Target Audience | Dimension | Implementation |
|--------|---------|-----------------|-----------|----------------|
| www.omnivoltaic.com | Corporate hub | All | - | apps/isr/omnivoltaic |
| mobility.omnivoltaic.com | E-mobility solution | B2B customers | 1 | apps/isr/mobility |
| cross-grid.omnivoltaic.com | Cross-grid solution | B2B customers | 1 | apps/isr/cross-grid (future) |
| ovk.omnivoltaic.com | Kenya B2B | B2B Kenya | 2A | apps/regional/ovk |
| ovt.omnivoltaic.com | Togo B2B | B2B Togo | 2A | apps/regional/ovt |
| shops.omnivoltaic.com/kenya | Kenya shop | B2C Kenya | 2B | apps/commerce/shops |
| shops.omnivoltaic.com/togo | Togo shop | B2C Togo | 2B | apps/commerce/shops |
| docs.omnivoltaic.com | Documentation | Internal/partners | 3 | apps/platforms/docs |
| assets.omnivoltaic.com | Asset mgmt | Internal/partners | 3 | apps/platforms/assets |
| enterprise.omnivoltaic.com | Odoo Portal | Internal + B2B clients | 3 | apps/platforms/enterprise |
| kenya_moto.com | Franchisee site | B2C local | 4 | apps/franchisee/platform |

### Information Flow Quick Reference

```
┌─────────────────────────────────────────────────────────────┐
│  DIMENSION 1: Solutions (Use-Case Driven)                   │
│  Company → Solutions → Products                             │
│  Domain: [solution].omnivoltaic.com                         │
│  Example: mobility.omnivoltaic.com, cross-grid.omnivoltaic.com │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  DIMENSION 2A: Regional B2B (Geography Driven)              │
│  Company → OV[X] → Services/Capabilities                    │
│  Domain: ov[x].omnivoltaic.com                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  DIMENSION 2B: Regional B2C Commerce                        │
│  Company → Country Shop → Categories → Products             │
│  Domain: shops.omnivoltaic.com/[country]                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  DIMENSION 3: Enterprise Capabilities (Cross-Cutting)       │
│  Company → [Capability Domains]                             │
│  Domain: [capability].omnivoltaic.com                       │
└─────────────────────────────────────────────────────────────┘
```

---

**Document End**
