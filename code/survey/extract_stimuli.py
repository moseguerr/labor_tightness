#!/usr/bin/env python3
"""
Extract real job posting phrases and full postings for experiment stimuli.

Reads raw XML zip files from the external drive, merges with CSV Main files
by BGTJobId to get salary/SOC metadata, applies the same dictionary matching
used in the main pipeline (get_final_variables.py), and extracts:
  1. Phrases in context for Study 1 (classification task)
  2. Full job postings for Study 2 (vignette construction)

Runs locally — no server required. Designed for memory efficiency:
processes one weekly XML zip at a time, stops early once targets are met.

Usage:
    python extract_stimuli.py [--data-root /Volumes/Expansion/All\ server/data/Burning\ Glass\ 2]
"""

import os
import sys
import re
import gc
import csv
import json
import random
import argparse
import unicodedata
import xml.etree.ElementTree as ET
from zipfile import ZipFile
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import tempfile
import pandas as pd

# ---------------------------------------------------------------------------
# Dictionary definitions — copied from get_final_variables.py (canonical source)
# Only the categories relevant for stimuli selection are included here.
# ---------------------------------------------------------------------------

meaningful_work = {
    "alignment with societal values": [
        "mission driven", "socially conscious", "ethical goals", "company mission",
        "values alignment", "purpose driven", "social impact focus", "shared values",
        "corporate mission", "ethical organization", "company values",
        "mission focused roles", "align with the purpose", "share values",
        "meaning of work", "pursuing career with purpose", "mutually rewarding",
        "purpose at work", "life changing", "heart pumping", "rewarding career",
        "making an impact", "social responsibility", "greater good",
        "double bottom line",
    ],
    "opportunities to make an impact": [
        "make a difference", "positively impact lives", "lasting impact",
        "rewarding work", "better future", "direct impact roles",
        "community building", "create positive change",
        "taking toughest challenges", "help others", "improve quality of life",
        "impact driven work", "help people", "fulfilling mission",
        "challenge yourself", "challenging and rewarding",
        "strengthening communities", "fulfilling careers", "engaging work",
        "interesting and challenging", "positive impact", "helping people",
        "meaningful work", "interesting work", "innovative work",
        "transformative journeys", "build stronger communities", "gratifying",
        "best work of their lives", "work with purpose", "make real impact",
        "improving quality life", "improving communities", "leaving a legacy",
        "career rewarding", "improvement human life",
    ],
    "working on innovation": [
        "breakthrough technologies", "cutting edge research", "innovative ideas",
        "changing future", "creative problem solving", "next gen solutions",
        "worldwide influence", "shaping future", "innovative companies",
        "innovative roles", "technology driven innovation",
        "leading product service innovation", "pioneering advancements",
        "disruptive innovation", "world leading companies", "develop breakthrough",
        "designing the future", "worlds most innovative company",
        "help build future", "history makers", "partner with great minds",
        "raise the bar", "leading research", "future constantly changing",
        "creative environment", "free thinkers", "leading innovation",
        "cutting edge technology", "transformative technologies",
        "driving progress", "vibrant work environment", "creating better future",
    ],
    "roles tied to solving global challenges": [
        "solving poverty", "climate change solutions",
        "addressing global challenges", "sustainable development goals",
        "humanitarian roles", "reduce inequality", "global impact",
        "worlds complex challenges", "solutions global",
        "worlds challenging issues", "inequality reduction",
        "solve realworld problems", "reducing inequality",
        "environmental challenges", "public health issues",
        "eradicating hunger", "bright future", "eliminate poverty",
        "a great environment", "environment that inspires",
        "solving global problems", "building resilient societies",
        "advancing human development",
    ],
}

environmental_initiatives = {
    "sustainability practices": [
        "sustainability", "carbon neutrality", "net zero", "recycling programs",
        "zero waste", "environmentally friendly", "eco friendly",
        "green practices", "circular economy", "waste reduction",
        "sustainable development", "sustainable growth",
        "sustainable industries", "sustainable packaging",
        "sustainable practices", "sustainable outcomes",
        "sustainable urbanization", "double bottom line",
        "responsible packaging material", "waste policy",
        "sustainable approach", "sustainable ways", "sustainable solutions",
        "resources management", "responsible consumption",
        "responsible farming", "responsible use",
        "lifestyle of health and sustainability", "resource conservation",
        "reducing waste",
    ],
    "renewable energy use": [
        "renewable energy", "solar energy", "wind energy", "green energy",
        "clean energy", "solar power", "wind power", "hydro power",
        "hydrogen power", "alternative energy", "energy efficient",
        "energy efficiencies", "energy efficiency", "energy star",
        "fuel efficiency", "hybrid energy", "hybrid vehicle", "hybrid car",
        "nuclear", "clean energies", "low carbon energy",
    ],
    "conservation programs": [
        "wildlife protection", "water conservation", "biodiversity programs",
        "land conservation", "habitat restoration", "forest preservation",
        "water use reduction", "natural resource conservation",
        "emission reduction", "ecosystem protection", "ocean resources",
        "overfishing", "fish stock", "amazon rain forest", "bio diversities",
        "biodiversity", "natural resources", "historic sites", "preservation",
        "protecting habitats", "marine conservation",
    ],
    "climate action": [
        "climate change", "climate crisis", "global warming",
        "paris agreement", "carbon dioxide", "carbon disclosure",
        "carbon emission", "carbon neutral", "co2", "emissions related",
        "greenhouse gas", "environmental impact", "environmental problems",
        "environmental performance", "environmental footprint",
        "climate neutral", "impact on the environment",
        "climate solutions", "low emissions",
    ],
    "environmental management and practices": [
        "environmental action", "environmental activism",
        "environmental safety", "environmental activities",
        "environmental disclosure", "environmental management systems",
        "environmental policies", "environmental policy",
        "environmental practices", "environmental protection",
        "environmental reform", "environmental responsibilities",
        "environmental responsibility", "environmental stewardship",
        "environmentally inclined", "environmentalist",
        "material footprint", "material stewardship", "groundwater",
        "hazardous waste", "toxic chemicals reduction", "waste recycling",
        "fuel technology", "oxidation", "environmentally safe",
        "environmentally neutral", "environmental supply chain",
        "pollution", "pollutant", "polluting", "ozone depletion",
        "ozone depleting", "gri frameworks", "esg", "gri ratings",
        "gri standards", "clean supply chains", "responsible resource use",
        "waste disposal", "recycling centers", "waste spill",
        "recycling nonhazardous solid waste", "industry leader recycling",
        "recycling simplified",
    ],
}

social_initiatives = {
    "diversity, equity, and inclusion programs": [
        "aboriginal peoples", "aboriginals", "affirmative action",
        "african american", "social class", "disabilities",
        "diversity inclusion", "disability status", "disabled",
        "discriminating", "fair wages", "discrimination", "discriminatory",
        "diversity", "workforce diversity", "equal employment",
        "equal opportunities", "equal opportunity", "equality",
        "ethnic diversities", "ethnic diversity", "ethnic mosaic",
        "ethnically", "ethnicities", "ethnicity", "female", "first nations",
        "first peoples", "gay", "creating inclusive", "gender", "hiv",
        "inclusive", "indigenous", "lesbian", "marital status", "minorities",
        "minority", "national origin", "native", "pregnancy", "race",
        "racial", "qualified candidates criminal", "religious diversities",
        "religious diversity", "same sex", "sexual orientation",
        "underrepresented group", "veteran", "women", "gender inclusion",
        "diverse leadership", "not obligated to disclose",
        "sealed or expunged", "will not be obligated to disclose",
        "convictions will not necessarily bar",
        "criminal record is not an automatic",
        "criminal record will be considered", "fair hiring practices",
        "diverse team", "equal pay", "pay equal work",
        "diverse backgrounds", "diverse group",
        "fair equitable compensation", "conviction records",
        "diverse workplace", "diverse workforce", "diverse environment",
        "culturally diverse", "diverse friendly",
        "diverse community", "equal consideration employment",
    ],
    "community engagement": [
        "community engagement", "volunteering", "local partnerships",
        "community involvement", "employee volunteer programs",
        "neighborhood support", "volunteer hours", "shared responsibility",
        "grassroots initiatives", "community development", "social impact",
        "corporate volunteerism", "civic engagement", "community project",
        "supporting local communities", "socially engaged",
        "impact communities", "community work",
        "engagement opportunities", "community efforts",
    ],
    "philanthropy": [
        "charitable giving", "corporate social responsibility",
        "scholarships", "nonprofit support", "foundation grants",
        "humanitarian aid", "cause based giving", "charity donations",
        "philanthropic initiatives", "donations", "giving back",
        "community philanthropy", "donor support", "responsible corporate",
        "community giving",
    ],
    "ethical supply chains": [
        "ethical sourcing", "fair trade", "responsible sourcing",
        "supply chain transparency", "labor rights", "sustainable sourcing",
        "supplier diversity", "worker protections", "fair labor standards",
        "environmental supply chain", "responsible farming",
        "worker equity", "transparent supply chains",
    ],
}

organizational_culture = {
    "psychological safety": [
        "open communication", "respectful conflict resolution",
        "constructive feedback", "safe to voice opinions",
        "no fear of retaliation", "supportive environment",
        "encouraging expression", "trust in leadership", "employees voice",
        "workers voice", "employee ideas", "warm and friendly culture",
        "trust", "protected", "inclusive feedback", "safe environment",
        "psychologically safe", "employee well being", "non judgmental",
    ],
    "recognition and celebration": [
        "employee recognition", "celebrating achievements", "shout outs",
        "employee awards", "appreciation programs", "incentive awards",
        "demonstrated achievements", "staff appreciation",
        "celebrates success", "team celebrations", "milestone recognition",
        "achievement rewards", "recognized and rewarded",
        "reinvest in our employees", "promote from within",
        "promoting from within", "recognized rewarded", "peer recognition",
        "employee appreciation", "team recognition",
        "achievement celebrations", "employee value",
    ],
    "collaborative environment": [
        "team collaboration", "supportive teams", "peer support",
        "cross functional collaboration", "helpful colleagues",
        "team oriented environment", "teamwork culture",
        "collaborative atmosphere", "team environment", "teamwork",
        "employee involvement", "employee relations",
        "worker representation", "teamoriented environment",
        "working men and women", "employees are key",
        "employees are our greatest asset", "care of our people",
        "collective problem solving", "team building",
        "collaborative work environment", "collaborative teams",
        "shared goals", "cooperative workplace",
    ],
    "transparency in leadership": [
        "transparent leadership", "clear communication from leaders",
        "honest decision making", "accessible management",
        "ethical leadership", "open door policy", "leader transparency",
        "managerial openness", "transparency", "leadership integrity",
        "honest leadership", "positive leadership",
        "organizational accountability", "environment openness",
        "held accountable", "strong leadership",
        "leadership communication", "management clear communication",
        "leadership oversight", "transparent decision making",
        "accountable leadership", "openness in management",
    ],
    "workplace recognition": [
        "best companies to work", "great place to work",
        "award winning staff", "best large employers",
        "employee friendly workplace", "award winning workplace",
        "best places work", "recognized employer", "employer of choice",
        "best places to work", "perfect place work", "wonderful place work",
        "ranked best companies", "awardwinning company",
        "excellent place work", "worlds admired companies",
        "leading companies world", "large companies world",
    ],
}

pecuniary_benefits = {
    "stock options or equity grants": [
        "stock options", "employee stock ownership", "equity grants",
        "stock purchase program", "company shares", "esop", "share options",
        "long term incentives", "equity packages", "stock purchase plan",
        "employee stock", "restricted stock units",
    ],
    "retirement plans": [
        "401k", "retirement", "pension", "savings plans",
        "employer match", "retirement benefits", "defined benefit",
        "employee savings",
    ],
    "insurance benefits": [
        "health insurance", "dental", "vision", "life insurance",
        "disability insurance", "medical plans", "health coverage",
        "health benefit", "health care", "healthcare", "dependent care",
        "dependent coverage", "mental health benefits",
        "mental health coverage",
    ],
    "paid time off": [
        "paid time off", "vacation time", "sick leave", "holiday pay",
        "paid vacation time", "sabbaticals", "parental leave",
        "maternal leave", "paternal leave",
    ],
    "tuition and education": [
        "tuition reimbursement", "education assistance",
        "educational programs", "continuing education",
        "college scholarship", "scholarships",
    ],
    "additional financial benefits": [
        "bonus", "competitive benefits", "benefits package",
        "employee discount", "commuter benefits", "relocation",
        "profit sharing", "sign on bonus", "performance bonus",
    ],
}

job_design_characteristics = {
    "flexible work arrangements": [
        "flexible schedule", "remote work", "work from home", "telecommute",
        "hybrid work", "flexible hours", "compressed workweek",
    ],
    "work-life balance": [
        "work life balance", "worklife balance", "balanced lifestyle",
        "balanced life", "family time", "worklife program",
        "workfamily", "healthy worklife",
    ],
}

career_development = {
    "skill development": [
        "professional development", "training", "skill development",
        "skills development", "leadership development",
        "continuous learning", "mentorship", "coaching",
    ],
    "career progression": [
        "career advancement", "career development", "career growth",
        "career opportunities", "career path", "career progression",
        "growth opportunities", "opportunities for advancement",
        "opportunities for growth", "promote from within",
    ],
}

job_tasks_requirements = {
    "job_tasks": [
        "manage", "lead", "design", "develop", "coordinate", "plan",
        "analyze", "implement", "research", "organize", "support",
        "communicate", "monitor", "evaluate", "train", "facilitate",
        "present", "report", "maintain", "oversee", "test", "consult",
        "build", "solve", "write", "deploy", "execute", "strategize",
        "duties include", "responsibilities include", "tasked with",
    ],
    "job_requirements": [
        "required", "must", "ability to", "mandatory",
        "minimum qualifications", "experience in", "desired", "preferred",
        "essential", "proficiency in", "certification", "background in",
        "knowledge of", "expertise in",
    ],
    "qualifications": [
        "bachelor", "master", "phd", "degree", "diploma", "certificate",
        "qualification", "accreditation", "years of experience",
    ],
}

# All dictionaries for purpose construct (Study 1 core categories)
PURPOSE_DICTS = {
    "meaningful_work": meaningful_work,
    "environmental_initiatives": environmental_initiatives,
    "social_initiatives": social_initiatives,
}

# Non-purpose categories (for contrast)
NON_PURPOSE_DICTS = {
    "organizational_culture": organizational_culture,
    "pecuniary_benefits": pecuniary_benefits,
    "job_design_characteristics": job_design_characteristics,
    "career_development": career_development,
    "job_tasks_requirements": job_tasks_requirements,
}

ALL_DICTS = {**PURPOSE_DICTS, **NON_PURPOSE_DICTS}

# IRB category labels (participant-facing)
CATEGORY_LABELS = {
    "meaningful_work": "The company's mission, values, or social/environmental impact",
    "environmental_initiatives": "The company's mission, values, or social/environmental impact",
    "social_initiatives": "The company's mission, values, or social/environmental impact",
    "organizational_culture": "The company treats employees well",
    "pecuniary_benefits": "Pay, benefits, or financial perks",
    "job_design_characteristics": "The company treats employees well",
    "career_development": "The company treats employees well",
    "job_tasks_requirements": "Job tasks, duties, or responsibilities",
}

# Map to the 6 IRB categories for Study 1
IRB_CATEGORIES = [
    "mission_values",      # org purpose / meaningful work / environmental / social
    "treats_well",         # org culture / job design / career dev
    "pay_benefits",        # pecuniary benefits
    "job_tasks",           # tasks, duties, responsibilities
    "job_requirements",    # requirements, qualifications
    "none_unsure",         # escape valve
]


# ---------------------------------------------------------------------------
# Text processing — same as get_final_variables.py
# ---------------------------------------------------------------------------

def clean_text(text):
    """Normalize and clean job posting text for dictionary matching."""
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8', 'ignore')
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', text)
    text = re.sub(r'[^a-zA-Z0-9\s.,!?]', '', text)
    return re.sub(r'\s+', ' ', text.lower()).strip()


def find_matches(clean_text_str, dictionary):
    """
    Find all dictionary matches in cleaned text.
    Returns list of (keyword, category, subcategory) tuples.
    """
    matches = []
    for subcategory, keywords in dictionary.items():
        for keyword in keywords:
            if keyword in clean_text_str:
                matches.append((keyword, subcategory))
    return matches


def extract_phrase_in_context(original_text, keyword, context_chars=150):
    """
    Find the keyword in the original (uncleaned) text and extract
    surrounding context to create a 1-2 sentence phrase-in-context.
    Returns (phrase_with_context, phrase_start, phrase_end) or None.
    """
    # Search case-insensitively in original text
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    match = pattern.search(original_text)
    if not match:
        # Try with flexible whitespace (keyword may have been normalized)
        flexible_pattern = re.compile(
            r'\s+'.join(re.escape(w) for w in keyword.split()),
            re.IGNORECASE
        )
        match = flexible_pattern.search(original_text)
    if not match:
        return None

    start = max(0, match.start() - context_chars)
    end = min(len(original_text), match.end() + context_chars)

    # Expand to sentence boundaries
    # Find sentence start (look backward for period/newline)
    while start > 0 and original_text[start] not in '.!?\n':
        start -= 1
    if start > 0:
        start += 1  # skip the punctuation itself

    # Find sentence end (look forward for period/newline)
    while end < len(original_text) and original_text[end] not in '.!?\n':
        end += 1
    if end < len(original_text):
        end += 1  # include the punctuation

    context = original_text[start:end].strip()

    # Clean up: remove excessive whitespace, asterisks, bullets
    context = re.sub(r'\s+', ' ', context)
    context = re.sub(r'^\s*[\*\-\u2022]\s*', '', context)

    # Limit to ~2 sentences
    sentences = re.split(r'(?<=[.!?])\s+', context)
    if len(sentences) > 3:
        # Find which sentence contains the keyword
        for i, sent in enumerate(sentences):
            if keyword.lower() in sent.lower():
                selected = sentences[max(0, i-1):i+2]
                context = ' '.join(selected)
                break

    return context.strip()


# ---------------------------------------------------------------------------
# XML parsing — adapted from xml_to_dataframe.py
# ---------------------------------------------------------------------------

def parse_xml_zip(zip_path, max_postings=None):
    """
    Parse a Lightcast XML zip file and yield job postings as dicts.
    Memory efficient: processes one <Job> element at a time.
    Only extracts JobID, JobText, CanonEmployer, IsDuplicate from XML;
    all other metadata (salary, SOC, NAICS, etc.) comes from CSV Main merge.
    """
    count = 0
    with tempfile.TemporaryDirectory() as tmpdir:
        with ZipFile(zip_path, 'r') as zf:
            xml_files = [f for f in zf.namelist() if f.endswith('.xml')]
            if not xml_files:
                return
            zf.extract(xml_files[0], tmpdir)
            xml_path = os.path.join(tmpdir, xml_files[0])

        fields = ['JobID', 'CanonEmployer', 'JobDate', 'JobText', 'IsDuplicate']

        for event, elem in ET.iterparse(xml_path, events=('end',)):
            if elem.tag != 'Job':
                continue

            posting = {}
            for field in fields:
                child = elem.find(field)
                posting[field] = child.text if child is not None else None
            elem.clear()

            # Skip duplicates and empty postings
            if posting.get('IsDuplicate') == '1':
                continue
            if not posting.get('JobText') or not posting.get('CanonEmployer'):
                continue

            count += 1
            yield posting

            if max_postings and count >= max_postings:
                return


# ---------------------------------------------------------------------------
# CSV Main loading — merge metadata by BGTJobId (following mergeMain.py)
# ---------------------------------------------------------------------------

def get_months_from_xml_filename(xml_zip_name):
    """
    Extract month(s) covered by an XML zip file from its filename.
    e.g. 'US_XML_AddFeed_20170129_20170204.zip' -> [('2017', '01'), ('2017', '02')]
         'US_XML_AddFeed_20170108_20170114.zip' -> [('2017', '01')]
    """
    match = re.search(r'(\d{4})(\d{2})\d{2}_(\d{4})(\d{2})\d{2}', xml_zip_name)
    if not match:
        return []
    y1, m1, y2, m2 = match.groups()
    months = [(y1, m1)]
    if (y1, m1) != (y2, m2):
        months.append((y2, m2))
    return months


def load_csv_main_lookup(data_root, year, month):
    """
    Load a CSV Main zip file and return a dict: BGTJobId -> metadata dict.
    CSV Main files follow mergeMain.py format: tab-separated, latin encoding.

    Path pattern: CSV/US/Add/Main/{year}/Main_{year}-{month}.zip
    """
    csv_dir = os.path.join(data_root, 'CSV', 'US', 'Add', 'Main', str(year))
    csv_zip = os.path.join(csv_dir, f'Main_{year}-{month}.zip')

    if not os.path.exists(csv_zip):
        print(f"  Warning: CSV Main not found: {csv_zip}")
        return {}

    # Read only the columns we need (keeps memory low)
    usecols = [
        'BGTJobId', 'CleanTitle', 'SOC', 'SOCName', 'OccFam', 'OccFamName',
        'Employer', 'Sector', 'SectorName', 'NAICS3',
        'City', 'State', 'County', 'BestFitMSA', 'BestFitMSAName',
        'MinSalary', 'MaxSalary', 'PayFrequency', 'Internship',
    ]

    try:
        df = pd.read_table(csv_zip, encoding='latin', engine='python',
                           delimiter='\t', usecols=usecols)
    except Exception as e:
        print(f"  Warning: Could not read {csv_zip}: {e}")
        return {}

    # Convert BGTJobId to string for matching with XML JobID
    df['BGTJobId'] = df['BGTJobId'].astype(str)

    # Use pandas to_dict for fast conversion (avoid iterrows)
    df = df.set_index('BGTJobId')
    # Fill NaN to avoid issues with dict conversion
    df = df.fillna({'MinSalary': -999, 'MaxSalary': -999, 'Internship': 0})
    df = df.fillna('')
    lookup = df.to_dict('index')

    del df
    gc.collect()
    return lookup


def enrich_postings_with_csv(postings, csv_lookup):
    """
    Merge CSV Main metadata into parsed XML postings by JobID = BGTJobId.
    Returns enriched postings (only those that matched).
    """
    enriched = []
    matched = 0
    for posting in postings:
        job_id = str(posting.get('JobID', ''))
        meta = csv_lookup.get(job_id)
        if meta:
            posting.update(meta)
            matched += 1
        enriched.append(posting)
    return enriched, matched


# ---------------------------------------------------------------------------
# Stimuli extraction logic
# ---------------------------------------------------------------------------

def extract_study1_phrases(postings, target_count=120):
    """
    From a list of job postings, extract phrases that match dictionary
    categories and their surrounding context. Aims for balanced coverage
    across all IRB categories, with emphasis on ambiguous boundary cases.
    """
    phrases = []
    seen_keywords = set()
    category_counts = defaultdict(int)

    # Target per IRB category (6 categories, ~20 each for 120 total)
    per_category_target = target_count // 5  # 5 substantive categories

    for posting in postings:
        original_text = posting['JobText']
        cleaned = clean_text(original_text)

        # Check all dictionaries
        for dict_name, dictionary in ALL_DICTS.items():
            matches = find_matches(cleaned, dictionary)
            for keyword, subcategory in matches:
                if keyword in seen_keywords:
                    continue

                # Map to IRB category
                if dict_name in ('meaningful_work', 'environmental_initiatives', 'social_initiatives'):
                    irb_cat = 'mission_values'
                elif dict_name in ('organizational_culture', 'job_design_characteristics', 'career_development'):
                    irb_cat = 'treats_well'
                elif dict_name == 'pecuniary_benefits':
                    irb_cat = 'pay_benefits'
                elif dict_name == 'job_tasks_requirements':
                    if subcategory in ('job_tasks',):
                        irb_cat = 'job_tasks'
                    else:
                        irb_cat = 'job_requirements'
                else:
                    continue

                # Skip if we have enough for this category
                if category_counts[irb_cat] >= per_category_target * 1.5:
                    continue

                # Extract context
                context = extract_phrase_in_context(original_text, keyword)
                if not context or len(context) < 20:
                    continue

                # Skip very short or very long contexts
                if len(context) > 400:
                    continue

                # Check for ambiguity — does this keyword also match other categories?
                cross_matches = []
                for other_name, other_dict in ALL_DICTS.items():
                    if other_name == dict_name:
                        continue
                    for other_sub, other_kws in other_dict.items():
                        if keyword in other_kws:
                            cross_matches.append(other_name)

                seen_keywords.add(keyword)
                category_counts[irb_cat] += 1

                phrases.append({
                    'phrase': keyword,
                    'context': context,
                    'dict_category': dict_name,
                    'dict_subcategory': subcategory,
                    'irb_category': irb_cat,
                    'is_ambiguous': len(cross_matches) > 0,
                    'cross_categories': cross_matches,
                    'source_employer': posting.get('Employer', posting.get('CanonEmployer', '')),
                    'source_job_title': posting.get('CleanTitle', ''),
                    'source_job_id': posting.get('JobID', ''),
                    'source_date': posting.get('JobDate', ''),
                    'source_soc': posting.get('SOC', ''),
                    'source_soc_name': posting.get('SOCName', ''),
                })

    return phrases


def extract_salary_from_text(text):
    """
    Parse salary figures from job posting text.
    Looks for patterns like $XX,XXX, $XX/hr, $XXk, salary ranges, etc.
    Returns (annual_salary_estimate, raw_match) or (None, None).
    """
    # Pattern: $XX,XXX or $XXX,XXX (annual salary range)
    annual_pattern = re.compile(
        r'\$\s?(\d{2,3}[,.]?\d{3})\s*(?:[-–to/]+\s*\$?\s*(\d{2,3}[,.]?\d{3}))?'
        r'\s*(?:per\s+year|/\s*year|annually|/\s*yr|a\s+year)?',
        re.IGNORECASE
    )
    # Pattern: $XX/hr or $XX per hour
    hourly_pattern = re.compile(
        r'\$\s?(\d{1,3}(?:\.\d{2})?)\s*(?:[-–to/]+\s*\$?\s*(\d{1,3}(?:\.\d{2})?))?'
        r'\s*(?:per\s+hour|/\s*h(?:ou)?r|hourly|an\s+hour)',
        re.IGNORECASE
    )
    # Pattern: $XXk
    k_pattern = re.compile(
        r'\$\s?(\d{2,3})[kK]\s*(?:[-–to/]+\s*\$?\s*(\d{2,3})[kK])?',
    )

    # Try annual first
    match = annual_pattern.search(text)
    if match:
        low = float(match.group(1).replace(',', '').replace('.', ''))
        high = float(match.group(2).replace(',', '').replace('.', '')) if match.group(2) else low
        # Sanity check: should be in reasonable annual salary range
        if 20000 <= low <= 500000:
            return (low + high) / 2, match.group(0)

    # Try $XXk
    match = k_pattern.search(text)
    if match:
        low = float(match.group(1)) * 1000
        high = float(match.group(2)) * 1000 if match.group(2) else low
        if 20000 <= low <= 500000:
            return (low + high) / 2, match.group(0)

    # Try hourly (convert to annual: hourly * 2080)
    match = hourly_pattern.search(text)
    if match:
        low = float(match.group(1)) * 2080
        high = float(match.group(2)) * 2080 if match.group(2) else low
        if 20000 <= low <= 300000:
            return (low + high) / 2, match.group(0)

    return None, None


def is_mid_level_role(job_title):
    """
    Check if a job title suggests a mid-level, recognizable role
    suitable for experiment vignettes.
    """
    if not job_title:
        return False
    title_lower = job_title.lower()
    # Positive signals: mid-level titles undergrads/Prolific participants recognize
    mid_level_keywords = [
        'analyst', 'coordinator', 'specialist', 'associate',
        'manager', 'supervisor', 'administrator', 'representative',
        'consultant', 'advisor', 'planner', 'designer',
        'marketing', 'operations', 'project', 'account',
        'human resources', 'recruiter', 'communications',
        'financial', 'business', 'sales',
    ]
    # Negative signals: too senior, too junior, or too specialized
    exclude_keywords = [
        'director', 'vice president', 'vp', 'chief', 'ceo', 'cfo', 'cto',
        'intern', 'entry level', 'junior', 'trainee',
        'nurse', 'doctor', 'physician', 'surgeon', 'rn', 'lpn',
        'driver', 'warehouse', 'cashier', 'barista', 'cook',
        'mechanic', 'technician', 'electrician', 'plumber',
    ]
    if any(kw in title_lower for kw in exclude_keywords):
        return False
    return any(kw in title_lower for kw in mid_level_keywords)


def extract_study2_postings(postings, target_count=60, require_salary=True):
    """
    Select full job postings suitable for Study 2 vignette construction.
    Uses MinSalary/MaxSalary from CSV Main merge (not regex from text).
    Filters on: mid-level roles, text length, salary presence, purpose language.

    If require_salary=True (default), only selects postings with salary data.
    Falls back to no-salary postings if not enough salary postings are found.
    """
    # First pass: collect candidates with salary
    candidates_with_salary = {'with_purpose': [], 'without_purpose': []}
    # Second pass: collect candidates without salary (fallback)
    candidates_no_salary = {'with_purpose': [], 'without_purpose': []}

    for posting in postings:
        text = posting['JobText']
        cleaned = clean_text(text)
        word_count = len(text.split())

        # Filter: text length (>150 words for meaningful content)
        if word_count < 150:
            continue

        # Filter: skip internships
        if str(posting.get('Internship', 0)) == '1':
            continue

        # Filter: mid-level role by job title (from CSV CleanTitle)
        job_title = posting.get('CleanTitle', '') or ''
        if not is_mid_level_role(job_title):
            continue

        # Check salary from CSV Main
        min_salary = posting.get('MinSalary', -999)
        max_salary = posting.get('MaxSalary', -999)
        try:
            min_salary = float(min_salary)
            max_salary = float(max_salary)
        except (ValueError, TypeError):
            min_salary, max_salary = -999, -999

        has_salary = min_salary > 0 or max_salary > 0
        mean_salary = None
        if has_salary:
            # Compute mean salary; if one is missing, use the other
            if min_salary > 0 and max_salary > 0:
                mean_salary = (min_salary + max_salary) / 2
            elif min_salary > 0:
                mean_salary = min_salary
            else:
                mean_salary = max_salary
            # Sanity check: reasonable annual range for mid-level
            if mean_salary < 25000 or mean_salary > 250000:
                has_salary = False
                mean_salary = None

        # Check purpose language — focus on meaningful_work and environmental
        # (social_initiatives DEI terms are in nearly every posting as EEO boilerplate)
        has_purpose = False
        purpose_terms = []
        # Core purpose: meaningful_work + environmental_initiatives
        for dict_name in ('meaningful_work', 'environmental_initiatives'):
            matches = find_matches(cleaned, PURPOSE_DICTS[dict_name])
            if matches:
                has_purpose = True
                purpose_terms.extend([m[0] for m in matches])
        # Social initiatives: only count non-boilerplate terms
        eeo_boilerplate = {
            'equal opportunity', 'equal employment', 'discrimination',
            'discriminatory', 'affirmative action', 'disability status',
            'disabled', 'national origin', 'sexual orientation', 'gender',
            'race', 'racial', 'veteran', 'women', 'minorities', 'minority',
            'marital status', 'pregnancy', 'native', 'inclusive',
            'diversity', 'female', 'religion', 'ethnicity', 'ethnic',
        }
        social_matches = find_matches(cleaned, PURPOSE_DICTS['social_initiatives'])
        non_boilerplate_social = [m for m in social_matches if m[0] not in eeo_boilerplate]
        if non_boilerplate_social:
            has_purpose = True
            purpose_terms.extend([m[0] for m in non_boilerplate_social])

        # Also check non-purpose categories
        non_purpose_terms = []
        for dict_name, dictionary in NON_PURPOSE_DICTS.items():
            if dict_name == 'job_tasks_requirements':
                continue  # Skip tasks — every posting has these
            matches = find_matches(cleaned, dictionary)
            non_purpose_terms.extend([m[0] for m in matches])

        purpose_bucket = 'with_purpose' if has_purpose else 'without_purpose'

        # Build record
        record = {
            'job_id': posting.get('JobID', ''),
            'employer': posting.get('Employer', posting.get('CanonEmployer', '')),
            'job_title': job_title,
            'soc': posting.get('SOC', ''),
            'soc_name': posting.get('SOCName', ''),
            'city': posting.get('City', ''),
            'state': posting.get('State', ''),
            'msa': posting.get('BestFitMSAName', ''),
            'sector_name': posting.get('SectorName', ''),
            'naics3': posting.get('NAICS3', ''),
            'date': posting.get('JobDate', ''),
            'min_salary': min_salary if has_salary else None,
            'max_salary': max_salary if has_salary else None,
            'mean_salary': mean_salary,
            'has_salary': has_salary,
            'has_purpose_language': has_purpose,
            'purpose_terms_found': purpose_terms,
            'non_purpose_terms_found': non_purpose_terms,
            'word_count': word_count,
            'job_text': text[:5000],
        }

        if has_salary:
            candidates_with_salary[purpose_bucket].append(record)
        else:
            candidates_no_salary[purpose_bucket].append(record)

    # Build final selection: prefer postings with salary
    half_target = target_count // 2
    result = []
    for bucket in ('with_purpose', 'without_purpose'):
        pool = candidates_with_salary[bucket][:half_target]
        # If not enough salary postings, fill from no-salary pool
        shortfall = half_target - len(pool)
        if shortfall > 0:
            pool.extend(candidates_no_salary[bucket][:shortfall])
        result.extend(pool)

    sal_count = sum(1 for r in candidates_with_salary['with_purpose']) + sum(1 for r in candidates_with_salary['without_purpose'])
    print(f"  Study 2 candidates: {sal_count} with salary, "
          f"{len(candidates_no_salary['with_purpose']) + len(candidates_no_salary['without_purpose'])} without salary")

    return result


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def get_xml_zips(data_root, years):
    """Get list of XML zip files for the given years."""
    zips = []
    for year in years:
        year_dir = os.path.join(data_root, 'Jobs', 'US', 'Add', str(year))
        if not os.path.isdir(year_dir):
            print(f"  Warning: {year_dir} not found, skipping year {year}")
            continue
        for f in sorted(os.listdir(year_dir)):
            if f.endswith('.zip') and 'XML_AddFeed' in f:
                zips.append(os.path.join(year_dir, f))
    return zips


def main():
    parser = argparse.ArgumentParser(description='Extract experiment stimuli from Lightcast data')
    parser.add_argument('--data-root',
                        default='/Volumes/Expansion/All server/data/Burning Glass 2',
                        help='Root directory of Burning Glass data')
    parser.add_argument('--output-dir',
                        default=os.path.join(os.path.dirname(__file__), 'stimuli'),
                        help='Output directory for stimuli files')
    parser.add_argument('--years', nargs='+', type=int, default=[2014, 2017, 2019],
                        help='Years to sample from (default: 2014 2017 2019)')
    parser.add_argument('--zips-per-year', type=int, default=4,
                        help='Number of weekly zip files to process per year')
    parser.add_argument('--postings-per-zip', type=int, default=5000,
                        help='Max postings to read from each zip file')
    parser.add_argument('--phrase-target', type=int, default=120,
                        help='Target number of phrases for Study 1')
    parser.add_argument('--posting-target', type=int, default=60,
                        help='Target number of postings for Study 2')
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    print("=" * 60)
    print("Extracting experiment stimuli from Lightcast job postings")
    print("=" * 60)
    print(f"Data root: {args.data_root}")
    print(f"Years: {args.years}")
    print(f"Zips per year: {args.zips_per_year}")
    print(f"Postings per zip: {args.postings_per_zip}")
    print(f"Output: {args.output_dir}")
    print()

    # Get XML zip files
    all_zips = get_xml_zips(args.data_root, args.years)
    print(f"Found {len(all_zips)} XML zip files across {len(args.years)} years")

    if not all_zips:
        print("ERROR: No XML zip files found. Check --data-root path.")
        sys.exit(1)

    # Sample a subset of zips per year (spread across the year)
    sampled_zips = []
    for year in args.years:
        year_zips = [z for z in all_zips if f'/{year}/' in z]
        if not year_zips:
            continue
        # Evenly space across the year
        step = max(1, len(year_zips) // args.zips_per_year)
        indices = list(range(0, len(year_zips), step))[:args.zips_per_year]
        for i in indices:
            sampled_zips.append(year_zips[i])

    print(f"Sampling {len(sampled_zips)} zip files:")
    for z in sampled_zips:
        print(f"  {os.path.basename(z)}")
    print()

    # Process zip files: parse XML, load CSV Main, merge by JobID
    all_postings = []
    csv_cache = {}  # (year, month) -> lookup dict, avoids re-reading same CSV

    for zip_path in sampled_zips:
        fname = os.path.basename(zip_path)
        print(f"Processing {fname}...")
        t0 = datetime.now()

        # Step 1: Determine which monthly CSV(s) to load for this XML zip
        months = get_months_from_xml_filename(fname)
        if not months:
            print(f"  Warning: could not extract month from {fname}, skipping")
            continue

        # Step 2: Load CSV Main lookup(s) for the month(s) covered
        csv_lookup = {}
        for year_str, month_str in months:
            key = (year_str, month_str)
            if key not in csv_cache:
                print(f"  Loading CSV Main for {year_str}-{month_str}...", end=' ', flush=True)
                csv_cache[key] = load_csv_main_lookup(args.data_root, year_str, month_str)
                print(f"{len(csv_cache[key])} rows")
            csv_lookup.update(csv_cache[key])

        # Step 3: Parse XML postings
        xml_postings = []
        for posting in parse_xml_zip(zip_path, max_postings=args.postings_per_zip):
            xml_postings.append(posting)

        # Step 4: Merge with CSV metadata
        enriched, matched = enrich_postings_with_csv(xml_postings, csv_lookup)
        all_postings.extend(enriched)

        elapsed = (datetime.now() - t0).total_seconds()
        print(f"  {len(xml_postings)} postings parsed, {matched} matched to CSV, {elapsed:.1f}s")

        del xml_postings, csv_lookup
        gc.collect()

    # Free CSV cache
    del csv_cache
    gc.collect()

    print(f"\nTotal postings collected: {len(all_postings)}")
    matched_total = sum(1 for p in all_postings if p.get('MinSalary') is not None)
    print(f"Matched to CSV Main (have salary/SOC): {matched_total}")

    # Shuffle to avoid systematic ordering
    random.seed(42)
    random.shuffle(all_postings)

    # --- Extract Study 1 phrases ---
    print("\n--- Study 1: Extracting phrases ---")
    phrases = extract_study1_phrases(all_postings, target_count=args.phrase_target)
    print(f"Extracted {len(phrases)} phrases")

    # Report category distribution
    cat_dist = defaultdict(int)
    for p in phrases:
        cat_dist[p['irb_category']] += 1
    print("Category distribution:")
    for cat, count in sorted(cat_dist.items()):
        print(f"  {cat}: {count}")
    ambig_count = sum(1 for p in phrases if p['is_ambiguous'])
    print(f"Ambiguous phrases: {ambig_count}")

    # --- Extract Study 2 postings ---
    print("\n--- Study 2: Extracting full postings ---")
    study2_postings = extract_study2_postings(all_postings, target_count=args.posting_target)
    print(f"Selected {len(study2_postings)} postings")
    purpose_count = sum(1 for p in study2_postings if p['has_purpose_language'])
    salary_count = sum(1 for p in study2_postings if p.get('has_salary'))
    print(f"  With purpose language: {purpose_count}")
    print(f"  Without purpose language: {len(study2_postings) - purpose_count}")
    print(f"  With salary data (from CSV): {salary_count}")

    # --- Save outputs ---
    print("\n--- Saving outputs ---")

    # Study 1 phrases
    phrases_path = os.path.join(args.output_dir, 'phrases_raw.json')
    with open(phrases_path, 'w') as f:
        json.dump(phrases, f, indent=2)
    print(f"Saved {len(phrases)} phrases to {phrases_path}")

    # Also save as CSV for easy review
    phrases_csv_path = os.path.join(args.output_dir, 'phrases_raw.csv')
    if phrases:
        with open(phrases_csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'phrase', 'context', 'irb_category', 'dict_category',
                'dict_subcategory', 'is_ambiguous', 'cross_categories',
                'source_employer', 'source_job_title', 'source_job_id',
                'source_date', 'source_soc', 'source_soc_name',
            ])
            writer.writeheader()
            for p in phrases:
                row = {**p, 'cross_categories': '|'.join(p['cross_categories'])}
                writer.writerow(row)
    print(f"Saved phrases CSV to {phrases_csv_path}")

    # Study 2 postings
    postings_path = os.path.join(args.output_dir, 'postings_selected.json')
    with open(postings_path, 'w') as f:
        json.dump(study2_postings, f, indent=2)
    print(f"Saved {len(study2_postings)} postings to {postings_path}")

    # Also save as CSV
    postings_csv_path = os.path.join(args.output_dir, 'postings_selected.csv')
    if study2_postings:
        with open(postings_csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'job_id', 'employer', 'job_title', 'soc', 'soc_name',
                'city', 'state', 'msa', 'sector_name', 'naics3', 'date',
                'min_salary', 'max_salary', 'mean_salary', 'has_salary',
                'has_purpose_language', 'purpose_terms_found',
                'non_purpose_terms_found', 'word_count',
            ])
            writer.writeheader()
            for p in study2_postings:
                row = {
                    **{k: v for k, v in p.items() if k != 'job_text'},
                    'purpose_terms_found': '|'.join(p['purpose_terms_found']),
                    'non_purpose_terms_found': '|'.join(p['non_purpose_terms_found']),
                }
                writer.writerow(row)
    print(f"Saved postings CSV to {postings_csv_path}")

    # Assessment document
    assessment_path = os.path.join(args.output_dir, 'stimuli_assessment.md')
    with open(assessment_path, 'w') as f:
        f.write("# Stimuli Extraction Assessment\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write("## Source Data\n\n")
        f.write(f"- Years sampled: {args.years}\n")
        f.write(f"- Zip files processed: {len(sampled_zips)}\n")
        f.write(f"- Total postings read: {len(all_postings)}\n\n")
        f.write("## Study 1 — Phrase Classification\n\n")
        f.write(f"- Total phrases extracted: {len(phrases)}\n")
        f.write(f"- Ambiguous (cross-category): {ambig_count}\n")
        f.write("- Category distribution:\n")
        for cat, count in sorted(cat_dist.items()):
            f.write(f"  - {cat}: {count}\n")
        f.write("\n### Review Needed\n\n")
        f.write("- [ ] Review all phrases for appropriateness\n")
        f.write("- [ ] Remove any with identifying employer information that should be anonymized\n")
        f.write("- [ ] Verify ambiguous phrases are genuinely ambiguous\n")
        f.write("- [ ] Select final ~80-100 from this larger set\n")
        f.write("- [ ] Add 5 practice items and 5 attention check anchors (from IRB materials)\n\n")
        f.write("## Study 2 — Job Posting Evaluation\n\n")
        f.write(f"- Total postings selected: {len(study2_postings)}\n")
        f.write(f"- With purpose language: {purpose_count}\n")
        f.write(f"- Without purpose language: {len(study2_postings) - purpose_count}\n")
        f.write(f"- With salary data (from CSV Main merge): {salary_count}\n")
        f.write("\n### Review Needed\n\n")
        f.write("- [ ] Review postings for vignette construction quality\n")
        f.write("- [ ] Ensure industry/occupation diversity\n")
        f.write("- [ ] Verify salary ranges are realistic for the role\n")
        f.write("- [ ] Use these as raw material — the final vignettes in the IRB are fictional composites\n\n")
        f.write("## IRB Notes\n\n")
        f.write("- Study 1 uses real phrases from real postings (employer names removed)\n")
        f.write("- Study 2 uses fictional company names and composite vignettes\n")
        f.write("- All stimuli should be reviewed against IRB Study Materials before deployment\n")
    print(f"Saved assessment to {assessment_path}")

    print("\n" + "=" * 60)
    print("Done. Review outputs in:", args.output_dir)
    print("=" * 60)


if __name__ == '__main__':
    main()
