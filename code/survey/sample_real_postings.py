#!/usr/bin/env python3
"""
Sample real job postings from Lightcast data for 3 target occupations.

Extracts JobText (XML) + salary/metadata (CSV Main) for postings that:
  - Have salary data (MinSalary > 0)
  - Match target SOC codes
  - Are from 2017-2019 (stable period, pre-COVID)

Outputs JSON with full posting text + metadata for manual review and
skeleton construction.

Usage:
    python sample_real_postings.py
"""

import os
import csv
import json
import random
import xml.etree.ElementTree as ET
from zipfile import ZipFile
from pathlib import Path
from collections import defaultdict

DATA_ROOT = "/Volumes/Expansion/All server/data/Burning Glass 2"
XML_ROOT = os.path.join(DATA_ROOT, "Jobs/US/Add")
CSV_ROOT = os.path.join(DATA_ROOT, "CSV/US/Add/Main")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "stimuli")

# Target occupations (SOC 2-digit prefix matching)
# Business/Management Analysts: 13-1111
# Financial Analysts: 13-2051
# Market Research Analysts: 13-1161
TARGET_SOCS = {
    '13-1111': 'Management Analyst',
    '13-2051': 'Financial Analyst',
    '13-1161': 'Market Research Analyst',
}

YEARS = [2017, 2018, 2019]
ZIPS_PER_YEAR = 3
TARGET_PER_SOC = 30  # aim for 30 postings per occupation


def load_csv_main_lookup(year, month):
    """Load CSV Main file into a dict keyed by BGTJobId."""
    csv_path = os.path.join(CSV_ROOT, str(year), f"Main_{year}-{month:02d}.zip")
    if not os.path.exists(csv_path):
        return {}

    lookup = {}
    with ZipFile(csv_path) as zf:
        for name in zf.namelist():
            if name.endswith('.txt') or name.endswith('.csv'):
                with zf.open(name) as f:
                    import io
                    text = io.TextIOWrapper(f, encoding='latin-1')
                    reader = csv.DictReader(text, delimiter='\t')
                    for row in reader:
                        job_id = row.get('BGTJobId', '').strip()
                        if not job_id:
                            continue
                        soc = row.get('SOC', '').strip()
                        if soc not in TARGET_SOCS:
                            continue
                        min_sal = row.get('MinSalary', '').strip()
                        max_sal = row.get('MaxSalary', '').strip()
                        try:
                            min_sal_f = float(min_sal) if min_sal else 0
                            max_sal_f = float(max_sal) if max_sal else 0
                        except ValueError:
                            continue
                        # Only keep postings with salary data
                        if min_sal_f < 20000:
                            continue
                        lookup[job_id] = {
                            'soc': soc,
                            'occupation': TARGET_SOCS[soc],
                            'min_salary': min_sal_f,
                            'max_salary': max_sal_f,
                            'job_title': row.get('CleanTitle', '').strip(),
                            'employer': row.get('Employer', '').strip(),
                            'city': row.get('City', '').strip(),
                            'state': row.get('State', '').strip(),
                            'naics3': row.get('BGTOcc', '').strip(),
                        }
    return lookup


def extract_xml_postings(year, month, csv_lookup):
    """Extract job text from XML files, matching against CSV lookup."""
    xml_dir = os.path.join(XML_ROOT, str(year))
    if not os.path.exists(xml_dir):
        return []

    results = []
    zip_files = sorted([f for f in os.listdir(xml_dir) if f.endswith('.zip')])

    # Find zips for this month
    month_str = f"{year}-{month:02d}"
    month_zips = [f for f in zip_files if month_str in f]
    if not month_zips:
        # Try broader match
        month_zips = zip_files[:2]

    for zf_name in month_zips[:1]:  # Process one zip per month
        zf_path = os.path.join(xml_dir, zf_name)
        print(f"  Processing {zf_name}...")
        try:
            with ZipFile(zf_path) as zf:
                for xml_name in zf.namelist():
                    if not xml_name.endswith('.xml'):
                        continue
                    try:
                        with zf.open(xml_name) as xf:
                            tree = ET.parse(xf)
                            root = tree.getroot()
                            for job in root.iter('Job'):
                                job_id_el = job.find('JobID')
                                job_text_el = job.find('JobText')
                                if job_id_el is None or job_text_el is None:
                                    continue
                                job_id = job_id_el.text.strip() if job_id_el.text else ''
                                if job_id not in csv_lookup:
                                    continue
                                job_text = job_text_el.text or ''
                                if len(job_text) < 200:
                                    continue
                                meta = csv_lookup[job_id]
                                results.append({
                                    'job_id': job_id,
                                    'job_text': job_text[:3000],  # Truncate very long texts
                                    **meta,
                                })
                    except ET.ParseError:
                        continue
        except Exception as e:
            print(f"  Error with {zf_name}: {e}")
            continue

    return results


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_postings = defaultdict(list)
    enough = {soc: False for soc in TARGET_SOCS}

    for year in YEARS:
        if all(enough.values()):
            break
        print(f"\n=== Year {year} ===")

        for month in random.sample(range(1, 13), ZIPS_PER_YEAR):
            if all(enough.values()):
                break

            print(f"\nLoading CSV Main for {year}-{month:02d}...")
            csv_lookup = load_csv_main_lookup(year, month)
            print(f"  Found {len(csv_lookup)} matching job IDs in CSV")

            if not csv_lookup:
                continue

            print(f"Extracting XML postings...")
            postings = extract_xml_postings(year, month, csv_lookup)
            print(f"  Extracted {len(postings)} postings with text")

            for p in postings:
                soc = p['soc']
                if len(all_postings[soc]) < TARGET_PER_SOC:
                    all_postings[soc].append(p)
                if len(all_postings[soc]) >= TARGET_PER_SOC:
                    enough[soc] = True

    # Summary
    print("\n=== Summary ===")
    for soc, name in TARGET_SOCS.items():
        count = len(all_postings[soc])
        print(f"  {name} ({soc}): {count} postings")
        if count > 0:
            salaries = [p['min_salary'] for p in all_postings[soc]]
            print(f"    Salary range: ${min(salaries):,.0f} - ${max(salaries):,.0f}")

    # Save
    output = {
        soc: all_postings[soc] for soc in TARGET_SOCS
    }
    output_path = os.path.join(OUTPUT_DIR, "real_posting_samples.json")
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\nSaved to {output_path}")


if __name__ == '__main__':
    main()
