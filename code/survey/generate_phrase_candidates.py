#!/usr/bin/env python3
"""
Generate candidate phrases for the bucket sort game.

Strategy: Use our 69 already-classified game phrases as seed embeddings,
then find new phrases from the research dictionary that are semantically
closest to each bucket's seeds. This anchors classification to our curated
examples rather than raw dictionary categories.

Steps:
  1. Load current game phrases (the 69 in load_stimuli.py) as seeds
  2. Compute embeddings for each bucket's seed phrases
  3. Extract all 2-6 word terms from the full research dictionary
  4. For each candidate, compute similarity to each bucket's centroid
  5. Assign to highest-similarity bucket, flag boundary cases
  6. Output ranked candidates per bucket for human review

Usage:
    python3 generate_phrase_candidates.py [--threshold 0.4] [--top-n 30]
"""

import os
import sys
import re
import json
from collections import defaultdict

import numpy as np
from sentence_transformers import SentenceTransformer, util

# ---------------------------------------------------------------------------
# Our 69 classified seed phrases, grouped by bucket
# (extracted from load_stimuli.py BUCKET_SORT_PHRASES)
# ---------------------------------------------------------------------------

SEEDS = {
    'purpose': [
        'mission driven', 'make a real difference', 'cutting edge research',
        'sustainable future', 'pioneering advancements', 'raise the bar',
        'breakthrough technologies', 'designing the future', 'shared values',
        'positive impact', 'diversity and inclusion', 'social responsibility',
        'we invest in our people', 'employee-first culture',
        'people are our greatest asset', 'collaborative team culture',
        'empowering our workforce', 'open door policy', 'inclusive workplace',
        'solving global challenges', 'driving progress',
        'building resilient communities', 'technology driven innovation',
        'partner with great minds',
    ],
    'good_employer': [
        'mentorship program', 'flexible work schedule',
        'career development programs', 'promotion opportunities',
        'remote work options', 'work-life balance',
        'advancement opportunities', 'continuous learning',
        'job security', 'ownership of projects',
        'great place to work', 'nurturing talent',
        'employee wellness programs', 'freedom to innovate',
    ],
    'compensation': [
        'competitive salary', '401k match', 'performance bonus',
        'health insurance', 'stock options', 'paid time off',
        'education assistance', 'comprehensive benefits package',
        'parental leave', 'annual merit increase', 'profit sharing',
        'total rewards', 'wellness benefits',
        'professional development budget', 'tuition reimbursement',
        'commission-based earnings',
    ],
    'job_tasks': [
        'manage cross-functional teams', 'analyze customer data',
        'prepare quarterly reports', 'oversee daily operations',
        'coordinate with vendors', 'conduct market research',
        'develop financial models', 'draft client proposals',
        'build dashboards', 'strong analytical skills',
        'project management experience',
        'creative problem solving', 'lead training sessions',
        'mentor junior staff', 'manage compensation plans',
    ],
}

# ---------------------------------------------------------------------------
# Full research dictionary — all terms from refine_dictionaries.py
# Flattened: just the terms, we don't use the dictionary categories for
# classification (we use seed similarity instead)
# ---------------------------------------------------------------------------

# Import dictionaries inline to avoid path issues
# These are copied from refine_dictionaries.py (canonical source)

pecuniary_benefits = {
    "stock options or equity grants": [
        "stock options", "employee stock ownership", "equity grants",
        "company shares", "esop", "share options", "long term incentives",
        "equity packages", "stock purchase plan", "employee stock",
        "restricted stock units", "stock appreciation rights",
        "performance based equity", "employee share purchase plans", "employee owned"
    ],
    "retirement plans": [
        "401k", "retirement", "pension", "savings plans",
        "employer matched retirement", "403b", "rrsp", "superannuation",
        "retirement benefits", "defined benefit plan", "defined contribution plan",
        "annuities", "deferred compensation plans"
    ],
    "insurance benefits": [
        "health insurance", "dental insurance", "vision insurance",
        "life insurance", "disability insurance", "medical plans",
        "mental health coverage", "pet insurance", "dependent care",
        "dependent coverage", "long term disability", "short term disability",
        "vision care plans", "long term care insurance",
    ],
    "tuition reimbursement": [
        "tuition reimbursement", "education assistance", "scholarships",
        "career training sponsorship", "certification reimbursement",
        "student loan assistance", "education support", "tuition aid",
        "tuition assistance", "scholarship programs", "tuition benefit",
        "student loan repayment assistance",
    ],
    "commuter subsidies": [
        "commuter benefits", "transportation stipend", "mileage reimbursement",
        "parking allowance", "subsidized transportation", "travel allowance",
        "public transit reimbursement", "commuter allowance",
    ],
    "paid time off": [
        "paid time off", "vacation days", "sick leave",
        "parental leave", "maternity leave", "bereavement leave",
        "paternity leave", "paid holidays", "flexible time off",
        "holiday pay", "personal leave", "wellness days",
        "mental health days", "vacation time", "sabbaticals",
        "volunteer time off",
    ],
    "additional financial benefits": [
        "bonus", "competitive benefits", "benefits package",
        "employee discount", "profit sharing", "sign on bonus",
        "performance bonus", "relocation assistance",
        "competitive salary", "annual merit increase",
        "comprehensive benefits", "wellness benefits",
        "total rewards", "commission based earnings",
        "employee referral award",
    ],
}

job_design_characteristics = {
    "flexible work arrangements": [
        "remote work", "work from home", "hybrid schedule",
        "flexible hours", "flextime", "compressed workweek",
        "flexible shifts", "distributed team", "remote friendly",
        "flexible workplace", "work anywhere",
        "flexible work schedule", "flexible schedule",
        "telecommuting options", "location independent",
    ],
    "job autonomy": [
        "autonomy", "decision making authority", "independence",
        "self directed", "minimal supervision", "creative freedom",
        "ownership of projects", "empowered decision making",
        "independent work environment", "project ownership",
        "freedom to innovate", "flat hierarchy",
    ],
    "work life balance initiatives": [
        "work life balance", "balanced lifestyle",
        "family time", "healthy worklife",
        "work life harmony", "family friendly policies",
        "employee well being initiatives", "wellness programs",
    ],
    "secure and decent work": [
        "job stability", "stable employment",
        "long term opportunities", "job security",
        "career stability", "ethical work environment",
    ],
}

career_development_opportunities = {
    "skill development programs": [
        "training programs", "skill development",
        "professional development", "upskilling programs",
        "reskilling opportunities", "continuous learning",
        "technical training", "leadership training",
        "career development workshops", "online courses",
    ],
    "mentorship and coaching": [
        "mentorship", "coaching", "career guidance",
        "employee development", "mentor programs",
        "one on one coaching", "peer mentorship",
        "executive coaching", "leadership mentoring",
        "career coaching", "personal growth",
        "learning opportunities",
    ],
    "clear career progression paths": [
        "promotion tracks", "career progression",
        "advancement opportunities", "growth opportunities",
        "career advancement", "career opportunities",
        "career path", "rapid advancement",
        "promotion opportunities", "clear advancement paths",
    ],
    "support for lateral moves": [
        "internal transfers", "cross functional moves",
        "internal mobility", "role flexibility",
        "job rotation programs", "diverse career paths",
    ],
}

organizational_culture = {
    "psychological safety": [
        "open communication", "respectful conflict resolution",
        "constructive feedback", "safe to voice opinions",
        "supportive environment", "encouraging expression",
        "trust in leadership", "warm and friendly culture",
        "inclusive feedback", "psychologically safe",
        "employee well being", "non judgmental",
    ],
    "inclusion of diverse perspectives": [
        "diversity in decision making", "inclusive leadership",
        "representation in leadership", "valuing diverse opinions",
        "inclusive workplace", "cultural inclusivity",
        "multicultural environment", "diverse voices",
        "equitable decision making", "inclusive teams",
        "inclusive work environment", "diverse perspectives",
    ],
    "recognition and celebration": [
        "employee recognition", "celebrating achievements",
        "appreciation programs", "team celebrations",
        "milestone recognition", "recognized and rewarded",
        "reinvest in our employees", "promote from within",
        "peer recognition", "employee appreciation",
    ],
    "collaborative environment": [
        "team collaboration", "supportive teams", "peer support",
        "cross functional collaboration", "helpful colleagues",
        "team oriented environment", "teamwork culture",
        "collaborative atmosphere", "team environment",
        "employee involvement", "employees are key",
        "employees are our greatest asset", "care of our people",
        "collective problem solving", "team building",
        "collaborative work environment", "shared goals",
    ],
    "transparency in leadership": [
        "transparent leadership", "honest decision making",
        "accessible management", "ethical leadership",
        "open door policy", "leadership integrity",
        "honest leadership", "strong leadership",
        "transparent decision making", "accountable leadership",
    ],
    "workplace recognition": [
        "best companies to work", "great place to work",
        "award winning workplace", "recognized employer",
        "employer of choice", "best places to work",
    ],
}

meaningful_work = {
    "alignment with societal values": [
        "mission driven", "socially conscious", "ethical goals",
        "values alignment", "purpose driven", "social impact focus",
        "shared values", "corporate mission", "ethical organization",
        "meaning of work", "purpose at work", "social responsibility",
        "greater good",
    ],
    "opportunities to make an impact": [
        "make a difference", "positively impact lives", "lasting impact",
        "rewarding work", "better future", "community building",
        "create positive change", "impact driven work",
        "challenging and rewarding", "positive impact", "meaningful work",
        "innovative work", "work with purpose", "make real impact",
    ],
    "working on innovation": [
        "breakthrough technologies", "cutting edge research",
        "innovative ideas", "creative problem solving",
        "next gen solutions", "shaping future",
        "pioneering advancements", "disruptive innovation",
        "designing the future", "partner with great minds",
        "raise the bar", "leading innovation",
        "cutting edge technology", "transformative technologies",
        "driving progress", "technology driven innovation",
    ],
    "roles tied to solving global challenges": [
        "addressing global challenges", "sustainable development goals",
        "global impact", "climate change solutions",
        "solving global problems", "building resilient societies",
        "advancing human development", "reduce inequality",
    ],
}

environmental_initiatives = {
    "sustainability practices": [
        "sustainability", "carbon neutrality", "net zero",
        "environmentally friendly", "eco friendly",
        "green practices", "circular economy",
        "sustainable development", "sustainable growth",
        "sustainable solutions", "waste reduction",
    ],
    "renewable energy": [
        "renewable energy", "clean energy", "solar energy",
        "energy efficiency", "green energy",
    ],
}

social_initiatives = {
    "community development": [
        "community outreach", "community engagement",
        "civic engagement", "community partnerships",
        "volunteering programs", "community investment",
    ],
    "diversity equity inclusion": [
        "diversity and inclusion", "equal opportunity",
        "gender equality", "inclusive hiring",
        "diverse workforce", "equity in workplace", "belonging",
    ],
    "philanthropy": [
        "charitable contributions", "corporate giving",
        "humanitarian aid", "giving back",
        "philanthropic initiatives",
    ],
}

job_tasks_requirements = {
    "job_tasks_verbs": [
        "manage cross functional teams", "analyze customer data",
        "prepare quarterly reports", "coordinate with vendors",
        "conduct market research", "develop financial models",
        "draft client proposals", "monitor performance metrics",
        "build dashboards", "lead training sessions",
        "mentor junior staff", "manage compensation plans",
        "design marketing campaigns", "oversee daily operations",
        "implement new systems", "write technical documentation",
        "present to stakeholders", "review compliance documentation",
        "develop business strategies", "maintain client relationships",
    ],
    "job_requirements": [
        "bachelor degree required", "years of experience",
        "strong analytical skills", "excellent communication skills",
        "proficiency in excel", "project management experience",
        "ability to multitask", "team player",
        "detail oriented", "self starter",
        "proven track record", "hands on experience",
    ],
}

ALL_DICTS = {
    'meaningful_work': meaningful_work,
    'organizational_culture': organizational_culture,
    'environmental_initiatives': environmental_initiatives,
    'social_initiatives': social_initiatives,
    'pecuniary_benefits': pecuniary_benefits,
    'job_design_characteristics': job_design_characteristics,
    'career_development_opportunities': career_development_opportunities,
    'job_tasks_requirements': job_tasks_requirements,
}


def normalize(phrase):
    return re.sub(r'[^a-z0-9 ]', '', phrase.lower().strip())


def word_count(phrase):
    return len(phrase.strip().split())


def is_usable(phrase):
    """2-6 words, not jargony abbreviations."""
    wc = word_count(phrase)
    if wc < 2 or wc > 6:
        return False
    skip = ['iso ', '403b', 'rrsp', 'esop', 'esg', 'gri ']
    lower = phrase.lower()
    return not any(s in lower for s in skip)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Generate phrase candidates using seed similarity')
    parser.add_argument('--threshold', type=float, default=0.35,
                        help='Minimum cosine similarity to best bucket (default: 0.35)')
    parser.add_argument('--top-n', type=int, default=30,
                        help='Top N candidates per bucket to show (default: 30)')
    args = parser.parse_args()

    print("Loading SentenceTransformer model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # --- Step 1: Compute bucket centroids from seed phrases ---
    print("Computing seed embeddings...")
    bucket_embeddings = {}
    bucket_centroids = {}
    for bucket, phrases in SEEDS.items():
        embeddings = model.encode(phrases, convert_to_tensor=True)
        bucket_embeddings[bucket] = embeddings
        # Centroid = mean embedding for the bucket
        bucket_centroids[bucket] = embeddings.mean(dim=0)

    # --- Step 2: Collect all dictionary terms as candidates ---
    seed_normalized = set()
    for phrases in SEEDS.values():
        for p in phrases:
            seed_normalized.add(normalize(p))

    candidates = []
    seen = set()
    for dict_name, dictionary in ALL_DICTS.items():
        for subcategory, terms in dictionary.items():
            for term in terms:
                term = term.strip()
                norm = normalize(term)
                if norm in seed_normalized or norm in seen:
                    continue
                if not is_usable(term):
                    continue
                seen.add(norm)
                candidates.append({
                    'phrase': term,
                    'source_dict': dict_name,
                    'source_subcat': subcategory,
                })

    print(f"Found {len(candidates)} candidate phrases (after dedup vs {len(seed_normalized)} seeds)")

    # --- Step 3: Compute similarity of each candidate to each bucket ---
    print("Computing candidate embeddings...")
    candidate_texts = [c['phrase'] for c in candidates]
    candidate_embeddings = model.encode(candidate_texts, convert_to_tensor=True)

    buckets = list(bucket_centroids.keys())
    centroid_matrix = np.stack([bucket_centroids[b].cpu().numpy() for b in buckets])
    candidate_matrix = candidate_embeddings.cpu().numpy()

    # Cosine similarity: each candidate vs each bucket centroid
    from sklearn.metrics.pairwise import cosine_similarity
    sim_matrix = cosine_similarity(candidate_matrix, centroid_matrix)

    # Also compute max similarity to any individual seed in each bucket
    # (catches phrases that are very close to one specific seed)
    for i, c in enumerate(candidates):
        best_bucket_idx = np.argmax(sim_matrix[i])
        best_bucket = buckets[best_bucket_idx]
        best_sim = sim_matrix[i][best_bucket_idx]

        # Second-best bucket for boundary detection
        sorted_sims = np.sort(sim_matrix[i])[::-1]
        second_sim = sorted_sims[1] if len(sorted_sims) > 1 else 0
        second_bucket_idx = np.argsort(sim_matrix[i])[::-1][1]
        second_bucket = buckets[second_bucket_idx]

        c['best_bucket'] = best_bucket
        c['best_sim'] = float(best_sim)
        c['second_bucket'] = second_bucket
        c['second_sim'] = float(second_sim)
        c['sim_gap'] = float(best_sim - second_sim)
        c['all_sims'] = {buckets[j]: float(sim_matrix[i][j]) for j in range(len(buckets))}

        # Flag as boundary if gap < 0.05
        c['is_boundary'] = c['sim_gap'] < 0.05

    # --- Step 4: Output results ---
    # Filter by threshold
    above_threshold = [c for c in candidates if c['best_sim'] >= args.threshold]
    below_threshold = len(candidates) - len(above_threshold)

    print(f"\n{'='*70}")
    print(f"RESULTS: {len(above_threshold)} candidates above threshold {args.threshold}")
    print(f"({below_threshold} candidates below threshold, excluded)")
    print(f"{'='*70}")

    for bucket in buckets:
        bucket_cands = sorted(
            [c for c in above_threshold if c['best_bucket'] == bucket],
            key=lambda c: -c['best_sim']
        )
        print(f"\n\n{'='*70}")
        print(f"  {bucket.upper()} — {len(bucket_cands)} candidates")
        print(f"{'='*70}")

        for c in bucket_cands[:args.top_n]:
            boundary_flag = ' *** BOUNDARY' if c['is_boundary'] else ''
            second_info = f"  (2nd: {c['second_bucket']}={c['second_sim']:.3f}, gap={c['sim_gap']:.3f})"
            print(f"  {c['best_sim']:.3f}  {c['phrase']:<40} [{c['source_dict']}/{c['source_subcat']}]{boundary_flag}{second_info}")

    # Boundary cases across all buckets
    boundary_cands = sorted(
        [c for c in above_threshold if c['is_boundary']],
        key=lambda c: c['sim_gap']
    )
    print(f"\n\n{'='*70}")
    print(f"  BOUNDARY CASES (gap < 0.05) — {len(boundary_cands)} phrases")
    print(f"{'='*70}")
    for c in boundary_cands[:30]:
        print(f"  gap={c['sim_gap']:.3f}  {c['phrase']:<35} {c['best_bucket']}({c['best_sim']:.3f}) vs {c['second_bucket']}({c['second_sim']:.3f})  [{c['source_dict']}]")

    # Save full results
    output_path = os.path.join(os.path.dirname(__file__), 'stimuli', 'phrase_candidates_keybert.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(above_threshold, f, indent=2, default=str)
    print(f"\n\nWrote {len(above_threshold)} candidates to {output_path}")


if __name__ == '__main__':
    main()
