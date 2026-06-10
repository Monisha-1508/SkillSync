from __future__ import annotations

from typing import NamedTuple


class Node(NamedTuple):
    key: str
    name: str
    bloom: int
    hours: int
    difficulty: str
    family: str
    tags: tuple[str, ...]
    root: str | None = None       # explicit first prerequisite (branch point)
    extra: tuple[str, ...] = ()   # additional prerequisites layered on top of the chain


# ── Foundation: shared root every track eventually traces back to ──────────
CHAIN_FOUNDATION: list[Node] = [
    Node("fnd.computing_basics", "Computing & Internet Basics", 1, 4, "beginner",
         "Digital Literacy", ("foundation",)),
    Node("fnd.typing_tools", "Dev Environment & Tooling Setup", 1, 3, "beginner",
         "Digital Literacy", ("foundation", "tools")),
    Node("fnd.prog_logic", "Programming Logic Building", 2, 10, "beginner",
         "Programming & Development", ("foundation", "programming"), root="fnd.computing_basics"),
    Node("fnd.git_basics", "Git & Version Control Basics", 2, 6, "beginner",
         "Tools & Collaboration", ("tools", "collaboration"), root="fnd.typing_tools"),
    Node("fnd.communication_basics", "Workplace Communication Basics", 1, 4, "beginner",
         "Communication", ("softskills", "communication")),
]

# ── SDE / core CS track ─────────────────────────────────────────────────────
CHAIN_SDE: list[Node] = [
    Node("sde.python_core", "Python Programming Core", 2, 16, "beginner",
         "Programming & Development", ("programming",), root="fnd.prog_logic"),
    Node("sde.control_flow", "Control Flow, Functions & Modules", 2, 10, "beginner",
         "Programming & Development", ("programming",)),
    Node("sde.oop", "Object-Oriented Programming", 3, 12, "intermediate",
         "Programming & Development", ("programming",)),
    Node("sde.arrays_strings", "Arrays & Strings", 3, 14, "intermediate",
         "Data Structures & Algorithms", ("dsa",)),
    Node("sde.complexity", "Time & Space Complexity (Big-O)", 3, 6, "intermediate",
         "Data Structures & Algorithms", ("dsa",)),
    Node("sde.recursion", "Recursion & Backtracking Foundations", 3, 12, "intermediate",
         "Data Structures & Algorithms", ("dsa",)),
    Node("sde.linked_lists", "Linked Lists", 3, 10, "intermediate",
         "Data Structures & Algorithms", ("dsa",)),
    Node("sde.stacks_queues", "Stacks & Queues", 3, 8, "intermediate",
         "Data Structures & Algorithms", ("dsa",)),
    Node("sde.hashing", "Hashing & Hash Maps", 3, 8, "intermediate",
         "Data Structures & Algorithms", ("dsa",)),
    Node("sde.trees", "Trees & Binary Search Trees", 4, 14, "intermediate",
         "Data Structures & Algorithms", ("dsa",)),
    Node("sde.heaps", "Heaps & Priority Queues", 4, 8, "intermediate",
         "Data Structures & Algorithms", ("dsa",)),
    Node("sde.graphs", "Graphs: BFS, DFS & Shortest Paths", 4, 16, "advanced",
         "Data Structures & Algorithms", ("dsa",)),
    Node("sde.sorting_searching", "Sorting & Searching Algorithms", 4, 10, "intermediate",
         "Data Structures & Algorithms", ("dsa", "algorithms")),
    Node("sde.greedy", "Greedy Algorithms", 4, 8, "advanced",
         "Data Structures & Algorithms", ("dsa", "algorithms")),
    Node("sde.dynamic_programming", "Dynamic Programming", 5, 18, "advanced",
         "Data Structures & Algorithms", ("dsa", "algorithms"), extra=("sde.recursion",)),
    Node("sde.advanced_patterns", "Advanced Problem-Solving Patterns", 5, 12, "advanced",
         "Data Structures & Algorithms", ("dsa", "algorithms", "placement")),
    Node("sde.dbms_sql", "Databases & SQL Fundamentals", 3, 12, "intermediate",
         "Data & Databases", ("data",), root="sde.control_flow"),
    Node("sde.os_basics", "Operating Systems Essentials", 3, 8, "intermediate",
         "Systems", ("systems",), root="sde.control_flow"),
    Node("sde.networks_basics", "Computer Networks Essentials", 3, 8, "intermediate",
         "Systems", ("systems",)),
    Node("sde.lld_design_patterns", "Low-Level Design & Design Patterns", 5, 14, "advanced",
         "Software Design", ("design",), extra=("sde.oop",)),
    Node("sde.rest_apis", "REST API Design & Development", 4, 10, "intermediate",
         "Software Design", ("backend",), extra=("sde.dbms_sql",)),
    Node("sde.hld_system_design", "High-Level Design & System Design Basics", 5, 16, "advanced",
         "Software Design", ("design",), extra=("sde.lld_design_patterns", "sde.networks_basics")),
    Node("sde.testing_fundamentals", "Unit Testing & Code Quality", 4, 6, "intermediate",
         "Software Quality", ("quality",)),
    Node("sde.scalability_patterns", "Scalability & Distributed Systems Patterns", 6, 14, "advanced",
         "Software Design", ("design", "stretch"), root="sde.hld_system_design"),
    Node("sde.competitive_patterns", "Competitive Programming Patterns", 5, 12, "advanced",
         "Data Structures & Algorithms", ("dsa", "stretch"), root="sde.dynamic_programming"),
]

# ── Data Analyst track ──────────────────────────────────────────────────────
CHAIN_DATA_ANALYST: list[Node] = [
    Node("da.excel_analysis", "Excel for Data Analysis", 2, 10, "beginner",
         "Data & Databases", ("data", "tools"), root="fnd.computing_basics"),
    Node("da.sql_fundamentals", "SQL Fundamentals", 2, 12, "beginner",
         "Data & Databases", ("data",)),
    Node("da.sql_joins_agg", "SQL Joins, Aggregation & Subqueries", 3, 10, "intermediate",
         "Data & Databases", ("data",)),
    Node("da.advanced_sql", "Advanced SQL: Window Functions & CTEs", 4, 8, "intermediate",
         "Data & Databases", ("data",)),
    Node("da.python_pandas", "Python for Data Analysis (Pandas & NumPy)", 3, 16, "intermediate",
         "Data & Databases", ("data", "programming"), root="fnd.prog_logic"),
    Node("da.data_cleaning", "Data Cleaning & Wrangling", 3, 10, "intermediate",
         "Data & Databases", ("data",)),
    Node("da.descriptive_stats", "Descriptive Statistics", 3, 8, "intermediate",
         "Statistics & Analytics", ("statistics",)),
    Node("da.inferential_stats", "Inferential Statistics & Hypothesis Testing", 4, 12, "intermediate",
         "Statistics & Analytics", ("statistics",)),
    Node("da.visualization_principles", "Data Visualization Principles", 3, 6, "intermediate",
         "Visualization & Storytelling", ("visualization",)),
    Node("da.viz_tools", "Visualization with Matplotlib & Seaborn", 4, 10, "intermediate",
         "Visualization & Storytelling", ("visualization", "tools")),
    Node("da.bi_tools", "Power BI / Tableau Fundamentals", 4, 12, "intermediate",
         "Visualization & Storytelling", ("tools", "visualization")),
    Node("da.storytelling", "Storytelling with Data & Dashboards", 5, 8, "advanced",
         "Visualization & Storytelling", ("communication", "visualization")),
    Node("da.ab_testing", "A/B Testing & Experimentation Basics", 5, 8, "advanced",
         "Statistics & Analytics", ("statistics", "stretch")),
    Node("da.business_metrics", "Business Metrics, KPIs & Domain Context", 4, 6, "intermediate",
         "Business Context", ("business",), root="da.descriptive_stats"),
]

# ── Capgemini Tech (enterprise Java) track ─────────────────────────────────
CHAIN_CAPGEMINI_TECH: list[Node] = [
    Node("cap.java_core", "Java Programming Core", 2, 16, "beginner",
         "Programming & Development", ("programming",), root="fnd.prog_logic"),
    Node("cap.java_oop", "Object-Oriented Programming in Java", 3, 12, "intermediate",
         "Programming & Development", ("programming",)),
    Node("cap.collections_generics", "Collections Framework & Generics", 3, 10, "intermediate",
         "Programming & Development", ("programming",)),
    Node("cap.exceptions_io", "Exception Handling & File I/O", 3, 6, "intermediate",
         "Programming & Development", ("programming",)),
    Node("cap.dbms_normalization", "DBMS Concepts & Normalization", 3, 10, "intermediate",
         "Data & Databases", ("data",)),
    Node("cap.jdbc_db", "JDBC & Database Connectivity", 3, 8, "intermediate",
         "Data & Databases", ("data", "backend"), extra=("cap.dbms_normalization",)),
    Node("cap.spring_core", "Spring Core & Dependency Injection", 4, 12, "intermediate",
         "Software Design", ("backend",)),
    Node("cap.spring_boot_rest", "Spring Boot & REST Microservices", 4, 14, "intermediate",
         "Software Design", ("backend",), extra=("cap.spring_core",)),
    Node("cap.networks_enterprise", "Computer Networks for Enterprise Systems", 3, 8, "intermediate",
         "Systems", ("systems",)),
    Node("cap.agile_scrum", "Agile & Scrum Fundamentals", 2, 5, "beginner",
         "Process & Delivery", ("process",), root="fnd.communication_basics"),
    Node("cap.junit_testing", "Unit Testing with JUnit & Mockito", 4, 6, "intermediate",
         "Software Quality", ("quality",)),
    Node("cap.cloud_fundamentals", "Cloud Fundamentals (Azure)", 3, 10, "intermediate",
         "Cloud & Platform", ("cloud",)),
    Node("cap.genai_basics", "GenAI & Agentic AI Foundations", 3, 10, "intermediate",
         "Emerging Tech", ("genai", "capgemini-priority")),
    Node("cap.client_comm", "Client Communication & Enterprise Etiquette", 3, 5, "intermediate",
         "Communication", ("softskills",)),
]

# ── Data Scientist track ────────────────────────────────────────────────────
CHAIN_DATA_SCIENTIST: list[Node] = [
    Node("ds.python_for_ds", "Python for Data Science", 2, 14, "beginner",
         "Programming & Development", ("programming", "data"), root="fnd.prog_logic"),
    Node("ds.linear_algebra", "Linear Algebra Foundations", 3, 10, "intermediate",
         "Mathematics", ("mathematics",)),
    Node("ds.probability_stats", "Probability & Statistics for ML", 3, 12, "intermediate",
         "Mathematics", ("statistics", "mathematics")),
    Node("ds.eda", "Exploratory Data Analysis", 3, 8, "intermediate",
         "Data & Databases", ("data",)),
    Node("ds.feature_engineering", "Feature Engineering", 4, 10, "intermediate",
         "Machine Learning", ("data", "ml")),
    Node("ds.regression", "Supervised Learning: Regression", 4, 10, "intermediate",
         "Machine Learning", ("ml",), extra=("ds.probability_stats",)),
    Node("ds.classification", "Supervised Learning: Classification", 4, 10, "intermediate",
         "Machine Learning", ("ml",)),
    Node("ds.model_evaluation", "Model Evaluation & Validation", 4, 8, "intermediate",
         "Machine Learning", ("ml",)),
    Node("ds.clustering", "Unsupervised Learning: Clustering & Dimensionality Reduction", 4, 10,
         "intermediate", "Machine Learning", ("ml",)),
    Node("ds.ensemble_methods", "Ensemble Methods (Bagging & Boosting)", 5, 8, "advanced",
         "Machine Learning", ("ml",)),
    Node("ds.neural_networks", "Neural Network Foundations", 4, 12, "intermediate",
         "Deep Learning", ("deep-learning",), extra=("ds.linear_algebra",)),
    Node("ds.cnn", "Deep Learning: CNNs for Vision", 5, 14, "advanced",
         "Deep Learning", ("deep-learning",)),
    Node("ds.transformers_nlp", "Deep Learning: Transformers & NLP", 5, 16, "advanced",
         "Deep Learning", ("deep-learning", "nlp")),
    Node("ds.cloud_for_ml", "Cloud Platforms for Machine Learning", 3, 8, "intermediate",
         "Cloud & Platform", ("cloud", "mlops"), root="ds.eda"),
    Node("ds.mlops", "MLOps & Model Deployment", 5, 12, "advanced",
         "MLOps & Deployment", ("mlops",), root="ds.transformers_nlp", extra=("ds.cloud_for_ml",)),
    Node("ds.ml_system_design", "ML System Design", 6, 14, "advanced",
         "MLOps & Deployment", ("design", "stretch")),
]

# ── Full Stack track ────────────────────────────────────────────────────────
CHAIN_FULL_STACK: list[Node] = [
    Node("fs.html_css", "HTML & CSS Fundamentals", 2, 12, "beginner",
         "Frontend Development", ("frontend",), root="fnd.computing_basics"),
    Node("fs.responsive_design", "Responsive & Accessible Design", 3, 8, "intermediate",
         "Frontend Development", ("frontend",)),
    Node("fs.javascript_core", "JavaScript Fundamentals", 2, 16, "beginner",
         "Frontend Development", ("programming", "frontend")),
    Node("fs.dom_browser", "DOM, Events & Browser APIs", 3, 8, "intermediate",
         "Frontend Development", ("frontend",)),
    Node("fs.es6_async", "Modern JS: ES6+ & Asynchronous Patterns", 3, 10, "intermediate",
         "Frontend Development", ("programming", "frontend")),
    Node("fs.react_core", "React Fundamentals", 3, 14, "intermediate",
         "Frontend Development", ("frontend",)),
    Node("fs.react_hooks_state", "React Hooks & State Management", 4, 12, "intermediate",
         "Frontend Development", ("frontend",)),
    Node("fs.node_express", "Node.js & Express Fundamentals", 3, 12, "intermediate",
         "Backend Development", ("backend",), root="fs.es6_async"),
    Node("fs.rest_apis_node", "REST API Development with Node", 4, 10, "intermediate",
         "Backend Development", ("backend",)),
    Node("fs.nosql_mongo", "MongoDB & NoSQL Fundamentals", 3, 8, "intermediate",
         "Data & Databases", ("data",)),
    Node("fs.auth_security", "Authentication & Authorization", 4, 8, "intermediate",
         "Backend Development", ("backend", "security")),
    Node("fs.git_collab", "Git Collaboration Workflows", 3, 5, "intermediate",
         "Tools & Collaboration", ("tools", "collaboration"), root="fnd.git_basics"),
    Node("fs.deployment_cicd", "Deployment & CI/CD Basics", 4, 8, "intermediate",
         "DevOps & Platform", ("devops",)),
    Node("fs.frontend_perf_testing", "Frontend Performance & Testing", 5, 8, "advanced",
         "Software Quality", ("frontend", "quality")),
]

# ── India placement / aptitude overlay (cross-cutting) ─────────────────────
CHAIN_APTITUDE: list[Node] = [
    Node("apt.quant_arithmetic", "Quantitative Aptitude: Arithmetic", 2, 10, "beginner",
         "Aptitude & Placement", ("aptitude", "placement")),
    Node("apt.quant_algebra_geometry", "Quantitative Aptitude: Algebra & Geometry", 3, 10,
         "intermediate", "Aptitude & Placement", ("aptitude", "placement")),
    Node("apt.logical_patterns", "Logical Reasoning: Patterns & Sequences", 3, 8, "intermediate",
         "Aptitude & Placement", ("aptitude", "placement")),
    Node("apt.logical_puzzles", "Logical Reasoning: Puzzles & Arrangements", 3, 8, "intermediate",
         "Aptitude & Placement", ("aptitude", "placement")),
    Node("apt.verbal_grammar", "Verbal Ability: Grammar & Vocabulary", 2, 8, "beginner",
         "Aptitude & Placement", ("aptitude", "communication"), root="fnd.communication_basics"),
    Node("apt.verbal_comprehension", "Verbal Ability: Reading Comprehension", 3, 6, "intermediate",
         "Aptitude & Placement", ("aptitude", "communication")),
    Node("apt.email_writing", "Email & Professional Writing", 3, 4, "intermediate",
         "Aptitude & Placement", ("communication", "placement"), root="apt.verbal_grammar"),
    Node("apt.gd_hr", "Group Discussion & HR Interview Skills", 4, 6, "intermediate",
         "Aptitude & Placement", ("communication", "placement")),
    Node("apt.resume_linkedin", "Resume Building & LinkedIn Optimization", 3, 5, "intermediate",
         "Career Readiness", ("career", "placement"), root="fnd.communication_basics"),
    Node("apt.star_behavioral", "Behavioral Interviews & STAR Technique", 4, 6, "intermediate",
         "Career Readiness", ("communication", "placement")),
    Node("apt.mock_test_strategy", "Mock Test Strategy & Time Management", 4, 5, "intermediate",
         "Aptitude & Placement", ("aptitude", "placement"),
         extra=("apt.quant_algebra_geometry", "apt.logical_puzzles")),
]

# ── Re-skiller bridge track (non-CS backgrounds) ───────────────────────────
CHAIN_BRIDGE: list[Node] = [
    Node("bridge.math_refresher", "Mathematics Refresher for Tech Careers", 2, 10, "beginner",
         "Bridge & Re-skilling", ("foundation", "mathematics", "bridge")),
    Node("bridge.stats_for_business", "Statistics for Business & Analytics", 3, 8, "intermediate",
         "Bridge & Re-skilling", ("statistics", "bridge")),
    Node("bridge.cs_concepts_bridge", "Core CS Concepts Bridge (for non-CS graduates)", 2, 12,
         "beginner", "Bridge & Re-skilling", ("foundation", "bridge"), root="fnd.computing_basics"),
    Node("bridge.portfolio_projects", "Project Portfolio Building", 5, 14, "advanced",
         "Career Readiness", ("career", "projects")),
    Node("bridge.opensource_basics", "Open Source Contribution Basics", 4, 6, "intermediate",
         "Tools & Collaboration", ("collaboration", "career")),
]

# ── Cross-cutting electives (cloud, GenAI, advanced ops) ───────────────────
# Each one names its own `root` rather than relying on list order: these are
# "pick what is useful to you" add-ons, not a track, and the default chaining
# rule (prerequisite = previous node in the list) would otherwise wire them
# into one accidental sequence - making "Email Etiquette" require Kubernetes
# first. The roots below describe three small, real groupings instead: a
# cloud-to-orchestration line, a GenAI-to-applied-LLM line, and a handful of
# standalone items that only assume the shared foundation.
CHAIN_ELECTIVES: list[Node] = [
    Node("xtra.cloud_computing", "Cloud Computing Fundamentals", 3, 8, "intermediate",
         "Cloud & Platform", ("cloud",), root="fnd.computing_basics"),
    Node("xtra.docker_containers", "Docker & Containers Basics", 4, 8, "intermediate",
         "DevOps & Platform", ("devops", "cloud"), root="xtra.cloud_computing"),
    Node("xtra.kubernetes_basics", "Kubernetes Fundamentals", 5, 10, "advanced",
         "DevOps & Platform", ("devops", "cloud", "stretch"), root="xtra.docker_containers"),
    Node("xtra.technical_writing", "Technical Writing & Documentation", 3, 4, "intermediate",
         "Communication", ("communication",), root="fnd.communication_basics"),
    Node("xtra.genai_prompting", "Generative AI Prompt Engineering", 3, 6, "intermediate",
         "Emerging Tech", ("genai",), root="fnd.prog_logic"),
    Node("xtra.llm_apps_langchain", "Building LLM Apps with LangChain", 5, 12, "advanced",
         "Emerging Tech", ("genai", "stretch"), root="xtra.genai_prompting"),
    Node("xtra.industry_awareness", "Industry Trends & Tech Awareness", 2, 3, "beginner",
         "Career Readiness", ("career",), root="fnd.communication_basics"),
    Node("xtra.email_etiquette_teamwork", "Email Etiquette & Remote Teamwork", 2, 3, "beginner",
         "Communication", ("softskills",), root="fnd.communication_basics"),
]

ALL_CHAINS: dict[str, list[Node]] = {
    "foundation": CHAIN_FOUNDATION,
    "sde": CHAIN_SDE,
    "data_analyst": CHAIN_DATA_ANALYST,
    "capgemini_tech": CHAIN_CAPGEMINI_TECH,
    "data_scientist": CHAIN_DATA_SCIENTIST,
    "full_stack": CHAIN_FULL_STACK,
    "aptitude": CHAIN_APTITUDE,
    "bridge": CHAIN_BRIDGE,
    "electives": CHAIN_ELECTIVES,
}

# Maps a target_role string (as captured at onboarding) to the chains whose
# nodes form that role's required-skill subgraph. "foundation" and "aptitude"
# are folded in for every role because every placement track touches them.
ROLE_TRACKS: dict[str, list[str]] = {
    "Software Development Engineer": ["foundation", "sde", "aptitude"],
    "Data Analyst": ["foundation", "data_analyst", "aptitude"],
    "Capgemini Technology Analyst": ["foundation", "capgemini_tech", "sde", "aptitude"],
    "Data Scientist": ["foundation", "data_scientist", "aptitude"],
    "Full Stack Developer": ["foundation", "full_stack", "aptitude"],
}

ROLE_DISPLAY_DESCRIPTIONS: dict[str, str] = {
    "Software Development Engineer": "Product & platform engineering roles - DSA, system design, backend craft.",
    "Data Analyst": "Insight and reporting roles - SQL, spreadsheets, statistics, dashboards.",
    "Capgemini Technology Analyst": "Enterprise delivery roles on Java/Spring stacks with client-facing GenAI work.",
    "Data Scientist": "Modelling roles - statistics, machine learning, deep learning, MLOps.",
    "Full Stack Developer": "End-to-end web product roles - HTML/JS/React through Node/databases/deploys.",
}
