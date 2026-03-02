#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jul 24 15:19:47 2022

@author: mgor
"""

### Import packages
import pandas as pd
import os
import re
from multiprocessing import Pool
import unicodedata
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import PCA
import numpy as np
import datetime
import gc
import glob
import json


# Dictionary definitions
pecuniary_benefits = {
    "stock options or equity grants": [
        "stock options", "employee stock ownership", "equity grants",'stock purchase program',
        "company shares", "esop", "share options", "long term incentives",
        "equity packages", "stock purchase plan", "employee stock",
        "restricted stock units", "stock appreciation rights",
        "performance based equity", "employee share purchase plans","employee owned","equity bonus",
        "equity awards","stock purchase plan",
        "stock incentive plan","equity-based profit sharing",
        "restricted equity",
        "employee stock plan",
        "ownership incentives",
        "equity distribution",
        "deferred stock units",
        "stock retention bonuses",
        "restricted share units (RSUs)",
        "employee equity participation",
        "employee profit sharing via equity",
        "equity growth opportunities",
        "capital accumulation plan",
        "equity matching program",
        "stock option buyback",
        "vesting schedule benefits",
        "equity vesting program"
    ],
    "retirement plans": [
        "401k", "retirement", "pension", "savings plans",
        "403b", "rrsp", "superannuation",
        "defined benefit plan", "defined contribution plan",
        "annuities", "deferred compensation plans",'savings account','savings programs',
        'savings stock investment plans'
    ],
    "insurance benefits": [
        "health insurance", "dental insurance", "vision insurance","healthcare insurance","annuity insurance",
        "life insurance", "disability insurance", "medical plans","dental services","dental care","catastrophic health insurance",
        "umbrella insurance coverage",
        "international health insurance",
        "telemedicine insurance plans",
        "portable health insurance",
        "cancer insurance coverage",
        "hospital indemnity insurance",
        "accident indemnity plans",
        "critical care insurance","preventive care coverage",
        "dependent life insurance","highdeductible health plan",
        "premium reimbursement plans", "health reimbursement arrangements",
        "health savings account-compatible insurance",
        "long-term care riders",
        "hospital cash plans",
        "mental health coverage", "pet insurance", "dependent insurance","disability protected","plan care",
        "dependent care", "dependent coverage", "family insurance","disability need","longterm disability"
        "spouse insurance", "critical illness insurance", "accident coverage","dental program",'physical disability', 
        "long term disability", "short term disability","disability term","disability status","medical dental",
        "vision care plans", "long term care insurance", "travel insurance","mental health care","life disability",
        "emergency childcare reimbursement","vision coverage","supplemental insurance","health vision",'mental disability'
    ],
    "tuition reimbursement or educational assistance": [
        "tuition reimbursement", "education assistance", "scholarships","education benefits",
        "career training sponsorship", "certification reimbursement","school loans",
        "student loan assistance", "education support", "tuition aid",'tuition discounts reimbursement',
        "dependent scholarship", "college scholarship", "educational programs",'tuition coverage',
        "work study support", "tuition assistance","tuition benefit",'student loan repayment assistance',
        'sponsorship opportunities','reimbursements for licenses and certifications',
        'scholarship programs', 'semester reimbursement program',
        'tuition assistance', "educational loan forgiveness",
        'tuition fee',
        'scholarship program'
    ],
    "commuter subsidies": [
        "commuter benefits", "transportation stipend", "mileage reimbursement",
        "parking allowance", "subsidized transportation", "company shuttle","home transportation",
        "public transit reimbursement", "commuter allowance", "carpool support",'parking reserved',
        'obtain parking',"travel reimbursement",
        'travel allowance','travel expense',
        'possible transportation',
        'transportation shuttle',
        'parking employee','parking provided',
        'reimbursements travel',
        'parking access',
        "public transportation", "electric vehicle subsidies", "bike to work schemes","mileage calculations expenses",
        "transit pass reimbursement","ride-share credits","fuel cost reimbursement","vanpool subsidies",
        "eco-commuter incentives","hybrid vehicle incentives","commuter tax benefits",
        "transportation pre-tax deductions","carpool parking discounts",
        "monthly transit cards",
        "workplace transportation program",
        "flexible commuter benefits",
        "regional rail pass coverage","green commuting incentives","urban transportation assistance",
        "train ticket reimbursement"
    ],
    "paid time off": [
        "paid time off", "unpaid time off","paid timeoff","unpaid timeoff","pto", "vacation days", "sick leave",
        "parental leave", "maternity leave", "bereavement leave",'paternity leave','paid maternity',
        "paid holidays", "flexible time off", "holiday pay", "personal leave",'sick time',
        "wellness days", "mental health days", "vacation time", "sabbaticals",
        "floating holidays", "personal days", "volunteer time off", "vacation",'paid time holidays',
        'leave paid time','holiday bonus',
        'maternity paternity leave','parental bonding leave',
        'generous holiday',"extended leave benefits",
        'protected pregnancy maternity',"adoption leave",
        "maternal leave", "paternal leave","paid family leave",
        "paid caregiving time","sabbatical program",
        "leave of absence with pay",
    ],
    "additional benefits": [
        "bonus", "child support", "childcare", "competitive benefits","child care",
        "employee assistance program", "employee discount", 'benefits including comprehensive',
        'excellent benefits including','benefits offered','money discounts'
        'personal time','bereavement paid',
        'paid bereavement',"housing stipend","meal allowances","concierge services",
        "on-site childcare","lunch plan","meal assistance",
        "financial planning services",
        "professional membership reimbursement",
        'benefits paid','exceptional benefits','exemplary compensation benefits package',
        'competitive compensation benefits','relocation package available',
        'care flex spending account', 'adoption fertility assistance',
        'care spending account', 'day care','coverage adoption fertility',"retail partnerships discounts",
        "free or subsidized meals",'daycare',
        "seasonal bonus","visa sponsorship",
        "flexible schedule", "full benefits", "guaranteed hours", 'employee referral award',
        "wellness", "union", 'offer great benefits','adoption benefit','family assistance program',
        "adoption assistance", "fertility benefits", "surrogacy assistance",
        "gym memberships", "wellness stipends", "legal assistance plans",
        "home office stipends", "relocation assistance",'competitive compensation benefits',
        "dependent care","flexible spending accounts","comprehensive benefits","outstanding benefits",
        "relocation provided","company discounts","wellness benefits",
    ],
    "profit sharing": [
        "profit sharing", "company wide profit sharing programs","share value","value sharing",'profit ownership',
        "annual profit disbursement",
        "gainsharing program",
        "profit bonus plan",
        "dividend sharing",
        "shared earnings program",
        "collective profit bonus",
        "revenue-sharing incentives",
    ]
}


job_design_characteristics = {
    "flexible work arrangements": [
        "remote work", "work from home", "hybrid schedule",
        "flexible hours", "flextime", "compressed workweek",'home job',
        "part time options", "job sharing", "flexible shifts","work remotely",
        "adjustable hours", "distributed team", "remote friendly",
        "flexible workplace", "work anywhere", "virtual work environment",
        "remote friendly culture", "location independent","working remote",
        "telecommuting options", "global teams", "asynchronous work","flexible work schedule",
        "work anywhere policy","remote management","flexible schedule",
        "work flexibility options","location flexibility","flexible working arrangements",
        "hybrid-friendly workplace","flexible work arrangements"
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
        'family healthy','career support worklife',"employee wellness balance",
        "harmonious work-life practices",
        "life enrichment programs",
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
        'safety hazards','job security',
        'stable supportive corporate',
        "workplace security measures","ethical workplace standards","inclusive and safe workplace",
        "health and safety protocols","safe operational policies","ethical job conditions",
        "corporate responsibility standards"
    ]
}




career_development_opportunities = {
    "skill development programs": [
        "training programs", "skill development","paid continuing education",
        "conference participation", "career growth workshops",'development training',
        "online courses", "professional development", "upskilling programs",
        "reskilling opportunities", "sponsor industry certifications", 
        "continuous learning", "worker development", "training initiatives"
        "jumpstart your career", "looking to grow","employee training",
        "technical training", "skills training", "learning programs","educational opportunities",
        "specialized training", "leadership training", "career training","continuing education reimbursement",
        "career development workshops", "skills enhancement","great training","management training",
        "certification funding",
        "customized training plans",
        "technical bootcamps",
        "industryspecific workshops",
        "microlearning sessions",
        "onthejob training",
        "vocational training programs",
        "tailored learning experiences",
        "certification sponsorship",
        "skills gap training",
        "apprenticeship programs",
        "knowledgesharing initiatives",
        "competencybuilding programs","online course reimbursement",'assistance scholarship programs',
        "vocational training assistance",
        "higher education sponsorship",
        "employee education grant",
        "functional training modules","skillbuilding programs",
        "skill training"
        
    ],
    "mentorship and coaching": [
        "career guidance", "employee development",
        "mentor programs", "one on one coaching", "peer mentorship",
        "executive coaching", "leadership mentoring",'candid meaningful feedback',
        "career coaching", "mentoring programs", "guidance programs","consistent feedback",
        "development coaching", "personalized coaching","feedback constantly","performance feedback",
        "personal growth","learning opportunities",'career advice','performance evaluations','career coaches',
        'regular feedback',"peer coaching","reverse mentorship programs","teambased coaching",
        "developmental feedback sessions",
        "collaborative mentoring",
        "growthfocused coaching",
        "talent mentorship",
        "skillspecific mentoring",
        "feedback-driven development",
        "personalized growth plans",
        "coaching for career acceleration",
        "mentoring for leadership roles",
        "structured coaching programs",
        "mentormentee networking",
        "leadership pipeline mentoring"
    ],
    "clear career progression paths": [
        "promotion tracks", "career progression", "advancement opportunities", 'opportunities grow',
        "opportunities for advancement", "opportunities for growth", "accelerate career",
        "growth opportunities", "career advancement", "career opportunities", 'internal promotions',
        "career mobility", "career development", "dynamic careers", "promotion cycle",'climb ladders',
        "careerdriven individuals", "rapid advancement", "career path","pursue desired career",
        "promotion opportunities", "climbing the ladder", "advance career","personal advancement",
        "growth tracks", "future leadership roles", "development opportunities",'growth plan', 'offers promotions',
        "clear advancement paths", "progression plans","grow career","promotion potential",
        "accelerated growth pathways","fasttrack promotion plans","leadership track opportunities",
        "defined growth milestones",
        "development pathways,"
        "growthcentric career tracks",
        "career plans",
        "tailored career roadmaps",
        "career acceleration programs",
        "personalized growth strategies"
    ],
    "support for lateral moves": [
        "skill diversification", "internal transfers", "cross functional moves",
        "lateral moves", "cross training opportunities", "internal mobility",
        "role flexibility", "career transitions within company", 
        "careeradvancing", "career growth", "professional growth",
        "role switching", "internal job opportunities", 
        "cross departmental opportunities", "team transitions", 
        "job rotation programs", "diverse career paths", "interdepartmental mobility",
        "lateral career","horizontal career shifts","multirole opportunities",
        "exploratory career transitions",
        "varied functional roles",
        "role enrichment programs",
        "internal job rotation schemes",
        "departmental switch opportunities",
        "flexible career pathways",
        "multidomain expertise development",
        "career flexibility initiatives",
        "role expansion programs"
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
        "employee well being", "non judgmental","openness to ideas",
        "trustbuilding practices",
        "emotionally supportive workplace",
        "open idea sharing",
        "safe communication channels",
        "respectful disagreement",
        "empathetic leadership",
        "inclusive decision making",
        "constructive discussions"
    ],
    "inclusion of diverse perspectives": [
        "diversity in decision making", "inclusive leadership",
        "representation in leadership", "valuing diverse opinions", "crosscultural perspectives","cross cultural perspectives",
        "inclusive workplace", "cultural inclusivity", "multicultural environment",
        "diverse voices", "equitable decision making", "inclusive teams","inclusive work environment",
        "diverse perspectives", "multicultural workforce", "cross cultural inclusion" , "crosscultural inclusion"
    ],
    "recognition and celebration": [
        "employee recognition", "celebrating achievements", 
        "shout outs", "employee awards", "appreciation programs",'incentive awards',
        'demonstrated achievements','valued employees',
        'incentive program',
        'annual incentive',
        'performancebased incentives',
        'employee earnings','incentive pay',
        'merit bonuses',
        'employee rewards recognition',
        'staff appreciation','celebrates success',
        "team celebrations", "milestone recognition", "achievement rewards", 
        "recognized and rewarded", "reinvest in our employees", 
        "promote from within", "promoting from within","recognized rewarded",
        "peer recognition", "employee appreciation", 
        "team recognition", "achievement celebrations", "employee value",
        "recognizing excellence",
        "appreciation awards",
        "team reward systems","teamreward systems",
        "reward and recognition framework"
    ],
    "collaborative environment": [
        "team collaboration", "supportive teams", "peer support",'team effort', 
        "cross functional collaboration", "helpful colleagues",'cooperative harmonious working',
        "team oriented environment", "teamwork culture", "collaborative atmosphere", 
        "team environment", "teamwork", "employee involvement", 'team culture','collaborative open environment',
        "employee relations", "worker representation", "teamoriented environment",
        "working men and women", "employees are key",  'supportive appreciative team','work collaboratively',
        "employees are our greatest asset", "care of our people",'teambased culture',
        "collective problem solving", "team building", "collaborative work environment",
        "collaborative teams", "shared goals", "cooperative workplace",'responsible employers',
        "shared accountability",
        "collaborative problem solving",
        "team synergy",
        "shared responsibility",
        "inclusive team efforts",
        "partnership culture",
        "integrated teamwork",
        "collaborative decision making",
        "employeedriven teams",
        "teamfirst mindset"
    ],
    "transparency in leadership": [
        "transparent leadership", "clear communication from leaders",
        "honest decision making", "accessible management","ethical leadership",
        "open door policy", "leader transparency", "managerial openness",
        "transparency", "leadership integrity", "honest leadership",   'positive leadership',
        'organizational accountability','dynamic leadership',
        'visible leadership',
        'organizational communication',
        'environment openness',
        'held accountable','strong leadership',
        'leadership communication',
        'management clear communication',
        'leadership oversight',"managerial honesty",
        "transparent corporate policies",
        "clarity in vision",
        "ethical decisionmaking practices",
        "integritydriven leadership",
        "open communication policies",
        "leader accountability",
        "transparent organizational goals",
        "transparent decision making", "accountable leadership", "openness in management"
    ],
    "workplace recognition": [
        "best companies work", "great place work", 'award winning staff','best large employers',
        "employee friendly workplace", "award winning workplace", "best places work","best employer", 
        "recognized employer", "employer of choice", "best places to work",'perfect place work',
        'wonderful place work','ranked best companies','awardwinning company','company ranking',
        'best midsize employers','leading global supplier','leading manufacturer','leading partner',
        'excellent place work','worlds admired companies','leading companies world', 'awesome place work',
        'large companies world','100 best companies','awardwinning fastgrowing company', "toprated employer",
        "best employer awards",
        "most admired companies",
        "leading workplace environment",
        "outstanding corporate recognition",
        "employer excellence",
        "recognized as a top employer",
        "renowned workplace culture",
        "global leader workplace",
        "highest employee satisfaction"
    ]
}


meaningful_work = {
    "alignment with societal values": [
        "mission driven", "socially conscious", "ethical goals", 'company mission',
        "values alignment", "purpose driven","purposedriven", "social impact focus", 'shared objectives values',
        'organizational values','corporate values',
        'company core values',"missiondriven", 
        "shared values", "corporate mission", "ethical organization",'company values',
        "mission focused roles", "align with the purpose", "share values",
        "meaning of work", "pursuing career with purpose", "mutually rewarding",
        "purpose at work", "life changing", "heart pumping","rewarding career",
        "making impact", "social responsibility", "greater good", "double bottom line",
        "purposedriven mission","social values", "ethically guided work",
        "valuesdriven organization",
        "socially responsible goals",
        "impactfocused mission",
        "integrity in action",
        "corporate purpose alignment",
        "work with meaning",
        "aligning career and values",
        "commitment to purpose",
        "missionaligned work",
        "shared ethical vision",
        "principledriven culture",
        "valuecentric mission"
    ],
    "opportunities to make an impact": [
        "make difference", "positively impact lives", "lasting impact","rewarding work",'better future','improve life','challenging rewarding', 
        'improve quality life','meaningful employment',
        "direct impact roles", 'change lives',"create positive change", "taking toughest challenges",
        "help others", "improve quality of life", "impact driven work", "help people",'fulfilling mission','opportunity make real difference',
        "challenge yourself", "challenging rewarding", 'fulfilling careers','impact peoples lives', 
        "engaging work", "interesting and challenging", "positive impact","helping people",'meaningful work','mission purpose driving',
        "interesting work", "innovative work", "transformative journeys", 'rewarding passion', 'impact peoples',
        "gratifying", "best work of their lives", "work with purpose","make real impact","improving quality life",'rewarding lifelong ',
        "leaving a legacy","career rewarding","improvement human life",'rewarding opportunities',
        "creating lasting change","transforming lives",
        "making a tangible difference",
        "lifeimproving work",
        "achieving meaningful goals",
        "realworld impact",
        "purposeful contribution",
        "making the world better",
        "driving positive change",
        "building a brighter future"
    ],
    "working on innovation": [
        "breakthrough technologies", "cutting edge research","innovative ideas", "changing future",
        "creative problem solving", "next gen solutions", "worldwide influence",'shaping future','innovative companies',
        "innovative roles", "technology driven innovation", "leading product service innovation",'impact future',
        "pioneering advancements", "disruptive innovation", "world leading companies",'develop breakthrough',
        "designing the future", "worlds most innovative company", 'help build future','help build future',
        "history makers", "partner with great minds", "raise the bar","leading research", 'future constantly changing',
        "creative environment", "free thinkers", "leading innovation",'cutting edge technology','innovative vibrant place work', 
        "transformative technologies", "driving progress","vibrant work environment",'creating better future',
        "nextgeneration technology",
        "revolutionary advancements",
        "pushing boundaries",
        "futureforward innovation","leadingedge roles","pioneering technologies",
        "disruptive solutions",
        "technological breakthroughs",
        "pathbreaking innovation",
        "shaping tomorrow",
        "cuttingedge projects",
        "gamechanging research",
        "advancing technology frontiers",
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
        "advancing human development",'global growth','global security challenges',
        "addressing inequality","sustainabilitydriven roles","resolving global crises",
        "championing social equity",
        "combatting climate change",
        "developing sustainable futures",
        "fighting global hunger",
        "advancing global equity",
        "humanitariandriven work",
        "resolving complex challenges",
        "tackling environmental issues",
        "global sustainability initiatives",
        "reducing social disparities",
        "advocating for global change",
        "achieving societal resilience"
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
        'sustainable approach','responsible implementation',
        'sustainable ways',
        'sustainable solutions',
        'resources management','sustainable future',
        'sustainable environment','sustainable world',
        'sustained growth',
        "responsible consumption", "responsible farming", 
        "responsible use", "lifestyle of health and sustainability",
        "resource conservation", "reducing waste",'environmentallyfriendly',
        'sustainable infrastructure',
        'sustainable projects',"ecoresponsible actions",
        "planetpositive solutions","environmentally mindful approaches",
        "sustainabilityfirst mindset","sustainable workplace practices"
    ],
    "renewable energy use": [
        "renewable energy", "solar energy", "wind energy", "green energy",
        "clean energy", "solar power", "wind power", "hydro power", 
        "hydrogen power", "alternative energy", "energy efficient", 
        "energy efficiencies", "energy efficiency", "energy star", 'energy performance',
        'sustainable energy',
        'solar strategies',
        "fuel efficiency", "hybrid energy", "hybrid vehicle", "hybrid car", 
        "nuclear", "clean energies", "low carbon energy","bioenergy",
        "renewable power sources",
        "energy independence",
        "community solar programs",
        "smart grid technologies","decarbonized energy","renewable energy adoption",
        "lowimpact energy","clean energy transition"
    ],
    "conservation programs": [
        "wildlife protection", "water conservation", "biodiversity programs", 
        "land conservation", "habitat restoration", "forest preservation",
        "water use reduction", "natural resource conservation", 'emission reduction',
        "ecosystem protection", "ocean resources", "overfishing", 
        "fish stock", "amazon rain forest", "bio diversities", "biodiversity", 
        "natural resources", "historic sites", "preservation",'water resources',
        'aquatic resources',"tree planting initiatives",
        "river restoration","wildlife corridors","urban green spaces",
        "land rehabilitation","endangered species protection",
        "habitat connectivity","community conservation projects",
        "watershed management",
        "reforestation programs",
        "natural capital preservation",
        "marine biodiversity preservation","wetland restoration","carbon sequestration programs",
        "environmental preservation efforts",
        "protecting habitats", "marine conservation"
    ],
    "climate action": [
        "climate change", "climate crisis", "global warming", 
        "paris agreement", "carbon dioxide", "carbon disclosure", 
        "carbon emission", "carbon neutral", "co2", 'emissions related',
        "greenhouse gas", "environmental impact", 'environmental problems',
        "environmental performance", "environmental footprint", 
        "climate neutral", "impact on the environment",'environmental conditions',
        'environmental production efficiency',
        "climate solutions", "low emissions", "climate adaptation strategies",
        "carbon capture technologies",
        "climate equity",
        "resilient climate solutions",
        "climate targets",
        "climatesmart agriculture",
        "climate resilience planning",
        "net-zero commitments",
        "climatepositive actions",
        "emissionfree technologies",
        "climate initiatives",
        "zero-emissions goals",
        "climate policy advocacy",
        "temperature control initiatives",
        "climate risk mitigation"
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
        'waste spill','environment regulations',
        'recycling nonhazardous solid waste',
        'industry leader recycling',
        'recycling simplified', "green certifications",
        "responsible resource extraction",
        "ecolabeling standards",
        "environmental auditing",
        "sustainable resource allocation",
        "wastewater treatment",
        "non-toxic manufacturing",
        "environmental risk assessments",
        "ecofriendly logistics",
        "environmental accountability",
        "sustainable fleet management",
        "hazardous material compliance",
        "clean production technologies"
    ]
}

social_initiatives = {
    "diversity, equity, and inclusion programs": [
        "aboriginal peoples", "aboriginals", "affirmative action", 
        "african american", "social class", "disabilities", "diversity inclusion",
        "disability status", "disabled", "discriminating", "fair wages",
        "discrimination", "discriminatory", "workforce diversity",
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
        "will not be obligated to disclose", 'fair employment practices',
        'diverse candidate',
        "convictions will not necessarily bar", 'fairness recruitment',
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
        'diverse friendly','applicants receive equal consideration', 
        'diverse community','equalopportunity employer', 
        'equal consideration employment', "inclusive hiring practices",
        "diverse hiring pipeline","inclusiondriven culture",
        "accessible workplace",
        "multicultural inclusion",
        "intersectional equity",
        "inclusive workplace policies",
        "equitable workplace solutions",
        "representation in leadership"
    ],
    "community engagement": [
        "community engagement", "volunteering", "local partnerships", "community involvement","improving communities",
        "employee volunteer programs", "neighborhood support", 'volunteer hours','shared responsibility',
        "grassroots initiatives", "community development", "social impact","community building", "build stronger communities",
        "corporate volunteerism", "civic engagement", "community project", "community involvement","strengthening communities",
        "supporting local communities", "socially engaged", "impact communities",'community work','workforce reflecting communities', 
        'engagement opportunities','community efforts','serving community','community initiatives','community initiative',
        "social responsibility programs",
        "communitydriven impact",
        "local economic development",
        "neighborhood revitalization",
        "partnerships with local organizations",
        "grassroots community programs",
        "volunteer engagement initiatives",
        "civic responsibility projects",
        "community wellbeing support",
        "collaborative community efforts",
        "employeedriven volunteerism",
        "local impact initiatives",
        "sustainable community partnerships",
        "communityfocused actions",
        "social equity in communities"
    ],
    "philanthropy": [
        "charitable giving", "corporate social responsibility", 
        "scholarships", "nonprofit support", "foundation grants",
        "humanitarian aid", "cause based giving", "charity donations",
        "philanthropic initiatives", "donations", "giving back",'corporate giving',
        "community philanthropy", "donor support",'responsible corporate','community giving',
        "corporate generosity programs",
        "charitable contributions",
        "philanthropic donations",
        "humanitarian support initiatives",
        "charitable partnerships",
        "fundraising campaigns",
        "community investment programs",
        "social good contributions",
        "corporate benevolence",
        "donor engagement programs",
        "responsible giving",
        "foundation initiatives",
        "giving back to society"
    ],
    "ethical supply chains": [
        "ethical sourcing", "fair trade", "responsible sourcing", 
        "supply chain transparency", "labor rights", "sustainable sourcing", 
        "supplier diversity", "worker protections", "fair labor standards",
        "environmental supply chain", "responsible farming", 
        "worker equity", "transparent supply chains",'public disclosure', "ethical procurement",
        "human rights in supply chains",
        "fair trade certifications",
        "labor equity standards",
        "responsible supplier relationships",
        "sustainable supply chain management",
        "workercentric supply chains",
        "transparency in procurement",
        "fair wage supply chain",
        "responsible trade practices",
        "ecofriendly sourcing",
        "certified ethical sourcing",
        "traceable supply chains",
        "ethical production processes",
        "responsible distribution networks"
    ]
}


job_tasks_requirements = {
    "job_tasks": [
        "manage", "lead", "design", "develop", "coordinate", "plan", "analyze",
        "implement", "research", "organize", "support", "communicate", "monitor",
        "evaluate", "train", "facilitate", "present", "report", "maintain",
        "oversee", "test", "consult", "build", "solve", "write", "debug",
        "deploy", "execute", "strategize", "coaching", "mentoring", "supervising",
        "duties include", "responsibilities include", "tasked with", "essential responsibilities", "administer",
        "delegate","review","assess","prepare","draft",
        "schedule","execute responsibilities","optimize",
        "troubleshoot","drive","advise","liaise","guide",
        "create","inspect","assist"
    ],
    "job_requirements": [
        "required", "must", "ability to", "mandatory", "minimum qualifications",
        "experience in", "desired", "preferred", "essential", "proficiency in",
        "certification", "background in", "knowledge of", "expertise in",
        "competency in", "fluency in", "responsibilities include", "ability to manage",
        "strong understanding of", "track record of", "commitment to", "ability to lead", "must have experience",
        "required expertise","ability to analyze", "strong proficiency in",
        "prior certification","mandatory background","demonstrated ability",
        "preferred qualifications","necessary credentials",
        "essential skills","technical proficiency","mandatory skills",
        "capacity to manage","ability to adapt","track record in"
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
        "demonstrates skills assigned", "emotional intelligence", "strategic thinking","networking skills",
        "digital literacy",
        "interpersonal skills","leadership capabilities","technical expertise",
        "conflict resolution","agility", "business acumen","problem analysis",
        "innovation skills","customer focus",
        "change management","crossfunctional collaboration","visualization skills",
        "research skills","technical writing"
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

old = [
    "401k", "access to electricity", "aboriginal peoples", "a great environment", 
    "balanced life", "acid rain", "gri frameworks", "accident coverage", 
    "affordable", "aboriginals", "accelerate the journey", "family time", 
    "alternative energy", "esg", "are willing to sponsor", 
    "align with the purpose", "affirmative action", "advancement opportunities", 
    "healthier and happier", "amazon rain forest", "gri ratings", 
    "benefits package", "alternative lives", "african american", 
    "best and the brightest", "healthy worklife", "bio diversities", 
    "gri standards", "bonus", "benefit society", "social class", 
    "best companies to work", "life partner", "biodiversity", "kld", 
    "child support", "benefit the world", "convictions will be reviewed on a", 
    "best company to work", "sustainable worklife", "caged animal", "msci", 
    "childcare", "big hearts", "convictions will not necessarily bar", 
    "best work of their lives", "wife", "carbon dioxide", "transparency", 
    "competitive benefits", "blended families", 
    "criminal record is not an automatic", "bright future", 
    "work life balance", "carbon disclosure", "iso standards", 
    "continuing education", "build a better world", 
    "criminal record will be considered", "care of our people", 
    "workfamily", "carbon emission", "iso 27001", "dental", "building a better world", 
    "disabilities", "career advancement", "worklife balance", 
    "carbon neutral", "dependent care", "causedriven", "disability status", 
    "career development", "worklife program", "circular economy", 
    "dependent coverage", "charitability", "disabled", "career mobility", 
    "time for family", "clean energies", "dependent insurance", "charitable", 
    "discriminating", "career opportunities", "balanced lifestyle", 
    "clean energy", "dependent scholarship", "charitably", "discrimination", 
    "career path", "balance work and leisure", "climate change", 
    "disability insurance", "charities", "discriminatory", 
    "career progression", "climate crisis", "education assistance", 
    "child labor", "diversity", "careeradvancing", "climate event", 
    "educational programs", "civic duties", "equal employment", 
    "careerdriven individuals", "climate neutral", "employee assistance program", 
    "civic duty", "equal opportunities", "challenge yourself", "co2", 
    "employee discount", "civic engagement", "equal opportunity", 
    "challenging and rewarding", "conservation", "employee recognition programs", 
    "civil liberties", "equality", "challenging work", "conserve", 
    "employee stock", "civil liberty", "ethnic diversities", 
    "continuous learning", "deforestation", "flexible schedule", "civil rights", 
    "ethnic diversity", "creative environment", "depleted", "full benefits", 
    "collective action", "ethnic mosaic", "decent work", "depletes", 
    "guaranteed hours", "collectively", "ethnically", "dynamic careers", 
    "depleting", "health benefit", "commitments", "ethnicities", 
    "earning potential", "depletion", "health care", "communal", "ethnicity", 
    "employee equity", "double bottom line", "health coverage", "communities", 
    "female", "employee happiness", "eco system", "health insurance", 
    "community development", "first nations", "employee involvement", 
    "ecosystem", "healthcare", "community group", "first peoples", 
    "employee relations", "ecological", "healthcaring", "community impact", 
    "gay", "employee safety", "energy access", "holiday pay", 
    "community minded", "gender", "employees are key", "energy consumption", 
    "indemnification", "community mission", "hiv", "employees are our greatest asset", 
    "energy efficiencies", "labor rights", "community outreach", "inclusive", 
    "employees voice", "energy efficiency", "legally protected status", 
    "community policies", "indigenous", "empower", "energy efficient", 
    "life insurance", "community policy", "lesbian", "endless opportunities", 
    "energy star", "long term disability", "community project", 
    "marital status", "endless possibilities", "environmental action", 
    "longterm disability", "companys purpose", "minorities", 
    "engaging work", "environmental activism", "maternal leave", 
    "compassion", "minority", "enjoyable", "environmental activities", 
    "medical plans", "constitutional right", "national origin", 
    "environment that inspires", "environmental disclosure", 
    "mental health benefits", "core belief", "native", 
    "excellent opportunity", "environmental footprint", 
    "mental health coverage", "core values", "not obligated to disclose", 
    "free thinkers", "environmental impact", "mileage reinbursment", 
    "cross culturalism", "race", "gratifying", "environmental inclination", 
    "open office spaces", "csr", "racial", "great place to work", 
    "environmental management systems", "paid time off", 
    "cultural preservation", "religious diversities", "great places to work", 
    "environmental performance", "paid vacation time", "cultures", 
    "religious diversity", "grow personally", "environmental policies", 
    "parental leave", "differencemaker", "same sex", "grow professionally", 
    "environmental policy", "pension", "disadvantaged", "sealed or expunged", 
    "growth opportunities", "environmental practices", "pet insurance", 
    "disadvantageous", "unbiased", "highly motivated", 
    "environmental protection", "public transportation", 
    "disadvantages", "underrepresented group", "history makers", 
    "environmental reform", "realocation programs", "disasters", 
    "veteran", "human element", "environmental resource", 
    "realocation support", "donating", "women", "innovative work", 
    "environmental responsibilities", "retirement", "drive innovation", 
    "sexual orientation", "intellectual curiosity", "environmental responsibility", 
    "sabbaticals", "economic inequality", "religion", "intellectually curious", 
    "environmental safety", "savings plans", "embodies", "pregnancy", 
    "intellectually stimulating", "environmental stance", "scholarships", 
    "enriching life", "interesting and challenging", 
    "environmental stewardship", "short term disability", "entitled rights", 
    "interesting work", "environmentalist", "shortterm disability", 
    "equitable impact", "investing in our employees", 
    "environmentally friendly", "sick leave", "equity", 
    "jumpstart your career", "environmentally inclined", 
    "skill development", "ethic", "life changing", "environmentally neutral", 
    "skills development", "ethical", "looking to grow", 
    "environmentally safe", "training", "even distribution", 
    "meaning of work", "environmental supply chain", "tuition reimbursement", 
    "evenly distributed", "mentorship", "fish stock", "union", 
    "fair", "famine", "opportunities for advancement", "fuel efficiency", 
    "vacation time", "opportunities for growth", "global warming", 
    "wellness", "partner with great minds", "green building", 
    "paternal leave", "forced labor", "professional growth", 
    "green energy", "coverage", "freedom", "promote from within", 
    "green engineering", "college scholarship", "give back", 
    "green growth", "greenhouse gas", "donate", "good profit"
]

old_nd = [
    "401k", "access to electricity", "a great environment", 
    "balanced life", "acid rain", "gri frameworks", "accident coverage", 
    "affordable", "accelerate the journey", "family time", 
    "alternative energy", "esg", "are willing to sponsor", 
    "align with the purpose", "advancement opportunities", 
    "healthier and happier", "amazon rain forest", "gri ratings", 
    "benefits package", "alternative lives", "best and the brightest", 
    "healthy worklife", "bio diversities", "gri standards", 
    "bonus", "benefit society", "best companies to work", 
    "life partner", "biodiversity", "kld", "child support", 
    "benefit the world", "best company to work", 
    "sustainable worklife", "caged animal", "msci", 
    "childcare", "big hearts", "best work of their lives", 
    "wife", "carbon dioxide", "transparency", 
    "competitive benefits", "blended families", "bright future", 
    "work life balance", "carbon disclosure", "iso standards", 
    "continuing education", "build a better world", 
    "care of our people", "workfamily", "carbon emission", 
    "iso 27001", "dental", "building a better world", 
    "career advancement", "worklife balance", 
    "carbon neutral", "dependent care", "causedriven", 
    "career development", "worklife program", "circular economy", 
    "dependent coverage", "charitability", 
    "career mobility", "time for family", "clean energies", 
    "dependent insurance", "charitable", "career opportunities", 
    "balanced lifestyle", "clean energy", "dependent scholarship", 
    "charitably", "career path", "balance work and leisure", 
    "climate change", "disability insurance", "charities", 
    "career progression", "climate crisis", "education assistance", 
    "child labor", "careeradvancing", "climate event", 
    "educational programs", "civic duties", 
    "challenge yourself", "climate neutral", 
    "employee assistance program", "civic duty", 
    "challenging and rewarding", "co2", 
    "employee discount", "civic engagement", 
    "challenging work", "conservation", "employee recognition programs", 
    "civil liberties", "conserve", "employee stock", "civil liberty", 
    "continuous learning", "deforestation", 
    "flexible schedule", "civil rights", 
    "creative environment", "depleted", "full benefits", 
    "collective action", "decent work", "depletes", 
    "guaranteed hours", "collectively", "dynamic careers", 
    "depleting", "health benefit", "commitments", 
    "earning potential", "depletion", "health care", 
    "communal", "employee equity", "double bottom line", 
    "health coverage", "communities", "employee happiness", 
    "eco system", "health insurance", 
    "community development", "employee involvement", 
    "ecosystem", "healthcare", "community group", 
    "employee relations", "ecological", "healthcaring", 
    "community impact", "employee safety", "energy access", 
    "holiday pay", "community minded", "employees are key", 
    "energy consumption", "indemnification", "community mission", 
    "employees are our greatest asset", 
    "energy efficiencies", "labor rights", "community outreach", 
    "empower", "energy efficiency", "legally protected status", 
    "community policies", "energy efficient", 
    "life insurance", "community policy", "endless opportunities", 
    "energy star", "long term disability", "community project", 
    "endless possibilities", "environmental action", 
    "longterm disability", "companys purpose", 
    "engaging work", "environmental activism", 
    "maternal leave", "compassion", "enjoyable", 
    "environmental activities", "medical plans", 
    "constitutional right", "excellent opportunity", 
    "environment that inspires", "environmental disclosure", 
    "mental health benefits", "core belief", 
    "excellent opportunity", "environmental footprint", 
    "mental health coverage", "core values", "not obligated to disclose", 
    "free thinkers", "environmental impact", "mileage reinbursment", 
    "cross culturalism", "gratifying", "environmental inclination", 
    "open office spaces", "csr", "great place to work", 
    "environmental management systems", "paid time off", 
    "cultural preservation", "great places to work", 
    "environmental performance", "paid vacation time", "cultures", 
    "grow personally", "environmental policies", 
    "parental leave", "differencemaker", "grow professionally", 
    "environmental policy", "pension", "sealed or expunged", 
    "growth opportunities", "environmental practices", 
    "pet insurance", "unbiased", "highly motivated", 
    "environmental protection", "public transportation", 
    "disasters", "history makers", "environmental resource", 
    "donating", "innovative work", "environmental responsibilities", 
    "retirement", "drive innovation", 
    "intellectual curiosity", "environmental responsibility", 
    "sabbaticals", "economic inequality", 
    "intellectually curious", "environmental safety", 
    "savings plans", "embodies", "intellectually stimulating", 
    "environmental stance", "scholarships", 
    "enriching life", "interesting and challenging", 
    "environmental stewardship", "short term disability", "entitled rights", 
    "interesting work", "environmentalist", "shortterm disability", 
    "investing in our employees", 
    "environmentally friendly", "sick leave", 
    "jumpstart your career", "environmentally inclined", 
    "skill development", "life changing", "environmentally neutral", 
    "skills development", "looking to grow", 
    "environmentally safe", "training", 
    "meaning of work", "environmental supply chain", "tuition reimbursement", 
    "mentorship", "fish stock", "union", 
    "fuel efficiency", "vacation time", "global warming", 
    "wellness", "partner with great minds", "green building", 
    "paternal leave", "professional growth", 
    "green energy", "coverage", "promote from within", 
    "green engineering", "college scholarship", 
    "green growth", "greenhouse gas", "donate", "good profit"
]

old = {"old": old}
old_nd = {"old_nd": old_nd}

def decode_structure(data):
    """
    Recursively decode byte strings in dictionaries, lists, or single values.
    """
    if isinstance(data, bytes):  # Decode byte string
        try:
            return data.decode('utf-8')
        except UnicodeDecodeError:
            return data.decode('latin1')  # Fallback for other encodings
    elif isinstance(data, list):  # Recursively process lists
        return [decode_structure(item) for item in data]
    elif isinstance(data, dict):  # Recursively process dictionaries
        return {decode_structure(key): decode_structure(value) for key, value in data.items()}
    return data  # Return as-is if not bytes, list, or dict

# Decode dictionaries, old, and old_nd
dictionaries = decode_structure(dictionaries)
old = decode_structure(old)
old_nd = decode_structure(old_nd)


# Text cleaning function
def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8', 'ignore')
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', text)
    text = re.sub(r'[^a-zA-Z0-9\s.,!?]', '', text)
    return re.sub(r'\s+', ' ', text.lower()).strip()

# Define function to count keywords and list matched terms
def keyword_count_and_terms(text, dictionary):
    count = 0
    terms = []
    for category, keywords in dictionary.items():
        for keyword in keywords:
            if keyword in text:
                count += 1
                terms.append(keyword)
    return count, terms

# Load and clean the data
def process_file(df):
    df = df.dropna(subset = ['JobText'])
    df= df[(df['CanonEmployer'].notna()) & (df['CanonEmployer'] != None) & (df['CanonEmployer'] != "None")]
    df['CleanText'] = df['JobText'].apply(clean_text)
    df = df.drop(columns=['IsDuplicate','IsDuplicateOf', 'JobReferenceID'])

    # Dictionary counts
    for dict_name, dictionary in dictionaries.items():
        df[f'{dict_name}_count'], df[f'{dict_name}_terms'] = zip(
            *df['CleanText'].apply(lambda x: keyword_count_and_terms(x, dictionary))
        )
    
    df['main'] = df['CleanText'].apply(lambda x: keyword_count_and_terms(x, old)[0])
    df['main_nd'] = df['CleanText'].apply(lambda x: keyword_count_and_terms(x, old_nd)[0])
    
    # Date
    df['year'] = df.JobDate.apply(lambda x: x[0:4])
    df['month'] = df.JobDate.apply(lambda x: x[5:7])
    
    return df

### Paralellize function
def parallelize_dataframe(df, func, n_cores):
    df_split = np.array_split(df, n_cores)
    pool = Pool(n_cores)
    df = pd.concat(pool.map(func, df_split))
    pool.close()
    pool.join()
    return df


    
# Function to process files for a given year
def process_files_by_year(start_year, end_year):
    for year in range(start_year, end_year + 1):  # Iterate over the years
        print(f"Processing year: {year}")
        
        # Declare path as a string
        path_txt = f'/global/home/pc_moseguera/output/processed/{year}'
        
        # Iterate over files in the directory
        for file in glob.glob(os.path.join(path_txt, '*.parquet')):
            file_name = os.path.basename(file)  # Extract the file name
            print("Started working on file: " + file_name + " Time is: " + datetime.datetime.now().strftime("%H:%M:%S"))
            
            df = pd.read_parquet(file)
            train = pd.DataFrame()
            
            for i in range(16):
                start_idx = i * 100000
                end_idx = (100000) * (i + 1) - 1
            
                # Ensure slice indices are within bounds
                if start_idx >= len(df):
                    print(f"Chunk {i} is out of bounds. Skipping.")
                    break
            
                df_aux = df.iloc[start_idx:min(end_idx, len(df) - 1)]  # Avoid slicing out of bounds
                print(f"Chunk {i}: Shape {df_aux.shape}")
            
                if df_aux.empty:
                    print(f"Chunk {i} is empty. Skipping.")
                    continue
            
                print(f"Started processing: {start_idx}. Time is: {datetime.datetime.now().strftime('%H:%M:%S')}")
                
                try:
                    aux = parallelize_dataframe(df_aux, process_file, 9)
                    train = pd.concat([train, aux], ignore_index=True)
                except Exception as e:
                    print(f"Error processing chunk {i}: {e}")
                    continue

            # Save the processed DataFrame to Parquet
            output_path = f"/global/home/pc_moseguera/output/processed/{year}/read_dictionaries/{file_name}"
            train.to_parquet(output_path, index=False, compression="zstd")
            
            # Clean up
            del train
            del df_aux
            gc.collect()

# Call the function for years 2011 to 2021
process_files_by_year(2010, 2022)
