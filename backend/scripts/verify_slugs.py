"""Verify that every company slug resolves to a live ATS job board."""
import time
import httpx

GREENHOUSE_API = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
ASHBY_API = "https://api.ashbyhq.com/posting-api/job-board/{slug}"

COMPANIES = [
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
    ("Vercel",      "vercel",      "ashby"),
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


def check(client: httpx.Client, name: str, slug: str, ats: str) -> None:
    if ats == "greenhouse":
        url = GREENHOUSE_API.format(slug=slug)
    else:
        url = ASHBY_API.format(slug=slug)

    try:
        r = client.get(url, timeout=10, follow_redirects=True)
        r.raise_for_status()
        body = r.json()
        count = len(body.get("jobs", []))
        print(f"  ✓  {name:<16} ({slug})  —  {count} jobs")
    except httpx.HTTPStatusError as e:
        print(f"  ✗  {name:<16} ({slug})  —  HTTP {e.response.status_code}")
    except Exception as e:
        print(f"  ✗  {name:<16} ({slug})  —  {e}")


if __name__ == "__main__":
    print("Verifying slugs...\n")
    with httpx.Client() as client:
        for name, slug, ats in COMPANIES:
            check(client, name, slug, ats)
            time.sleep(0.5)
    print("\nDone.")
