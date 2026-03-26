from datetime import datetime, timezone

TIER_WEIGHT = {
    "faang":   1.0,
    "unicorn": 0.7,
    "startup": 0.5,
}

def compute_final_score(
    skill_fit: int,
    role_fit: int,
    experience_fit: int,
    posted_at: str | None,
    company_tier: str,        # "faang" | "unicorn" | "startup"
) -> float:
    match_score = (skill_fit * 0.50 + role_fit * 0.30 + experience_fit * 0.20) / 100

    recency = 1.0
    if posted_at:
        try:
            days_ago = (
                datetime.now(timezone.utc)
                - datetime.fromisoformat(str(posted_at))
            ).days
            recency = 1.0 if days_ago == 0 else 0.7 if days_ago <= 7 else 0.5
        except Exception:
            recency = 0.7

    tier = TIER_WEIGHT.get(str(company_tier).lower(), 0.5)

    return round(
        (match_score * 0.50) +
        (recency     * 0.30) +
        (tier        * 0.12),
        4
    )