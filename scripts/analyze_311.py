#!/usr/bin/env python3
"""
Comprehensive analytical engine for DC 311 Sentinel.
Queries data/warehouse.duckdb and produces four committed JSON artifacts:
1. data/summary_top.json          - All specific service code & 129 description trends, monthly series, and categories
2. data/geography_stats.json      - Ward (8) and ANC (46) volumes, Location Quotients, SLA, and map matrices
3. data/emerging_issues.json      - YTD Same-Period YoY, 30-Day surge & acceleration, weather-adjusted residuals
4. data/operational_patterns.json - Daily weather sensitivity, unstructured DETAILS audit & NLP insights, Agency SLA, repeats

Strictly adheres to:
- Strictly zero emojis across code, logs, and outputs
- No 90-day window in emerging analysis (uses YTD Same-Period YoY + 30-Day Surge + Weather-Adjusted Residual)
"""

import json
import math
import os
import re
import time
from collections import Counter, defaultdict
from datetime import date, timedelta

import duckdb

from spatial_utils import anc_sort_key
from text_utils import clean_service_desc

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WAREHOUSE_DB = os.path.join(BASE_DIR, "data", "warehouse.duckdb")
CONFIG_JSON = os.path.join(BASE_DIR, "data", "config.json")

OUT_SUMMARY_TOP = os.path.join(BASE_DIR, "data", "summary_top.json")
OUT_GEOGRAPHY = os.path.join(BASE_DIR, "data", "geography_stats.json")
OUT_EMERGING = os.path.join(BASE_DIR, "data", "emerging_issues.json")
OUT_PATTERNS = os.path.join(BASE_DIR, "data", "operational_patterns.json")

STOPWORDS = {
    "the", "and", "for", "that", "this", "with", "from", "have", "has", "had",
    "are", "was", "were", "been", "being", "will", "would", "could", "should",
    "not", "but", "they", "their", "there", "here", "where", "when", "what",
    "which", "who", "whom", "whose", "why", "how", "all", "any", "both", "each",
    "few", "more", "most", "other", "some", "such", "no", "nor", "only", "own",
    "same", "so", "than", "too", "very", "can", "just", "don", "now", "into",
    "out", "about", "after", "again", "against", "above", "below", "between",
    "down", "during", "before", "under", "over", "through", "further", "then",
    "once", "please", "thank", "thanks", "you", "your", "our", "my", "me", "we",
    "us", "he", "she", "it", "its", "his", "her", "them",
}

TOKEN_RE = re.compile(r"\b[a-z][a-z0-9'-]{2,22}\b")
ADMIN_TEST_CODES = {"Test01", "SAMPLE", "TEST", "zTest1", "S0081"}
ADMIN_TEST_SQL_IN = "('Test01', 'SAMPLE', 'TEST', 'zTest1', 'S0081')"


def is_test_code(code: str, desc: str = "") -> bool:
    if not code:
        return False
    if code in ADMIN_TEST_CODES:
        return True
    lower_code = code.lower()
    lower_desc = desc.lower() if desc else ""
    if lower_code.startswith("ztest") or lower_code.startswith("test"):
        return True
    if "do not use" in lower_desc:
        return True
    return False


def log_rate_ratio_and_z(c26, n26_days, c25, n25_days):
    r26 = (c26 + 0.5) / max(1.0, float(n26_days))
    r25 = (c25 + 0.5) / max(1.0, float(n25_days))
    rr = r26 / r25
    se = math.sqrt(1.0 / (c26 + 0.5) + 1.0 / (c25 + 0.5))
    z = math.log(rr) / se
    pct = ((r26 - r25) / r25) * 100.0
    return round(rr, 3), round(pct, 1), round(z, 2)


def pearson_r(xs, ys):
    n = len(xs)
    if n < 5:
        return 0.0
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx < 1e-9 or dy < 1e-9:
        return 0.0
    return round(num / (dx * dy), 3)


def fit_weather_baseline_and_predict(daily_2025, daily_2026_ytd):
    """
    Fits a daily linear response model on 2025 daily counts:
      count = b0 + b_rain * rain_3d_in + b_snow * snow_3d_in + b_temp * (temp_mean_f - 60)
              + b_freeze * max(0, 35 - temp_mean_f) + b_wknd * is_weekend
    using ridge-regularized normal equations, then predicts expected 2026 YTD volume
    given actual 2026 daily weather.
    """
    if not daily_2025 or not daily_2026_ytd:
        return sum(r["cnt"] for r in daily_2026_ytd)

    def feat_vec(d):
        t = d["temp_mean_f"]
        return [
            1.0,
            float(d["rain_3d_in"]),
            float(d["snow_3d_in"]),
            (t - 60.0) / 20.0,
            max(0.0, 35.0 - t) / 15.0,
            1.0 if d["is_wknd"] else 0.0,
        ]

    k = 6
    xtx = [[0.0] * k for _ in range(k)]
    xty = [0.0] * k
    for d in daily_2025:
        x = feat_vec(d)
        y = float(d["cnt"])
        for i in range(k):
            xty[i] += x[i] * y
            for j in range(k):
                xtx[i][j] += x[i] * x[j]

    for i in range(1, k):
        xtx[i][i] += 5.0
    xtx[0][0] += 1e-6

    aug = [xtx[i][:] + [xty[i]] for i in range(k)]
    for i in range(k):
        pivot = aug[i][i]
        if abs(pivot) < 1e-12:
            continue
        for j in range(i, k + 1):
            aug[i][j] /= pivot
        for r in range(k):
            if r != i:
                factor = aug[r][i]
                for j in range(i, k + 1):
                    aug[r][j] -= factor * aug[i][j]

    beta = [aug[i][k] for i in range(k)]

    pred_total = 0.0
    for d in daily_2026_ytd:
        x = feat_vec(d)
        val = sum(b * xi for b, xi in zip(beta, x))
        pred_total += max(0.0, val)

    return round(pred_total, 1)


def extract_details_and_corridor_insights(con):
    """
    Audits all populated DETAILS records across 2025-2026, extracts unstructured
    narrative templates, keywords, and bigrams, and computes top street corridors
    per service code from STREETADDRESS.
    """
    print("Auditing unstructured DETAILS text and street corridor patterns...")

    # 1. Full audit of all non-null DETAILS records
    details_rows = con.execute(
        """
        SELECT
            service_code,
            service_desc,
            agency,
            req_year,
            ward,
            is_closed,
            resolution_hours,
            TRIM(REPLACE(details, CHR(160), ' ')) AS clean_details
        FROM requests
        WHERE details IS NOT NULL
          AND LENGTH(TRIM(details)) > 0
          AND service_code NOT IN ('Test01', 'SAMPLE', 'TEST', 'zTest1', 'S0081')
        """
    ).fetchall()

    by_code_details = defaultdict(lambda: {
        "count_2025": 0,
        "count_2026": 0,
        "service_desc": "",
        "agency": "",
        "unigrams": Counter(),
        "bigrams": Counter(),
        "sample_notes": Counter(),
        "closed_count": 0,
    })
    distinct_notes = Counter()
    dgs_mass_closure_count = 0

    for scode, sdesc, agency, yr, ward, is_closed, res_hrs, text in details_rows:
        info = by_code_details[scode]
        info["service_desc"] = sdesc
        info["agency"] = agency
        if int(yr) == 2025:
            info["count_2025"] += 1
        else:
            info["count_2026"] += 1
        if is_closed:
            info["closed_count"] += 1
        info["sample_notes"][text] += 1
        distinct_notes[(scode, sdesc, agency, int(yr), text)] += 1
        if "closed this request for any further action" in text.lower():
            dgs_mass_closure_count += 1

        tokens = [
            t for t in TOKEN_RE.findall(text.lower())
            if t not in STOPWORDS and not t.isdigit() and len(t) >= 3
        ]
        info["unigrams"].update(set(tokens))
        if len(tokens) >= 2:
            bis = {f"{tokens[i]} {tokens[i+1]}" for i in range(len(tokens) - 1)}
            info["bigrams"].update(bis)

    details_code_summary = []
    for scode, info in sorted(
        by_code_details.items(),
        key=lambda kv: kv[1]["count_2025"] + kv[1]["count_2026"],
        reverse=True,
    ):
        tot_d = info["count_2025"] + info["count_2026"]
        top_note, top_note_cnt = info["sample_notes"].most_common(1)[0]
        details_code_summary.append({
            "service_code": scode,
            "service_desc": info["service_desc"],
            "agency": info["agency"],
            "details_2025": info["count_2025"],
            "details_2026": info["count_2026"],
            "total_details": tot_d,
            "closed_pct": round(info["closed_count"] / max(1, tot_d) * 100.0, 1),
            "dominant_note": top_note,
            "dominant_note_count": top_note_cnt,
            "top_terms": [w for w, _ in info["unigrams"].most_common(8)],
            "top_phrases": [b for b, _ in info["bigrams"].most_common(6)],
        })

    distinct_notes_list = [
        {
            "service_code": scode,
            "service_desc": sdesc,
            "agency": agency,
            "year": yr,
            "count": cnt,
            "note_text": note,
        }
        for (scode, sdesc, agency, yr, note), cnt in distinct_notes.most_common(25)
    ]

    # 2. Extract top street corridor hotspots from STREETADDRESS per service code (2026 YTD)
    corridor_rows = con.execute(
        """
        WITH norm_addr AS (
            SELECT
                service_code,
                TRIM(REGEXP_REPLACE(UPPER(COALESCE(street_address, '')), '^[0-9-]+\\s+', '')) AS street_corridor,
                ward
            FROM requests
            WHERE req_year = 2026
              AND street_address IS NOT NULL
              AND LENGTH(TRIM(street_address)) >= 5
              AND service_code NOT IN ('Test01', 'SAMPLE', 'TEST', 'zTest1', 'S0081')
        )
        SELECT
            service_code,
            street_corridor,
            MODE(ward) AS primary_ward,
            COUNT(*) AS cnt
        FROM norm_addr
        WHERE LENGTH(street_corridor) >= 4
          AND street_corridor NOT IN ('UNKNOWN', 'NONE', 'NULL')
        GROUP BY service_code, street_corridor
        HAVING COUNT(*) >= 10
        QUALIFY ROW_NUMBER() OVER (PARTITION BY service_code ORDER BY COUNT(*) DESC) <= 5
        """
    ).fetchall()

    corridors_by_code = defaultdict(list)
    for scode, corr, w, cnt in corridor_rows:
        corridors_by_code[scode].append({
            "corridor": corr,
            "ward": str(w) if w else "",
            "count_2026": int(cnt),
        })

    details_audit = {
        "total_populated_2025_2026": len(details_rows),
        "populated_2025": sum(x["details_2025"] for x in details_code_summary),
        "populated_2026": sum(x["details_2026"] for x in details_code_summary),
        "dgs_mass_closure_boilerplate_count": dgs_mass_closure_count,
        "dgs_mass_closure_share_pct": round(dgs_mass_closure_count / max(1, len(details_rows)) * 100.0, 1),
        "by_service_code": details_code_summary,
        "distinct_notes": distinct_notes_list,
    }

    return details_audit, corridors_by_code


def run_analytics():
    t0 = time.time()
    with open(CONFIG_JSON, "r", encoding="utf-8") as f:
        config = json.load(f)
    ward_council = config.get("ward_councilmembers", {})

    con = duckdb.connect(WAREHOUSE_DB, read_only=True)
    con.execute("SET TimeZone='America/New_York';")

    max_date_2026 = con.execute(
        f"SELECT MAX(add_date) FROM requests WHERE req_year = 2026 AND service_code NOT IN {ADMIN_TEST_SQL_IN}"
    ).fetchone()[0]
    max_doy_2026 = con.execute(
        f"SELECT MAX(req_doy) FROM requests WHERE req_year = 2026 AND service_code NOT IN {ADMIN_TEST_SQL_IN}"
    ).fetchone()[0]
    d30_start_2026 = con.execute(
        f"SELECT CAST('{max_date_2026}' AS DATE) - INTERVAL 29 DAY"
    ).fetchone()[0].strftime("%Y-%m-%d")
    d30_min_doy = max(1, int(max_doy_2026) - 29)

    n_days_2026_ytd = int(max_doy_2026)
    n_days_2025_ytd = int(max_doy_2026)

    print(
        f"Running analytics through cutoff {max_date_2026} (DOY {max_doy_2026}, "
        f"30-day window starting {d30_start_2026})..."
    )

    details_audit, corridors_by_code = extract_details_and_corridor_insights(con)

    # =========================================================================
    # 1. ALL SPECIFIC SERVICE QUERIES & 129 DESCRIPTIONS (summary_top.json)
    # =========================================================================
    # Also collect all distinct descriptions per service_code so renames (e.g. S0311, SIGTRAMA) are transparent
    desc_alias_rows = con.execute(
        """
        SELECT
            service_code,
            service_desc,
            COUNT(*) FILTER (WHERE req_year = 2026) AS c26,
            COUNT(*) FILTER (WHERE req_year = 2025) AS c25
        FROM requests
        WHERE service_code NOT IN ('Test01', 'SAMPLE', 'TEST', 'zTest1', 'S0081')
        GROUP BY service_code, service_desc
        ORDER BY service_code, c26 DESC, c25 DESC
        """
    ).fetchall()

    code_primary_desc = {}
    code_aliases = defaultdict(list)
    raw_descriptions_2026 = []
    for scode, sdesc, c26, c25 in desc_alias_rows:
        if is_test_code(scode, sdesc):
            continue
        cleaned_desc = clean_service_desc(sdesc)
        if scode not in code_primary_desc:
            code_primary_desc[scode] = cleaned_desc
        else:
            if cleaned_desc != code_primary_desc[scode]:
                code_aliases[scode].append({"service_desc": cleaned_desc, "count_2026": int(c26), "count_2025": int(c25)})
        if c26 > 0 or c25 > 0:
            raw_descriptions_2026.append({
                "service_code": scode,
                "service_desc": cleaned_desc,
                "count_2026_ytd": int(c26),
                "count_2025_full": int(c25),
            })
    raw_descriptions_2026.sort(key=lambda x: x["count_2026_ytd"], reverse=True)

    service_rows = con.execute(
        f"""
        SELECT
            service_code,
            ANY_VALUE(category) AS category,
            MODE(agency) AS agency,
            COUNT(*) FILTER (WHERE req_year = 2026 AND req_doy <= {max_doy_2026}) AS c26_ytd,
            COUNT(*) FILTER (WHERE req_year = 2025 AND req_doy <= {max_doy_2026}) AS c25_ytd,
            COUNT(*) FILTER (WHERE req_year = 2025) AS c25_full,
            COUNT(*) FILTER (WHERE req_year = 2026 AND req_doy BETWEEN {d30_min_doy} AND {max_doy_2026}) AS c26_30d,
            COUNT(*) FILTER (WHERE req_year = 2025 AND req_doy BETWEEN {d30_min_doy} AND {max_doy_2026}) AS c25_30d,
            ROUND(MEDIAN(resolution_hours) FILTER (WHERE req_year = 2026 AND resolution_hours IS NOT NULL), 1) AS med_res_hrs_26,
            ROUND(QUANTILE_CONT(resolution_hours, 0.90) FILTER (WHERE req_year = 2026 AND resolution_hours IS NOT NULL), 1) AS p90_res_hrs_26,
            ROUND(AVG(CASE WHEN sla_met THEN 100.0 ELSE 0.0 END) FILTER (WHERE req_year = 2026 AND sla_met IS NOT NULL), 1) AS sla_pct_26,
            COUNT(*) FILTER (WHERE req_year = 2026 AND NOT is_closed) AS open_26,
            COUNT(*) FILTER (WHERE details IS NOT NULL AND LENGTH(TRIM(details)) > 0) AS details_cnt_all,
            ROUND(MEDIAN(resolution_hours) FILTER (WHERE req_year = 2026 AND req_doy <= {max_doy_2026} AND resolution_hours IS NOT NULL), 1) AS med_res_hrs_26_ytd,
            ROUND(MEDIAN(resolution_hours) FILTER (WHERE req_year = 2025 AND req_doy <= {max_doy_2026} AND resolution_hours IS NOT NULL), 1) AS med_res_hrs_25_ytd,
            ROUND(MEDIAN(resolution_hours) FILTER (WHERE req_year = 2026 AND req_doy BETWEEN {d30_min_doy} AND {max_doy_2026} AND resolution_hours IS NOT NULL), 1) AS med_res_hrs_26_30d,
            ROUND(MEDIAN(resolution_hours) FILTER (WHERE req_year = 2025 AND req_doy BETWEEN {d30_min_doy} AND {max_doy_2026} AND resolution_hours IS NOT NULL), 1) AS med_res_hrs_25_30d
        FROM requests
        WHERE service_code NOT IN ('Test01', 'SAMPLE', 'TEST', 'zTest1', 'S0081')
        GROUP BY service_code
        ORDER BY c26_ytd DESC, c25_full DESC
        """
    ).fetchall()

    monthly_code_rows = con.execute(
        """
        SELECT service_code, req_year, req_month, COUNT(*) AS cnt
        FROM requests
        WHERE service_code NOT IN ('Test01', 'SAMPLE', 'TEST', 'zTest1', 'S0081')
        GROUP BY service_code, req_year, req_month
        """
    ).fetchall()
    monthly_by_code = defaultdict(lambda: {2025: [0] * 12, 2026: [0] * 12})
    for scode, yr, mo, cnt in monthly_code_rows:
        if int(yr) in (2025, 2026) and 1 <= int(mo) <= 12:
            monthly_by_code[scode][int(yr)][int(mo) - 1] = int(cnt)

    filtered_service_rows = [r for r in service_rows if not is_test_code(r[0])]
    tot_26_ytd = sum(r[3] for r in filtered_service_rows)
    tot_25_ytd = sum(r[4] for r in filtered_service_rows)
    tot_25_full = sum(r[5] for r in filtered_service_rows)

    sorted_25 = sorted(filtered_service_rows, key=lambda r: r[4], reverse=True)
    rank_25_map = {r[0]: idx + 1 for idx, r in enumerate(sorted_25) if r[4] > 0}

    all_queries = []
    for idx, r in enumerate(filtered_service_rows):
        (
            scode, cat, agency, c26_ytd, c25_ytd, c25_full,
            c26_30d, c25_30d, med_hrs, p90_hrs, sla_pct, open_26, details_cnt_all,
            med_res_26_ytd, med_res_25_ytd, med_res_26_30d, med_res_25_30d
        ) = r
        sdesc = code_primary_desc.get(scode, scode)
        rank_26 = idx + 1 if c26_ytd > 0 else None
        rank_25 = rank_25_map.get(scode)
        rank_delta = (rank_25 - rank_26) if (rank_26 and rank_25) else None
        rr_ytd, yoy_pct, z_ytd = log_rate_ratio_and_z(c26_ytd, n_days_2026_ytd, c25_ytd, n_days_2025_ytd)
        rr_30d, d30_pct, z_30d = log_rate_ratio_and_z(c26_30d, 30, c25_30d, 30)

        all_queries.append({
            "service_code": scode,
            "service_desc": sdesc,
            "legacy_aliases": [a["service_desc"] for a in code_aliases.get(scode, [])],
            "category": cat,
            "agency": agency,
            "count_2026_ytd": int(c26_ytd),
            "count_2025_ytd": int(c25_ytd),
            "count_2025_full": int(c25_full),
            "count_2026_30d": int(c26_30d),
            "count_2025_30d": int(c25_30d),
            "yoy_pct": yoy_pct if c25_ytd >= 10 else None,
            "d30_yoy_pct": d30_pct if c25_30d >= 5 else None,
            "share_2026_pct": round(c26_ytd / max(1, tot_26_ytd) * 100.0, 2),
            "rank_2026": rank_26,
            "rank_2025_ytd": rank_25,
            "rank_delta": rank_delta,
            "median_res_hours": float(med_hrs) if med_hrs is not None else None,
            "median_res_hours_2026_ytd": float(med_res_26_ytd) if med_res_26_ytd is not None else None,
            "median_res_hours_2025_ytd": float(med_res_25_ytd) if med_res_25_ytd is not None else None,
            "median_res_hours_2026_30d": float(med_res_26_30d) if med_res_26_30d is not None else None,
            "median_res_hours_2025_30d": float(med_res_25_30d) if med_res_25_30d is not None else None,
            "p90_res_hours": float(p90_hrs) if p90_hrs is not None else None,
            "sla_pct": float(sla_pct) if sla_pct is not None else None,
            "open_count": int(open_26),
            "open_pct": round(open_26 / max(1, c26_ytd) * 100.0, 1) if c26_ytd > 0 else 0.0,
            "details_count": int(details_cnt_all),
            "top_corridors_2026": corridors_by_code.get(scode, []),
            "monthly_2025": monthly_by_code[scode][2025],
            "monthly_2026": monthly_by_code[scode][2026],
        })

    # Category family rollups
    cat_agg = defaultdict(lambda: {
        "c26_ytd": 0, "c25_ytd": 0, "c25_full": 0,
        "c26_30d": 0, "c25_30d": 0, "open_26": 0,
        "monthly_2025": [0] * 12, "monthly_2026": [0] * 12,
        "query_count": 0,
    })
    for q in all_queries:
        c = cat_agg[q["category"]]
        c["c26_ytd"] += q["count_2026_ytd"]
        c["c25_ytd"] += q["count_2025_ytd"]
        c["c25_full"] += q["count_2025_full"]
        c["c26_30d"] += q["count_2026_30d"]
        c["c25_30d"] += q["count_2025_30d"]
        c["open_26"] += q["open_count"]
        c["query_count"] += 1
        for m in range(12):
            c["monthly_2025"][m] += q["monthly_2025"][m]
            c["monthly_2026"][m] += q["monthly_2026"][m]

    cat_sla_rows = con.execute(
        f"""
        SELECT
            category,
            ROUND(MEDIAN(resolution_hours) FILTER (WHERE req_year = 2026 AND resolution_hours IS NOT NULL), 1) AS med_hrs,
            ROUND(AVG(CASE WHEN sla_met THEN 100.0 ELSE 0.0 END) FILTER (WHERE req_year = 2026 AND sla_met IS NOT NULL), 1) AS sla_pct
        FROM requests
        WHERE service_code NOT IN {ADMIN_TEST_SQL_IN}
        GROUP BY category
        """
    ).fetchall()
    cat_sla_map = {r[0]: (r[1], r[2]) for r in cat_sla_rows}

    categories_list = []
    for cat_name, c in cat_agg.items():
        _, yoy_pct, _ = log_rate_ratio_and_z(c["c26_ytd"], n_days_2026_ytd, c["c25_ytd"], n_days_2025_ytd)
        _, d30_pct, _ = log_rate_ratio_and_z(c["c26_30d"], 30, c["c25_30d"], 30)
        med_hrs, sla_pct = cat_sla_map.get(cat_name, (None, None))
        categories_list.append({
            "category": cat_name,
            "query_count": c["query_count"],
            "count_2026_ytd": c["c26_ytd"],
            "count_2025_ytd": c["c25_ytd"],
            "count_2025_full": c["c25_full"],
            "yoy_pct": yoy_pct,
            "d30_yoy_pct": d30_pct,
            "share_2026_pct": round(c["c26_ytd"] / max(1, tot_26_ytd) * 100.0, 2),
            "median_res_hours": float(med_hrs) if med_hrs is not None else None,
            "sla_pct": float(sla_pct) if sla_pct is not None else None,
            "open_count": c["open_26"],
            "monthly_2025": c["monthly_2025"],
            "monthly_2026": c["monthly_2026"],
        })
    categories_list.sort(key=lambda x: x["count_2026_ytd"], reverse=True)

    city_kpi_row = con.execute(
        f"""
        SELECT
            ROUND(MEDIAN(resolution_hours) FILTER (WHERE req_year = 2026 AND resolution_hours IS NOT NULL), 1) AS med_res_26,
            ROUND(MEDIAN(resolution_hours) FILTER (WHERE req_year = 2025 AND resolution_hours IS NOT NULL), 1) AS med_res_25,
            ROUND(AVG(CASE WHEN sla_met THEN 100.0 ELSE 0.0 END) FILTER (WHERE req_year = 2026 AND sla_met IS NOT NULL), 1) AS sla_26,
            ROUND(AVG(CASE WHEN sla_met THEN 100.0 ELSE 0.0 END) FILTER (WHERE req_year = 2025 AND sla_met IS NOT NULL), 1) AS sla_25,
            COUNT(*) FILTER (WHERE req_year = 2026 AND NOT is_closed) AS open_26,
            COUNT(*) FILTER (WHERE details IS NOT NULL AND LENGTH(TRIM(details)) > 0) AS details_all,
            COUNT(*) FILTER (WHERE req_year = 2026 AND req_doy BETWEEN {d30_min_doy} AND {max_doy_2026}) AS d30_26,
            COUNT(*) FILTER (WHERE req_year = 2025 AND req_doy BETWEEN {d30_min_doy} AND {max_doy_2026}) AS d30_25
        FROM requests
        WHERE service_code NOT IN {ADMIN_TEST_SQL_IN}
        """
    ).fetchone()

    _, city_yoy_pct, _ = log_rate_ratio_and_z(tot_26_ytd, n_days_2026_ytd, tot_25_ytd, n_days_2025_ytd)
    _, city_d30_pct, _ = log_rate_ratio_and_z(city_kpi_row[6], 30, city_kpi_row[7], 30)

    summary_top_payload = {
        "metadata": {
            "cutoff_date": str(max_date_2026),
            "cutoff_doy": int(max_doy_2026),
            "d30_start_date": d30_start_2026,
            "total_2026_ytd": int(tot_26_ytd),
            "total_2025_ytd": int(tot_25_ytd),
            "total_2025_full": int(tot_25_full),
            "total_all_rows": int(tot_26_ytd + tot_25_full),
            "yoy_pct": city_yoy_pct,
            "d30_2026": int(city_kpi_row[6]),
            "d30_2025": int(city_kpi_row[7]),
            "d30_yoy_pct": city_d30_pct,
            "median_res_hours_2026": float(city_kpi_row[0] or 0.0),
            "median_res_hours_2025": float(city_kpi_row[1] or 0.0),
            "sla_pct_2026": float(city_kpi_row[2] or 0.0),
            "sla_pct_2025": float(city_kpi_row[3] or 0.0),
            "open_backlog_2026": int(city_kpi_row[4] or 0),
            "details_populated_total": int(city_kpi_row[5] or 0),
            "distinct_service_codes_2026": sum(1 for q in all_queries if q["count_2026_ytd"] > 0),
            "distinct_service_codes_all": len(all_queries),
            "distinct_descriptions_2026": sum(1 for d in raw_descriptions_2026 if d["count_2026_ytd"] > 0),
        },
        "categories": categories_list,
        "service_queries": all_queries,
        "raw_descriptions": raw_descriptions_2026,
    }

    with open(OUT_SUMMARY_TOP, "w", encoding="utf-8") as f:
        json.dump(summary_top_payload, f, separators=(",", ":"))
    print(
        f"Wrote {OUT_SUMMARY_TOP} ({len(all_queries)} canonical service codes, "
        f"{len(raw_descriptions_2026)} distinct descriptions)"
    )

    # =========================================================================
    # 2. WARD & ANC AREAS OF CONCERN + LOCATION QUOTIENTS (geography_stats.json)
    # =========================================================================
    city_code_share = {
        q["service_code"]: (q["count_2026_ytd"] / max(1, tot_26_ytd))
        for q in all_queries
        if q["count_2026_ytd"] > 0
    }
    city_cat_share = {
        c["category"]: (c["count_2026_ytd"] / max(1, tot_26_ytd))
        for c in categories_list
        if c["count_2026_ytd"] > 0
    }
    code_desc_map = {q["service_code"]: q["service_desc"] for q in all_queries}
    code_cat_map = {q["service_code"]: q["category"] for q in all_queries}

    def build_geo_profiles(geo_col, min_lq_count):
        base_rows = con.execute(
            f"""
            SELECT
                {geo_col} AS geo_id,
                COUNT(*) FILTER (WHERE req_year = 2026 AND req_doy <= {max_doy_2026}) AS c26_ytd,
                COUNT(*) FILTER (WHERE req_year = 2025 AND req_doy <= {max_doy_2026}) AS c25_ytd,
                COUNT(*) FILTER (WHERE req_year = 2025) AS c25_full,
                COUNT(*) FILTER (WHERE req_year = 2026 AND req_doy BETWEEN {d30_min_doy} AND {max_doy_2026}) AS c26_30d,
                COUNT(*) FILTER (WHERE req_year = 2025 AND req_doy BETWEEN {d30_min_doy} AND {max_doy_2026}) AS c25_30d,
                ROUND(MEDIAN(resolution_hours) FILTER (WHERE req_year = 2026 AND resolution_hours IS NOT NULL), 1) AS med_hrs,
                ROUND(AVG(CASE WHEN sla_met THEN 100.0 ELSE 0.0 END) FILTER (WHERE req_year = 2026 AND sla_met IS NOT NULL), 1) AS sla_pct,
                COUNT(*) FILTER (WHERE req_year = 2026 AND NOT is_closed) AS open_cnt,
                COUNT(DISTINCT mar_id) FILTER (WHERE req_year = 2026 AND mar_id IS NOT NULL) AS unique_addresses
            FROM requests
            WHERE {geo_col} IS NOT NULL AND service_code NOT IN ('Test01', 'SAMPLE', 'TEST', 'zTest1', 'S0081')
            GROUP BY {geo_col}
            """
        ).fetchall()

        code_geo_rows = con.execute(
            f"""
            SELECT
                {geo_col} AS geo_id,
                service_code,
                COUNT(*) FILTER (WHERE req_year = 2026 AND req_doy <= {max_doy_2026}) AS c26_ytd,
                COUNT(*) FILTER (WHERE req_year = 2025 AND req_doy <= {max_doy_2026}) AS c25_ytd,
                COUNT(*) FILTER (WHERE req_year = 2026 AND req_doy BETWEEN {d30_min_doy} AND {max_doy_2026}) AS c26_30d,
                COUNT(*) FILTER (WHERE req_year = 2025 AND req_doy BETWEEN {d30_min_doy} AND {max_doy_2026}) AS c25_30d,
                COUNT(*) FILTER (WHERE req_year = 2026 AND NOT is_closed) AS open_cnt
            FROM requests
            WHERE {geo_col} IS NOT NULL AND service_code NOT IN ('Test01', 'SAMPLE', 'TEST', 'zTest1', 'S0081')
            GROUP BY {geo_col}, service_code
            """
        ).fetchall()

        by_geo = defaultdict(list)
        for g_id, scode, c26, c25, d30_26, d30_25, op_cnt in code_geo_rows:
            by_geo[str(g_id)].append((scode, int(c26), int(c25), int(d30_26), int(d30_25), int(op_cnt)))

        profiles = {}
        for row in base_rows:
            g_id = str(row[0])
            _, c26_ytd, c25_ytd, c25_full, c26_30d, c25_30d, med_hrs, sla_pct, open_cnt, uniq_addr = row
            _, yoy_pct, _ = log_rate_ratio_and_z(c26_ytd, n_days_2026_ytd, c25_ytd, n_days_2025_ytd)
            _, d30_pct, _ = log_rate_ratio_and_z(c26_30d, 30, c25_30d, 30)

            code_list = by_geo[g_id]
            top_by_vol = sorted(code_list, key=lambda x: x[1], reverse=True)

            top_requests = []
            signature_lq = []
            emerging_in_geo = []
            per_cat = defaultdict(lambda: {"c26": 0, "c25": 0, "d30_26": 0, "d30_25": 0, "open": 0})
            per_code_map = {}

            for scode, sc26, sc25, sd30_26, sd30_25, sop in top_by_vol:
                if is_test_code(scode):
                    continue
                sdesc = code_desc_map.get(scode, scode)
                scat = code_cat_map.get(scode, "Government Info & Admin")
                per_cat[scat]["c26"] += sc26
                per_cat[scat]["c25"] += sc25
                per_cat[scat]["d30_26"] += sd30_26
                per_cat[scat]["d30_25"] += sd30_25
                per_cat[scat]["open"] += sop

                local_share = sc26 / max(1, c26_ytd)
                city_sh = city_code_share.get(scode, 0.0)
                lq = round(local_share / city_sh, 2) if city_sh > 0 else 1.0
                rr_s, yoy_s, z_s = log_rate_ratio_and_z(sc26, n_days_2026_ytd, sc25, n_days_2025_ytd)
                _, d30_s, _ = log_rate_ratio_and_z(sd30_26, 30, sd30_25, 30)

                item = {
                    "service_code": scode,
                    "service_desc": sdesc,
                    "category": scat,
                    "count_2026_ytd": sc26,
                    "count_2025_ytd": sc25,
                    "share_pct": round(local_share * 100.0, 2),
                    "yoy_pct": yoy_s if sc25 >= 5 else None,
                    "d30_yoy_pct": d30_s if sd30_25 >= 3 else None,
                    "lq": lq,
                    "open_count": sop,
                }
                if len(top_requests) < 15 and sc26 > 0:
                    top_requests.append(item)
                if sc26 >= min_lq_count and lq >= 1.25:
                    signature_lq.append(item)
                if sc26 >= max(20, min_lq_count) and sc25 >= 10 and rr_s >= 1.25 and z_s >= 2.5:
                    emerging_in_geo.append({**item, "z_score": z_s, "rate_ratio": rr_s})

                per_code_map[scode] = {
                    "c26": sc26,
                    "c25": sc25,
                    "yoy_pct": yoy_s if sc25 >= 5 else 0.0,
                    "d30_pct": d30_s if sd30_25 >= 3 else 0.0,
                    "lq": lq,
                    "open_pct": round(sop / max(1, sc26) * 100.0, 1) if sc26 > 0 else 0.0,
                }

            signature_lq.sort(key=lambda x: x["lq"], reverse=True)
            emerging_in_geo.sort(key=lambda x: x["rate_ratio"] * math.log1p(x["count_2026_ytd"]), reverse=True)

            cat_breakdown = {}
            for cname, cm in per_cat.items():
                c_share = cm["c26"] / max(1, c26_ytd)
                c_city_sh = city_cat_share.get(cname, 0.0)
                c_lq = round(c_share / c_city_sh, 2) if c_city_sh > 0 else 1.0
                _, c_yoy, _ = log_rate_ratio_and_z(cm["c26"], n_days_2026_ytd, cm["c25"], n_days_2025_ytd)
                _, c_d30, _ = log_rate_ratio_and_z(cm["d30_26"], 30, cm["d30_25"], 30)
                cat_breakdown[cname] = {
                    "c26": cm["c26"],
                    "c25": cm["c25"],
                    "yoy_pct": c_yoy,
                    "d30_pct": c_d30,
                    "lq": c_lq,
                    "open_pct": round(cm["open"] / max(1, cm["c26"]) * 100.0, 1) if cm["c26"] > 0 else 0.0,
                }

            ward_num = g_id if geo_col == "ward" else (re.match(r"^([1-8])", g_id).group(1) if re.match(r"^([1-8])", g_id) else "")
            profiles[g_id] = {
                "id": g_id,
                "ward": ward_num,
                "councilmember": ward_council.get(str(ward_num), ""),
                "count_2026_ytd": int(c26_ytd),
                "count_2025_ytd": int(c25_ytd),
                "count_2025_full": int(c25_full),
                "count_2026_30d": int(c26_30d),
                "count_2025_30d": int(c25_30d),
                "yoy_pct": yoy_pct,
                "d30_yoy_pct": d30_pct,
                "share_city_pct": round(c26_ytd / max(1, tot_26_ytd) * 100.0, 2),
                "median_res_hours": float(med_hrs) if med_hrs is not None else None,
                "sla_pct": float(sla_pct) if sla_pct is not None else None,
                "open_count": int(open_cnt),
                "open_pct": round(open_cnt / max(1, c26_ytd) * 100.0, 1) if c26_ytd > 0 else 0.0,
                "unique_addresses": int(uniq_addr),
                "top_requests": top_requests[:12],
                "signature_concerns": signature_lq[:10],
                "emerging_requests": emerging_in_geo[:8],
                "categories": cat_breakdown,
                "top_codes": {k: per_code_map[k] for k in [q["service_code"] for q in all_queries[:45]] if k in per_code_map},
            }
        return profiles

    wards_profiles = build_geo_profiles("ward", min_lq_count=35)
    ancs_profiles = build_geo_profiles("anc", min_lq_count=15)

    ordered_ancs = {
        k: ancs_profiles[k]
        for k in sorted(ancs_profiles.keys(), key=anc_sort_key)
    }
    ordered_wards = {
        str(w): wards_profiles[str(w)]
        for w in range(1, 9)
        if str(w) in wards_profiles
    }

    geography_payload = {
        "wards": ordered_wards,
        "ancs": ordered_ancs,
        "map_dynamic_codes": [
            {"service_code": q["service_code"], "service_desc": q["service_desc"], "category": q["category"]}
            for q in all_queries[:45]
            if q["service_code"] not in ADMIN_TEST_CODES
        ],
    }
    with open(OUT_GEOGRAPHY, "w", encoding="utf-8") as f:
        json.dump(geography_payload, f, separators=(",", ":"))
    print(f"Wrote {OUT_GEOGRAPHY} ({len(ordered_wards)} Wards, {len(ordered_ancs)} ANCs)")

    # =========================================================================
    # 3. EMERGING ISSUES & WEATHER-ADJUSTED SURGE DETECTION (emerging_issues.json)
    # =========================================================================
    print("Computing weather-adjusted baselines and emerging issue trajectories...")

    weather_rows = con.execute(
        f"""
        SELECT
            weather_date,
            EXTRACT(YEAR FROM weather_date) AS yr,
            EXTRACT(DAYOFYEAR FROM weather_date) AS doy,
            EXTRACT(ISODOW FROM weather_date) IN (6, 7) AS is_wknd,
            temp_max_f,
            temp_min_f,
            temp_mean_f,
            precip_in,
            rain_in,
            snow_in,
            rain_3d_in,
            snow_3d_in,
            is_rainy_day,
            is_heavy_rain_day,
            is_snow_day,
            is_freeze_day,
            is_heat_day
        FROM weather_daily
        WHERE (EXTRACT(YEAR FROM weather_date) = 2025)
           OR (EXTRACT(YEAR FROM weather_date) = 2026 AND EXTRACT(DAYOFYEAR FROM weather_date) <= {max_doy_2026})
        ORDER BY weather_date
        """
    ).fetchall()

    weather_by_date = {}
    for w in weather_rows:
        dt_str = str(w[0])
        weather_by_date[dt_str] = {
            "date": dt_str,
            "year": int(w[1]),
            "doy": int(w[2]),
            "is_wknd": bool(w[3]),
            "temp_max_f": float(w[4]),
            "temp_min_f": float(w[5]),
            "temp_mean_f": float(w[6]),
            "precip_in": float(w[7]),
            "rain_in": float(w[8]),
            "snow_in": float(w[9]),
            "rain_3d_in": float(w[10]),
            "snow_3d_in": float(w[11]),
            "is_rainy_day": bool(w[12]),
            "is_heavy_rain_day": bool(w[13]),
            "is_snow_day": bool(w[14]),
            "is_freeze_day": bool(w[15]),
            "is_heat_day": bool(w[16]),
        }

    daily_code_rows = con.execute(
        f"""
        SELECT
            service_code,
            CAST(add_date AS VARCHAR) AS dt,
            COUNT(*) AS cnt
        FROM requests
        WHERE service_code NOT IN ('Test01', 'SAMPLE', 'TEST', 'zTest1', 'S0081')
          AND ((req_year = 2025) OR (req_year = 2026 AND req_doy <= {max_doy_2026}))
        GROUP BY service_code, add_date
        """
    ).fetchall()

    code_date_cnt = defaultdict(dict)
    for scode, dt_str, cnt in daily_code_rows:
        code_date_cnt[scode][dt_str] = int(cnt)

    dates_2025_full = [d for d, info in weather_by_date.items() if info["year"] == 2025]
    dates_2026_ytd = [d for d, info in weather_by_date.items() if info["year"] == 2026 and info["doy"] <= max_doy_2026]

    emerging_items = []
    weather_sensitivity_items = []

    for q in all_queries:
        scode = q["service_code"]
        if is_test_code(scode):
            continue
        c26_ytd = q["count_2026_ytd"]
        c25_ytd = q["count_2025_ytd"]
        c26_30d = q["count_2026_30d"]
        c25_30d = q["count_2025_30d"]

        if c26_ytd < 15 and c25_ytd < 15:
            continue

        rr_ytd, pct_ytd, z_ytd = log_rate_ratio_and_z(c26_ytd, n_days_2026_ytd, c25_ytd, n_days_2025_ytd)
        rr_30d, pct_30d, z_30d = log_rate_ratio_and_z(c26_30d, 30, c25_30d, 30)
        accel_ratio = round(rr_30d / max(0.1, rr_ytd), 2)

        cnt_map = code_date_cnt[scode]
        series_25 = [{**weather_by_date[d], "cnt": cnt_map.get(d, 0)} for d in dates_2025_full]
        series_26_ytd = [{**weather_by_date[d], "cnt": cnt_map.get(d, 0)} for d in dates_2026_ytd]
        all_series = series_25 + series_26_ytd

        rain3d_vals = [x["rain_3d_in"] for x in all_series]
        temp_vals = [x["temp_mean_f"] for x in all_series]
        snow3d_vals = [x["snow_3d_in"] for x in all_series]
        cnt_vals = [x["cnt"] for x in all_series]

        r_rain = pearson_r(rain3d_vals, cnt_vals)
        r_temp = pearson_r(temp_vals, cnt_vals)
        r_snow = pearson_r(snow3d_vals, cnt_vals)

        dry_days = [x["cnt"] for x in all_series if x["rain_3d_in"] < 0.05 and x["snow_3d_in"] < 0.05]
        heavy_rain_days = [x["cnt"] for x in all_series if x["rain_3d_in"] >= 0.50]
        freeze_days = [x["cnt"] for x in all_series if x["is_freeze_day"]]
        heat_days = [x["cnt"] for x in all_series if x["is_heat_day"]]
        mild_days = [x["cnt"] for x in all_series if 50.0 <= x["temp_mean_f"] <= 72.0]

        avg_dry = (sum(dry_days) / len(dry_days)) if dry_days else 0.1
        avg_heavy_rain = (sum(heavy_rain_days) / len(heavy_rain_days)) if heavy_rain_days else 0.0
        avg_freeze = (sum(freeze_days) / len(freeze_days)) if freeze_days else 0.0
        avg_heat = (sum(heat_days) / len(heat_days)) if heat_days else 0.0
        avg_mild = (sum(mild_days) / len(mild_days)) if mild_days else 0.1

        heavy_rain_mult = round((avg_heavy_rain + 0.05) / (avg_dry + 0.05), 2)
        freeze_mult = round((avg_freeze + 0.05) / (avg_mild + 0.05), 2)
        heat_mult = round((avg_heat + 0.05) / (avg_mild + 0.05), 2)

        if abs(r_snow) >= 0.25 or freeze_mult >= 1.8:
            weather_tag = "Snow / Freeze Sensitive"
        elif r_rain >= 0.10 or heavy_rain_mult >= 1.25:
            weather_tag = "Rainfall Sensitive"
        elif r_temp >= 0.22 or heat_mult >= 1.40:
            weather_tag = "Warmth / Heat Sensitive"
        elif r_temp <= -0.20:
            weather_tag = "Cold Weather Sensitive"
        else:
            weather_tag = "Weather Neutral"

        expected_26_weather = fit_weather_baseline_and_predict(series_25, series_26_ytd) if c25_ytd >= 30 else float(c25_ytd)
        weather_adj_pct = (
            round((c26_ytd - expected_26_weather) / max(1.0, expected_26_weather) * 100.0, 1)
            if c25_ytd >= 20
            else None
        )

        if c25_ytd < 5 and c26_ytd >= 25:
            status = "NEW_OR_EXPANDED"
        elif c26_ytd >= 40 and rr_ytd >= 1.20 and z_ytd >= 3.0:
            if weather_adj_pct is not None and weather_adj_pct < 8.0 and weather_tag != "Weather Neutral":
                status = "WEATHER_DRIVEN_INCREASE"
            elif c26_30d >= 15 and accel_ratio >= 1.15:
                status = "EMERGING_ACCELERATING"
            else:
                status = "EMERGING_SURGE"
        elif c26_30d >= 25 and rr_30d >= 1.30 and z_30d >= 2.8:
            status = "RECENT_30D_SURGE"
        elif c25_ytd >= 40 and rr_ytd <= 0.80 and z_ytd <= -3.0:
            status = "DECLINING"
        else:
            status = "STABLE"

        def to_days(h):
            if h is None:
                return None
            return int(math.ceil(float(h) / 24.0))

        ytd_d26 = to_days(q.get("median_res_hours_2026_ytd"))
        ytd_d25 = to_days(q.get("median_res_hours_2025_ytd"))
        if ytd_d25 is not None and ytd_d26 is not None:
            if ytd_d25 > 0:
                ytd_res_pct = round(((ytd_d26 - ytd_d25) / ytd_d25) * 100.0, 1)
            elif ytd_d26 == 0:
                ytd_res_pct = 0.0
            else:
                ytd_res_pct = None
        else:
            ytd_res_pct = None

        d30_d26 = to_days(q.get("median_res_hours_2026_30d"))
        d30_d25 = to_days(q.get("median_res_hours_2025_30d"))
        if d30_d25 is not None and d30_d26 is not None:
            if d30_d25 > 0:
                d30_res_pct = round(((d30_d26 - d30_d25) / d30_d25) * 100.0, 1)
            elif d30_d26 == 0:
                d30_res_pct = 0.0
            else:
                d30_res_pct = None
        else:
            d30_res_pct = None

        item = {
            "service_code": scode,
            "service_desc": q["service_desc"],
            "legacy_aliases": q["legacy_aliases"],
            "category": q["category"],
            "agency": q["agency"],
            "status": status,
            "ytd_2026": c26_ytd,
            "ytd_2025": c25_ytd,
            "ytd_rr": rr_ytd,
            "ytd_yoy_pct": pct_ytd if c25_ytd >= 5 else None,
            "ytd_z": z_ytd,
            "ytd_res_days_2026": ytd_d26,
            "ytd_res_days_2025": ytd_d25,
            "ytd_res_pct": ytd_res_pct,
            "d30_2026": c26_30d,
            "d30_2025": c25_30d,
            "d30_rr": rr_30d,
            "d30_yoy_pct": pct_30d if c25_30d >= 5 else None,
            "d30_z": z_30d,
            "d30_res_days_2026": d30_d26,
            "d30_res_days_2025": d30_d25,
            "d30_res_pct": d30_res_pct,
            "acceleration_ratio": accel_ratio,
            "weather_expected_2026": expected_26_weather,
            "weather_adj_yoy_pct": weather_adj_pct,
            "weather_tag": weather_tag,
            "r_rain_3d": r_rain,
            "r_temp": r_temp,
            "r_snow_3d": r_snow,
            "heavy_rain_mult": heavy_rain_mult,
            "freeze_mult": freeze_mult,
            "heat_mult": heat_mult,
            "median_res_hours": q["median_res_hours"],
            "sla_pct": q["sla_pct"],
            "top_corridors_2026": q["top_corridors_2026"][:3],
        }
        emerging_items.append(item)
        if c26_ytd >= 100:
            weather_sensitivity_items.append(item)

    emerging_items.sort(
        key=lambda x: (
            1 if x["status"] in ("EMERGING_ACCELERATING", "EMERGING_SURGE", "RECENT_30D_SURGE") else 0,
            (x["ytd_rr"] * 0.65 + min(4.0, x["d30_rr"]) * 0.35) * math.log1p(x["ytd_2026"]),
        ),
        reverse=True,
    )

    max_iso_week = min(45, (max_doy_2026 // 7) + 1)
    weekly_code_rows = con.execute(
        f"""
        SELECT
            service_code,
            req_year,
            LEAST({max_iso_week}, CAST(((req_doy - 1) // 7) + 1 AS INTEGER)) AS wk,
            COUNT(*) AS cnt,
            MEDIAN(resolution_hours) AS med_res_hours
        FROM requests
        WHERE req_doy <= {max_doy_2026}
          AND service_code NOT IN ('Test01', 'SAMPLE', 'TEST', 'zTest1', 'S0081')
        GROUP BY service_code, req_year, wk
        """
    ).fetchall()

    weekly_by_code = defaultdict(lambda: {2025: [0] * max_iso_week, 2026: [0] * max_iso_week})
    weekly_res_by_code = defaultdict(lambda: {2025: [None] * max_iso_week, 2026: [None] * max_iso_week})
    for scode, yr, wk, cnt, med_res in weekly_code_rows:
        w_idx = int(wk) - 1
        if int(yr) in (2025, 2026) and 0 <= w_idx < max_iso_week:
            weekly_by_code[scode][int(yr)][w_idx] = int(cnt)
            if med_res is not None:
                weekly_res_by_code[scode][int(yr)][w_idx] = int(math.ceil(float(med_res) / 24.0))

    weekly_weather_rows = con.execute(
        f"""
        SELECT
            EXTRACT(YEAR FROM weather_date) AS yr,
            LEAST({max_iso_week}, CAST(((EXTRACT(DAYOFYEAR FROM weather_date) - 1) // 7) + 1 AS INTEGER)) AS wk,
            ROUND(SUM(rain_in), 2) AS rain_sum,
            ROUND(SUM(snow_in), 2) AS snow_sum,
            ROUND(AVG(temp_mean_f), 1) AS temp_avg,
            ROUND(MAX(temp_max_f), 1) AS temp_max
        FROM weather_daily
        WHERE EXTRACT(DAYOFYEAR FROM weather_date) <= {max_doy_2026}
        GROUP BY yr, wk
        ORDER BY yr, wk
        """
    ).fetchall()

    year_start = date(2026, 1, 1)
    max_dt_2026 = date.fromisoformat(str(max_date_2026)) if not isinstance(max_date_2026, date) else max_date_2026
    week_date_labels = []
    for w in range(1, max_iso_week + 1):
        d_start = year_start + timedelta(days=(w - 1) * 7)
        if w == max_iso_week:
            d_end = min(year_start + timedelta(days=w * 7 - 1), max_dt_2026)
        else:
            d_end = year_start + timedelta(days=w * 7 - 1)
        week_date_labels.append(f"{d_start.month}/{d_start.day}-{d_end.month}/{d_end.day}")

    weekly_weather = {
        "weeks": week_date_labels,
        "week_codes": [f"W{w:02d}" for w in range(1, max_iso_week + 1)],
        "rain_2025": [0.0] * max_iso_week,
        "rain_2026": [0.0] * max_iso_week,
        "snow_2025": [0.0] * max_iso_week,
        "snow_2026": [0.0] * max_iso_week,
        "temp_2025": [0.0] * max_iso_week,
        "temp_2026": [0.0] * max_iso_week,
    }
    for yr, wk, r_sum, s_sum, t_avg, _ in weekly_weather_rows:
        idx = int(wk) - 1
        if 0 <= idx < max_iso_week:
            if int(yr) == 2025:
                weekly_weather["rain_2025"][idx] = float(r_sum)
                weekly_weather["snow_2025"][idx] = float(s_sum)
                weekly_weather["temp_2025"][idx] = float(t_avg)
            elif int(yr) == 2026:
                weekly_weather["rain_2026"][idx] = float(r_sum)
                weekly_weather["snow_2026"][idx] = float(s_sum)
                weekly_weather["temp_2026"][idx] = float(t_avg)

    weekly_trajectories = {
        item["service_code"]: {
            "w2025": weekly_by_code[item["service_code"]][2025],
            "w2026": weekly_by_code[item["service_code"]][2026],
            "res_days_2025": weekly_res_by_code[item["service_code"]][2025],
            "res_days_2026": weekly_res_by_code[item["service_code"]][2026],
        }
        for item in emerging_items
    }

    ward_emerging_map = {
        str(w): ordered_wards[str(w)]["emerging_requests"]
        for w in range(1, 9)
        if str(w) in ordered_wards
    }

    emerging_payload = {
        "cutoff_date": str(max_date_2026),
        "d30_start_date": d30_start_2026,
        "items": emerging_items,
        "ward_emerging": ward_emerging_map,
        "weekly_weather": weekly_weather,
        "weekly_trajectories": weekly_trajectories,
    }
    with open(OUT_EMERGING, "w", encoding="utf-8") as f:
        json.dump(emerging_payload, f, separators=(",", ":"))
    print(f"Wrote {OUT_EMERGING} ({len(emerging_items)} evaluated service codes)")

    # =========================================================================
    # 4. OPERATIONAL, WEATHER & DETAILS PATTERNS (operational_patterns.json)
    # =========================================================================
    weather_summary_rows = con.execute(
        f"""
        SELECT
            EXTRACT(YEAR FROM weather_date) AS yr,
            ROUND(SUM(rain_in), 2) AS total_rain_in,
            ROUND(SUM(snow_in), 2) AS total_snow_in,
            ROUND(SUM(precip_in), 2) AS total_precip_in,
            COUNT(*) FILTER (WHERE is_rainy_day) AS rainy_days,
            COUNT(*) FILTER (WHERE is_heavy_rain_day) AS heavy_rain_days,
            COUNT(*) FILTER (WHERE is_snow_day) AS snow_days,
            COUNT(*) FILTER (WHERE is_freeze_day) AS freeze_days,
            COUNT(*) FILTER (WHERE is_heat_day) AS heat_days,
            ROUND(AVG(temp_mean_f), 1) AS avg_temp_f,
            ROUND(MAX(temp_max_f), 1) AS max_temp_f,
            ROUND(MIN(temp_min_f), 1) AS min_temp_f
        FROM weather_daily
        WHERE EXTRACT(DAYOFYEAR FROM weather_date) <= {max_doy_2026}
        GROUP BY yr
        ORDER BY yr
        """
    ).fetchall()

    weather_ytd_comparison = {}
    for row in weather_summary_rows:
        yr = str(int(row[0]))
        weather_ytd_comparison[yr] = {
            "total_rain_in": float(row[1]),
            "total_snow_in": float(row[2]),
            "total_precip_in": float(row[3]),
            "rainy_days": int(row[4]),
            "heavy_rain_days": int(row[5]),
            "snow_days": int(row[6]),
            "freeze_days": int(row[7]),
            "heat_days": int(row[8]),
            "avg_temp_f": float(row[9]),
            "max_temp_f": float(row[10]),
            "min_temp_f": float(row[11]),
        }

    agency_rows = con.execute(
        f"""
        SELECT
            agency,
            COUNT(*) FILTER (WHERE req_year = 2026 AND req_doy <= {max_doy_2026}) AS c26_ytd,
            COUNT(*) FILTER (WHERE req_year = 2025 AND req_doy <= {max_doy_2026}) AS c25_ytd,
            ROUND(MEDIAN(resolution_hours) FILTER (WHERE req_year = 2026 AND resolution_hours IS NOT NULL), 1) AS med_res_26,
            ROUND(QUANTILE_CONT(resolution_hours, 0.90) FILTER (WHERE req_year = 2026 AND resolution_hours IS NOT NULL), 1) AS p90_res_26,
            ROUND(AVG(CASE WHEN sla_met THEN 100.0 ELSE 0.0 END) FILTER (WHERE req_year = 2026 AND sla_met IS NOT NULL), 1) AS sla_26,
            ROUND(AVG(CASE WHEN sla_met THEN 100.0 ELSE 0.0 END) FILTER (WHERE req_year = 2025 AND sla_met IS NOT NULL), 1) AS sla_25,
            COUNT(*) FILTER (WHERE req_year = 2026 AND NOT is_closed) AS open_26,
            COUNT(*) FILTER (WHERE req_year = 2026 AND NOT is_closed AND req_doy <= {max_doy_2026 - 30}) AS aged_open_30d
        FROM requests
        WHERE service_code NOT IN ('Test01', 'SAMPLE', 'TEST', 'zTest1', 'S0081')
        GROUP BY agency
        HAVING c26_ytd >= 20 OR c25_ytd >= 20
        ORDER BY c26_ytd DESC
        """
    ).fetchall()

    agencies = []
    for r in agency_rows:
        ag, c26, c25, med_h, p90_h, sla26, sla25, op26, aged30 = r
        _, yoy_ag, _ = log_rate_ratio_and_z(c26, n_days_2026_ytd, c25, n_days_2025_ytd)
        agencies.append({
            "agency": ag,
            "count_2026_ytd": int(c26),
            "count_2025_ytd": int(c25),
            "yoy_pct": yoy_ag,
            "share_2026_pct": round(c26 / max(1, tot_26_ytd) * 100.0, 2),
            "median_res_hours": float(med_h) if med_h is not None else None,
            "p90_res_hours": float(p90_h) if p90_h is not None else None,
            "sla_pct_2026": float(sla26) if sla26 is not None else None,
            "sla_pct_2025": float(sla25) if sla25 is not None else None,
            "open_count": int(op26),
            "aged_open_30d": int(aged30),
        })

    dow_rows = con.execute(
        """
        SELECT req_isodow, COUNT(*) AS cnt
        FROM requests
        WHERE req_year = 2026
          AND service_code NOT IN ('Test01', 'SAMPLE', 'TEST', 'zTest1', 'S0081')
        GROUP BY req_isodow
        ORDER BY req_isodow
        """
    ).fetchall()
    dow_counts = [0] * 7
    for d, cnt in dow_rows:
        if 1 <= int(d) <= 7:
            dow_counts[int(d) - 1] = int(cnt)

    hour_rows = con.execute(
        """
        SELECT req_hour, COUNT(*) AS cnt
        FROM requests
        WHERE req_year = 2026
          AND service_code NOT IN ('Test01', 'SAMPLE', 'TEST', 'zTest1', 'S0081')
        GROUP BY req_hour
        ORDER BY req_hour
        """
    ).fetchall()
    hour_counts = [0] * 24
    for h, cnt in hour_rows:
        if 0 <= int(h) <= 23:
            hour_counts[int(h)] = int(cnt)

    repeat_by_code_rows = con.execute(
        """
        WITH addr_code AS (
            SELECT
                mar_id,
                service_code,
                ANY_VALUE(ward) AS ward,
                ANY_VALUE(anc) AS anc,
                COUNT(*) AS ticket_cnt
            FROM requests
            WHERE req_year = 2026
              AND mar_id IS NOT NULL
              AND mar_id > 0
              AND service_code NOT IN ('Test01', 'SAMPLE', 'TEST', 'zTest1', 'S0081')
            GROUP BY mar_id, service_code
            HAVING COUNT(*) >= 5
        )
        SELECT
            service_code,
            COUNT(*) AS chronic_locations_5plus,
            COUNT(*) FILTER (WHERE ticket_cnt >= 10) AS chronic_locations_10plus,
            SUM(ticket_cnt) AS total_chronic_tickets,
            MAX(ticket_cnt) AS max_tickets_single_location
        FROM addr_code
        GROUP BY service_code
        ORDER BY chronic_locations_5plus DESC
        LIMIT 35
        """
    ).fetchall()

    repeat_by_code = [
        {
            "service_code": r[0],
            "service_desc": code_primary_desc.get(r[0], r[0]),
            "locations_5plus": int(r[1]),
            "locations_10plus": int(r[2]),
            "total_chronic_tickets": int(r[3]),
            "max_single_location": int(r[4]),
        }
        for r in repeat_by_code_rows
    ]

    repeat_by_ward_rows = con.execute(
        """
        WITH addr_code AS (
            SELECT
                mar_id,
                ward,
                service_code,
                COUNT(*) AS ticket_cnt
            FROM requests
            WHERE req_year = 2026
              AND mar_id IS NOT NULL
              AND mar_id > 0
              AND ward IS NOT NULL
              AND service_code NOT IN ('Test01', 'SAMPLE', 'TEST', 'zTest1', 'S0081')
            GROUP BY mar_id, ward, service_code
            HAVING COUNT(*) >= 5
        )
        SELECT
            ward,
            COUNT(DISTINCT mar_id) AS chronic_properties,
            SUM(ticket_cnt) AS chronic_tickets
        FROM addr_code
        GROUP BY ward
        ORDER BY ward
        """
    ).fetchall()
    repeat_by_ward = {
        str(r[0]): {"chronic_properties": int(r[1]), "chronic_tickets": int(r[2])}
        for r in repeat_by_ward_rows
    }

    patterns_payload = {
        "weather_ytd_comparison": weather_ytd_comparison,
        "weather_sensitive_queries": sorted(
            weather_sensitivity_items,
            key=lambda x: max(abs(x["r_rain_3d"]), abs(x["r_temp"]), abs(x["r_snow_3d"])),
            reverse=True,
        )[:50],
        "details_audit": details_audit,
        "corridors_by_code": corridors_by_code,
        "agencies": agencies,
        "temporal": {
            "dow_labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            "dow_counts_2026": dow_counts,
            "hour_counts_2026": hour_counts,
        },
        "repeat_hotspots": {
            "by_service_code": repeat_by_code,
            "by_ward": repeat_by_ward,
        },
    }

    with open(OUT_PATTERNS, "w", encoding="utf-8") as f:
        json.dump(patterns_payload, f, separators=(",", ":"))
    print(f"Wrote {OUT_PATTERNS}")

    con.close()
    print(f"Analytics completed in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    run_analytics()
