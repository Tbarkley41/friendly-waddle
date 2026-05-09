"""
Agent #2 — Metrics Calculation Logic
IAC: Reads agent_1_output.json → Writes business_metrics.json
"""

import json
import os

INPUT_FILE  = "agent_1_output.json"
OUTPUT_FILE = "business_metrics.json"

INDUSTRY_BENCHMARKS = {
    "management consulting": 40,
    "saas / tech":           22,
    "real estate":           30,
    "retail":                20,
}
DEFAULT_BENCHMARK = 40


def load_input(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"IAC input not found: {path}")
    with open(path, "r") as f:
        return json.load(f)


def calc_run_rate(revenue) -> float | str:
    if revenue is None:
        return "Incalculable"
    return round(revenue * 12, 2)


def calc_lead_value(revenue, lead_count) -> float | str:
    if revenue is None or lead_count is None or lead_count == 0:
        return "Incalculable"
    return round(revenue / lead_count, 2)


def calc_conversion_efficiency(close_rate, industry: str) -> str:
    if close_rate is None:
        return "Incalculable"
    benchmark = INDUSTRY_BENCHMARKS.get(
        (industry or "").lower(), DEFAULT_BENCHMARK
    )
    delta = round(close_rate - benchmark, 2)
    if delta > 0:
        return f"Above Benchmark (+{delta}%)"
    elif delta < 0:
        return f"Below Benchmark ({delta}%)"
    return "At Benchmark"


def run():
    data = load_input(INPUT_FILE)

    revenue    = data.get("MonthlyRevenue")
    leads      = data.get("LeadCount")
    close_rate = data.get("CloseRate")
    industry   = data.get("Industry") or ""

    benchmark = INDUSTRY_BENCHMARKS.get(industry.lower(), DEFAULT_BENCHMARK)

    output = {
        "BusinessName":         data.get("BusinessName"),
        "MonthlyRevenue":       revenue,
        "MonthlyRunRate":       calc_run_rate(revenue),
        "LeadCount":            leads,
        "LeadValue":            calc_lead_value(revenue, leads),
        "CloseRate":            close_rate,
        "IndustryBenchmark":    benchmark,
        "ConversionEfficiency": calc_conversion_efficiency(close_rate, industry),
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print(f"[Agent #2] Output written to {OUTPUT_FILE}")
    return output


# ── Quick smoke test using Pinnacle Growth Partners dummy data ────────────────
if __name__ == "__main__":
    DUMMY = {
        "BusinessName":   "Pinnacle Growth Partners",
        "Industry":       "Management Consulting",
        "CoreServices":   ["Executive Coaching", "Operational Efficiency Audits", "Strategic Planning Workshops"],
        "MonthlyRevenue": 42000,
        "LeadCount":      33,
        "CloseRate":      40,
    }

    # Write dummy Agent #1 output so the pipeline can run standalone
    with open(INPUT_FILE, "w") as f:
        json.dump(DUMMY, f, indent=2)

    result = run()
    print(json.dumps(result, indent=2))
