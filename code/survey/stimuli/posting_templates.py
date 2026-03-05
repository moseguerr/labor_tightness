"""
Posting templates for the ranking task experiment.

Design:
  - 3 occupation pools (Business Analyst, Financial Analyst, Marketing Analyst)
  - 4 signal types per pool (purpose_innovation, purpose_social, good_employer, neutral)
  - Wage levels counterbalanced across participants
  - All postings use fictional company names but real language patterns
    grounded in Lightcast job posting data (2017-2019 samples)

Each posting has the same structure:
  - company_intro: Neutral company description (~50 words)
  - role_description: Standard role duties (~60 words)
  - signal_section_title + signal_section_text: The experimental manipulation (~70 words)
  - requirements_text: Standard requirements (~30 words)

Signal type definitions:
  - purpose_innovation: Mission framed around innovation, pioneering, reshaping industry
  - purpose_social: Mission framed around social impact, equity, community
  - good_employer: Framed around employee benefits, development, workplace quality
  - neutral: Factual, administrative details only (control)
"""

# Wage levels: high and low per occupation
# These are realistic salary ranges from Lightcast data for each SOC
WAGE_RANGES = {
    'business_analyst': {
        'high': {'text': '$88,000 - $105,000', 'low': 88000, 'high_val': 105000},
        'low':  {'text': '$52,000 - $64,000',  'low': 52000, 'high_val': 64000},
    },
    'financial_analyst': {
        'high': {'text': '$85,000 - $100,000', 'low': 85000, 'high_val': 100000},
        'low':  {'text': '$50,000 - $62,000',  'low': 50000, 'high_val': 62000},
    },
    'marketing_analyst': {
        'high': {'text': '$78,000 - $92,000',  'low': 78000, 'high_val': 92000},
        'low':  {'text': '$45,000 - $55,000',  'low': 45000, 'high_val': 55000},
    },
}

POSTINGS = {
    # =================================================================
    # BUSINESS ANALYST (SOC 13-1111)
    # =================================================================
    'business_analyst': [
        {
            'signal_type': 'purpose_innovation',
            'company_name': 'Vantage Strategy Group',
            'job_title': 'Business Analyst',
            'company_intro': (
                'Vantage Strategy Group is a management consulting firm that works '
                'with Fortune 500 clients on market entry, competitive positioning, '
                'and corporate transformation. Founded in 2011, the firm has grown '
                'to over 400 professionals across six offices.'
            ),
            'role_description': (
                'As a Business Analyst, you will develop competitive landscape '
                'analyses, build financial models to evaluate strategic options, '
                'and prepare client-facing presentations that translate complex '
                'data into actionable recommendations. You will work with '
                'engagement managers to scope research questions and synthesize '
                'findings for senior leadership at client organizations.'
            ),
            'signal_section_title': 'Who We Are',
            'signal_section_text': (
                'We are redefining how strategic advisory works. Our team operates '
                'at the intersection of rigorous analysis and bold thinking \u2014 we '
                'do not recycle frameworks, we build new ones. We recruit people '
                'who want to be part of building something that has not been done '
                'before, who find energy in problems without obvious answers. '
                'Our culture rewards intellectual courage, moves fast on '
                'high-conviction ideas, and holds every deliverable to a standard '
                'that reshapes how our clients think about their markets.'
            ),
            'requirements_text': (
                "Bachelor\u2019s degree in business, economics, or a related field. "
                'Two to three years of experience in consulting, corporate '
                'strategy, or a related analytical role.'
            ),
        },
        {
            'signal_type': 'purpose_social',
            'company_name': 'Bridgewell Financial',
            'job_title': 'Business Analyst',
            'company_intro': (
                'Bridgewell Financial is a community development financial '
                'institution that provides lending and advisory services to '
                'underserved communities across the Mid-Atlantic region. The '
                'organization manages a portfolio of over $200 million in '
                'community investments.'
            ),
            'role_description': (
                'As a Business Analyst, you will build financial models for loan '
                'underwriting, conduct portfolio risk assessments, and prepare '
                'quarterly reports on fund performance for internal leadership and '
                'external investors. You will collaborate with the lending team to '
                'evaluate borrower applications and develop recommendations that '
                'balance financial sustainability with community outcomes.'
            ),
            'signal_section_title': 'Our Mission',
            'signal_section_text': (
                'Our mission is to make financial access equitable for communities '
                'that traditional institutions have overlooked. We measure success '
                'not just in returns but in neighborhoods revitalized and families '
                'given a fair chance. Joining Bridgewell means your analytical '
                'work contributes directly to reducing inequality \u2014 every model '
                'you build helps capital flow to where it is needed most. We are '
                'looking for people who believe business can be a force for good '
                'and want their skills to serve a purpose larger than profit.'
            ),
            'requirements_text': (
                "Bachelor\u2019s degree in finance, economics, business, or a "
                'related field. Two to three years of experience in financial '
                'analysis, lending, or a related analytical role.'
            ),
        },
        {
            'signal_type': 'good_employer',
            'company_name': 'Crestline Industries',
            'job_title': 'Business Analyst',
            'company_intro': (
                'Crestline Industries is a mid-size consumer products company with '
                'a portfolio of brands in home goods and personal care. '
                'Headquartered in the greater Washington, D.C. area, the company '
                'distributes through major retail partners and a growing '
                'direct-to-consumer channel.'
            ),
            'role_description': (
                'As a Business Analyst, you will analyze sales performance data '
                'across product lines, develop forecasting models, and prepare '
                'reports for the leadership team on market trends and competitive '
                'positioning. You will support the strategy team in evaluating '
                'new market opportunities and tracking key performance indicators '
                'across business units.'
            ),
            'signal_section_title': 'Working at Crestline',
            'signal_section_text': (
                'We offer a structured mentorship program that pairs every new '
                'hire with a senior leader, a clear promotion track reviewed '
                'annually, and flexible hybrid work arrangements with three days '
                'in-office. Employees receive a dedicated professional development '
                'budget of $2,000 per year for courses, conferences, or '
                'certifications. We have been recognized as a top workplace by '
                'the Washington Business Journal for three consecutive years. '
                'Benefits include comprehensive health coverage, a 401(k) match, '
                'and four weeks of paid time off starting in your first year.'
            ),
            'requirements_text': (
                "Bachelor\u2019s degree in business, analytics, economics, or a "
                'related field. Two to three years of experience in business '
                'analysis, strategy, or a related coordination role.'
            ),
        },
        {
            'signal_type': 'neutral',
            'company_name': 'Thornbury Corp',
            'job_title': 'Business Analyst',
            'company_intro': (
                'Thornbury Corp is a national logistics and supply chain '
                'management company that serves retail and manufacturing clients '
                'across the United States. The company operates distribution '
                'centers in twelve states and coordinates freight movement for '
                'over 300 accounts.'
            ),
            'role_description': (
                'As a Business Analyst, you will monitor daily throughput '
                'metrics across distribution sites, identify bottlenecks in order '
                'fulfillment workflows, and develop process improvement '
                'recommendations supported by data analysis. You will build '
                'reports on cost variance, carrier performance, and inventory '
                'turnover for the operations leadership team.'
            ),
            'signal_section_title': 'Additional Information',
            'signal_section_text': (
                'This is a full-time position reporting to the Director of '
                'Business Analytics. The role is based in our corporate office '
                'with standard business hours. Travel to distribution sites may be '
                'required up to two times per quarter for on-site data collection '
                'and process review. The position includes eligibility for the '
                "company\u2019s standard benefits package. Analysts in this group "
                'typically work with Excel, SQL, and internal reporting tools on a '
                'daily basis.'
            ),
            'requirements_text': (
                "Bachelor\u2019s degree in business, supply chain, "
                'analytics, or a related field. Two to three years of '
                'experience in business analysis, operations, or a related '
                'analytical role.'
            ),
        },
    ],

    # =================================================================
    # FINANCIAL ANALYST (SOC 13-2051)
    # =================================================================
    'financial_analyst': [
        {
            'signal_type': 'purpose_innovation',
            'company_name': 'Novalink Group',
            'job_title': 'Financial Analyst',
            'company_intro': (
                'Novalink Group is a financial technology firm that builds '
                'predictive analytics platforms for enterprise treasury and '
                'risk management teams. The company serves over 150 mid-market '
                'and enterprise clients and was recently named to a list of '
                'fastest-growing fintech companies.'
            ),
            'role_description': (
                'As a Financial Analyst, you will design and maintain financial '
                'models that forecast cash flow positions, analyze investment '
                'portfolio performance, and prepare variance reports for senior '
                'leadership. You will collaborate with product teams to evaluate '
                'new revenue opportunities and support quarterly planning with '
                'scenario analyses.'
            ),
            'signal_section_title': 'Who We Are',
            'signal_section_text': (
                'We are building the future of how organizations manage financial '
                'risk. Our team sits at the frontier of applied data science '
                'and capital markets \u2014 we believe the next generation of '
                'financial decisions will be driven by evidence, not intuition. We '
                'recruit people who are energized by hard problems and want to '
                'pioneer approaches that do not exist yet. Our culture is built on '
                'rigorous thinking, fast iteration, and a shared conviction that '
                'we are creating something that will fundamentally change how '
                'companies manage their capital.'
            ),
            'requirements_text': (
                "Bachelor\u2019s degree in finance, economics, data science, "
                'or a related field. Two to three years of experience in '
                'financial analysis, investment research, or a related '
                'quantitative role.'
            ),
        },
        {
            'signal_type': 'purpose_social',
            'company_name': 'Clearpath Foundation',
            'job_title': 'Financial Analyst',
            'company_intro': (
                'Clearpath Foundation is a nonprofit financial intermediary that '
                'manages grant-funded programs and impact investment vehicles '
                'focused on workforce development and affordable housing. The '
                'organization administers over $150 million in active grants '
                'across 30 states.'
            ),
            'role_description': (
                'As a Financial Analyst, you will track grant expenditures against '
                'budgets, prepare financial reports for federal and state funders, '
                'and conduct cost-benefit analyses on program outcomes. You will '
                'work with program officers to ensure compliance with funder '
                'requirements and develop projections for grant renewal '
                'applications.'
            ),
            'signal_section_title': 'Our Mission',
            'signal_section_text': (
                'We exist to channel capital toward the communities and people '
                'who need it most. Every dollar we manage supports families '
                'seeking stable housing or workers building new careers. Your '
                'financial expertise here translates directly into measurable '
                'social outcomes \u2014 when you identify savings, those funds reach '
                'another cohort of participants. We seek people who want their '
                'professional skills to serve a larger purpose and who care about '
                'building an economy that works for everyone, not just a few.'
            ),
            'requirements_text': (
                "Bachelor\u2019s degree in finance, accounting, economics, or a "
                'related field. Two to three years of experience in financial '
                'analysis, grant management, or a related analytical role.'
            ),
        },
        {
            'signal_type': 'good_employer',
            'company_name': 'Hearthstone Solutions',
            'job_title': 'Financial Analyst',
            'company_intro': (
                'Hearthstone Solutions is a professional services firm specializing '
                'in corporate finance advisory for mid-market companies undergoing '
                'mergers, acquisitions, or restructuring. Founded in 2008, the '
                'firm has completed over 600 engagements across healthcare, '
                'technology, and manufacturing sectors.'
            ),
            'role_description': (
                'As a Financial Analyst, you will build valuation models, conduct '
                'due diligence analyses, and prepare deal memoranda for client '
                'presentations. You will support managing directors in evaluating '
                'acquisition targets and developing financial projections for '
                'transaction planning.'
            ),
            'signal_section_title': 'Why Hearthstone',
            'signal_section_text': (
                'We believe people do their best work when they are genuinely '
                'supported. Every employee receives a personal development plan '
                'built with their manager in the first 90 days, with quarterly '
                'check-ins and a $2,500 annual learning stipend. Our hybrid model '
                'offers full schedule flexibility \u2014 you choose your in-office '
                'days. We run an internal mobility program so employees can '
                'explore different practice areas without leaving the firm. '
                'Benefits include fully covered health and dental insurance, '
                'a 5% 401(k) match, and five weeks of paid time off.'
            ),
            'requirements_text': (
                "Bachelor\u2019s degree in finance, accounting, economics, or a "
                'related field. Two to three years of experience in financial '
                'analysis, investment banking, or a related advisory role.'
            ),
        },
        {
            'signal_type': 'neutral',
            'company_name': 'Greystone Partners',
            'job_title': 'Financial Analyst',
            'company_intro': (
                'Greystone Partners is a regional accounting and business advisory '
                'firm that provides audit, tax, and consulting services to '
                'privately held companies. The firm has offices in three '
                'Mid-Atlantic cities and serves clients in construction, '
                'healthcare, and professional services.'
            ),
            'role_description': (
                'As a Financial Analyst, you will prepare monthly financial '
                'statements, reconcile general ledger accounts, and assist with '
                'the annual budgeting process. You will support the audit team '
                'by gathering documentation, running analytical procedures, '
                'and drafting workpapers for review by senior staff.'
            ),
            'signal_section_title': 'Additional Information',
            'signal_section_text': (
                'This is a full-time position reporting to the Finance Manager. '
                'The role is based in our main office with standard business '
                'hours, Monday through Friday. Occasional overtime may be '
                'required during busy season (January through April). The '
                'position includes eligibility for the firm\u2019s standard benefits '
                'package. Analysts typically use Excel, QuickBooks, and the '
                'firm\u2019s proprietary audit software on a daily basis.'
            ),
            'requirements_text': (
                "Bachelor\u2019s degree in accounting, finance, economics, or a "
                'related field. Two to three years of experience in financial '
                'analysis, accounting, or a related analytical role.'
            ),
        },
    ],

    # =================================================================
    # MARKETING ANALYST (SOC 13-1161)
    # =================================================================
    'marketing_analyst': [
        {
            'signal_type': 'purpose_innovation',
            'company_name': 'Meridian Ventures',
            'job_title': 'Marketing Analyst',
            'company_intro': (
                'Meridian Ventures is a digital marketing technology company that '
                'develops audience analytics and campaign optimization platforms '
                'for enterprise brands. The company works with over 200 clients '
                'across retail, media, and consumer technology sectors.'
            ),
            'role_description': (
                'As a Marketing Analyst, you will analyze campaign performance '
                'data across digital channels, build attribution models, and '
                'prepare reports on audience engagement and conversion metrics. '
                'You will work with account managers to optimize media spend '
                'allocation and develop data-driven recommendations for client '
                'marketing strategies.'
            ),
            'signal_section_title': 'Who We Are',
            'signal_section_text': (
                'We are building the next generation of marketing intelligence. '
                'Our platform uses machine learning to solve attribution problems '
                'that the industry has treated as unsolvable for decades. We '
                'recruit people who want to work on problems at the edge of '
                "what\u2019s possible, who are excited by the idea of replacing "
                'guesswork with precision. Our culture values intellectual '
                'ambition, rapid experimentation, and the kind of analytical '
                'rigor that creates new categories rather than competing in '
                'existing ones.'
            ),
            'requirements_text': (
                "Bachelor\u2019s degree in marketing, statistics, business, or a "
                'related field. Two to three years of experience in marketing '
                'analytics, digital media, or a related quantitative role.'
            ),
        },
        {
            'signal_type': 'purpose_social',
            'company_name': 'Mosaic Health',
            'job_title': 'Marketing Analyst',
            'company_intro': (
                'Mosaic Health is a nonprofit health system that operates '
                'community clinics and outreach programs serving low-income and '
                'uninsured populations. The organization provides primary care, '
                'behavioral health, and preventive services at 14 locations '
                'across three counties.'
            ),
            'role_description': (
                'As a Marketing Analyst, you will track outreach campaign '
                'performance, analyze patient acquisition data, and prepare '
                'reports on community engagement metrics for the communications '
                'team. You will support the development of messaging strategies '
                'that increase awareness of available health services among '
                'target populations.'
            ),
            'signal_section_title': 'Our Mission',
            'signal_section_text': (
                'We believe healthcare is a right, not a privilege. Every '
                'campaign you help shape connects someone to care they might '
                'not have known was available \u2014 a screening that catches a '
                'condition early, a counseling session that changes a trajectory. '
                'Your work in marketing directly supports our mission to close '
                'the health equity gap in the communities we serve. We seek '
                'people who want their professional skills to make a tangible '
                'difference in the lives of people who have been underserved '
                'by the healthcare system.'
            ),
            'requirements_text': (
                "Bachelor\u2019s degree in marketing, communications, public health, "
                'or a related field. Two to three years of experience in '
                'marketing analysis, health communications, or a related role.'
            ),
        },
        {
            'signal_type': 'good_employer',
            'company_name': 'Ridgeline Media',
            'job_title': 'Marketing Analyst',
            'company_intro': (
                'Ridgeline Media is a mid-size digital media company that '
                'produces content and manages advertising partnerships for '
                'lifestyle and entertainment brands. The company is headquartered '
                'in a major U.S. metro area and employs approximately 350 '
                'people across editorial, sales, and analytics teams.'
            ),
            'role_description': (
                'As a Marketing Analyst, you will manage campaign reporting '
                'dashboards, analyze audience engagement trends, and develop '
                'insights that inform content and advertising strategy. You will '
                'coordinate with the sales team to prepare performance summaries '
                'for advertising clients and support quarterly business reviews.'
            ),
            'signal_section_title': 'Working at Ridgeline',
            'signal_section_text': (
                'We invest in our people. Every employee is paired with a mentor '
                'from senior leadership and receives a personal learning budget '
                'of $2,000 per year. We offer fully flexible remote work, a '
                'four-day summer schedule, and an annual team retreat. Our '
                'promotion process is transparent \u2014 criteria are published and '
                'reviewed with every employee twice a year. Benefits include '
                'full medical, dental, and vision coverage, a 4% 401(k) match, '
                'and four weeks of paid time off from day one.'
            ),
            'requirements_text': (
                "Bachelor\u2019s degree in marketing, communications, business, or a "
                'related field. Two to three years of experience in marketing '
                'analytics, media planning, or a related coordination role.'
            ),
        },
        {
            'signal_type': 'neutral',
            'company_name': 'Stonebridge Corp',
            'job_title': 'Marketing Analyst',
            'company_intro': (
                'Stonebridge Corp is a national building materials distributor '
                'that supplies commercial construction firms across the eastern '
                'United States. The company manages a product catalog of over '
                '15,000 items and operates regional warehouses in eight states.'
            ),
            'role_description': (
                'As a Marketing Analyst, you will track product catalog '
                'performance metrics, analyze customer purchase patterns, and '
                'prepare reports on promotional campaign results for the '
                'marketing director. You will support trade show planning by '
                'compiling competitive intelligence and coordinating materials '
                'with external vendors.'
            ),
            'signal_section_title': 'Additional Information',
            'signal_section_text': (
                'This is a full-time position reporting to the Marketing '
                'Director. The role is based in our corporate headquarters with '
                'standard business hours, Monday through Friday. Occasional '
                'travel to industry trade shows may be required two to three '
                'times per year. The position includes eligibility for the '
                "company\u2019s standard benefits package. Analysts in this team "
                'typically use Excel, Google Analytics, and the company\u2019s CRM '
                'system on a daily basis.'
            ),
            'requirements_text': (
                "Bachelor\u2019s degree in marketing, business, communications, or a "
                'related field. Two to three years of experience in marketing '
                'analysis, trade marketing, or a related analytical role.'
            ),
        },
    ],
}
