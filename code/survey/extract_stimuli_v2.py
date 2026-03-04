#!/usr/bin/env python3
"""
Study 1 Stimuli Pipeline v2 — KeyBERT extraction + Codex CLI assessment.

Replaces keyword-level extraction with phrase-level stimuli graded on a
difficulty spectrum. Produces ~80-100 phrases for an IRB classification
experiment validating the organizational purpose dictionary.

Stages:
  1. Sample real postings from XML+CSV → parquet (parallel, 3 years)
  2. KeyBERT candidate extraction (parallel, 3 chunks)
  3. Codex CLI assessment (parallel, 3 threads)
  4. Seed augmentation (IRB examples + dictionary terms)
  5. Boundary assessment report
  6. Output files

Usage:
    python extract_stimuli_v2.py
    python extract_stimuli_v2.py --stage 1        # Run only Stage 1
    python extract_stimuli_v2.py --skip-codex      # Stages 1-2 only
    python extract_stimuli_v2.py --force-resample  # Re-run Stage 1
"""

import os
import sys
import re
import gc
import csv
import json
import time
import random
import logging
import argparse
import threading
import subprocess
import tempfile
import unicodedata
import xml.etree.ElementTree as ET
from zipfile import ZipFile
from collections import defaultdict, Counter
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DEFAULT_DATA_ROOT = "/Volumes/Expansion/All server/data/Burning Glass 2"
DEFAULT_OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "survey", "stimuli"
)
DEFAULT_YEARS = [2013, 2016, 2019]
DEFAULT_ZIPS_PER_YEAR = 2
DEFAULT_POSTINGS_PER_ZIP = 5000
DEFAULT_BATCH_SIZE = 10
MAX_WORKERS = 3

# Industry tier definitions (NAICS 3-digit codes)
HIGH_PURPOSE_NAICS = {611, 612, 613, 614, 615, 621, 622, 623, 624, 813}
NEUTRAL_NAICS = {441, 442, 443, 444, 445, 446, 447, 448, 451, 452, 453, 454,
                 511, 512, 515, 517, 518, 519, 541, 542}
LOW_PURPOSE_NAICS = {211, 212, 213, 221, 521, 522, 523, 524, 525,
                     331, 332, 333, 334, 335, 336, 337, 338, 339}

# Pre-filter patterns for Stage 2
TASK_VERBS = {'manage', 'coordinate', 'develop', 'plan', 'implement',
              'execute', 'oversee', 'lead', 'direct', 'administer',
              'facilitate', 'organize', 'prepare', 'maintain', 'monitor'}
REQ_PATTERNS = re.compile(
    r'years?\s+(?:of\s+)?experience|degree\s+required|must\s+have|'
    r'preferred\s+qualif|minimum\s+qualif|required\s+skills?|'
    r'bachelor|master|certification\s+required', re.IGNORECASE)
TITLE_PATTERNS = re.compile(
    r'(?:manager|analyst|coordinator|specialist|director|associate)\s+'
    r'(?:position|role|opening)$', re.IGNORECASE)

# Company/organization name patterns
COMPANY_PATTERNS = re.compile(
    r'\b(?:inc|corp|llc|ltd|co\b|group|associates|organization|enterprise|'
    r'university|hospital|center|institute|laboratory|solutions|technologies|'
    r'systems|industries|pharmaceuticals|automotive|insurance|financial|'
    r'healthcare|foundation|scientific|consulting)\b', re.IGNORECASE)

# Geographic/location patterns
GEO_PATTERNS = re.compile(
    r'\b(?:florida|texas|california|virginia|new york|kentucky|ohio|'
    r'pennsylvania|washington|oregon|portland|jacksonville|rochester|'
    r'pittsburgh|arlington|bellevue|chicago|baltimore|minneapolis|'
    r'nationwide|headquarters|headquartered|metro|county|location|'
    r'branch|office\s+(?:in|at|near)|map\s+type)\b', re.IGNORECASE)

# Web/UI/structural junk
WEB_PATTERNS = re.compile(
    r'\b(?:www|\.com|http|\.org|\.net|careers?\b|website|apply\b|click|'
    r'sign\s*in|login|submit|printable|format|requisition|'
    r'job\s*(?:description|search|posting|number|id|details|cart)|'
    r'view\s+(?:all|more)|back\s+to)\b', re.IGNORECASE)

# Technical/clinical occupation terms
CLINICAL_PATTERNS = re.compile(
    r'\b(?:nurse|nursing|physician|technician|cpa|coder|counseling|'
    r'clinical|surgical|diagnostic|radiology|pharmacy|dental\s+(?:assisting|hygiene)|'
    r'mechanic|welder|electrician|plumber|hvac|cdl|forklift|transplant|'
    r'dialysis|icu|nicu|oncology|cardiology|orthopedic)\b', re.IGNORECASE)

# Semantic anchors for similarity filtering — phrases we WANT to find
SEMANTIC_ANCHORS = [
    # organizational purpose / mission values
    'mission driven', 'make a real difference', 'work with purpose',
    'shared values', 'committed to sustainability', 'positive impact',
    'making a difference', 'social responsibility', 'environmental stewardship',
    'ethical sourcing', 'community engagement', 'force for good',
    'meaningful work', 'lasting impact', 'improve lives through innovation',
    'diversity and inclusion', 'equitable future', 'passion for impact',
    'purpose driven', 'changing the world', 'social impact',
    # good employer / treats well
    'career development', 'work life balance', 'invest in employees',
    'collaborative culture', 'supportive workplace', 'professional growth',
    'open door policy', 'transparent leadership', 'team environment',
    'top employer', 'psychologically safe', 'continuous learning',
    'career advancement', 'mentorship programs', 'recognition awards',
    'employee wellbeing', 'flexible scheduling', 'inclusive workplace',
    'empowering employees', 'nurturing environment', 'great place to work',
    # pecuniary / pay and benefits
    'health dental vision insurance', 'retirement plan', 'performance bonus',
    'stock purchase plan', 'paid time off', 'commuter benefits',
    'tuition reimbursement', 'competitive salary', 'signing bonus',
    'profit sharing', 'employee discount', 'relocation assistance',
    # job tasks (representative)
    'develop marketing campaigns', 'analyze data prepare reports',
    'coordinate teams launch products', 'manage vendor relationships',
    'oversee daily operations', 'design training programs',
]
MIN_ANCHOR_SIMILARITY = 0.50

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def setup_logging(output_dir):
    log_path = os.path.join(output_dir, 'stimuli_pipeline.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_path, mode='a'),
            logging.StreamHandler(sys.stdout),
        ]
    )
    return logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Reusable functions from extract_stimuli.py
# ---------------------------------------------------------------------------

def clean_text(text):
    """Normalize and clean job posting text for dictionary matching."""
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8', 'ignore')
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', text)
    text = re.sub(r'[^a-zA-Z0-9\s.,!?]', '', text)
    return re.sub(r'\s+', ' ', text.lower()).strip()


def parse_xml_zip(zip_path, max_postings=None):
    """Parse a Lightcast XML zip file and yield job postings as dicts."""
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

            if posting.get('IsDuplicate') == '1':
                continue
            if not posting.get('JobText') or not posting.get('CanonEmployer'):
                continue

            count += 1
            yield posting
            if max_postings and count >= max_postings:
                return


def get_months_from_xml_filename(xml_zip_name):
    """Extract month(s) covered by an XML zip from its filename."""
    match = re.search(r'(\d{4})(\d{2})\d{2}_(\d{4})(\d{2})\d{2}', xml_zip_name)
    if not match:
        return []
    y1, m1, y2, m2 = match.groups()
    months = [(y1, m1)]
    if (y1, m1) != (y2, m2):
        months.append((y2, m2))
    return months


def load_csv_main_lookup(data_root, year, month):
    """Load a CSV Main zip and return dict: BGTJobId -> metadata dict."""
    csv_zip = os.path.join(
        data_root, 'CSV', 'US', 'Add', 'Main', str(year),
        f'Main_{year}-{month}.zip')
    if not os.path.exists(csv_zip):
        return {}

    usecols = [
        'BGTJobId', 'CleanTitle', 'SOC', 'SOCName',
        'Employer', 'Sector', 'SectorName', 'NAICS3',
        'City', 'State', 'BestFitMSA', 'BestFitMSAName',
        'MinSalary', 'MaxSalary',
    ]
    try:
        df = pd.read_table(csv_zip, encoding='latin', engine='python',
                           delimiter='\t', usecols=usecols)
    except Exception:
        return {}

    df['BGTJobId'] = df['BGTJobId'].astype(str)
    df = df.set_index('BGTJobId')
    df = df.fillna({'MinSalary': -999, 'MaxSalary': -999})
    df = df.fillna('')
    lookup = df.to_dict('index')
    del df
    gc.collect()
    return lookup


def classify_naics(naics3):
    """Classify a 3-digit NAICS code into an industry tier."""
    try:
        n = int(naics3)
    except (ValueError, TypeError):
        return None
    if n in HIGH_PURPOSE_NAICS:
        return 'high_purpose'
    if n in NEUTRAL_NAICS:
        return 'neutral'
    if n in LOW_PURPOSE_NAICS:
        return 'low_purpose'
    return None


def extract_context_sentences(text, phrase, n_sentences=2):
    """Extract n sentences before and after the sentence containing phrase."""
    if not text or not phrase:
        return ""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    phrase_lower = phrase.lower()
    target_idx = None
    for i, sent in enumerate(sentences):
        if phrase_lower in sent.lower():
            target_idx = i
            break
    if target_idx is None:
        # Fuzzy: try flexible whitespace
        pattern = re.compile(r'\s+'.join(re.escape(w) for w in phrase.split()),
                             re.IGNORECASE)
        for i, sent in enumerate(sentences):
            if pattern.search(sent):
                target_idx = i
                break
    if target_idx is None:
        return text[:500]

    start = max(0, target_idx - n_sentences)
    end = min(len(sentences), target_idx + n_sentences + 1)
    context = ' '.join(sentences[start:end]).strip()
    context = re.sub(r'\s+', ' ', context)
    return context[:500]


# ---------------------------------------------------------------------------
# Stage 1: Sample postings → parquet
# ---------------------------------------------------------------------------

def sample_year(args_tuple):
    """Worker function: sample postings for one year. Returns a list of dicts."""
    year, data_root, zips_per_year, postings_per_zip = args_tuple

    xml_dir = os.path.join(data_root, 'Jobs', 'US', 'Add', str(year))
    if not os.path.isdir(xml_dir):
        print(f"  Year {year}: XML directory not found: {xml_dir}")
        return []

    all_zips = sorted([f for f in os.listdir(xml_dir) if f.endswith('.zip')])
    if not all_zips:
        print(f"  Year {year}: no zip files found")
        return []

    # Pick evenly spaced zips
    step = max(1, len(all_zips) // zips_per_year)
    indices = list(range(0, len(all_zips), step))[:zips_per_year]
    selected_zips = [all_zips[i] for i in indices]
    print(f"  Year {year}: selected {len(selected_zips)} zips from {len(all_zips)} total")

    # Load CSV lookups for the months covered
    csv_cache = {}
    for zip_name in selected_zips:
        for y, m in get_months_from_xml_filename(zip_name):
            if (y, m) not in csv_cache:
                csv_cache[(y, m)] = load_csv_main_lookup(data_root, y, m)

    # Parse and collect
    candidates = {'high_purpose': [], 'neutral': [], 'low_purpose': []}
    target_per_tier = 30

    for zip_name in selected_zips:
        zip_path = os.path.join(xml_dir, zip_name)
        months = get_months_from_xml_filename(zip_name)

        for posting in parse_xml_zip(zip_path, max_postings=postings_per_zip):
            job_id = str(posting.get('JobID', ''))
            job_text = posting.get('JobText', '')

            # Must have substantial text
            if len(job_text) < 200:
                continue

            # Try to find CSV metadata
            meta = None
            for y, m in months:
                lookup = csv_cache.get((y, m), {})
                if job_id in lookup:
                    meta = lookup[job_id]
                    break
            if not meta:
                continue

            # Filter: SOC prefix 11-43, employer present, NAICS available
            soc = str(meta.get('SOC', ''))
            if not soc or len(soc) < 2:
                continue
            try:
                soc_prefix = int(soc.split('-')[0])
            except ValueError:
                continue
            if soc_prefix < 11 or soc_prefix > 43:
                continue

            naics3 = meta.get('NAICS3', '')
            tier = classify_naics(naics3)
            if not tier:
                continue

            employer = meta.get('Employer', '') or posting.get('CanonEmployer', '')
            if not employer:
                continue

            # Check if this tier still needs postings
            if len(candidates[tier]) >= target_per_tier:
                continue

            row = {
                'job_id': job_id,
                'job_text': job_text,
                'clean_title': meta.get('CleanTitle', ''),
                'soc': soc,
                'soc_name': meta.get('SOCName', ''),
                'naics3': int(naics3) if naics3 else 0,
                'sector_name': meta.get('SectorName', ''),
                'employer': employer,
                'city': meta.get('City', ''),
                'state': meta.get('State', ''),
                'min_salary': float(meta.get('MinSalary', -999)),
                'max_salary': float(meta.get('MaxSalary', -999)),
                'year': year,
                'industry_tier': tier,
            }
            candidates[tier].append(row)

        # Check if all tiers are full
        if all(len(v) >= target_per_tier for v in candidates.values()):
            break

    result = []
    for tier_rows in candidates.values():
        result.extend(tier_rows)
    print(f"  Year {year}: sampled {len(result)} postings "
          f"(HP={len(candidates['high_purpose'])}, "
          f"N={len(candidates['neutral'])}, "
          f"LP={len(candidates['low_purpose'])})")

    # Free memory
    del csv_cache
    gc.collect()
    return result


def run_stage1(data_root, output_dir, years, zips_per_year, postings_per_zip, logger):
    """Stage 1: Sample postings from XML+CSV, write to parquet."""
    logger.info("=== STAGE 1: Sample postings ===")

    parquet_path = os.path.join(output_dir, 'sampled_postings.parquet')

    args_list = [(y, data_root, zips_per_year, postings_per_zip) for y in years]

    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(sample_year, a): a[0] for a in args_list}
        all_rows = []
        for future in as_completed(futures):
            year = futures[future]
            try:
                rows = future.result()
                all_rows.extend(rows)
            except Exception as e:
                logger.error(f"Year {year} failed: {e}")

    if not all_rows:
        logger.error("No postings sampled. Check data paths.")
        return None

    df = pd.DataFrame(all_rows)
    df.to_parquet(parquet_path, index=False)
    logger.info(f"Wrote {len(df)} postings to {parquet_path}")
    return parquet_path


def checkpoint1(output_dir, years, logger):
    """Validate Stage 1 output."""
    logger.info("--- Checkpoint 1 ---")
    parquet_path = os.path.join(output_dir, 'sampled_postings.parquet')
    ok = True

    # 1.1: Exists and readable
    if not os.path.exists(parquet_path):
        logger.error("CHECK 1.1 FAIL: parquet not found")
        return False
    df = pd.read_parquet(parquet_path)

    # 1.2: Row count
    n = len(df)
    if not (100 <= n <= 600):
        logger.error(f"CHECK 1.2 FAIL: {n} rows (expected 100-600)")
        ok = False
    else:
        logger.info(f"CHECK 1.2 OK: {n} rows")

    # 1.3: All years present
    present_years = set(df['year'].unique())
    expected_years = set(years)
    if not expected_years.issubset(present_years):
        logger.error(f"CHECK 1.3 FAIL: missing years {expected_years - present_years}")
        ok = False
    else:
        logger.info(f"CHECK 1.3 OK: years {sorted(present_years)}")

    # 1.4: All tiers present
    tiers = set(df['industry_tier'].unique())
    expected_tiers = {'high_purpose', 'neutral', 'low_purpose'}
    if not expected_tiers.issubset(tiers):
        logger.error(f"CHECK 1.4 FAIL: missing tiers {expected_tiers - tiers}")
        ok = False
    else:
        logger.info(f"CHECK 1.4 OK: tiers {sorted(tiers)}")

    # 1.5: Balance
    tier_counts = df['industry_tier'].value_counts()
    for tier in expected_tiers:
        pct = tier_counts.get(tier, 0) / n
        if pct < 0.15:
            logger.warning(f"CHECK 1.5 WARN: {tier} = {pct:.1%} (< 20%)")

    # 1.6: job_text quality
    null_text = df['job_text'].isna().sum()
    short_text = (df['job_text'].str.len() < 200).sum()
    if null_text > 0 or short_text > 0:
        logger.warning(f"CHECK 1.6 WARN: {null_text} null texts, {short_text} short texts")

    # 1.7: Distribution table
    cross = pd.crosstab(df['year'], df['industry_tier'])
    logger.info(f"Distribution:\n{cross}")

    if not ok:
        os.remove(parquet_path)
        logger.error("Checkpoint 1 FAILED — parquet deleted")
    else:
        logger.info("Checkpoint 1 PASSED")
    return ok


# ---------------------------------------------------------------------------
# Stage 2: Targeted branding phrase extraction
# ---------------------------------------------------------------------------

# Vocabulary cues that signal a sentence contains employer branding language
BRANDING_CUES = re.compile(
    r'\b(?:'
    # Purpose / mission
    r'mission|purpose|values?|impact|difference|meaningful|'
    r'sustainability|stewardship|responsibility|ethical|equitable|'
    r'community|communities|social\s+good|force\s+for\s+good|'
    # Good employer / treats well
    r'career\s+(?:development|growth|advancement|path)|'
    r'work[- ]life\s+balance|flexible\s+(?:work|schedule|hours)|'
    r'collaborative\s+(?:culture|environment|team)|'
    r'supportive|inclusive|diversity|mentorship|mentor|'
    r'recognition|employee\s+(?:engagement|wellbeing|well-being|satisfaction)|'
    r'professional\s+(?:development|growth)|'
    r'great\s+place\s+to\s+work|best\s+place|top\s+employer|'
    r'psychologically\s+safe|open[- ]door|'
    r'invest(?:s|ing)?\s+in\s+(?:our|their|your)?\s*(?:people|employees|team)|'
    r'nurturing|empowering|'
    # Pecuniary
    r'competitive\s+(?:salary|pay|compensation|benefits|total)|'
    r'tuition\s+(?:reimbursement|assistance)|'
    r'generous\s+(?:benefits|pto|time\s+off|paid)|'
    r'retirement\s+(?:plan|benefits|savings)|'
    r'stock\s+(?:purchase|options)|profit\s+sharing|'
    r'signing\s+bonus|performance\s+bonus|'
    # Catch-all branding signals
    r'we\s+(?:believe|strive|value|are\s+committed|are\s+proud|offer|provide)|'
    r'(?:dedicated|committed|passionate)\s+(?:to|about)|'
    r'rewarding\s+(?:career|work|experience)|'
    r'culture\s+of|our\s+people|our\s+team'
    r')\b', re.IGNORECASE)


def split_sentences(text):
    """Split text into sentences, handling common job posting formatting."""
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    # Split on sentence-ending punctuation, bullet points, and line breaks
    sents = re.split(r'[.!?]\s+|(?:â¢|\*|·|â)\s*|(?:\n|\r)', text)
    return [s.strip() for s in sents if len(s.strip()) > 15]



def extraction_worker(args_tuple):
    """Worker: extract branding phrases from a chunk of postings.

    Strategy:
    1. Split posting into sentences
    2. Identify branding sentences via vocabulary cues
    3. Run KeyBERT on branding sections to extract meaningful phrases
    4. Also run KeyBERT on full text but with fewer candidates
    Returns list of dicts.
    """
    chunk, chunk_id = args_tuple
    from keybert import KeyBERT

    kw_model = KeyBERT("all-MiniLM-L6-v2")
    results = []

    for _, row in chunk.iterrows():
        job_text = row['job_text']
        meta = {
            'job_id': row['job_id'],
            'naics3': row['naics3'],
            'soc': row['soc'],
            'year': row['year'],
            'industry_tier': row['industry_tier'],
            'employer': row['employer'],
        }

        # Step 1: Find branding sentences
        sentences = split_sentences(job_text)
        branding_sents = [s for s in sentences if BRANDING_CUES.search(s)]

        # Step 2: Run KeyBERT on branding sections (primary source)
        branding_text = ' '.join(branding_sents)
        if len(branding_text) > 50:
            try:
                keyphrases = kw_model.extract_keywords(
                    branding_text,
                    keyphrase_ngram_range=(2, 5),
                    stop_words="english",
                    top_n=15,
                    use_mmr=True,
                    diversity=0.6,
                )
                for phrase, score in keyphrases:
                    context = extract_context_sentences(job_text, phrase)
                    results.append({
                        'phrase': phrase.strip().lower(),
                        'extraction_score': round(score, 4),
                        'context': context,
                        'source': 'keybert_branding',
                        **meta,
                    })
            except Exception:
                pass

        # Step 3: Run KeyBERT on full text (supplementary, fewer candidates)
        try:
            keyphrases = kw_model.extract_keywords(
                job_text,
                keyphrase_ngram_range=(2, 4),
                stop_words="english",
                top_n=10,
                use_mmr=True,
                diversity=0.5,
            )
            for phrase, score in keyphrases:
                context = extract_context_sentences(job_text, phrase)
                results.append({
                    'phrase': phrase.strip().lower(),
                    'extraction_score': round(score, 4),
                    'context': context,
                    'source': 'keybert_fulltext',
                    **meta,
                })
        except Exception:
            pass

    print(f"  Chunk {chunk_id}: {len(results)} raw candidates "
          f"from {len(chunk)} postings")
    return results


def semantic_filter(phrases, contexts, anchor_embs, model, threshold):
    """Keep phrases with semantic similarity >= threshold to any anchor.

    Returns boolean mask and similarity scores.
    """
    import numpy as np
    if len(phrases) == 0:
        return [], []
    phrase_embs = model.encode(phrases, normalize_embeddings=True, batch_size=256)
    sims = (phrase_embs @ anchor_embs.T).max(axis=1)
    return sims >= threshold, sims


def run_stage2(output_dir, logger):
    """Stage 2: Targeted branding phrase extraction.

    Hybrid approach:
    1. Identify branding sentences in each posting via vocabulary cues
    2. Extract n-grams from those sentences
    3. Run KeyBERT on branding sections for supplementary candidates
    4. Semantic filter: keep only phrases close to employer branding anchors
    5. Pattern-based junk removal for remaining garbage
    """
    logger.info("=== STAGE 2: Branding phrase extraction ===")

    parquet_path = os.path.join(output_dir, 'sampled_postings.parquet')
    candidates_path = os.path.join(output_dir, 'keybert_candidates.csv')

    df = pd.read_parquet(parquet_path)
    n_postings = len(df)
    logger.info(f"Loaded {n_postings} postings")

    # Split into chunks for parallel processing
    chunk_size = max(1, n_postings // MAX_WORKERS)
    chunks = []
    for i in range(0, n_postings, chunk_size):
        chunks.append((df.iloc[i:i + chunk_size].copy(), len(chunks)))

    # Run extraction in parallel
    all_results = []
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(extraction_worker, c): c[1] for c in chunks}
        for future in as_completed(futures):
            try:
                results = future.result()
                all_results.extend(results)
            except Exception as e:
                logger.error(f"Extraction chunk failed: {e}")

    if not all_results:
        logger.error("No phrases extracted")
        return None

    cand_df = pd.DataFrame(all_results)
    logger.info(f"Raw extracted phrases: {len(cand_df)}")

    # --- Pattern-based junk removal ---
    n_before = len(cand_df)
    junk_stats = {}

    # Remove too short
    mask = cand_df['phrase'].apply(lambda p: len(p.split()) < 2)
    junk_stats['too_short'] = mask.sum()
    cand_df = cand_df[~mask]

    # Remove phrases with digits
    mask = cand_df['phrase'].str.contains(r'\d')
    junk_stats['has_digits'] = mask.sum()
    cand_df = cand_df[~mask]

    # Remove single-char tokens
    mask = cand_df['phrase'].apply(lambda p: any(len(t) <= 1 for t in p.split()))
    junk_stats['short_tokens'] = mask.sum()
    cand_df = cand_df[~mask]

    # Remove company/org name patterns
    mask = cand_df['phrase'].apply(lambda p: bool(COMPANY_PATTERNS.search(p)))
    junk_stats['company_names'] = mask.sum()
    cand_df = cand_df[~mask]

    # Remove employer name matches
    def matches_employer(row):
        employer = str(row.get('employer', '')).lower().strip()
        if len(employer) < 3:
            return False
        for w in employer.split():
            if len(w) > 3 and w in row['phrase']:
                return True
        return False
    mask = cand_df.apply(matches_employer, axis=1)
    junk_stats['employer_match'] = mask.sum()
    cand_df = cand_df[~mask]

    # Remove geographic content
    mask = cand_df['phrase'].apply(lambda p: bool(GEO_PATTERNS.search(p)))
    junk_stats['geographic'] = mask.sum()
    cand_df = cand_df[~mask]

    # Remove web/UI junk
    mask = cand_df['phrase'].apply(lambda p: bool(WEB_PATTERNS.search(p)))
    junk_stats['web_junk'] = mask.sum()
    cand_df = cand_df[~mask]

    # Remove clinical/technical terms
    mask = cand_df['phrase'].apply(lambda p: bool(CLINICAL_PATTERNS.search(p)))
    junk_stats['clinical'] = mask.sum()
    cand_df = cand_df[~mask]

    logger.info(f"After junk removal: {len(cand_df)} "
                f"(removed {n_before - len(cand_df)}, stats: {junk_stats})")

    # --- Deduplicate phrases before semantic filtering ---
    cand_df = cand_df.drop_duplicates(subset=['phrase'])
    logger.info(f"Unique phrases: {len(cand_df)}")

    # --- Semantic similarity filtering ---
    from sentence_transformers import SentenceTransformer
    import numpy as np

    model = SentenceTransformer('all-MiniLM-L6-v2')
    anchor_embs = model.encode(SEMANTIC_ANCHORS, normalize_embeddings=True)

    phrases_list = cand_df['phrase'].tolist()
    keep_mask, sims = semantic_filter(
        phrases_list, None, anchor_embs, model, MIN_ANCHOR_SIMILARITY)

    cand_df = cand_df.copy()
    cand_df['anchor_similarity'] = sims
    n_before_sem = len(cand_df)
    cand_df = cand_df[keep_mask]
    logger.info(f"After semantic filter (>= {MIN_ANCHOR_SIMILARITY}): "
                f"{len(cand_df)} (removed {n_before_sem - len(cand_df)})")

    del model
    gc.collect()

    # --- Record cross-firm frequency from pre-dedup data ---
    cand_df['cross_firm_frequency'] = 1  # will be updated from raw data

    # Sort by similarity (best matches first)
    cand_df = cand_df.sort_values('anchor_similarity', ascending=False)
    cand_df.to_csv(candidates_path, index=False)
    logger.info(f"Wrote {len(cand_df)} candidates to {candidates_path}")
    return candidates_path


def checkpoint2(output_dir, logger):
    """Validate Stage 2 output."""
    logger.info("--- Checkpoint 2 ---")
    candidates_path = os.path.join(output_dir, 'keybert_candidates.csv')
    ok = True

    if not os.path.exists(candidates_path):
        logger.error("CHECK 2.1 FAIL: candidates.csv not found")
        return False

    df = pd.read_csv(candidates_path)

    # 2.1: Row count
    if len(df) < 50:
        logger.error(f"CHECK 2.1 FAIL: only {len(df)} candidates (expected > 100)")
        ok = False
    else:
        logger.info(f"CHECK 2.1 OK: {len(df)} candidates")

    # 2.2: No duplicate (phrase, job_id) — already deduped to unique phrases
    dupes = df.duplicated(subset=['phrase']).sum()
    if dupes > 0:
        logger.warning(f"CHECK 2.2 WARN: {dupes} duplicate phrases")

    # 2.3: All tiers represented
    tiers = set(df['industry_tier'].unique())
    if len(tiers) < 3:
        logger.warning(f"CHECK 2.3 WARN: only {len(tiers)} tiers in candidates")

    # 2.4: Sample phrases per tier
    for tier in sorted(df['industry_tier'].unique()):
        samples = df[df['industry_tier'] == tier]['phrase'].head(5).tolist()
        logger.info(f"  {tier}: {samples}")

    # 2.5: Context quality
    null_ctx = df['context'].isna().sum()
    if null_ctx > 0:
        logger.warning(f"CHECK 2.5 WARN: {null_ctx} null contexts")

    logger.info("Checkpoint 2 PASSED" if ok else "Checkpoint 2 FAILED")
    return ok


# ---------------------------------------------------------------------------
# Stage 3: Codex CLI assessment
# ---------------------------------------------------------------------------

_jsonl_lock = threading.Lock()


def load_instructions(output_dir):
    """Load the assessment instructions markdown."""
    inst_path = os.path.join(output_dir, 'assessment_instructions.md')
    if os.path.exists(inst_path):
        with open(inst_path) as f:
            return f.read()
    # Fallback: use the one in the repo
    repo_inst = os.path.join(os.path.dirname(__file__), 'stimuli', 'assessment_instructions.md')
    if os.path.exists(repo_inst):
        with open(repo_inst) as f:
            return f.read()
    return ""


def build_batch_prompt(instructions, batch_items):
    """Build a Codex prompt for a batch of phrases."""
    items_text = "\n\n".join([
        f"PHRASE {i+1}: \"{item['phrase']}\"\n"
        f"CONTEXT: \"{item['context']}\"\n"
        f"INDUSTRY: {item.get('industry_tier', 'unknown')}"
        for i, item in enumerate(batch_items)
    ])
    prompt = (
        f"{instructions}\n\n"
        f"Assess these {len(batch_items)} phrases. "
        f"Return ONLY a JSON array:\n\n{items_text}"
    )
    return prompt


def assess_batch_codex(batch_id, batch_items, instructions, output_dir, logger):
    """Run Codex CLI on one batch. Returns list of assessment dicts."""
    outfile = os.path.join(tempfile.gettempdir(), f'codex_batch_{batch_id}.txt')
    prompt = build_batch_prompt(instructions, batch_items)

    try:
        result = subprocess.run(
            ['npx', '@openai/codex', 'exec', '-o', outfile, prompt],
            capture_output=True, text=True, timeout=120,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
    except subprocess.TimeoutExpired:
        logger.warning(f"Batch {batch_id}: Codex timed out")
        return []
    except Exception as e:
        logger.warning(f"Batch {batch_id}: subprocess error: {e}")
        return []

    # Read output file
    if not os.path.exists(outfile):
        logger.warning(f"Batch {batch_id}: no output file")
        return []

    try:
        with open(outfile) as f:
            raw = f.read().strip()
        assessments = json.loads(raw)
        if not isinstance(assessments, list):
            assessments = [assessments]
    except json.JSONDecodeError:
        # Log the raw output for debugging
        error_log = os.path.join(output_dir, 'parse_errors.log')
        with open(error_log, 'a') as f:
            f.write(f"--- Batch {batch_id} ---\n{raw}\n\n")
        logger.warning(f"Batch {batch_id}: JSON parse error (logged to parse_errors.log)")
        return []
    finally:
        if os.path.exists(outfile):
            os.remove(outfile)

    # Write to JSONL
    jsonl_path = os.path.join(output_dir, 'phrase_assessments_raw.jsonl')
    with _jsonl_lock:
        with open(jsonl_path, 'a') as f:
            for a in assessments:
                a['_batch_id'] = batch_id
                a['_source'] = 'lightcast'
                f.write(json.dumps(a) + '\n')

    return assessments


def run_stage3(output_dir, batch_size, logger):
    """Stage 3: Codex CLI assessment of KeyBERT candidates."""
    logger.info("=== STAGE 3: Codex CLI assessment ===")

    candidates_path = os.path.join(output_dir, 'keybert_candidates.csv')
    jsonl_path = os.path.join(output_dir, 'phrase_assessments_raw.jsonl')
    progress_path = os.path.join(output_dir, '_batch_progress.json')

    df = pd.read_csv(candidates_path)
    instructions = load_instructions(output_dir)

    # Resume support
    completed_batches = set()
    if os.path.exists(progress_path):
        with open(progress_path) as f:
            completed_batches = set(json.load(f).get('completed', []))

    # Build batches
    records = df.to_dict('records')
    batches = []
    for i in range(0, len(records), batch_size):
        batch_id = i // batch_size
        if batch_id in completed_batches:
            continue
        batches.append((batch_id, records[i:i+batch_size]))

    logger.info(f"Batches to process: {len(batches)} "
                f"(skipping {len(completed_batches)} completed)")

    all_assessments = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {}
        for batch_id, batch_items in batches:
            time.sleep(2)  # Stagger launches
            future = pool.submit(
                assess_batch_codex, batch_id, batch_items,
                instructions, output_dir, logger)
            futures[future] = batch_id

        for future in as_completed(futures):
            batch_id = futures[future]
            try:
                results = future.result()
                all_assessments.extend(results)
                completed_batches.add(batch_id)
                # Save progress
                with open(progress_path, 'w') as f:
                    json.dump({'completed': sorted(completed_batches)}, f)
                logger.info(f"Batch {batch_id}: {len(results)} assessments")
            except Exception as e:
                logger.error(f"Batch {batch_id} failed: {e}")

    logger.info(f"Total assessments: {len(all_assessments)}")
    return jsonl_path


def checkpoint3(output_dir, logger):
    """Validate Stage 3 output."""
    logger.info("--- Checkpoint 3 ---")
    jsonl_path = os.path.join(output_dir, 'phrase_assessments_raw.jsonl')

    if not os.path.exists(jsonl_path):
        logger.error("CHECK 3.1 FAIL: assessments file not found")
        return False

    assessments = []
    parse_errors = 0
    with open(jsonl_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                a = json.loads(line)
                assessments.append(a)
            except json.JSONDecodeError:
                parse_errors += 1

    total = len(assessments) + parse_errors
    error_rate = parse_errors / max(total, 1)
    logger.info(f"CHECK 3.2: {len(assessments)} valid, {parse_errors} errors "
                f"({error_rate:.1%} error rate)")

    if error_rate >= 0.15:
        logger.error("CHECK 3.3 FAIL: error rate >= 15%")
        return False

    # Check required fields
    required_fields = {'phrase', 'usable', 'primary_category', 'difficulty', 'boundary_pair'}
    missing_field_count = 0
    for a in assessments:
        if not required_fields.issubset(a.keys()):
            missing_field_count += 1
    if missing_field_count > 0:
        logger.warning(f"CHECK 3.4 WARN: {missing_field_count} assessments missing required fields")

    # Difficulty distribution
    difficulties = Counter(a.get('difficulty', 'unknown') for a in assessments)
    logger.info(f"CHECK 3.5 Difficulty: {dict(difficulties)}")
    easy_pct = difficulties.get('easy', 0) / max(len(assessments), 1)
    if easy_pct > 0.8:
        logger.warning("CHECK 3.5 WARN: > 80% easy — model may be under-calibrated")

    # Category distribution
    cats = Counter(a.get('primary_category', 'unknown') for a in assessments)
    logger.info(f"CHECK 3.6 Categories: {dict(cats)}")

    # Sample hard phrases
    hard = [a for a in assessments if a.get('difficulty') == 'hard']
    logger.info(f"CHECK 3.7 Sample HARD phrases ({len(hard)} total):")
    for a in hard[:3]:
        logger.info(f"  \"{a.get('phrase')}\" — {a.get('difficulty_rationale', '')[:100]}")

    logger.info("Checkpoint 3 PASSED")
    return True


# ---------------------------------------------------------------------------
# Stage 4: Seed augmentation
# ---------------------------------------------------------------------------

IRB_SEED_PHRASES = [
    "Making a positive impact on communities worldwide",
    "Committed to sustainability and environmental stewardship",
    "Our mission is to improve lives through innovation",
    "Diversity and inclusion are core to who we are",
    "Volunteer time off to support causes you care about",
    "Building a more equitable future for underserved communities",
    "Invest in your professional growth through mentorship programs",
    "Open-door policy and transparent leadership",
    "Collaborative team environment where your voice matters",
    "Recognized as a top employer for work-life balance",
    "Continuous learning and career advancement opportunities",
    "Supportive and psychologically safe workplace",
    "Competitive health, dental, and vision insurance",
    "Annual performance bonus up to 15% of salary",
    "Employee stock purchase plan",
    "Generous paid time off including 20 vacation days",
    "Commuter benefits and parking allowance",
    "Tuition reimbursement up to $5,000 per year",
    "Develop and execute marketing campaigns across digital channels",
    "Analyze sales data and prepare monthly reports",
    "Coordinate with cross-functional teams to launch new products",
    "Manage vendor relationships and negotiate contracts",
    "Oversee daily operations of the customer service department",
    "Design and implement training programs for new hires",
    "Bachelor's degree in business, marketing, or related field required",
    "Proficiency in SQL and data visualization tools",
    "Strong written and verbal communication skills",
    "Minimum 5 years of experience in project management",
    "PMP or equivalent certification preferred",
    "Ability to travel up to 25% domestically",
]

def _load_all_dicts():
    """Lazy-load dictionaries from extract_stimuli.py."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    from extract_stimuli import (
        meaningful_work, environmental_initiatives, social_initiatives,
        organizational_culture, pecuniary_benefits,
        career_development, job_design_characteristics, job_tasks_requirements,
    )
    return {
        'meaningful_work': meaningful_work,
        'environmental_initiatives': environmental_initiatives,
        'social_initiatives': social_initiatives,
        'organizational_culture': organizational_culture,
        'pecuniary_benefits': pecuniary_benefits,
        'career_development': career_development,
        'job_design_characteristics': job_design_characteristics,
        'job_tasks_requirements': job_tasks_requirements,
    }


def get_dictionary_seeds():
    """Extract 2-4 word terms from all dictionaries."""
    all_dicts = _load_all_dicts()
    seeds = []
    for dict_name, dictionary in all_dicts.items():
        for subcategory, terms in dictionary.items():
            for term in terms:
                n_words = len(term.split())
                if 2 <= n_words <= 4:
                    seeds.append({
                        'phrase': term,
                        'context': 'Employer branding section of a job posting. No additional context.',
                        'source': 'dictionary',
                        'dict_name': dict_name,
                        'industry_tier': 'unknown',
                    })
    # Deduplicate
    seen = set()
    unique = []
    for s in seeds:
        if s['phrase'] not in seen:
            seen.add(s['phrase'])
            unique.append(s)
    return unique


def run_stage4(output_dir, batch_size, logger):
    """Stage 4: Run seeds through Codex assessment."""
    logger.info("=== STAGE 4: Seed augmentation ===")

    instructions = load_instructions(output_dir)
    jsonl_path = os.path.join(output_dir, 'phrase_assessments_raw.jsonl')

    # Source A: IRB seeds
    irb_items = [
        {'phrase': p,
         'context': 'IRB application example. No posting context available.',
         'industry_tier': 'unknown',
         '_seed_source': 'irb_seed'}
        for p in IRB_SEED_PHRASES
    ]

    # Source B: Dictionary seeds
    dict_seeds = get_dictionary_seeds()
    for s in dict_seeds:
        s['_seed_source'] = 'dictionary'
    logger.info(f"Dictionary seeds: {len(dict_seeds)} unique multi-word terms")

    all_items = irb_items + dict_seeds

    # Batch and assess
    batches = []
    for i in range(0, len(all_items), batch_size):
        batch_id = 9000 + i // batch_size  # Offset to avoid collision with Stage 3
        batches.append((batch_id, all_items[i:i+batch_size]))

    logger.info(f"Seed batches: {len(batches)}")

    # Track source for each batch item so we can tag JSONL correctly
    batch_sources = {}
    for batch_id, batch_items in batches:
        batch_sources[batch_id] = [item.get('_seed_source', 'dictionary') for item in batch_items]

    all_assessments = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {}
        for batch_id, batch_items in batches:
            time.sleep(2)
            future = pool.submit(
                assess_batch_codex, batch_id, batch_items,
                instructions, output_dir, logger)
            futures[future] = batch_id

        for future in as_completed(futures):
            batch_id = futures[future]
            try:
                results = future.result()
                all_assessments.extend(results)
                logger.info(f"Seed batch {batch_id}: {len(results)} assessments")
            except Exception as e:
                logger.error(f"Seed batch {batch_id} failed: {e}")

    # Fix source tags in JSONL — assess_batch_codex writes _source='lightcast',
    # but seed assessments need correct source tags
    jsonl_path = os.path.join(output_dir, 'phrase_assessments_raw.jsonl')
    if os.path.exists(jsonl_path):
        lines = []
        with open(jsonl_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    a = json.loads(line)
                    bid = a.get('_batch_id')
                    if bid is not None and bid >= 9000:
                        # Determine source from the phrase
                        phrase_lower = a.get('phrase', '').lower()
                        if any(p.lower() == phrase_lower for p in IRB_SEED_PHRASES):
                            a['_source'] = 'irb_seed'
                        else:
                            a['_source'] = 'dictionary'
                    lines.append(json.dumps(a))
                except json.JSONDecodeError:
                    lines.append(line)
        with open(jsonl_path, 'w') as f:
            f.write('\n'.join(lines) + '\n')

    logger.info(f"Total seed assessments: {len(all_assessments)}")
    return len(all_assessments)


def checkpoint4(output_dir, logger):
    """Validate Stage 4 output."""
    logger.info("--- Checkpoint 4 ---")
    jsonl_path = os.path.join(output_dir, 'phrase_assessments_raw.jsonl')

    assessments = []
    with open(jsonl_path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    assessments.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    # Check IRB seeds present
    assessed_phrases = {a.get('phrase', '').lower() for a in assessments}
    irb_found = sum(1 for p in IRB_SEED_PHRASES if p.lower() in assessed_phrases)
    logger.info(f"CHECK 4.1: {irb_found}/{len(IRB_SEED_PHRASES)} IRB seeds found")

    # Check source tags
    sources = Counter(a.get('_source', 'unknown') for a in assessments)
    logger.info(f"CHECK 4.3 Sources: {dict(sources)}")

    # IRB seed difficulty distribution
    irb_assessed = [a for a in assessments if a.get('_source') == 'irb_seed']
    irb_diff = Counter(a.get('difficulty', 'unknown') for a in irb_assessed)
    logger.info(f"CHECK 4.4 IRB seed difficulties: {dict(irb_diff)}")
    if irb_diff.get('easy', 0) == len(irb_assessed) and len(irb_assessed) > 0:
        logger.warning("CHECK 4.4 WARN: all IRB seeds rated EASY — expected some boundary cases")

    logger.info("Checkpoint 4 PASSED")
    return True


# ---------------------------------------------------------------------------
# Stage 5: Boundary assessment report
# ---------------------------------------------------------------------------

def run_stage5(output_dir, logger):
    """Stage 5: Generate boundary assessment report."""
    logger.info("=== STAGE 5: Boundary assessment report ===")

    jsonl_path = os.path.join(output_dir, 'phrase_assessments_raw.jsonl')
    report_path = os.path.join(output_dir, 'stimuli_assessment_v2.md')

    assessments = []
    with open(jsonl_path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    assessments.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    usable = [a for a in assessments if a.get('usable', False)]
    flagged = [a for a in assessments if not a.get('usable', False)]

    lines = []
    lines.append("# Stimuli Assessment Report v2")
    lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"\nTotal assessed: {len(assessments)}")
    lines.append(f"Usable: {len(usable)}")
    lines.append(f"Flagged/excluded: {len(flagged)}")

    # Section 1: Boundary Coverage
    lines.append("\n## Section 1: Boundary Coverage\n")
    boundary_pairs = ['purpose/good_employer', 'purpose/task', 'good_employer/pecuniary']
    all_pass = True
    for bp in boundary_pairs:
        bp_items = [a for a in usable if a.get('boundary_pair') == bp]
        hard = sum(1 for a in bp_items if a.get('difficulty') == 'hard')
        medium = sum(1 for a in bp_items if a.get('difficulty') == 'medium')
        status = "PASS" if hard >= 5 else "FAIL"
        if status == "FAIL":
            all_pass = False
        lines.append(f"  {bp}: hard={hard} medium={medium} [{status}]")
        if status == "FAIL":
            lines.append(f"    ACTION: {bp} has only {hard} hard cases (need 5)")

    lines.append(f"\nOverall boundary coverage: {'PASS' if all_pass else 'FAIL'}")

    # Section 2: Difficulty Distribution
    lines.append("\n## Section 2: Difficulty Distribution\n")
    categories = ['organizational_purpose', 'good_employer', 'pecuniary', 'job_task', 'unclear']
    for cat in categories:
        cat_items = [a for a in usable if a.get('primary_category') == cat]
        diff = Counter(a.get('difficulty', 'unknown') for a in cat_items)
        flags = []
        if diff.get('hard', 0) == 0 and len(cat_items) > 0:
            flags.append("NO HARD CASES")
        if diff.get('easy', 0) == 0 and len(cat_items) > 0:
            flags.append("NO EASY ANCHORS")
        flag_str = f" !! {', '.join(flags)}" if flags else ""
        lines.append(f"  {cat}: easy={diff.get('easy',0)} medium={diff.get('medium',0)} "
                     f"hard={diff.get('hard',0)} (total={len(cat_items)}){flag_str}")

    # Section 3: Theoretical Coherence Audit
    lines.append("\n## Section 3: Theoretical Coherence Audit\n")
    theory_terms = ['identity', 'sorting', 'employment', 'signaling', 'signal',
                    'task', 'mission', 'values', 'condition', 'compensation']
    hard_items = [a for a in usable if a.get('difficulty') == 'hard']
    flagged_hard = []
    for a in hard_items:
        rationale = (a.get('difficulty_rationale', '') or '').lower()
        if not any(t in rationale for t in theory_terms):
            flagged_hard.append(a)

    lines.append(f"Total HARD-rated phrases: {len(hard_items)}")
    lines.append(f"Flagged for surface-only rationale: {len(flagged_hard)}")
    for a in flagged_hard:
        lines.append(f"  FLAGGED: \"{a.get('phrase')}\" — \"{a.get('difficulty_rationale', '')}\"")

    # Section 4: Context Dependence
    lines.append("\n## Section 4: Context Dependence Review\n")
    high_ctx = [a for a in usable if a.get('context_dependence') == 'high']
    lines.append(f"High context dependence: {len(high_ctx)} phrases")
    for a in high_ctx:
        lines.append(f"  \"{a.get('phrase')}\" — {a.get('context_note', '')}")

    # Section 5: Attention Check Candidates
    lines.append("\n## Section 5: Attention Check Candidates\n")
    for cat in categories:
        easy_in_cat = [a for a in usable
                       if a.get('primary_category') == cat and a.get('difficulty') == 'easy']
        if easy_in_cat:
            pick = easy_in_cat[0]
            lines.append(f"  {cat}: \"{pick.get('phrase')}\"")
        else:
            lines.append(f"  {cat}: NO EASY CANDIDATE AVAILABLE")

    # Section 6: Final Composition
    lines.append("\n## Section 6: Final Composition\n")
    lines.append(f"Total usable phrases: {len(usable)}")
    lines.append(f"Target: 80-100")

    # Category × difficulty breakdown
    lines.append("\nBreakdown by category and difficulty:")
    for cat in categories:
        cat_items = [a for a in usable if a.get('primary_category') == cat]
        diff = Counter(a.get('difficulty', 'unknown') for a in cat_items)
        lines.append(f"  {cat}: {dict(diff)} (total={len(cat_items)})")

    # Source breakdown
    sources = Counter(a.get('_source', 'unknown') for a in usable)
    lines.append(f"\nBreakdown by source: {dict(sources)}")

    # Gap analysis
    if len(usable) < 80:
        lines.append(f"\n!! BELOW TARGET: {len(usable)} usable phrases (need 80)")
        deficit_cats = [(cat, len([a for a in usable if a.get('primary_category') == cat]))
                        for cat in categories]
        deficit_cats.sort(key=lambda x: x[1])
        lines.append("Categories needing supplementation:")
        for cat, count in deficit_cats:
            if count < 10:
                lines.append(f"  {cat}: {count} (needs more)")

    report = '\n'.join(lines)
    with open(report_path, 'w') as f:
        f.write(report)

    logger.info(f"Report written to {report_path}")
    return report_path


def checkpoint5(output_dir, logger):
    """Validate Stage 5 output."""
    logger.info("--- Checkpoint 5 ---")
    report_path = os.path.join(output_dir, 'stimuli_assessment_v2.md')

    if not os.path.exists(report_path):
        logger.error("CHECK 5.1 FAIL: report not found")
        return False

    with open(report_path) as f:
        content = f.read()

    required_sections = [
        'Section 1: Boundary Coverage',
        'Section 2: Difficulty Distribution',
        'Section 3: Theoretical Coherence',
        'Section 4: Context Dependence',
        'Section 5: Attention Check',
        'Section 6: Final Composition',
    ]
    for section in required_sections:
        if section not in content:
            logger.warning(f"CHECK 5.2 WARN: missing section '{section}'")

    # Check boundary pass/fail
    for bp in ['purpose/good_employer', 'purpose/task', 'good_employer/pecuniary']:
        if f'{bp}' in content and 'FAIL' in content.split(bp)[1].split('\n')[0]:
            logger.warning(f"CHECK 5.3: {bp} FAILED boundary coverage gate")

    logger.info("Checkpoint 5 PASSED")
    return True


# ---------------------------------------------------------------------------
# Stage 6: Output files
# ---------------------------------------------------------------------------

def run_stage6(output_dir, logger):
    """Stage 6: Write final output CSVs."""
    logger.info("=== STAGE 6: Output files ===")

    jsonl_path = os.path.join(output_dir, 'phrase_assessments_raw.jsonl')
    candidates_csv = os.path.join(output_dir, 'phrases_candidate.csv')
    flagged_csv = os.path.join(output_dir, 'phrases_flagged.csv')

    assessments = []
    with open(jsonl_path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    assessments.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    # Split usable vs flagged
    usable = [a for a in assessments if a.get('usable', False)]
    flagged = [a for a in assessments if not a.get('usable', False)
               or a.get('context_dependence') == 'high']

    # Write candidates
    if usable:
        cols = ['phrase', 'cleaned_phrase', '_source', 'primary_category',
                'secondary_category', 'boundary_pair', 'difficulty',
                'difficulty_rationale', 'context_dependence', 'context_note',
                '_batch_id']
        df_usable = pd.DataFrame(usable)
        # Ensure all columns exist
        for c in cols:
            if c not in df_usable.columns:
                df_usable[c] = ''
        df_usable = df_usable.rename(columns={'_source': 'source'})
        df_usable.to_csv(candidates_csv, index=False)
        logger.info(f"Wrote {len(df_usable)} candidates to {candidates_csv}")

    # Write flagged
    if flagged:
        df_flagged = pd.DataFrame(flagged)
        df_flagged.to_csv(flagged_csv, index=False)
        logger.info(f"Wrote {len(df_flagged)} flagged to {flagged_csv}")

    return candidates_csv


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Study 1 Stimuli Pipeline v2')
    parser.add_argument('--data-root', default=DEFAULT_DATA_ROOT)
    parser.add_argument('--output-dir', default=DEFAULT_OUTPUT_DIR)
    parser.add_argument('--years', default=','.join(map(str, DEFAULT_YEARS)))
    parser.add_argument('--zips-per-year', type=int, default=DEFAULT_ZIPS_PER_YEAR)
    parser.add_argument('--postings-per-zip', type=int, default=DEFAULT_POSTINGS_PER_ZIP)
    parser.add_argument('--batch-size', type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument('--force-resample', action='store_true')
    parser.add_argument('--force-extract', action='store_true')
    parser.add_argument('--stage', type=int, help='Run only this stage (1-6)')
    parser.add_argument('--skip-codex', action='store_true')
    args = parser.parse_args()

    years = [int(y) for y in args.years.split(',')]
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    logger = setup_logging(output_dir)
    logger.info("=" * 60)
    logger.info("Study 1 Stimuli Pipeline v2")
    logger.info(f"Data root: {args.data_root}")
    logger.info(f"Output dir: {output_dir}")
    logger.info(f"Years: {years}")
    logger.info("=" * 60)

    # Check external drive
    if not os.path.isdir(args.data_root):
        logger.error(f"Data root not found: {args.data_root}")
        logger.error("Is the external drive mounted?")
        sys.exit(1)

    run_all = args.stage is None

    # Stage 1
    if run_all or args.stage == 1:
        parquet_path = os.path.join(output_dir, 'sampled_postings.parquet')
        if os.path.exists(parquet_path) and not args.force_resample:
            logger.info("Stage 1: parquet exists, skipping (use --force-resample to re-run)")
        else:
            run_stage1(args.data_root, output_dir, years,
                       args.zips_per_year, args.postings_per_zip, logger)
        if not checkpoint1(output_dir, years, logger):
            logger.error("Pipeline stopped at Checkpoint 1")
            sys.exit(1)

    # Stage 2
    if run_all or args.stage == 2:
        candidates_path = os.path.join(output_dir, 'keybert_candidates.csv')
        if os.path.exists(candidates_path) and not args.force_extract:
            logger.info("Stage 2: candidates exist, skipping (use --force-extract to re-run)")
        else:
            run_stage2(output_dir, logger)
        if not checkpoint2(output_dir, logger):
            logger.error("Pipeline stopped at Checkpoint 2")
            sys.exit(1)

    if args.skip_codex:
        logger.info("Skipping Stages 3-6 (--skip-codex)")
        return

    # Stage 3
    if run_all or args.stage == 3:
        # Clear previous JSONL if re-running
        jsonl_path = os.path.join(output_dir, 'phrase_assessments_raw.jsonl')
        if args.stage == 3 and os.path.exists(jsonl_path):
            # Don't clear — resume support handles this
            pass
        run_stage3(output_dir, args.batch_size, logger)
        if not checkpoint3(output_dir, logger):
            logger.error("Pipeline stopped at Checkpoint 3")
            sys.exit(1)

    # Stage 4
    if run_all or args.stage == 4:
        run_stage4(output_dir, args.batch_size, logger)
        checkpoint4(output_dir, logger)

    # Stage 5
    if run_all or args.stage == 5:
        run_stage5(output_dir, logger)
        checkpoint5(output_dir, logger)

    # Stage 6
    if run_all or args.stage == 6:
        run_stage6(output_dir, logger)

    logger.info("=" * 60)
    logger.info("Pipeline complete")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
