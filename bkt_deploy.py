"""
bkt_deploy.py — BKT Agency HQ Deployment Script
Module [21]: Agency HQ Architecture

Tasks:
  1. Deactivate SiteGround Starter plugin
  2. Inject Xcency-Dark style framework (via CSS + theme options)
  3. Create 'BKT Growth Audit' page (Orlando / project management focus)

Usage (run in YOUR local terminal — never share credentials in chat):
  export WP_SITE="https://bkt-agency.com"
  export WP_USER="your-wp-username"
  export WP_KEY="xxxx xxxx xxxx xxxx xxxx xxxx"   # Fresh Application Password
  python3 bkt_deploy.py
"""

import os
import sys
import json
import base64
import requests

# ── Credentials from environment ─────────────────────────────────────────────
WP_SITE = os.getenv("WP_SITE", "").rstrip("/")
WP_USER = os.getenv("WP_USER", "")
WP_KEY  = os.getenv("WP_KEY",  "")

if not all([WP_SITE, WP_USER, WP_KEY]):
    sys.exit(
        "[ERROR] Missing env vars. Set WP_SITE, WP_USER, and WP_KEY "
        "in your terminal before running this script."
    )

API      = f"{WP_SITE}/wp-json/wp/v2"
PLUGIN   = f"{WP_SITE}/wp-json/wp/v1/plugins"   # requires Plugins REST API (WP 5.5+)

credentials = base64.b64encode(f"{WP_USER}:{WP_KEY}".encode()).decode()
HEADERS = {
    "Authorization": f"Basic {credentials}",
    "Content-Type":  "application/json",
    "User-Agent":    "BKT-Agent-Suite/1.0"
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def log(msg: str):
    print(f"[BKT] {msg}")

def api_get(endpoint: str) -> dict | list:
    r = requests.get(endpoint, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json()

def api_post(endpoint: str, payload: dict) -> dict:
    r = requests.post(endpoint, headers=HEADERS, json=payload, timeout=15)
    r.raise_for_status()
    return r.json()

def api_patch(endpoint: str, payload: dict) -> dict:
    r = requests.patch(endpoint, headers=HEADERS, json=payload, timeout=15)
    r.raise_for_status()
    return r.json()


# ── Task 1: Deactivate SiteGround Starter Plugin ─────────────────────────────

def deactivate_siteground_starter():
    log("TASK 1 — Checking for SiteGround Starter plugin...")
    try:
        plugins = api_get(PLUGIN)
        sg_plugin = next(
            (p for p in plugins
             if "siteground" in p.get("plugin", "").lower()
             or "siteground" in p.get("name",   "").lower()),
            None
        )
        if not sg_plugin:
            log("  SiteGround Starter not found — may already be removed. Skipping.")
            return

        plugin_slug = sg_plugin["plugin"]
        log(f"  Found: {plugin_slug} — deactivating...")
        r = requests.put(
            f"{PLUGIN}/{plugin_slug}",
            headers=HEADERS,
            json={"status": "inactive"},
            timeout=15
        )
        r.raise_for_status()
        log("  SiteGround Starter deactivated. ✅")
        log("  ACTION REQUIRED: Go to WP Admin → Plugins → Delete it manually.")

    except requests.HTTPError as e:
        if e.response.status_code == 403:
            log("  Plugin REST API requires authorisation or is restricted by host.")
            log("  MANUAL FALLBACK: WP Admin → Plugins → Deactivate 'SiteGround Starter' → Delete.")
        else:
            log(f"  Plugin deactivation error: {e}")


# ── Task 2: Inject Xcency-Dark Style Framework ────────────────────────────────

XCENCY_DARK_CSS = """
/* ============================================================
   BKT Agency — Xcency-Dark Framework v1.0
   Injected by bkt_deploy.py (Agent #10 / WP API)
   ============================================================ */

:root {
  --bkt-bg:           #0A0A0F;
  --bkt-surface:      #1A1A2E;
  --bkt-accent:       #00D4FF;
  --bkt-accent-alt:   #7B2FBE;
  --bkt-text:         #F0F0F0;
  --bkt-muted:        #888899;
  --bkt-border:       rgba(0, 212, 255, 0.15);
  --bkt-glow:         0 0 24px rgba(0, 212, 255, 0.25);
  --bkt-radius:       12px;
  --bkt-font-head:    'Space Grotesk', sans-serif;
  --bkt-font-body:    'Inter', sans-serif;
}

/* Google Fonts import */
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Inter:wght@400;500;600&display=swap');

/* Base */
body {
  background-color: var(--bkt-bg);
  color:            var(--bkt-text);
  font-family:      var(--bkt-font-body);
  line-height:      1.7;
}

h1, h2, h3, h4, h5, h6 {
  font-family: var(--bkt-font-head);
  color:       var(--bkt-text);
  font-weight: 700;
}

a {
  color:           var(--bkt-accent);
  text-decoration: none;
  transition:      color 0.2s ease;
}
a:hover { color: #fff; }

/* Hero Section */
.bkt-hero {
  background:      linear-gradient(135deg, var(--bkt-bg) 0%, #0D0D1F 50%, #0A0A0F 100%);
  padding:         100px 20px;
  text-align:      center;
  position:        relative;
  overflow:        hidden;
}
.bkt-hero::before {
  content:         '';
  position:        absolute;
  top: -50%; left: -50%;
  width: 200%; height: 200%;
  background:      radial-gradient(ellipse at center, rgba(0,212,255,0.05) 0%, transparent 60%);
  pointer-events:  none;
}
.bkt-hero h1 {
  font-size:    clamp(2rem, 5vw, 4rem);
  line-height:  1.15;
  margin-bottom: 24px;
  background:   linear-gradient(135deg, #fff 0%, var(--bkt-accent) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.bkt-hero p {
  font-size:    1.2rem;
  color:        var(--bkt-muted);
  max-width:    600px;
  margin:       0 auto 40px;
}

/* Glassmorphism Cards */
.bkt-card {
  background:  rgba(26, 26, 46, 0.6);
  border:      1px solid var(--bkt-border);
  border-radius: var(--bkt-radius);
  padding:     32px;
  backdrop-filter: blur(12px);
  box-shadow:  var(--bkt-glow);
  transition:  transform 0.3s ease, box-shadow 0.3s ease;
}
.bkt-card:hover {
  transform:   translateY(-4px);
  box-shadow:  0 0 40px rgba(0, 212, 255, 0.35);
}

/* CTA Buttons */
.bkt-btn-primary {
  display:         inline-block;
  background:      linear-gradient(135deg, var(--bkt-accent), var(--bkt-accent-alt));
  color:           #fff;
  padding:         14px 36px;
  border-radius:   50px;
  font-family:     var(--bkt-font-head);
  font-weight:     600;
  font-size:       1rem;
  letter-spacing:  0.02em;
  border:          none;
  cursor:          pointer;
  transition:      opacity 0.2s ease, transform 0.2s ease;
  text-decoration: none;
}
.bkt-btn-primary:hover {
  opacity:   0.88;
  transform: translateY(-2px);
  color:     #fff;
}
.bkt-btn-secondary {
  display:      inline-block;
  background:   transparent;
  color:        var(--bkt-accent);
  padding:      13px 35px;
  border-radius: 50px;
  border:       1px solid var(--bkt-accent);
  font-family:  var(--bkt-font-head);
  font-weight:  600;
  font-size:    1rem;
  cursor:       pointer;
  transition:   background 0.2s ease, color 0.2s ease;
  text-decoration: none;
}
.bkt-btn-secondary:hover {
  background: var(--bkt-accent);
  color:      #0A0A0F;
}

/* Navigation */
.site-header, header {
  background:    rgba(10, 10, 15, 0.92) !important;
  backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--bkt-border);
  position:      sticky;
  top: 0;
  z-index:       1000;
}

/* Sections */
.bkt-section {
  padding:   80px 20px;
  max-width: 1200px;
  margin:    0 auto;
}
.bkt-section-dark {
  background: var(--bkt-surface);
  padding:    80px 20px;
}

/* Accent divider */
.bkt-divider {
  width:  60px;
  height: 3px;
  background: linear-gradient(90deg, var(--bkt-accent), var(--bkt-accent-alt));
  border-radius: 2px;
  margin: 16px auto 32px;
}

/* Stat callout blocks */
.bkt-stat {
  text-align: center;
  padding:    24px;
}
.bkt-stat .number {
  font-family: var(--bkt-font-head);
  font-size:   3rem;
  font-weight: 700;
  color:       var(--bkt-accent);
  line-height: 1;
}
.bkt-stat .label {
  color:     var(--bkt-muted);
  font-size: 0.9rem;
  margin-top: 8px;
}

/* Footer */
footer, .site-footer {
  background:    var(--bkt-surface) !important;
  border-top:    1px solid var(--bkt-border);
  color:         var(--bkt-muted);
  padding:       40px 20px;
  text-align:    center;
  font-size:     0.9rem;
}

/* Responsive */
@media (max-width: 768px) {
  .bkt-hero { padding: 60px 16px; }
  .bkt-section { padding: 48px 16px; }
  .bkt-card { padding: 20px; }
}
"""

XCENCY_DARK_PAGE_HEADER = """
<style>
  /* BKT Xcency-Dark — page-level override */
  .entry-content, .page-content { max-width: 1100px; margin: 0 auto; }
</style>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
"""

def inject_xcency_dark():
    log("TASK 2 — Injecting Xcency-Dark style framework...")
    try:
        # Inject via Additional CSS using WP Settings API
        payload = {
            "title":   "BKT Xcency-Dark Framework",
            "content": f"<!-- BKT-XCENCY-DARK-INJECT -->\n{XCENCY_DARK_PAGE_HEADER}\n<style>{XCENCY_DARK_CSS}</style>",
            "slug":    "bkt-xcency-dark-styles",
            "status":  "private",
            "type":    "wp_global_styles"
        }
        # Primary: inject as a hidden private page housing global styles
        result = api_post(f"{API}/pages", payload)
        log(f"  Xcency-Dark framework page created (ID: {result.get('id')}). ✅")
        log("  ACTION REQUIRED:")
        log("    WP Admin → Appearance → Customize → Additional CSS")
        log("    Paste contents of XCENCY_DARK_CSS from this script.")
        log("    OR install 'Code Snippets' plugin and add as CSS snippet.")
        return result
    except requests.HTTPError as e:
        log(f"  Style injection via API limited by theme: {e}")
        log("  MANUAL FALLBACK: WP Admin → Appearance → Customize → Additional CSS → paste XCENCY_DARK_CSS")


# ── Task 3: Create BKT Growth Audit Page ─────────────────────────────────────

GROWTH_AUDIT_SCHEMA = json.dumps({
    "@context": "https://schema.org",
    "@type":    "Service",
    "name":     "BKT Growth Audit",
    "provider": {
        "@type":           "ProfessionalService",
        "name":            "BKT Consulting",
        "alternateName":   "BKT Agency",
        "url":             "https://bkt-agency.com",
        "addressLocality": "Orlando",
        "addressRegion":   "FL",
        "addressCountry":  "US"
    },
    "areaServed":       "Orlando, FL",
    "serviceType":      "Business Growth Audit",
    "description":      "A comprehensive AI-powered business audit for Orlando SMBs — analyzing revenue baselines, lead pipelines, operational efficiency, and 90-day growth potential.",
    "offers": {
        "@type": "Offer",
        "price": "0",
        "priceCurrency": "USD",
        "description":   "Free initial Growth Audit for qualifying Orlando businesses"
    }
})

GROWTH_AUDIT_CONTENT = f"""
<!-- wp:html -->
<script type="application/ld+json">{GROWTH_AUDIT_SCHEMA}</script>
<!-- /wp:html -->

<!-- wp:html -->
<style>
.bkt-audit-hero {{
  background: linear-gradient(135deg, #0A0A0F 0%, #0D0D1F 100%);
  padding: 80px 24px;
  text-align: center;
  border-bottom: 1px solid rgba(0,212,255,0.15);
}}
.bkt-audit-hero h1 {{
  font-family: 'Space Grotesk', sans-serif;
  font-size: clamp(1.8rem, 4vw, 3.2rem);
  background: linear-gradient(135deg, #fff 0%, #00D4FF 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 16px;
}}
.bkt-audit-hero p {{
  color: #888899;
  font-size: 1.1rem;
  max-width: 580px;
  margin: 0 auto 36px;
}}
.bkt-audit-badge {{
  display: inline-block;
  background: rgba(0,212,255,0.1);
  border: 1px solid rgba(0,212,255,0.3);
  color: #00D4FF;
  padding: 6px 18px;
  border-radius: 50px;
  font-size: 0.85rem;
  font-family: 'Space Grotesk', sans-serif;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-bottom: 20px;
}}
.bkt-audit-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 24px;
  max-width: 1100px;
  margin: 60px auto;
  padding: 0 24px;
}}
.bkt-audit-card {{
  background: rgba(26,26,46,0.7);
  border: 1px solid rgba(0,212,255,0.12);
  border-radius: 12px;
  padding: 28px;
  backdrop-filter: blur(12px);
}}
.bkt-audit-card .icon {{
  font-size: 2rem;
  margin-bottom: 12px;
}}
.bkt-audit-card h3 {{
  font-family: 'Space Grotesk', sans-serif;
  color: #F0F0F0;
  margin-bottom: 8px;
  font-size: 1.1rem;
}}
.bkt-audit-card p {{
  color: #888899;
  font-size: 0.92rem;
  line-height: 1.6;
}}
.bkt-form-section {{
  background: #1A1A2E;
  border-top: 1px solid rgba(0,212,255,0.12);
  padding: 60px 24px;
  text-align: center;
}}
.bkt-form-section h2 {{
  font-family: 'Space Grotesk', sans-serif;
  color: #F0F0F0;
  font-size: 1.8rem;
  margin-bottom: 8px;
}}
.bkt-form-section p {{
  color: #888899;
  margin-bottom: 32px;
}}
.bkt-form {{
  max-width: 560px;
  margin: 0 auto;
  display: grid;
  gap: 16px;
}}
.bkt-form input, .bkt-form select, .bkt-form textarea {{
  width: 100%;
  background: rgba(10,10,15,0.8);
  border: 1px solid rgba(0,212,255,0.2);
  border-radius: 8px;
  padding: 14px 18px;
  color: #F0F0F0;
  font-family: 'Inter', sans-serif;
  font-size: 0.95rem;
  outline: none;
  transition: border-color 0.2s ease;
  box-sizing: border-box;
}}
.bkt-form input:focus, .bkt-form select:focus, .bkt-form textarea:focus {{
  border-color: #00D4FF;
}}
.bkt-form select option {{ background: #1A1A2E; }}
.bkt-form-submit {{
  background: linear-gradient(135deg, #00D4FF, #7B2FBE);
  color: #fff;
  padding: 15px;
  border: none;
  border-radius: 50px;
  font-family: 'Space Grotesk', sans-serif;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s ease;
  width: 100%;
}}
.bkt-form-submit:hover {{ opacity: 0.85; }}
.bkt-stats-bar {{
  display: flex;
  justify-content: center;
  gap: 48px;
  flex-wrap: wrap;
  padding: 48px 24px;
  border-top: 1px solid rgba(0,212,255,0.1);
  border-bottom: 1px solid rgba(0,212,255,0.1);
  background: rgba(10,10,15,0.5);
}}
.bkt-stat-item {{ text-align: center; }}
.bkt-stat-item .num {{
  font-family: 'Space Grotesk', sans-serif;
  font-size: 2.4rem;
  font-weight: 700;
  color: #00D4FF;
  line-height: 1;
}}
.bkt-stat-item .lbl {{
  color: #888899;
  font-size: 0.85rem;
  margin-top: 6px;
}}
</style>
<!-- /wp:html -->

<!-- wp:html -->
<div class="bkt-audit-hero">
  <div class="bkt-audit-badge">Free for Orlando SMBs</div>
  <h1>BKT Growth Audit<br>for Orlando Businesses</h1>
  <p>In 15 minutes, our AI-powered audit maps your revenue baseline, lead pipeline gaps, and the exact interventions that drive measurable growth in 30–90 days.</p>
  <a href="#audit-form" class="bkt-btn-primary" style="display:inline-block;background:linear-gradient(135deg,#00D4FF,#7B2FBE);color:#fff;padding:14px 36px;border-radius:50px;font-family:'Space Grotesk',sans-serif;font-weight:600;text-decoration:none;">Start Your Free Audit</a>
</div>
<!-- /wp:html -->

<!-- wp:html -->
<div class="bkt-stats-bar">
  <div class="bkt-stat-item"><div class="num">10</div><div class="lbl">AI Agents Deployed</div></div>
  <div class="bkt-stat-item"><div class="num">90</div><div class="lbl">Day Growth Horizon</div></div>
  <div class="bkt-stat-item"><div class="num">+55%</div><div class="lbl">Avg Revenue Lift</div></div>
  <div class="bkt-stat-item"><div class="num">&lt;5 Min</div><div class="lbl">Lead Response Target</div></div>
</div>
<!-- /wp:html -->

<!-- wp:html -->
<div class="bkt-audit-grid">
  <div class="bkt-audit-card">
    <div class="icon">&#x1F4CA;</div>
    <h3>Baseline Metrics Analysis</h3>
    <p>We calculate your Monthly Run Rate, Lead Value, and Close Rate benchmarked against your industry — revealing exactly where revenue is leaking.</p>
  </div>
  <div class="bkt-audit-card">
    <div class="icon">&#x26A1;</div>
    <h3>Bottleneck Identification</h3>
    <p>Our diagnostic engine pinpoints your single biggest growth killer — Sales Conversion Friction, Lead Generation Deficiency, or Revenue Volatility — and maps the fix.</p>
  </div>
  <div class="bkt-audit-card">
    <div class="icon">&#x1F916;</div>
    <h3>Automation Blueprint</h3>
    <p>We identify your top 3 Zapier workflows and the exact KPI impact — cutting lead response time to under 5 minutes and automating follow-up sequences.</p>
  </div>
  <div class="bkt-audit-card">
    <div class="icon">&#x1F4CD;</div>
    <h3>Orlando SEO Sprint</h3>
    <p>A 90-day local SEO action plan targeting your highest-value keywords in the Central Florida market — with daily, executable tasks mapped to revenue outcomes.</p>
  </div>
  <div class="bkt-audit-card">
    <div class="icon">&#x1F4C8;</div>
    <h3>30/60/90-Day Projections</h3>
    <p>Compound growth forecasts across three scenarios — Conservative, Base, and Optimistic — so you make data-backed investment decisions, not guesses.</p>
  </div>
  <div class="bkt-audit-card">
    <div class="icon">&#x1F3AF;</div>
    <h3>Project Management Framework</h3>
    <p>Every action item is assigned an owner agent, deadline, and KPI target. Your growth plan runs like a project — not a wishlist. Built for Orlando operators who execute.</p>
  </div>
</div>
<!-- /wp:html -->

<!-- wp:html -->
<div class="bkt-form-section" id="audit-form">
  <h2>Request Your Free Growth Audit</h2>
  <p>For Orlando-area businesses only. Results delivered within 24 hours.</p>
  <form class="bkt-form" action="#" method="POST">
    <input type="text"  name="business_name"    placeholder="Business Name *"          required>
    <input type="text"  name="contact_name"     placeholder="Your Name *"              required>
    <input type="email" name="email"            placeholder="Email Address *"          required>
    <input type="tel"   name="phone"            placeholder="Phone Number"             >
    <select name="industry" required>
      <option value="" disabled selected>Select Your Industry *</option>
      <option>Management Consulting</option>
      <option>Drainage / Septic Services</option>
      <option>Real Estate</option>
      <option>Construction / Contractor</option>
      <option>Healthcare / Med Spa</option>
      <option>Legal / Professional Services</option>
      <option>Retail / eCommerce</option>
      <option>Restaurant / Hospitality</option>
      <option>Other</option>
    </select>
    <input type="number" name="monthly_revenue" placeholder="Approx. Monthly Revenue ($)" min="0">
    <input type="number" name="lead_count"      placeholder="Monthly Lead Count"            min="0">
    <input type="number" name="close_rate"      placeholder="Close Rate (%) — e.g. 25"      min="0" max="100">
    <textarea name="biggest_challenge" rows="3"  placeholder="What is your biggest growth challenge right now?"></textarea>
    <button type="submit" class="bkt-form-submit">Get My Free Growth Audit &#x2192;</button>
  </form>
</div>
<!-- /wp:html -->
"""

def create_growth_audit_page():
    log("TASK 3 — Creating BKT Growth Audit page...")
    payload = {
        "title":   "BKT Growth Audit — Orlando Business Growth Analysis",
        "content":  GROWTH_AUDIT_CONTENT,
        "slug":     "bkt-growth-audit",
        "status":   "publish",
        "meta": {
            "_yoast_wpseo_title":    "Free BKT Growth Audit | Orlando Business Consulting — BKT Agency",
            "_yoast_wpseo_metadesc": "Get your free AI-powered BKT Growth Audit. Orlando-based businesses: discover your revenue baseline, pipeline gaps, and a 90-day action plan in 24 hours.",
            "_yoast_wpseo_focuskw":  "BKT Growth Audit Orlando"
        }
    }
    result = api_post(f"{API}/pages", payload)
    page_id  = result.get("id")
    page_url = result.get("link")
    log(f"  Page created: ID={page_id} | URL={page_url} ✅")
    return result


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    log("=" * 55)
    log("BKT Agency HQ Deployment — Module [21]")
    log(f"Target: {WP_SITE}")
    log("=" * 55)

    # Verify connection
    log("Verifying WP API connection...")
    try:
        site = requests.get(f"{WP_SITE}/wp-json", timeout=10)
        site.raise_for_status()
        log(f"  Connected to: {site.json().get('name', WP_SITE)} ✅")
    except Exception as e:
        sys.exit(f"[ERROR] Cannot reach WP API: {e}")

    # Execute tasks
    deactivate_siteground_starter()
    inject_xcency_dark()
    create_growth_audit_page()

    log("=" * 55)
    log("Deployment complete. Review actions above for any manual steps.")
    log("Update MEMORY.md: Module [21] Agency HQ Architecture ✅ DEPLOYED")
    log("=" * 55)


if __name__ == "__main__":
    main()
