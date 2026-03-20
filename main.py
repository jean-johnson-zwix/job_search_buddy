import time
import logging
from dotenv import load_dotenv
load_dotenv()

from pipeline.graph import build_pipeline

# logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

if __name__ == "__main__":
    start = time.perf_counter()
    logging.info("JOB SEARCH BUDDY waking up")
    pipeline = build_pipeline()
    result = pipeline.invoke({
        "companies":        [],
        "candidate_skills": [],
        "already_scored":   set(),
        "new_jobs":         [],
        "known_jobs":       [],
        "extracted_jobs":   [],
        "matched_jobs":     [],
        "stats":  {"fetched": 0, "new": 0, "known": 0,
                "extracted": 0, "matched": 0, "skipped": 0},
        "errors": [],
    })
    
    #calculate time
    elapsed = time.perf_counter() - start
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    s = result.get("stats", {})
    e = result.get("errors", [])
    logging.info(
        f"JOB SEARCH BUDDY GOT THE JOB DONE in {minutes}m {seconds}s — "
        f"fetched:{s.get('fetched',0)} "
        f"extracted:{s.get('extracted',0)} "
        f"matched:{s.get('matched',0)} "
        f"skipped:{s.get('skipped',0)} "
        f"errors:{len(e)}"
    )