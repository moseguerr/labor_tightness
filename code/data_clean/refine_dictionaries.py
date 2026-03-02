import os
import pandas as pd
import gc
from joblib import Parallel, delayed
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from transformers import pipeline
from sentence_transformers import SentenceTransformer, util
from sklearn.metrics.pairwise import cosine_similarity
import unicodedata
import re
import random
from itertools import chain
from keybert import KeyBERT
from collections import defaultdict
import logging
import torch

# Dictionary definitions
pecuniary_benefits = {
    "stock options or equity grants": [
        "stock options", "employee stock ownership", "equity grants",
        "company shares", "esop", "share options", "long term incentives",
        "equity packages", "stock purchase plan", "employee stock",
        "restricted stock units", "stock appreciation rights",
        "performance based equity", "employee share purchase plans","employee owned"
    ],
    "retirement plans": [
        "401k", "retirement", "pension", "savings plans",
        "employer matched retirement", "403b", "rrsp", "superannuation",
        "retirement benefits", "defined benefit plan", "defined contribution plan",
        "annuities", "deferred compensation plans"
    ],
    "insurance benefits": [
        "health insurance", "dental insurance", "vision insurance","healthcare insurance","annuity insurance",
        "life insurance", "disability insurance", "medical plans","dental services","dental care",
        "mental health coverage", "pet insurance", "dependent insurance","disability protected","plan care",
        "dependent care", "dependent coverage", "family insurance","disability need","longterm disability"
        "spouse insurance", "critical illness insurance", "accident coverage","dental program"
        "long term disability", "short term disability","disability term","disability status","medical dental",
        "vision care plans", "long term care insurance", "travel insurance","mental health care","life disability",
        "emergency childcare reimbursement","vision coverage","supplemental insurance","health vision",
    ],
    "tuition reimbursement or educational assistance": [
        "tuition reimbursement", "education assistance", "scholarships","education benefits",
        "career training sponsorship", "certification reimbursement","school loans",
        "student loan assistance", "education support", "tuition aid",
        "dependent scholarship", "college scholarship", "educational programs",
        "work study support", "dependent tuition","tuition benefit",'student loan repayment assistance',
        'sponsorship opportunities',
        'scholarship programs',
        'tuition assistance',
        'tuition fee','assistance scholarship programs',
        'scholarship program'
    ],
    "commuter subsidies": [
        "commuter benefits", "transportation stipend", "mileage reimbursement",
        "parking allowance", "subsidized transportation", "company shuttle","home transportation",
        "public transit reimbursement", "commuter allowance", "carpool support",'parking reserved',
        'obtain parking',
        'travel allowance',
        "public transportation", "electric vehicle subsidies", "bike to work schemes","mileage calculations expenses"
    ],
    "paid time off": [
        "paid time off", "pto", "vacation days", "sick leave",
        "parental leave", "maternity leave", "bereavement leave",'paternity leave','paid maternity',
        "paid holidays", "flexible time off", "holiday pay", "personal leave",'sick time',
        "wellness days", "mental health days", "vacation time", "sabbaticals",
        "floating holidays", "personal days", "volunteer time off", "vacation",'paid time holidays',
        'leave paid time',
        'maternity paternity leave',
        "maternal leave", "paternal leave"
    ],
    "additional benefits": [
        "bonus", "child support", "childcare", "competitive benefits","child care",
        "employee assistance program", "employee discount", 'benefits including comprehensive',
        'excellent benefits including','benefits offered',
        'benefits paid','exceptional benefits','exemplary compensation benefits package',
        'competitive compensation benefits','relocation package available',
        'care flex spending account', 'adoption fertility assistance',
        'care spending account', 'day care','coverage adoption fertility',
        "flexible schedule", "full benefits", "guaranteed hours", 'employee referral award',
        "wellness", "union", 'offer great benefits','adoption benefit','family assistance program',
        "adoption assistance", "fertility benefits", "surrogacy assistance",
        "gym memberships", "wellness stipends", "legal assistance plans",
        "home office stipends", "relocation assistance",'competitive compensation benefits',
        "dependent care","flexible spending accounts","comprehensive benefits","outstanding benefits",
        "relocation provided","company discounts","wellness benefits",
    ],
    "profit sharing": [
        "profit sharing", "company wide profit sharing programs","share value","value sharing",'profit ownership'
    ]
}


job_design_characteristics = {
    "flexible work arrangements": [
        "remote work", "work from home", "hybrid schedule",
        "flexible hours", "flextime", "compressed workweek",
        "part time options", "job sharing", "flexible shifts","work remotely",
        "adjustable hours", "distributed team", "remote friendly",
        "flexible workplace", "work anywhere", "virtual work environment",
        "remote friendly culture", "location independent","working remote",
        "telecommuting options", "global teams", "asynchronous work","flexible work schedule",
        "work anywhere policy","remote management","flexible schedule"
    ],
    "job autonomy": [
        "autonomy", "decision making authority", "independence",
        "self directed", "minimal supervision", "creative freedom",
        "control over work", "self managed", "initiative driven",
        "ownership of projects", "empowered decision making",
        "self starter", "independent decision making", 
        "flat hierarchy", "flat organization", "non hierarchical structure",
        "decentralized decision making", "empowered teams",
        "independent work environment", "project ownership",
        "freedom to innovate", "minimal oversight",
        "decision making flexibility","work independently",
        "flat structure", "collaborative decision making","decentralized management",
    ],
    "work life balance initiatives": [
        "work life balance", "worklife balance", "worklife program", 
        "workfamily", "healthy worklife", "sustainable worklife", 
        "balanced life", "balanced lifestyle", "family time", 
        "healthier and happier", "time for family", 'balance work personal lives',
        "balance work and leisure", "healthy lifestyle", 'balance personal',
        "work life harmony", "work life integration", 'worklife quality',
        "family friendly policies", "flexible leave policies",'healthy environment',
        "wellness programs", "mindfulness support", 'familyfriendly hours',
        'family healthy','career support worklife',
        'programs help employees healthy','celebrate family',
        "reduced work hours", "part time schedules", 'healthy habits',
        "employee well being initiatives", "family leave policies","comprehensive leave program"
        "mental health days","family medical leave"
    ],
    "secure and decent work": [
        "secure work", "decent work", "stable employment",
        "ethical work environment", 'safe healthy environment',
        'safe working environment','safety practices',
        'supportive corporate environment',
        "long term opportunities", "job stability",'safe inclusive environment',
        "livable wages", "accident safety investigations",'safe healthful working',
        "iso standards", "iso 27001","fair ethical manner","stable company","ensure safe work",
        "stable workforce",'safety practices','performing tasks safely','work safety', 'safe work environment',
        'career opportunities stability','safe healthful working',
        'secure job',
        'safe work practices',
        'safe productive work',
        'adequate work',
        'career stability',
        'safety regulations',
        'safety policies',
        'safety concerns',
        'safety rules',
        'safety precautions',
        'safety hazards',
        'job security',
        'stable supportive corporate',
    ]
}




career_development_opportunities = {
    "skill development programs": [
        "training programs", "skill development","paid continuing education",
        "conference participation", "career growth workshops",
        "online courses", "professional development", "upskilling programs",
        "reskilling opportunities", "sponsor industry certifications", 
        "continuous learning", "worker development", "training initiatives"
        "jumpstart your career", "looking to grow","employee training",
        "technical training", "skills training", "learning programs","educational opportunities",
        "specialized training", "leadership training", "career training","continuing education reimbursement",
        "career development workshops", "skills enhancement","great training","management training",
        
    ],
    "mentorship and coaching": [
        "mentorship", "coaching", "career guidance", "employee development",
        "mentor programs", "one on one coaching", "peer mentorship",
        "executive coaching", "leadership mentoring",'candid meaningful feedback',
        "career coaching", "mentoring programs", "guidance programs","consistent feedback",
        "development coaching", "personalized coaching","feedback constantly","performance feedback",
        "personal growth","learning opportunities"
    ],
    "clear career progression paths": [
        "promotion tracks", "career progression", "advancement opportunities", 
        "opportunities for advancement", "opportunities for growth", "accelerate career",
        "growth opportunities", "career advancement", "career opportunities", 
        "career mobility", "career development", "dynamic careers", "promotion cycle",
        "careerdriven individuals", "rapid advancement", "career path","pursue desired career",
        "promotion opportunities", "climbing the ladder", "advance career","personal advancement",
        "growth tracks", "future leadership roles", "development opportunities"
        "clear advancement paths", "progression plans","grow career","promotion potential"
    ],
    "support for lateral moves": [
        "skill diversification", "internal transfers", "cross functional moves",
        "lateral moves", "cross training opportunities", "internal mobility",
        "role flexibility", "career transitions within company", 
        "careeradvancing", "career growth", "professional growth",
        "role switching", "internal job opportunities", 
        "cross departmental opportunities", "team transitions", 
        "job rotation programs", "diverse career paths"
    ]
}



organizational_culture = {
    "psychological safety": [
        "open communication", "respectful conflict resolution", 
        "constructive feedback", "safe to voice opinions", 
        "no fear of retaliation", "supportive environment", 
        "encouraging expression", "trust in leadership", 
        "employees voice", "workers voice", "employee ideas", 
        "warm and friendly culture", "trust", "protected",
        "inclusive feedback", "safe environment", "psychologically safe",
        "employee well being", "non judgmental"
    ],
    "inclusion of diverse perspectives": [
        "diversity in decision making", "inclusive leadership",
        "representation in leadership", "valuing diverse opinions",
        "inclusive workplace", "cultural inclusivity", "multicultural environment",
        "diverse voices", "equitable decision making", "inclusive teams","inclusive work environment",
        "diverse perspectives", "multicultural workforce", "cross cultural inclusion"
    ],
    "recognition and celebration": [
        "employee recognition", "celebrating achievements", 
        "shout outs", "employee awards", "appreciation programs",'incentive awards',
        'demonstrated achievements',
        'staff appreciation','celebrates success',
        "team celebrations", "milestone recognition", "achievement rewards", 
        "recognized and rewarded", "reinvest in our employees", 
        "promote from within", "promoting from within","recognized rewarded",
        "peer recognition", "employee appreciation", 
        "team recognition", "achievement celebrations", "employee value"
    ],
    "collaborative environment": [
        "team collaboration", "supportive teams", "peer support",
        "cross functional collaboration", "helpful colleagues",
        "team oriented environment", "teamwork culture", "collaborative atmosphere", 
        "team environment", "teamwork", "employee involvement", 
        "employee relations", "worker representation", "teamoriented environment",
        "working men and women", "employees are key", 
        "employees are our greatest asset", "care of our people",
        "collective problem solving", "team building", "collaborative work environment",
        "collaborative teams", "shared goals", "cooperative workplace"
    ],
    "transparency in leadership": [
        "transparent leadership", "clear communication from leaders",
        "honest decision making", "accessible management","ethical leadership",
        "open door policy", "leader transparency", "managerial openness",
        "transparency", "leadership integrity", "honest leadership",   'positive leadership',
        'organizational accountability',
        'environment openness',
        'held accountable','strong leadership',
        'leadership communication',
        'management clear communication',
        'leadership oversight',
        "transparent decision making", "accountable leadership", "openness in management"
    ],
    "workplace recognition": [
        "best companies to work", "great place to work", 'award winning staff','best large employers',
        "employee friendly workplace", "award winning workplace", "best places work",
        "recognized employer", "employer of choice", "best places to work",'perfect place work',
        'wonderful place work','ranked best companies','awardwinning company',
        'excellent place work','worlds admired companies','leading companies world',
        'large companies world'
    ]
}


meaningful_work = {
    "alignment with societal values": [
        "mission driven", "socially conscious", "ethical goals", 'company mission',
        "values alignment", "purpose driven", "social impact focus", 
        "shared values", "corporate mission", "ethical organization",'company values',
        "mission focused roles", "align with the purpose", "share values",
        "meaning of work", "pursuing career with purpose", "mutually rewarding",
        "purpose at work", "life changing", "heart pumping","rewarding career",
        "making an impact", "social responsibility", "greater good", "double bottom line"
    ],
    "opportunities to make an impact": [
        "make a difference", "positively impact lives", "lasting impact","rewarding work",'better future',
        "direct impact roles", "community building", "create positive change", "taking toughest challenges",
        "help others", "improve quality of life", "impact driven work", "help people",'fulfilling mission',
        "challenge yourself", "challenging and rewarding","strengthening communities" 'fulfilling careers',
        "engaging work", "interesting and challenging", "positive impact","helping people",'meaningful work',
        "interesting work", "innovative work", "transformative journeys", "build stronger communities",
        "gratifying", "best work of their lives", "work with purpose","make real impact","improving quality life",
        "improving communities", "leaving a legacy","career rewarding","improvement human life"
    ],
    "working on innovation": [
        "breakthrough technologies", "cutting edge research","innovative ideas", "changing future",
        "creative problem solving", "next gen solutions", "worldwide influence",'shaping future','innovative companies',
        "innovative roles", "technology driven innovation", "leading product service innovation",
        "pioneering advancements", "disruptive innovation", "world leading companies",'develop breakthrough',
        "designing the future", "worlds most innovative company", 'help build future','help build future',
        "history makers", "partner with great minds", "raise the bar","leading research", 'future constantly changing',
        "creative environment", "free thinkers", "leading innovation",'cutting edge technology',
        "transformative technologies", "driving progress","vibrant work environment",'creating better future'
    ],
    "roles tied to solving global challenges": [
        "solving poverty", "climate change solutions", 
        "addressing global challenges", "sustainable development goals", 
        "humanitarian roles", "reduce inequality", "global impact", 'worlds complex challenges',
        'solutions global','worlds challenging issues',"inequality reduction",
        'solve realworld problems',"reducing inequality",
        "environmental challenges", "public health issues", 
        "eradicating hunger", "bright future", "eliminate poverty",
        "a great environment", "environment that inspires",
        "solving global problems", "building resilient societies",
        "advancing human development"
    ]
}


environmental_initiatives = {
    "sustainability practices": [
        "sustainability", "carbon neutrality", "net zero", "recycling programs",
        "zero waste", "environmentally friendly", "eco friendly", 
        "green practices", "circular economy", "waste reduction", 
        "sustainable development", "sustainable growth", 
        "sustainable industries", "sustainable packaging", 
        "sustainable practices", "sustainable outcomes", 
        "sustainable urbanization", "double bottom line", 'responsible packaging material',
        'waste policy',
        'sustainable approach',
        'sustainable ways',
        'sustainable solutions',
        'resources management',
        "responsible consumption", "responsible farming", 
        "responsible use", "lifestyle of health and sustainability",
        "resource conservation", "reducing waste"
    ],
    "renewable energy use": [
        "renewable energy", "solar energy", "wind energy", "green energy",
        "clean energy", "solar power", "wind power", "hydro power", 
        "hydrogen power", "alternative energy", "energy efficient", 
        "energy efficiencies", "energy efficiency", "energy star", 
        "fuel efficiency", "hybrid energy", "hybrid vehicle", "hybrid car", 
        "nuclear", "clean energies", "low carbon energy"
    ],
    "conservation programs": [
        "wildlife protection", "water conservation", "biodiversity programs", 
        "land conservation", "habitat restoration", "forest preservation",
        "water use reduction", "natural resource conservation", 'emission reduction',
        "ecosystem protection", "ocean resources", "overfishing", 
        "fish stock", "amazon rain forest", "bio diversities", "biodiversity", 
        "natural resources", "historic sites", "preservation",
        "protecting habitats", "marine conservation"
    ],
    "climate action": [
        "climate change", "climate crisis", "global warming", 
        "paris agreement", "carbon dioxide", "carbon disclosure", 
        "carbon emission", "carbon neutral", "co2", 'emissions related',
        "greenhouse gas", "environmental impact", 'environmental problems',
        "environmental performance", "environmental footprint", 
        "climate neutral", "impact on the environment",
        "climate solutions", "low emissions"
    ],
    "environmental management and practices": [
        "environmental action", "environmental activism", "environmental safety",
        "environmental activities", "environmental disclosure", 
        "environmental management systems", "environmental policies", 
        "environmental policy", "environmental practices", 
        "environmental protection", "environmental reform", 
        "environmental responsibilities", "environmental responsibility", 
        "environmental stewardship", "environmentally inclined", 
        "environmentalist", "material footprint", "material stewardship", 
        "groundwater", "hazardous waste", "toxic chemicals reduction", 
        "waste recycling", "fuel technology", "oxidation", 
        "environmentally safe", "environmentally neutral", 
        "environmental supply chain", "pollution", "pollutant", 
        "polluting", "ozone depletion", "ozone depleting", 
        "gri frameworks", "esg", "gri ratings", "gri standards",
        "clean supply chains", "responsible resource use",'waste disposal',
        'recycling centers',
        'waste spill',
        'recycling nonhazardous solid waste',
        'industry leader recycling',
        'recycling simplified'
    ]
}

social_initiatives = {
    "diversity, equity, and inclusion programs": [
        "aboriginal peoples", "aboriginals", "affirmative action", 
        "african american", "social class", "disabilities", "diversity inclusion",
        "disability status", "disabled", "discriminating", "fair wages",
        "discrimination", "discriminatory", "diversity", "workforce diversity",
        "equal employment", "equal opportunities", "equal opportunity", 
        "equality", "ethnic diversities", "ethnic diversity", 
        "ethnic mosaic", "ethnically", "ethnicities", "ethnicity", 
        "female", "first nations", "first peoples", "gay", "creating inclusive",
        "gender", "hiv", "inclusive", "indigenous", "lesbian", 
        "marital status", "minorities", "minority", "national origin", 
        "native", "pregnancy", "race", "racial", "qualified candidates criminal",
        "religious diversities", "religious diversity", 
        "same sex", "sexual orientation", "underrepresented group", 
        "veteran", "women", "gender inclusion", "diverse leadership",
        "not obligated to disclose", "sealed or expunged", 
        "will not be obligated to disclose", 
        "convictions will be reviewed on a", 
        "convictions will not necessarily bar", 
        "criminal record is not an automatic", 
        "criminal record will be considered",
        "fair hiring practices", 'diverse team',
        'equal pay',
        'pay equal work',
        'diverse backgrounds',
        'diverse group', 'fair equitable compensation',
        'conviction records',
        'diverse workplace',
        'diverse workforce',
        'diverse environment',
        'culturally diverse',
        'diverse friendly',
        'diverse community',
        'equal consideration employment'
    ],
    "community engagement": [
        "community engagement", "volunteering", "local partnerships", "community involvement",
        "employee volunteer programs", "neighborhood support", 'volunteer hours','shared responsibility',
        "grassroots initiatives", "community development", "social impact",
        "corporate volunteerism", "civic engagement", "community project", "community involvement",
        "supporting local communities", "socially engaged", "impact communities",'community work',
        'local neighborhood',
        'engagement opportunities','community efforts',
    ],
    "philanthropy": [
        "charitable giving", "corporate social responsibility", 
        "scholarships", "nonprofit support", "foundation grants",
        "humanitarian aid", "cause based giving", "charity donations",
        "philanthropic initiatives", "donations", "giving back",
        "community philanthropy", "donor support",'responsible corporate','community giving'
    ],
    "ethical supply chains": [
        "ethical sourcing", "fair trade", "responsible sourcing", 
        "supply chain transparency", "labor rights", "sustainable sourcing", 
        "supplier diversity", "worker protections", "fair labor standards",
        "environmental supply chain", "responsible farming", 
        "worker equity", "transparent supply chains"
    ]
}


job_tasks_requirements = {
    "job_tasks": [
        "manage", "lead", "design", "develop", "coordinate", "plan", "analyze",
        "implement", "research", "organize", "support", "communicate", "monitor",
        "evaluate", "train", "facilitate", "present", "report", "maintain",
        "oversee", "test", "consult", "build", "solve", "write", "debug",
        "deploy", "execute", "strategize", "coaching", "mentoring", "supervising",
        "duties include", "responsibilities include", "tasked with", "essential responsibilities"
    ],
    "job_requirements": [
        "required", "must", "ability to", "mandatory", "minimum qualifications",
        "experience in", "desired", "preferred", "essential", "proficiency in",
        "certification", "background in", "knowledge of", "expertise in",
        "competency in", "fluency in", "responsibilities include", "ability to manage",
        "strong understanding of", "track record of", "commitment to", "ability to lead"
    ],
    "qualifications": [
        "bachelor", "master", "phd", "degree", "diploma", "certificate",
        "qualification", "accreditation", "certification", "training",
        "education", "license", "credential", "undergraduate", "postgraduate",
        "graduate", "associate", "specialization", "minor", "major"
    ],
    "experience": [
        "years of experience", "proven track record", "demonstrated experience", "experience demonstrated"
        "prior experience", "work history", "hands-on experience", "relevant experience",
        "extensive experience", "minimum of", "at least", "industry experience",
        "professional experience", "field experience", "internship", "apprenticeship",
        "coaching experience", "mentoring experience", "leadership experience",
        "experience in project management", "experience working in"
    ],
    "skills": [
        "technical skills", "soft skills", "communication skills", "leadership skills",
        "problem-solving", "analytical skills", "teamwork", "collaboration",
        "critical thinking", "time management", "organization", "project management",
        "coding", "programming", "data analysis", "marketing", "sales", "graphic design",
        "presentation skills", "negotiation skills", "customer service", "writing skills",
        "adaptability", "creativity", "decision making", "attention to detail",
        "training skills", "mentoring skills", "facilitation skills","required skills",
        "demonstrates skills assigned"
    ]
}


# Dictionaries
dictionaries = {
    "pecuniary_benefits": pecuniary_benefits,
    "job_design_characteristics": job_design_characteristics,
    "career_development_opportunities": career_development_opportunities,
    "organizational_culture": organizational_culture,
    "meaningful_work": meaningful_work,
    "environmental_initiatives": environmental_initiatives,
    "social_initiatives":social_initiatives,
    "job_tasks_requirements": job_tasks_requirements
}



# Text cleaning function
def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8', 'ignore')
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', text)
    text = re.sub(r'[^a-zA-Z0-9\s.,!?]', '', text)
    return re.sub(r'\s+', ' ', text.lower()).strip()

# Load models globally
keybert_model = KeyBERT("all-MiniLM-L6-v2")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
summarizer = None  # Set to None initially

def initialize_models():
    """
    Initialize the summarizer model if not already initialized.
    This ensures that the summarizer is loaded properly for each process.
    """
    global summarizer
    if summarizer is None:
        summarizer = pipeline("summarization", model="facebook/bart-large-cnn", tokenizer="facebook/bart-large-cnn")


def refine_dictionaries_with_texts(texts, dictionaries, threshold, ngram_range):
    """
    Refine dictionaries to capture nuanced terms for job postings.
    Ensures:
    1. Retention of distinct terms (e.g., "remote work" and "flexible work arrangements").
    2. Avoidance of terms that lead to double counting (e.g., "remote work" and "remote work arrangement").
    3. Category-aware refinement to prevent redundancy.
    """
    initialize_models()

    # Precompute embeddings for all dictionary terms
    precomputed_embeddings = {}
    existing_terms_set = set()  # Track terms already in the dictionaries
    for dict_name, categories in dictionaries.items():
        precomputed_embeddings[dict_name] = {}
        for category, terms in categories.items():
            terms = [str(term) for term in terms if isinstance(term, str)]
            precomputed_embeddings[dict_name][category] = embedding_model.encode(
                terms, convert_to_tensor=True
            )
            existing_terms_set.update(terms)

    # Extract and clean n-grams
    vectorizer = CountVectorizer(stop_words="english", ngram_range=ngram_range)
    text_features = vectorizer.fit_transform(texts)
    extracted_terms = [term for term in vectorizer.get_feature_names_out() if term.strip()]

    # Compute embeddings for extracted terms
    try:
        extracted_embeddings = embedding_model.encode(extracted_terms, convert_to_tensor=True)
        if extracted_embeddings is None:
            raise ValueError("Extracted embeddings are invalid.")
    except Exception as e:
        raise ValueError(f"Error computing embeddings: {e}")

    # Match terms with dictionary categories
    term_to_best_category = {}
    for dict_name, categories in precomputed_embeddings.items():
        for category, category_embedding in categories.items():
            try:
                similarity_scores = util.pytorch_cos_sim(extracted_embeddings, category_embedding)
                max_similarity, _ = similarity_scores.max(dim=1)
            except Exception as e:
                raise ValueError(f"Error computing similarity for {category}: {e}")

            for idx, similarity in enumerate(max_similarity):
                term = extracted_terms[idx]
                try:
                    similarity = similarity.item()
                    if isinstance(similarity, (int, float)) and similarity >= threshold:
                        if term not in term_to_best_category or term_to_best_category[term][2] < similarity:
                            term_to_best_category[term] = (dict_name, category, similarity)
                except Exception as e:
                    print(f"Error processing similarity for term '{term}': {e}")
                    continue

    # Remove redundancy (prioritize by threshold and length)
    def is_redundant(term, term_list):
        """Check if term is a subset or superset of any term in the term_list."""
        return any(
            term in other_term or other_term in term
            for other_term in term_list
        )

    # Sort terms by threshold first, then length
    term_data = sorted(
        term_to_best_category.items(),
        key=lambda x: (-x[1][2], -len(x[0]))  # Sort by similarity (desc) and length (desc)
    )

    refined_terms = {dict_name: {category: [] for category in categories} for dict_name, categories in dictionaries.items()}
    unique_terms = set()  # Track unique terms added across categories
    for term, (best_dict, best_category, similarity) in term_data:
        if term not in existing_terms_set:  # Skip terms already in the dictionary
            # Avoid subsets/supersets in the same category
            existing_category_terms = refined_terms[best_dict][best_category]
            if not is_redundant(term, existing_category_terms):
                refined_terms[best_dict][best_category].append(term)
                unique_terms.add(term)

    # Final filtering step for dictionary consistency
    for dict_name, categories in refined_terms.items():
        for category, terms in categories.items():
            terms = sorted(terms, key=lambda x: (-len(x), x))  # Sort for consistency
            # Filter against existing terms in the category
            filtered_terms = [
                term for term in terms
                if not is_redundant(term, dictionaries[dict_name][category])
            ]
            refined_terms[dict_name][category] = filtered_terms

    return refined_terms

# Parallel processing for DataFrame
def parallelize_refine_dictionaries_combined_to_dataframe(df, dictionaries, n_jobs, chunk_size, threshold, ngram_range):
    """
    Parallel processing for refining dictionaries using a combined text approach,
    returning results as a DataFrame.
    
    Parameters:
        df (DataFrame): DataFrame containing the column "CleanedText" with job postings or documents.
        dictionaries (dict): Existing dictionaries to refine.
        n_jobs (int): Number of parallel jobs to run.
        chunk_size (int): Size of chunks for parallel processing.
        threshold (float): Similarity threshold for term matching.
        ngram_range (tuple): Range of n-grams to consider for extraction.

    Returns:
        DataFrame: A DataFrame with columns 'dictionary', 'category', 'proposed_term'.
    """
    try:
        # Combine all text into a single large text
        combined_text = " ".join(df["CleanedText"].dropna().tolist())

        # Split the combined text into chunks
        words = combined_text.split()
        total_words = len(words)
        chunks = [
            " ".join(words[i:i + chunk_size])
            for i in range(0, total_words, chunk_size)
        ]

        # Define a helper function to process each chunk
        def process_chunk(chunk):
            return refine_dictionaries_with_texts(
                texts=[chunk],  # Provide chunk as a single-element list
                dictionaries=dictionaries,
                threshold=threshold,
                ngram_range=ngram_range
            )

        # Perform parallel processing
        results = Parallel(n_jobs=n_jobs, backend='loky', timeout=3600)(
            delayed(process_chunk)(chunk) for chunk in chunks
        )

        # Convert results to a list of rows for the DataFrame
        proposed_terms_list = []
        for result in results:
            for dict_name, categories in result.items():
                for category, terms in categories.items():
                    for term in terms:
                        proposed_terms_list.append({
                            "dictionary": dict_name,
                            "category": category,
                            "proposed_term": term
                        })

        # Create and return the DataFrame
        return pd.DataFrame(proposed_terms_list)

    except Exception as e:
        print(f"Error during parallel execution: {e}")
        return pd.DataFrame(columns=["dictionary", "category", "proposed_term"])


# Path settings
data_directory = "/global/home/pc_moseguera/output/processed/"
output_file = "/global/home/pc_moseguera/output/auxiliary/dictionaries/refined_terms_single_file.parquet"

# Years to process
years = [str(year) for year in range(2010, 2023)]

# Sample size per year
sample_size_per_year = 300

# Initialize an empty DataFrame to store concatenated samples
all_samples = pd.DataFrame()


# Process each year
for selected_year in years:
    year_folder = os.path.join(data_directory, selected_year)

    if os.path.exists(year_folder):
        parquet_files = [f for f in os.listdir(year_folder) if f.endswith('.parquet')]
        if parquet_files:
            selected_file = random.choice(parquet_files)
            sample_file = os.path.join(year_folder, selected_file)
            print(f"Processing file: {sample_file}")
            
            # Read the parquet file
            df = pd.read_parquet(sample_file)
            
            # Check if the required column is present and valid
            if 'JobText' not in df.columns or df['JobText'].isnull().all():
                print(f"File {sample_file} does not have a valid `JobText` column. Skipping...")
                continue
            
            # Filter the dataset
            df = df[(df['CanonEmployer'].notna()) & (df['CanonEmployer'] != None) & (df['CanonEmployer'] != "None")]

            # Sample the required number of rows
            if len(df) > sample_size_per_year:
                df_aux = df.sample(n=sample_size_per_year)
            else:
                print(f"Dataset for year {selected_year} has less than {sample_size_per_year} rows. Using the entire dataset.")
                df_aux = df.copy()
            
            # Clean the JobText column
            df_aux["CleanedText"] = df_aux["JobText"].apply(clean_text)
            
            # Concatenate the samples
            df_sample = pd.concat([all_samples, df_aux], ignore_index=True)
            
            # Explicitly delete the intermediate DataFrame and trigger garbage collection
            del df_aux
            del df
            gc.collect()
        else:
            print(f"No parquet files found in {year_folder}.")
    else:
        print(f"Year folder {year_folder} does not exist.")

# Output the concatenated DataFrame
print(f"Concatenated sample has {len(all_samples)} rows.")


refined_df = parallelize_refine_dictionaries_combined_to_dataframe(
    df_sample,  # DataFrame with a "CleanedText" column
    dictionaries,  # Existing dictionaries
    n_jobs=2,  # Number of parallel jobs
    chunk_size=1000,  # Approximate number of words per chunk
    threshold=0.7,  # Similarity threshold
    ngram_range=(2, 4)  # N-gram range
)

refined_df = refined_df[refined_df['dictionary'] != 'job_tasks_requirements']

    # Save results
refined_df.to_parquet(output_file, index=False)
print(f"Saved proposed terms to `{output_file}`.")
