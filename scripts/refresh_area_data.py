#!/usr/bin/env python3
"""Refreshes data/suburb-area-data.json, the crime + demographics dataset
the chatbot (api/chat.js) uses to answer crime-rate and demographic
questions with real, sourced figures instead of generic web search.

Sources:
  - Crime: QLD Police Service open-data "Crime locations" API
    (documented at data.qld.gov.au/dataset/crime-locations-2000-present).
    Pulls a rolling 12-month window per suburb.
  - Demographics: ABS 2021 Census, via the public ArcGIS FeatureServer
    that backs the Census QuickStats site (tables G01 and G37, Suburbs
    and Localities layer). Will need bumping to the 2026 Census tables
    once ABS publishes them.

Run this every 3 months or so to keep the crime window current. Census
demographics only change every 5 years and don't need refreshing until
the next Census results are out.

Usage: python3 scripts/refresh_area_data.py
"""
import datetime
import json
import os
import subprocess
import time
import urllib.parse
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(ROOT, 'data', 'suburb-area-data.json')

CRIME_API = "https://a5c7zwf7e5.execute-api.ap-southeast-2.amazonaws.com/dev/offences"
ABS_G01 = "https://services1.arcgis.com/v8Kimc579yljmjSP/ArcGIS/rest/services/ABS_2021_Census_G01_Selected_person_characteristics_by_sex_Beta/FeatureServer/10/query"
ABS_G37 = "https://services1.arcgis.com/v8Kimc579yljmjSP/ArcGIS/rest/services/ABS_2021_Census_G37_Beta/FeatureServer/10/query"
ABS_G01_FIELDS = "SAL_CODE_2021,SAL_NAME_2021,Tot_P_P,Age_0_4_yr_P,Age_5_14_yr_P,Age_15_19_yr_P,Age_20_24_yr_P,Age_25_34_yr_P,Age_35_44_yr_P,Age_45_54_yr_P,Age_55_64_yr_P,Age_65_74_yr_P,Age_75_84_yr_P,Age_85ov_P"
ABS_G37_FIELDS = "SAL_CODE_2021,SAL_NAME_2021,O_OR_Total,O_MTG_Total,R_Tot_Total,Oth_ten_type_Total,Ten_type_NS_Total,Total_Total"

# slug -> (QPS crime-boundary name, ABS census SAL name).
# These sometimes differ from each other and from the display name, when a
# small locality has no boundary of its own and is folded into a neighbour
# (e.g. Kirra -> Coolangatta in both datasets).
GC_SLUGS = {"bilinga", "broadbeach", "burleigh-heads", "coolangatta", "currumbin", "hope-island",
            "kirra", "mermaid-beach", "miami", "mudgeeraba", "palm-beach", "robina", "southport",
            "surfers-paradise", "tugun", "varsity-lakes"}

SUBURBS = {
    "bilinga":                    ("Bilinga", "Bilinga"),
    "broadbeach":                 ("Broadbeach", "Broadbeach"),
    "burleigh-heads":             ("Burleigh Heads", "Burleigh Heads"),
    "coolangatta":                ("Coolangatta", "Coolangatta"),
    "currumbin":                  ("Currumbin", "Currumbin"),
    "hope-island":                ("Hope Island", "Hope Island"),
    "kirra":                      ("Coolangatta", "Coolangatta"),
    "mermaid-beach":              ("Mermaid Beach", "Mermaid Beach"),
    "miami":                      ("Miami", "Miami"),
    "mudgeeraba":                 ("Mudgeeraba", "Mudgeeraba"),
    "palm-beach":                 ("Palm Beach", "Palm Beach"),
    "robina":                     ("Robina", "Robina"),
    "southport":                  ("Southport", "Southport"),
    "surfers-paradise":           ("Surfers Paradise", "Surfers Paradise"),
    "tugun":                      ("Tugun", "Tugun"),
    "varsity-lakes":              ("Varsity Lakes", "Varsity Lakes"),
    "atherton-tablelands":        ("Atherton", "Atherton"),
    "bayview-heights":            ("Bayview Heights", "Bayview Heights"),
    "bentley-park":               ("Bentley Park", "Bentley Park"),
    "brinsmead":                  ("Brinsmead", "Brinsmead"),
    "cairns-city":                ("Cairns City", "Cairns City"),
    "cairns-north":               ("Cairns North", "Cairns North"),
    "clifton-beach":              ("Clifton Beach", "Clifton Beach"),
    "earlville":                  ("Earlville", "Earlville"),
    "edge-hill":                  ("Edge Hill", "Edge Hill"),
    "edmonton":                   ("Edmonton", "Edmonton"),
    "freshwater":                 ("Freshwater", "Freshwater"),
    "gordonvale":                 ("Gordonvale", "Gordonvale"),
    "kewarra-beach":              ("Kewarra Beach", "Kewarra Beach"),
    "kuranda":                    ("Kuranda", "Kuranda"),
    "manoora":                    ("Manoora", "Manoora"),
    "manunda":                    ("Manunda", "Manunda"),
    "mooroobool":                 ("Mooroobool", "Mooroobool"),
    "mount-sheridan":             ("Mount Sheridan", "Mount Sheridan"),
    "palm-cove":                  ("Palm Cove", "Palm Cove"),
    "parramatta-park":            ("Parramatta Park", "Parramatta Park"),
    "port-douglas":               ("Port Douglas", "Port Douglas"),
    "redlynch":                   ("Redlynch", "Redlynch"),
    "smithfield":                 ("Smithfield", "Smithfield"),
    "trinity-beach":              ("Trinity Beach", "Trinity Beach"),
    "trinity-park":               ("Trinity Park", "Trinity Park"),
    "whitfield":                  ("Whitfield", "Whitfield"),
    "woree":                      ("Woree", "Woree"),
    "yorkeys-knob":               ("Yorkeys Knob", "Yorkeys Knob"),
}


def display_name(slug):
    return slug.replace("-", " ").title()


def curl_json(url):
    out = subprocess.run(["curl", "-s", "--max-time", "30", url], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def fetch_crime(qps_name, start, end):
    params = {"locationType": "SUBURB", "startDate": start, "locationName": qps_name, "endDate": end, "format": "JSON"}
    records = curl_json(CRIME_API + "?" + urllib.parse.urlencode(params))
    type_counts = Counter(r["Type"] for r in records)
    return {
        "total_offences": len(records),
        "top_offence_types": [{"type": t, "count": c} for t, c in type_counts.most_common(5)],
    }


def abs_query(base_url, fields, sal_name):
    for candidate in (sal_name, "{} (Qld)".format(sal_name)):
        where = "SAL_NAME_2021='{}'".format(candidate.replace("'", "''"))
        params = {"where": where, "outFields": fields, "returnGeometry": "false", "f": "json"}
        data = curl_json(base_url + "?" + urllib.parse.urlencode(params))
        feats = data.get("features", [])
        qld = [f["attributes"] for f in feats if f["attributes"].get("SAL_CODE_2021", "").startswith("3")]
        if qld:
            return qld[0]
        if len(feats) == 1:
            return feats[0]["attributes"]
    return None


def fetch_demographics(sal_name):
    g01 = abs_query(ABS_G01, ABS_G01_FIELDS, sal_name)
    time.sleep(0.15)
    g37 = abs_query(ABS_G37, ABS_G37_FIELDS, sal_name)
    time.sleep(0.15)
    if not g01 or not g37:
        return None

    pop = g01["Tot_P_P"]
    children = g01["Age_0_4_yr_P"] + g01["Age_5_14_yr_P"]
    young_adult = g01["Age_15_19_yr_P"] + g01["Age_20_24_yr_P"]
    working_age = g01["Age_25_34_yr_P"] + g01["Age_35_44_yr_P"] + g01["Age_45_54_yr_P"] + g01["Age_55_64_yr_P"]
    seniors = g01["Age_65_74_yr_P"] + g01["Age_75_84_yr_P"] + g01["Age_85ov_P"]
    total_hh = g37["Total_Total"] or 1
    owner_occupied = g37["O_OR_Total"] + g37["O_MTG_Total"]

    return {
        "census_year": 2021,
        "population": pop,
        "age_mix_pct": {
            "children_0_14": round(children / pop * 100, 1) if pop else None,
            "young_adult_15_24": round(young_adult / pop * 100, 1) if pop else None,
            "working_age_25_64": round(working_age / pop * 100, 1) if pop else None,
            "seniors_65_plus": round(seniors / pop * 100, 1) if pop else None,
        },
        "owner_occupied_pct": round(owner_occupied / total_hh * 100, 1),
        "renting_pct": round(g37["R_Tot_Total"] / total_hh * 100, 1),
        "abs_sal_code": g01["SAL_CODE_2021"],
    }


def main():
    today = datetime.date.today()
    start = (today.replace(day=1) - datetime.timedelta(days=365)).strftime("%m-%d-%Y")
    end = (today.replace(day=1) - datetime.timedelta(days=1)).strftime("%m-%d-%Y")  # last day of prior month

    suburbs = {}
    for slug, (qps_name, sal_name) in SUBURBS.items():
        name = display_name(slug)
        try:
            crime = fetch_crime(qps_name, start, end)
        except Exception as e:
            print("CRIME FAILED", slug, e)
            crime = None
        try:
            demo = fetch_demographics(sal_name)
        except Exception as e:
            print("ABS FAILED", slug, e)
            demo = None

        boundary_note = None
        if qps_name.lower() != name.lower():
            boundary_note = "Reported under the {} QPS suburb boundary, {} does not have its own separate crime-reporting boundary.".format(qps_name, name)

        suburbs[slug] = {
            "display_name": name,
            "region": "gc" if slug in GC_SLUGS else "cairns",
            "crime": {
                "period": "{} to {}".format(start, end),
                "total_offences": crime["total_offences"],
                "top_offence_types": crime["top_offence_types"],
                "qps_boundary_name": qps_name,
                "boundary_note": boundary_note,
            } if crime else None,
            "demographics": demo,
        }
        print(slug, "-> crime:", "ok" if crime else "MISSING", "| demo:", "ok" if demo else "MISSING")
        time.sleep(0.2)

    dataset = {
        "generated_at": today.isoformat(),
        "sources": {
            "crime": {
                "name": "Queensland Police Service Open Data Portal — Crime locations (suburb boundary API)",
                "url": "https://www.police.qld.gov.au/maps-and-statistics",
                "note": "Reported offences, 12-month rolling period. Suburb boundaries are QPS crime-reporting boundaries, which occasionally group small localities under a neighbouring suburb name (see boundary_note per suburb).",
            },
            "demographics": {
                "name": "Australian Bureau of Statistics, 2021 Census of Population and Housing",
                "url": "https://www.abs.gov.au/census",
                "note": "Most recent published Census. Next Census is 2026; this data will be stale until those results are released.",
            },
        },
        "suburbs": suburbs,
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, 'w') as f:
        json.dump(dataset, f, indent=2)
    print("\nWrote", OUT_PATH, "with", len(suburbs), "suburbs")


if __name__ == "__main__":
    main()
