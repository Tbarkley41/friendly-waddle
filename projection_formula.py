"""
Agent #7 — Growth Projection Formula
Calculates CMGR and 30/90/180-day compound forecasts from IAC inputs.
IAC: Reads business_metrics.json, automation_strategy.json, seo_recommendations.json
     Writes growth_projections.json
"""

import json
import re
import os
from datetime import date

# ── IAC file paths ────────────────────────────────────────────────────────────
INPUTS = {
    "metrics":    "business_metrics.json",
    "automation": "automation_strategy.json",
    "seo":        "seo_recommendations.json",
}
OUTPUT_FILE = "growth_projections.json"

HORIZONS = {
    "Day30":  {"months": 1, "confidence": "High Confidence"},
    "Day90":  {"months": 3, "confidence": "Medium Confidence"},
    "Day180": {"months": 6, "confidence": "Low Confidence"},
}

SCENARIO_MULTIPLIERS = {"Conservative": 0.6, "Base": 1.0, "Optimistic": 1.4}


# ── Helpers ───────────────────────────────────────────────────────────────────

def load(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"IAC input missing: {path}")
    with open(path) as f:
        return json.load(f)


def extract_pct(text: str) -> float:
    """Pull first numeric value from an impact string like '+25% organic traffic'."""
    if not text or not isinstance(text, str):
        return 0.0
    match = re.search(r"[-+]?(\d+(?:\.\d+)?)\s*%", text)
    return float(match.group(1)) if match else 0.0


def cmgr(total_lift_pct: float, months: int = 6) -> float:
    """
    Compound Monthly Growth Rate derived from total projected lift over the
    full 6-month horizon.
      CMGR = (1 + total_lift/100)^(1/months) - 1
    """
    if months <= 0:
        return 0.0
    return round((1 + total_lift_pct / 100) ** (1 / months) - 1, 6)


def compound(baseline: float, rate: float, months: int) -> float:
    """Apply compound growth: baseline * (1 + rate)^months."""
    return round(baseline * (1 + rate) ** months, 2)


def project_close_rate(baseline: float, lift_pct: float, months: int,
                       scenario_mult: float = 1.0) -> float:
    """Linear close rate lift capped at 95%."""
    adjusted_lift = (lift_pct * scenario_mult * months) / 6
    return round(min(baseline + adjusted_lift, 95.0), 2)


# ── Driver Aggregation ────────────────────────────────────────────────────────

def aggregate_drivers(automation: dict, seo: dict) -> dict:
    zapier_lead_lift      = 0.0
    zapier_close_lift     = 0.0
    zapier_churn_reduction = 0.0

    for wf in automation.get("Top3Workflows", []):
        pct = extract_pct(wf.get("EstimatedImpact", ""))
        kpi = wf.get("KPITarget", "").lower()
        if "leadcount" in kpi or "lead" in kpi:
            zapier_lead_lift = max(zapier_lead_lift, pct)
        elif "closerate" in kpi or "close" in kpi:
            zapier_close_lift = max(zapier_close_lift, pct)
        elif "churn" in kpi or "retention" in kpi:
            zapier_churn_reduction = max(zapier_churn_reduction, pct)

    seo_lead_lift    = 0.0
    seo_traffic_lift = 0.0

    for task in seo.get("DailyTasks", []):
        pct    = extract_pct(task.get("EstimatedImpact", ""))
        impact = task.get("EstimatedImpact", "").lower()
        if "lead" in impact:
            seo_lead_lift = max(seo_lead_lift, pct)
        if "traffic" in impact or "organic" in impact or "impression" in impact:
            seo_traffic_lift = max(seo_traffic_lift, pct)

    # Combine lead lifts — avoid double-counting by blending overlap at 50%
    total_lead_lift = (max(zapier_lead_lift, seo_lead_lift)
                       + min(zapier_lead_lift, seo_lead_lift) * 0.5)

    return {
        "ZapierCloseRateLift":   zapier_close_lift,
        "ZapierLeadLift":        zapier_lead_lift,
        "ZapierChurnReduction":  zapier_churn_reduction,
        "SEOLeadLift":           seo_lead_lift,
        "SEOTrafficLift":        seo_traffic_lift,
        "TotalLeadLift":         round(total_lead_lift, 2),
        "TotalCloseRateLift":    round(zapier_close_lift, 2),
        "TotalTrafficLift":      round(seo_traffic_lift, 2),
    }


# ── Core Projection Engine ────────────────────────────────────────────────────

def build_projections(baseline_rev: float, baseline_leads: float,
                      baseline_close: float, drivers: dict) -> tuple[dict, float]:

    revenue_cmgr = cmgr(drivers["TotalLeadLift"] + drivers["TotalCloseRateLift"])
    lead_cmgr    = cmgr(drivers["TotalLeadLift"])

    projections = {}
    for label, cfg in HORIZONS.items():
        m = cfg["months"]
        scenarios = {}
        for scenario, mult in SCENARIO_MULTIPLIERS.items():
            scenarios[scenario] = {
                "Revenue":   compound(baseline_rev,   revenue_cmgr * mult, m),
                "Leads":     compound(baseline_leads, lead_cmgr * mult,    m),
                "CloseRate": project_close_rate(baseline_close,
                                                drivers["TotalCloseRateLift"],
                                                m, mult),
            }
        projections[label] = {"Confidence": cfg["confidence"], **scenarios}

    return projections, round(revenue_cmgr, 6)


# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    metrics    = load(INPUTS["metrics"])
    automation = load(INPUTS["automation"])
    seo        = load(INPUTS["seo"])

    baseline_rev   = metrics.get("MonthlyRevenue") or 0
    baseline_leads = metrics.get("LeadCount")      or 0
    baseline_close = metrics.get("CloseRate")      or 0

    drivers               = aggregate_drivers(automation, seo)
    projections, rev_cmgr = build_projections(baseline_rev, baseline_leads,
                                               baseline_close, drivers)

    output = {
        "BusinessName":    metrics.get("BusinessName"),
        "GeneratedDate":   date.today().isoformat(),
        "BaselineSnapshot": {
            "MonthlyRevenue": baseline_rev,
            "LeadCount":      baseline_leads,
            "CloseRate":      baseline_close,
        },
        "GrowthDrivers": {
            **{k: v for k, v in drivers.items()
               if k.startswith("Total")},
            "CMGR": rev_cmgr,
        },
        "Projections": projections,
        "ProjectionDisclaimer": (
            "Forecasts are model-based estimates. "
            "Validate against actuals at each horizon."
        ),
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print(f"[Agent #7] Output written to {OUTPUT_FILE}")
    return output


# ── Smoke Test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Inject minimal dummy IAC files if not present
    DUMMY_METRICS = {
        "BusinessName": "Pinnacle Growth Partners", "Industry": "Management Consulting",
        "MonthlyRevenue": 42000, "LeadCount": 33, "CloseRate": 40,
        "MonthlyRunRate": 504000, "LeadValue": 1272.73,
        "IndustryBenchmark": 40, "ConversionEfficiency": "At Benchmark"
    }
    DUMMY_AUTOMATION = {
        "BusinessName": "Pinnacle Growth Partners",
        "PrimaryBottleneck": "No Critical Bottleneck Detected",
        "ImpactSeverity": "Low",
        "Top3Workflows": [
            {"Rank": 1, "WorkflowName": "Lead Nurture Sequence",
             "KPITarget": "CloseRate",  "EstimatedImpact": "+25% CloseRate in 30 days"},
            {"Rank": 2, "WorkflowName": "Ad-to-Sheet Lead Capture",
             "KPITarget": "LeadCount",  "EstimatedImpact": "+30% LeadCount in 30 days"},
            {"Rank": 3, "WorkflowName": "Retention Alert System",
             "KPITarget": "RetentionRate", "EstimatedImpact": "+28% RetentionRate in 30 days"},
        ]
    }
    DUMMY_SEO = {
        "BusinessName": "Pinnacle Growth Partners",
        "PriorityMode": "Brand Awareness",
        "DailyTasks": [
            {"Rank": 1, "TaskName": "Thought Leadership Article",
             "EstimatedImpact": "+25% LinkedIn profile views in 30 days"},
            {"Rank": 2, "TaskName": "Internal Linking Audit",
             "EstimatedImpact": "+10% page authority in 30 days"},
            {"Rank": 3, "TaskName": "Build Local Citation Listings",
             "EstimatedImpact": "+10% local SEO ranking signals in 45 days"},
        ]
    }

    for path, data in [
        (INPUTS["metrics"],    DUMMY_METRICS),
        (INPUTS["automation"], DUMMY_AUTOMATION),
        (INPUTS["seo"],        DUMMY_SEO),
    ]:
        if not os.path.exists(path):
            with open(path, "w") as f:
                json.dump(data, f, indent=2)

    result = run()
    print(json.dumps(result, indent=2))
