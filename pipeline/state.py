from typing import TypedDict


class PipelineState(TypedDict):
    
    # load at start
    companies: list[dict] 
    candidate_skills: list[str]
    job_resume_match_prompt: str
    already_scored: set

    # ingestion_node: retrieve and filter nodes
    new_jobs: list[dict]
    known_jobs: list[dict]

    # extraction_node: extract skills for each jobs
    extracted_jobs: list[dict]

    # matcher_node: match jobs to resume
    matched_jobs: list[dict]

    # diagnostics:
    states: dict
    errors: list
