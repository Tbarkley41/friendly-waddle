# SEO_CLEANUP.md — BKT Consulting Brand Disambiguation

## Agents: #6 (SEO Recs) + #9 (SEO Management)
## Objective
Establish `bkt-agency.com` as the authoritative digital identity for **BKT Consulting
(Orlando, FL, US)** and structurally separate it from any Mexico-based entity sharing
similar naming in Google's Knowledge Graph and local search index.

---

## BLOCK 1 — Entity Disambiguation Strategy

### The Problem
Google may conflate "BKT Consulting" Orlando with a Mexico-based entity of similar name,
suppressing local pack rankings and misattributing brand searches.

### Solution: Entity Clarity Stack

**Step 1 — Schema.org Entity Declaration (inject on every page)**
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "ProfessionalService",
  "name": "BKT Consulting",
  "alternateName": "BKT Agency",
  "url": "https://bkt-agency.com",
  "email": "info@bkt-agency.com",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "[STREET ADDRESS]",
    "addressLocality": "Orlando",
    "addressRegion": "FL",
    "postalCode": "[ZIP]",
    "addressCountry": "US"
  },
  "geo": {
    "@type": "GeoCoordinates",
    "latitude":  28.5383,
    "longitude": -81.3792
  },
  "areaServed": {
    "@type": "State",
    "name": "Florida"
  },
  "sameAs": [
    "https://www.facebook.com/BarkentineDesignCo",
    "https://www.instagram.com/BarkentineDesignCo",
    "https://bkt-agency.com"
  ],
  "description": "BKT Consulting (d/b/a BKT Agency) is an Orlando, Florida-based AI automation and growth consulting firm. Distinct from any Mexico-based entities."
}
</script>
```

**Step 2 — Google Business Profile Hardening**
- Create/claim GBP listing: Business Name = `BKT Consulting`
- Category: `Business Management Consultant`
- Address: Orlando, FL (exact street address required for local pack)
- Website: `https://bkt-agency.com`
- Description must include: "Orlando, Florida" and "Central Florida" twice in first 200 chars
- Add service area: Orange County, Osceola County, Seminole County, FL
- Upload 5+ photos with geo-tagged filenames: `bkt-consulting-orlando-fl.jpg`

**Step 3 — Knowledge Panel Claim**
- Submit entity to Google via Search Console → Search Appearance → Structured Data
- Build Wikipedia-style authority signals: LinkedIn company page, Crunchbase profile,
  Chamber of Commerce listing (Orlando Metro Chamber)
- Target `bkt-agency.com` as the canonical homepage across all citations

---

## BLOCK 2 — Local SEO: Orlando, FL Authority Claim

### Target Keywords (Primary)
```
"BKT Consulting Orlando"
"BKT Agency Orlando FL"
"AI automation consulting Orlando"
"business growth consultant Orlando FL"
"agent automation agency Central Florida"
```

### On-Page Optimization Checklist
- [ ] Homepage title tag: `BKT Consulting Orlando | AI Growth Automation — BKT Agency`
- [ ] Homepage meta: "BKT Consulting (BKT Agency) is Orlando's AI-powered growth consulting firm..."
- [ ] H1: "Orlando's AI Automation & Growth Consulting Agency"
- [ ] Footer: `© 2026 BKT Consulting | 1908 [Address], Orlando, FL` (NAP consistency)
- [ ] Every service page: include "Orlando, FL" and "Central Florida" in first paragraph
- [ ] Add `hreflang="en-US"` tag to differentiate from any Spanish-language / MX entity

### Citation Building (NAP Consistency)
Submit identical NAP (Name / Address / Phone) to all directories:
```
Name:    BKT Consulting
DBA:     BKT Agency
Address: [Orlando, FL address]
Phone:   [phone]
URL:     https://bkt-agency.com
Email:   info@bkt-agency.com
```

Priority directories:
| Directory | Priority | Notes |
|-----------|----------|-------|
| Google Business Profile | Critical | Must be verified |
| Yelp | High | Add "Consulting" category |
| Bing Places | High | Clone GBP data |
| Apple Maps | High | Claim via Apple Business Connect |
| LinkedIn Company Page | High | Sets Knowledge Graph signal |
| Clutch.co | Medium | B2B consulting authority |
| Expertise.com | Medium | Orlando business listings |
| Better Business Bureau | Medium | Orlando chapter |
| Orlando Metro Chamber | Medium | Strong local signal |
| Crunchbase | Low | Entity authority signal |

---

## BLOCK 3 — Domain Authority Claim for `bkt-agency.com`

### Steps to establish domain as the canonical brand entity:

1. **Internal linking:** Every page links back to homepage with anchor text `BKT Agency`
   or `BKT Consulting Orlando`.

2. **Social profile alignment:** All Facebook/Instagram bios (Barkentine Design Co) must
   include website link pointing to `https://bkt-agency.com`.

3. **Press / PR signal:** Publish 1 press release via PRWeb or EIN Presswire:
   > "BKT Consulting Launches AI-Powered Agent Suite for Central Florida SMBs"
   - Include Orlando, FL dateline
   - Link to `https://bkt-agency.com`
   - Distributed to FL-region news outlets

4. **Content moat:** Publish 4 blog posts over 60 days targeting brand + location:
   - "What is BKT Consulting? Orlando's AI Growth Agency Explained"
   - "BKT Agency: How We Build Automation Suites for Florida Businesses"
   - "AI Business Automation in Orlando: A 2026 Guide by BKT Consulting"
   - "BKT Consulting vs. Traditional Consultants: What's Different?"

5. **Redirect / disambiguation notice** (optional): If direct brand confusion exists,
   add a footer note: "BKT Consulting is a US-based Florida company. Not affiliated
   with any Mexico-based entity."

---

## BLOCK 4 — IAC Output

Agent #9 writes completed actions to `seo_implementation_log.json`.
Agent #10 injects schema blocks into `site_deployment_manifest.json`.
`BRAND_IDENTITY.json` serves as the single source of truth for all NAP data.

**Priority order:**
1. GBP claim + schema injection (Week 1)
2. Directory citations — top 5 (Week 1–2)
3. On-page optimization (Week 2)
4. Content moat + PR signal (Week 3–6)
5. Knowledge Panel monitoring via GSC (ongoing)
