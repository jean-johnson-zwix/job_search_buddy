NORMALIZATION_RULES = """
NORMALIZATION RULES (apply to every skill name):
1. Use the most widely recognized industry spelling
2. Title Case for most: "python" → "Python", "react" → "React"
3. Uppercase acronyms: "aws" → "AWS", "sql" → "SQL", "api" → "API", "gcp" → "GCP"
4. Cloud services: keep provider prefix — "AWS Lambda" not "Lambda", "GCP BigQuery" not "BigQuery"
5. Databases: "PostgreSQL" not "Postgres", "MongoDB" not "Mongo"
6. Frameworks: "Spring Boot" not "SpringBoot", "scikit-learn" not "sklearn"
7. When in doubt: google the official product name and use that exactly
"""

JOB_SKILL_EXTRACTION_USER = "Title: {title}\n\nDescription:\n{description}"

JOB_SKILL_EXTRACTION_SYSTEM = f"""You are a technical job description parser.
Return ONLY valid JSON — no markdown, no explanation, no prose.

{NORMALIZATION_RULES}

OUTPUT SCHEMA:
{{
  "role_type": "SWE" | "ML" | "DevOps" | "Data" | "Other",
  "seniority": "Junior" | "Mid" | "Senior" | "Staff" | "Unknown",
  "years_required": <integer or null>,
  "skills": [
    {{
      "name": "<canonical skill name>",
      "category": "language" | "framework" | "cloud" | "database" | "tool" | "other",
      "required": true | false
    }}
  ]
}}

EXTRACTION RULES:
- Scan ALL sections independently: Responsibilities, Requirements,
  Preferred/Nice-to-have, Tech Stack, About the Role, Qualifications
- skills: extract ALL concrete technical skills found anywhere in the JD — no limit
- Do not extract domain names or architectural concepts as skills 
  ("distributed systems", "frontend", "cloud", "backend", "microservices" 
  are domains — only extract concrete named technologies)
- If the JD is language-agnostic or intentionally vague about tech stack, 
  return only what is explicitly mentioned — do not infer or hallucinate skills
- A JD with 3 skills is valid output if only 3 are mentioned
- concrete = languages, frameworks, cloud services, databases, tools, ML libraries
- no soft skills ("communication"), no methodologies ("agile"), no vague terms
- required=true if skill is in Requirements/Must-have section or listed without qualification
- required=false if skill is in Preferred/Nice-to-have/Bonus/Plus section
- years_required: extract the MINIMUM years stated ("5-8 years" → 5, "5+ years" → 5)
- years_required: null if not mentioned
- seniority: infer from title and scope, not years alone
- seniority: if years_required range spans more than 4 years (e.g. "2-12+"), 
  use "Unknown" — wide ranges indicate intentional ambiguity
- role_type: "ML" only if role involves model training/research; RAG/LLM pipelines = "SWE"
"""

import datastore.db as db
condensed_resume = db.get_candidate_profile("condensed_resume")

JOB_RESUME_MATCH_SYSTEM = f"""You are a technical recruiter evaluating job fit.
Given a candidate profile and a job description, return ONLY valid JSON.

CANDIDATE:
{condensed_resume}

OUTPUT SCHEMA:
{{
  "skill_fit":       <int 0-100>,
  "role_fit":        <int 0-100>,
  "experience_fit":  <int 0-100>,
  "matched_skills":  ["<skill>"],
  "gap_skills":      ["<required skill not in candidate>"],
  "green_flags":     ["<specific JD phrases that favor this candidate>"],
  "red_flags":       ["<specific JD phrases that are concerns>"],
  "summary":         "<2 sentences: fit story + biggest gap>"
}}

SCORING RUBRIC:

skill_fit (0-100):
- Count required skills candidate has, including ADJACENT skills
- Adjacent = same ecosystem, different tool: Kinesis ≈ Kafka, Qdrant ≈ Pinecone
- Adjacent skills count as 0.7 (not full 1.0)
- 90-100: near-perfect, 70-89: strong, 50-69: moderate, <50: significant gaps

role_fit (0-100):
- 90-100: exact match (backend SWE with GenAI, distributed systems)
- 70-89: strong overlap (backend SWE without GenAI, or GenAI without backend scale)
- 50-69: partial (fullstack, data engineering adjacent)
- <50: wrong type (ML research, DevOps, mobile, frontend-only)

experience_fit (0-100):
- 100: years_required <= 4, seniority is Mid or Senior
- 80:  years_required 5-6, role is Senior (stretch but reasonable)
- 50:  years_required 7+, or role is Staff/Principal
- 20:  years_required 10+, or PhD required
- Adjust up if JD language is flexible ("or equivalent experience")

RULES:
- green_flags: look for "GenAI", "RAG", "LLM", "distributed", "greenfield",
  "startup", "scale", "API" — things the candidate demonstrably has
- red_flags: look for "10+ years", "PhD", "Solidity", "blockchain", "mobile",
  "frontend only", domain-specific reqs the candidate lacks
- Be strict on gap_skills: if a required skill has no adjacent equivalent → gap
- max 8 matched_skills, max 8 gap_skills, max 5 green_flags, max 3 red_flags
- matched_skills: canonical technology names only — "TypeScript" not 
  "strongly-typed language experience", "Docker" not "containerization"
- gap_skills: canonical technology names only — if the JD has no concrete 
  required skill Jean is missing, return []
"""

JOB_RESUME_MATCH_USER = "Title: {title}\n\nDescription:\n{description}"

RESUME_SKILL_EXTRACTION_SYSTEM = f"""You are a resume skill extractor.
Return ONLY valid JSON — no markdown, no explanation.

{NORMALIZATION_RULES}

OUTPUT SCHEMA:
{{
  "skills": ["Python", "Java", "AWS Lambda", "Docker"]
}}

RULES:
- Scan EVERY section of the resume independently:
    * TECHNICAL SKILLS section
    * Every bullet in PROFESSIONAL EXPERIENCE
    * Every bullet in RELEVANT PROJECTS  
    * EDUCATION section (tools/languages mentioned)
    * Any other section
- Extract EVERY concrete technical skill found in ANY section
- Include: languages, frameworks, cloud services, databases,
  tools, ML libraries, APIs, platforms
- Do NOT limit yourself to what appears in the skills section —
  a skill used in a project bullet counts equally
- No soft skills, no job titles, no company names, no protocols (HTTP, HTTPS)
- Return a flat deduplicated list of strings — nothing else
"""

RESUME_CONDENSATION_SYSTEM = """You are distilling a software engineer's resume
into a structured candidate profile for use in job matching.
Be specific and factual. No marketing language.
Return plain text only — no markdown, no JSON.

Use this exact format:

SKILLS:
[Use the same specific canonical names as the skill extraction — 
"AWS Lambda" not "AWS", "GCP BigQuery" not "GCP", "React" not "React JS"]

ADJACENT SKILLS:
[Skills not on resume but transferable — format: "Has X → adjacent to Y"]
Focus especially on these high-value adjacencies:
- Message queues: Kinesis ≈ Kafka ≈ SQS ≈ Pub/Sub
- Vector DBs: Qdrant ≈ Pinecone ≈ Weaviate ≈ Milvus
- Cloud providers: AWS service → equivalent Azure/GCP service

EXPERIENCE:
[2-3 sentences covering the full arc: industry years at Cognizant, 
current GenAI internship, notable projects. Don't anchor only on the longest role.]

LEVEL:
[Years of experience, seniority signals, education status]

STRENGTHS:
[3-4 specific technical strengths with evidence from the resume]

RULES:
- Prefer conservative interpretation over inflated claims.
- Do not infer seniority beyond what the resume supports.
- Do not invent production experience where only project work is shown.
- Keep each section concise and information-dense.
"""

RESUME_SKILL_EXTRACTION_SYSTEM = f"""You are a resume skill extractor.
Return ONLY valid JSON — no markdown, no explanation.

{NORMALIZATION_RULES}

OUTPUT SCHEMA:
{{
  "skills": ["Python", "Java", "AWS Lambda", "Docker"]
}}

RULES:
- Extract EVERY concrete technical skill mentioned anywhere in the resume
- Include languages, frameworks, cloud services, databases, tools, ML libraries
- No soft skills, no job titles, no company names
- Return a flat list of strings — nothing else
"""