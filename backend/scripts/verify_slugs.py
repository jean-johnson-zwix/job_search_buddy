"""Verify that every company slug resolves to a live ATS job board."""
import time
import httpx

GREENHOUSE_API = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
ASHBY_API = "https://api.ashbyhq.com/posting-api/job-board/{slug}"

EXISTING = [
    # (name, slug, ats)
    # FAANG — Greenhouse
    ("Stripe",      "stripe",      "greenhouse"),
    ("Airbnb",      "airbnb",      "greenhouse"),
    ("Lyft",        "lyft",        "greenhouse"),
    ("Dropbox",     "dropbox",     "greenhouse"),
    ("Reddit",      "reddit",      "greenhouse"),
    ("Robinhood",   "robinhood",   "greenhouse"),
    ("Cloudflare",  "cloudflare",  "greenhouse"),
    ("Databricks",  "databricks",  "greenhouse"),
    ("Coinbase",    "coinbase",    "greenhouse"),
    # Unicorn — Greenhouse
    ("Anthropic",   "anthropic",   "greenhouse"),
    ("Brex",        "brex",        "greenhouse"),
    ("Datadog",     "datadog",     "greenhouse"),
    ("Asana",       "asana",       "greenhouse"),
    ("Grammarly",   "grammarly",   "greenhouse"),
    ("Scale AI",    "scaleai",     "greenhouse"),
    ("Chime",       "chime",       "greenhouse"),
    ("Gusto",       "gusto",       "greenhouse"),
    ("Airtable",    "airtable",    "greenhouse"),
    # Unicorn — Ashby
    ("Vercel",      "vercel",      "ashby"),       # suspected wrong ATS — should be greenhouse
    ("Linear",      "linear",      "ashby"),
    ("Retool",      "retool",      "ashby"),
    ("Replit",      "replit",      "ashby"),
    ("Mercury",     "mercury",     "ashby"),
    ("Perplexity",  "perplexity",  "ashby"),
    # Startup — Ashby
    ("Raycast",     "raycast",     "ashby"),
    ("Posthog",     "posthog",     "ashby"),
    ("Supabase",    "supabase",    "ashby"),
]

# Corrections to existing entries — previously failed or wrong ATS
CORRECTIONS = [
    ("Vercel (GH)",         "vercel",               "greenhouse"),   # fix: move from Ashby
    ("OpenAI",              "openai",               "ashby"),        # fix: was on GH, moved to Ashby
    ("Notion",              "notion",               "ashby"),        # fix: was on GH, moved to Ashby
    ("Ramp",                "ramp",                 "ashby"),        # fix: correct ATS
    ("Confluent",           "confluent",            "ashby"),        # fix: correct ATS
    ("Deel",                "deel",                 "ashby"),        # fix: correct ATS
    ("Miro",                "realtimeboardglobal",  "greenhouse"),   # fix: non-obvious slug
]

# Net-new companies to evaluate
CANDIDATES = [
    # FAANG — Greenhouse
    ("DoorDash",        "doordashusa",          "greenhouse"),
    ("MongoDB",         "mongodb",              "greenhouse"),
    ("Twilio",          "twilio",               "greenhouse"),
    ("Okta",            "okta",                 "greenhouse"),
    # FAANG — Ashby
    ("Snowflake",       "snowflake",            "ashby"),
    # Unicorn — Greenhouse
    ("Figma",           "figma",                "greenhouse"),
    ("Duolingo",        "duolingo",             "greenhouse"),
    ("Instacart",       "instacart",            "greenhouse"),
    ("PagerDuty",       "pagerduty",            "greenhouse"),
    ("HashiCorp",       "hashicorp",            "greenhouse"),
    ("Affirm",          "affirm",               "greenhouse"),
    ("Together AI",     "togetherai",           "greenhouse"),
    # Unicorn — Ashby
    ("Cursor",          "cursor",               "ashby"),
    ("Cohere",          "cohere",               "ashby"),
    ("Anyscale",        "anyscale",             "ashby"),
    ("ElevenLabs",      "elevenlabs",           "ashby"),
    ("Character.AI",    "character",            "ashby"),
    # Startup — Greenhouse
    ("Warp Terminal",   "warp",                 "greenhouse"),
    ("Descript",        "descript",             "greenhouse"),
    # Startup — Ashby
    ("Modal",           "modal",                "ashby"),
    ("LangChain",       "langchain",            "ashby"),
    ("Cognition",       "cognition",            "ashby"),
    ("Harvey",          "harvey",               "ashby"),
    ("Writer",          "writer",               "ashby"),
]


def check(client: httpx.Client, name: str, slug: str, ats: str) -> tuple[bool, int]:
    url = GREENHOUSE_API.format(slug=slug) if ats == "greenhouse" else ASHBY_API.format(slug=slug)
    try:
        r = client.get(url, timeout=10, follow_redirects=True)
        r.raise_for_status()
        count = len(r.json().get("jobs", []))
        print(f"  ✓  {name:<22} ({ats:<12} {slug})  —  {count} jobs")
        return True, count
    except httpx.HTTPStatusError as e:
        print(f"  ✗  {name:<22} ({ats:<12} {slug})  —  HTTP {e.response.status_code}")
        return False, 0
    except Exception as e:
        print(f"  ✗  {name:<22} ({ats:<12} {slug})  —  {e}")
        return False, 0


if __name__ == "__main__":
    with httpx.Client() as client:
        print("=" * 60)
        print("EXISTING COMPANIES")
        print("=" * 60)
        for name, slug, ats in EXISTING:
            check(client, name, slug, ats)
            time.sleep(0.3)

        print()
        print("=" * 60)
        print("CORRECTIONS (wrong ATS or slug)")
        print("=" * 60)
        for name, slug, ats in CORRECTIONS:
            check(client, name, slug, ats)
            time.sleep(0.3)

        print()
        print("=" * 60)
        print("CANDIDATES (new)")
        print("=" * 60)
        passed, failed = [], []
        for name, slug, ats in CANDIDATES:
            ok, count = check(client, name, slug, ats)
            (passed if ok else failed).append((name, slug, ats, count))
            time.sleep(0.3)

        print()
        print("=" * 60)
        print(f"CANDIDATES SUMMARY  —  {len(passed)} passed / {len(failed)} failed")
        print("=" * 60)
        if passed:
            print("\n  Ready to add:")
            for name, slug, ats, count in passed:
                print(f"    {name:<22} {ats:<12} {slug}  ({count} jobs)")
        if failed:
            print("\n  Failed — skip or investigate:")
            for name, slug, ats, _ in failed:
                print(f"    {name:<22} {ats:<12} {slug}")

        print("\nDone.")
