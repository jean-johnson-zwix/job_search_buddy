import base64
import json
import logging
import os
from datetime import date

import httpx

import datastore.db as db

logger = logging.getLogger(__name__)

RESEND_API_KEY  = os.environ["RESEND_API_KEY"]
DIGEST_EMAIL_TO = os.environ["DIGEST_EMAIL_TO"]
FROM_EMAIL      = os.environ.get("DIGEST_EMAIL_FROM", "digest@yourdomain.com")
RESEND_URL      = "https://api.resend.com/emails"

TIER_LABEL = {
    "faang":   "FAANG",
    "unicorn": "Unicorn",
    "startup": "Startup",
}

TIER_COLOR = {
    "faang":   "#1F4E79",
    "unicorn": "#6B4FBB",
    "startup": "#2E7D32",
}

def send_daily_digest():
    today   = date.today()
    matches = db.get_top_matches(limit=15, run_date=today)

    if not matches:
        logger.warning("No matches found for today — skipping email")
        return

    from ingestion.resume_reader import get_resume
    try:
        resume_text = get_resume()
    except Exception:
        logger.warning("Could not fetch resume — using placeholder")
        resume_text = "[Paste your resume here]"

    md      = generate_claude_prompts(matches, resume_text)
    subject = f"Job Search Buddy: {len(matches)} matches — {today.strftime('%b %d')}"

    _send(subject=subject, markdown=md, matches=matches, today=today)
    logger.info(f"Digest sent to {DIGEST_EMAIL_TO} — {len(matches)} jobs")


def generate_claude_prompts(matches: list[dict], resume_text: str) -> str:
    today = date.today().strftime("%B %d, %Y")

    sections = [
        f"# Job Search Buddy — Claude Resume Prompts",
        f"*Generated: {today} · {len(matches)} matches*\n",
        "## How to use",
        "1. Pick a job below",
        "2. Copy the entire section (from `---` to the next `---`)",
        "3. Paste into [Claude.ai](https://claude.ai)",
        "4. Claude will rewrite your resume bullets for that role\n",
    ]

    for i, m in enumerate(matches, 1):
        job          = m.get("jobs", {}) or {}
        company      = job.get("companies", {}) or {}
        title        = job.get("title", "")
        company_name = company.get("name", "")
        apply_url    = job.get("apply_url", "")
        description  = (job.get("description", "") or "").strip()
        summary      = m.get("summary", "")
        gaps         = m.get("gap_skills", [])    or []
        greens       = m.get("green_flags", [])   or []
        matched      = m.get("matched_skills", []) or []
        skill_fit    = m.get("skill_fit", 0)
        role_fit     = m.get("role_fit", 0)
        exp_fit      = m.get("experience_fit", 0)
        final        = m.get("final_score", 0)
        posted       = (job.get("posted_at", "") or "")[:10]
        location     = job.get("location", "")
        remote       = job.get("remote", False)
        location_str = f"{location} (Remote)" if remote else location

        gap_str     = ", ".join(gaps)    if gaps    else "none"
        green_str   = ", ".join(greens)  if greens  else "none"
        matched_str = ", ".join(matched) if matched else "none"

        section = f"""---

## #{i} {title} @ {company_name}

| | |
|---|---|
| **Apply** | {apply_url} |
| **Location** | {location_str} |
| **Posted** | {posted} |
| **Scores** | skill:{skill_fit}% · role:{role_fit}% · exp:{exp_fit}% · final:{final} |
| **Matched skills** | {matched_str} |
| **Gaps** | {gap_str} |
| **Green flags** | {green_str} |

**AI summary:** {summary}

### Job Description

{description}

### My Resume

{resume_text}

### Claude Prompt
I need help optimizing my resume for this job posting. 
Please analyze the job description and help me tailor my resume to maximize ATS compatibility and recruiter appeal.
---
JOB DESCRIPTION:
I am applying for the {title} role at {company_name}.
{description}
---
MY CURRENT RESUME/EXPERIENCE:
{resume_text}
---
INSTRUCTIONS:
1. Extract all required skills, preferred skills, and important keywords from the job description
2. Identify which of my experiences and skills are most relevant
3. Create a professional summary (2-3 sentences) that:
   - Includes 5-7 key keywords from the job description
   - Highlights my most relevant skills and quantifiable achievements
   - Matches the tone and level of the position
4. List any critical missing keywords or skills I should add if I have them
Using the job description and my resume above, please:
1. Rewrite my resume bullets to best match this role
2. Emphasize these strengths the JD values: {green_str}
3. Address these gaps where I have adjacent experience: {gap_str}
4. Keep all bullets specific, quantified, and honest — do not invent experience
---
RETURN FORMAT
- Optimized professional summary
- Rewritten bullet points for each role
- Skills section with categorized technical and soft skills
- Gap analysis (what's missing)
- Overall ATS compatibility score and tips
"""
        sections.append(section)

    sections.append("---")
    return "\n".join(sections)

def _send(subject: str, markdown: str, matches: list[dict], today: date):
    payload = {
        "from":    FROM_EMAIL,
        "to":      [DIGEST_EMAIL_TO],
        "subject": subject,
        "html":    _build_summary_html(matches, today),
        "attachments": [
            {
                "filename": f"claude_prompts_{today.isoformat()}.md",
                "content":  base64.b64encode(markdown.encode()).decode(),
            }
        ],
    }
    try:
        r = httpx.post(
            RESEND_URL,
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type":  "application/json",
            },
            content=json.dumps(payload),
            timeout=30,
        )
        r.raise_for_status()
        logger.info(f"Resend response: {r.json()}")
    except httpx.HTTPStatusError as e:
        logger.error(f"Resend error {e.response.status_code}: {e.response.text}")
        raise

def _build_summary_html(matches: list[dict], today: date) -> str:
    rows = ""
    for i, m in enumerate(matches, 1):
        job          = m.get("jobs", {}) or {}
        company      = job.get("companies", {}) or {}
        title        = job.get("title", "")
        company_name = company.get("name", "")
        apply_url    = job.get("apply_url", "")
        location     = job.get("location", "")
        remote       = job.get("remote", False)
        posted       = (job.get("posted_at", "") or "")[:10] or "—"
        seniority    = job.get("seniority", "")
        tier         = (company.get("tier", "") or "").lower()
        skill_fit    = m.get("skill_fit", 0)
        role_fit     = m.get("role_fit", 0)
        exp_fit      = m.get("experience_fit", 0)
        gaps         = m.get("gap_skills", [])   or []
        greens       = m.get("green_flags", [])  or []
        summary      = m.get("summary", "")

        location_str = f"{location} · Remote" if remote else location

        # Skill fit color
        if skill_fit >= 80:
            fit_color = "#2E7D32"
            fit_bg    = "#E8F5E9"
        elif skill_fit >= 60:
            fit_color = "#E65100"
            fit_bg    = "#FFF3E0"
        else:
            fit_color = "#C62828"
            fit_bg    = "#FFEBEE"

        tier_color = TIER_COLOR.get(tier, "#555")
        tier_label = TIER_LABEL.get(tier, tier.upper() if tier else "")

        gap_html = (
            f'<span style="color:#C62828;font-size:12px;">⚠ Gaps: {", ".join(gaps[:4])}</span>'
            if gaps else
            '<span style="color:#2E7D32;font-size:12px;">✓ No hard gaps</span>'
        )

        green_html = (
            f'<span style="color:#1565C0;font-size:12px;">✓ {" · ".join(greens[:3])}</span>'
            if greens else ""
        )

        apply_btn = (
            f'<a href="{apply_url}" target="_blank" '
            f'style="display:inline-block;background:#1F4E79;color:#fff;'
            f'padding:6px 16px;border-radius:4px;text-decoration:none;'
            f'font-size:12px;white-space:nowrap;">Apply →</a>'
            if apply_url else
            '<span style="color:#999;font-size:12px;">No link</span>'
        )

        rows += f"""
        <tr style="border-bottom:1px solid #eee;">

          <!-- Rank -->
          <td style="padding:14px 8px;text-align:center;vertical-align:top;">
            <span style="font-size:18px;font-weight:700;color:#1F4E79;">#{i}</span>
          </td>

          <!-- Job details -->
          <td style="padding:14px 8px;vertical-align:top;">
            <div style="font-weight:600;font-size:15px;color:#1a1a1a;margin-bottom:2px;">
              {title}
            </div>
            <div style="margin-bottom:4px;">
              <span style="font-weight:600;color:{tier_color};font-size:13px;">
                {company_name}
              </span>
              &nbsp;
              <span style="background:{tier_color};color:#fff;font-size:10px;
                           padding:2px 6px;border-radius:10px;font-weight:600;">
                {tier_label}
              </span>
              &nbsp;
              <span style="color:#888;font-size:12px;">{seniority}</span>
            </div>
            <div style="color:#888;font-size:12px;margin-bottom:6px;">
              📍 {location_str} &nbsp;·&nbsp; 📅 {posted}
            </div>
            <div style="margin-bottom:4px;">{gap_html}</div>
            <div style="margin-bottom:6px;">{green_html}</div>
            <div style="font-size:12px;color:#555;font-style:italic;
                        border-left:3px solid #ddd;padding-left:8px;margin-top:6px;">
              {summary}
            </div>
          </td>

          <!-- Scores -->
          <td style="padding:14px 8px;text-align:center;vertical-align:top;
                     white-space:nowrap;">
            <div style="background:{fit_bg};border-radius:8px;padding:8px 12px;
                        display:inline-block;">
              <span style="font-size:22px;font-weight:700;color:{fit_color};">
                {skill_fit}%
              </span>
              <div style="font-size:10px;color:#888;margin-top:2px;">skill fit</div>
            </div>
            <div style="font-size:11px;color:#888;margin-top:6px;">
              role: {role_fit}%<br>exp: {exp_fit}%
            </div>
          </td>

          <!-- Apply -->
          <td style="padding:14px 8px;text-align:center;vertical-align:top;">
            {apply_btn}
          </td>

        </tr>
        """

    return f"""<!DOCTYPE html>
<html>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
             max-width:720px;margin:0 auto;padding:24px;color:#1a1a1a;
             background:#f9f9f9;">

  <!-- Header -->
  <div style="background:#1F4E79;border-radius:10px;padding:24px 28px;margin-bottom:24px;">
    <h2 style="color:#fff;margin:0 0 4px;">Job Search Buddy</h2>
    <p style="color:#B3CDE8;margin:0;font-size:14px;">
      {today.strftime("%A, %B %d %Y")} &nbsp;·&nbsp;
      {len(matches)} matches ranked by fit + recency + tier
    </p>
  </div>

  <!-- Job table -->
  <div style="background:#fff;border-radius:10px;overflow:hidden;
              box-shadow:0 1px 4px rgba(0,0,0,0.08);">
    <table style="width:100%;border-collapse:collapse;">
      <thead>
        <tr style="background:#F5F7FA;border-bottom:2px solid #E8ECF0;">
          <th style="padding:10px 8px;text-align:center;color:#666;
                     font-size:12px;width:36px;">#</th>
          <th style="padding:10px 8px;text-align:left;color:#666;font-size:12px;">
            Role &amp; Company</th>
          <th style="padding:10px 8px;text-align:center;color:#666;
                     font-size:12px;width:80px;">Fit</th>
          <th style="padding:10px 8px;text-align:center;color:#666;
                     font-size:12px;width:70px;">Apply</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
  </div>

  <!-- Attachment nudge -->
  <div style="background:#EEF4FF;border-radius:10px;border-left:4px solid #1F4E79;
              padding:16px 20px;margin:20px 0;">
    <p style="margin:0;font-size:13px;color:#444;line-height:1.6;">
      <strong>📎 Attached:</strong> <code>claude_prompts.md</code><br>
      Open → pick a job section → paste into
      <a href="https://claude.ai" style="color:#1F4E79;font-weight:600;">Claude.ai</a>
      → get tailored resume bullets in seconds.
    </p>
  </div>

  <!-- Dashboard link -->
  <p style="text-align:center;font-size:13px;color:#888;margin-top:16px;">
    Full trends and skill gaps →
    <a href="https://your-dashboard-url.vercel.app"
       style="color:#1F4E79;font-weight:600;">Open dashboard</a>
  </p>

  <p style="text-align:center;font-size:11px;color:#bbb;margin-top:24px;">
    Job Search Buddy · Gemini + Supabase · auto-generated daily at 7am MST
  </p>

</body>
</html>"""