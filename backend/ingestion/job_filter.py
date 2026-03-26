import re
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

STALE_DAYS = 30

_SPONSORSHIP_DENIAL_RE = re.compile(
    r"no sponsorship"
    r"|no visa sponsorship"
    r"|will not provide sponsorship"
    r"|sponsorship is not available"
    r"|must be authorized to work in the US without sponsorship"
    r"|authorization to work in the United States without employer sponsorship"
    r"|not able to provide sponsorship"
    r"|candidates who do not require sponsorship"
    r"|without current or future sponsorship",
    re.IGNORECASE,
)


def is_fresh(job: dict) -> bool:
    """Return True if posted_at is within STALE_DAYS, or None/missing, or unparseable."""
    posted_at = job.get("posted_at")
    if not posted_at:
        return True
    try:
        dt = datetime.fromisoformat(posted_at)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=STALE_DAYS)
        return dt >= cutoff
    except Exception:
        return True


def requires_sponsorship_denial(job: dict) -> bool:
    """Return True if the job description explicitly denies visa sponsorship."""
    description = job.get("description") or ""
    if not description:
        return False
    return bool(_SPONSORSHIP_DENIAL_RE.search(description))

EXCLUDE_SENIORITY = [
    r"\bstaff\b",
    r"\bprincipal\b",
    r"\bvp\b",
    r"\bvice president\b",
    r"\bdirector\b",
    r"\bhead of\b",
    r"\bchief\b",
    r"\bcto\b", r"\bcoo\b", r"\bceo\b",
    r"\blead\b",
    r"\bmanager\b",
    r"\bdistinguished\b",       # Distinguished Engineer = Fellow-level
    r"\bsr\.?\s+director\b",    # Sr. Director
]


IRRELEVANT_PRIMARY = [
    # sales & GTM
    r"\baccount executive\b",
    r"\baccount manager\b",
    r"\bsales\b",
    r"\bbusiness development\b",
    r"\bsolutions engineer\b",      # pre-sales
    r"\bsolutions architect\b",     # pre-sales
    r"\bspecialist solutions\b",
    r"\bforward deployed\b",        # GTM engineering
    r"\bpresales\b",
    r"\bpartner solutions\b",
    r"\bfield engineer\b",          # field/implementation
    r"\bscale solution\b",
    r"\bdeveloper relations\b",     # DevRel ≠ eng
    # marketing
    r"\bmarketing\b",
    r"\bcontent\b",
    r"\bcopywriter\b",
    r"\bseo\b",
    r"\bcampaign\b",
    r"\bbrand\b",
    # finance / legal / admin
    r"\bfinance\b",
    r"\baccounting\b",
    r"\baccountant\b",
    r"\bpayroll\b",
    r"\bcontroller\b",
    r"\bparalegal\b",
    r"\bcounsel\b",
    r"\blegal\b",
    r"\bcompliance\b",
    r"\btax\b",
    r"\btreasury\b",
    r"\baudit\b",
    r"\bequity administrator\b",
    # people / recruiting
    r"\brecruit\b",
    r"\btalent acquisition\b",
    r"\btalent attraction\b",
    r"\bhuman resources\b",
    r"\bhr\b",
    r"\bpeople partner\b",
    r"\bpeople ops\b",
    r"\bpeople process\b",
    r"\bbenefits partner\b",
    # operations / admin
    r"\boffice manager\b",
    r"\bexecutive assistant\b",
    r"\bchief of staff\b",
    r"\boperations program\b",
    r"\boperations manager\b",
    r"\boperations specialist\b",
    r"\bprogram manager\b",
    r"\bproject manager\b",
    r"\btechnical program manager\b",
    r"\btechnical project manager\b",
    # design / UX
    r"\bdesigner\b",
    r"\bux\b",
    r"\bui designer\b",
    r"\bgraphic\b",
    r"\bcreative\b",
    r"\bproduct design\b",
    # support / customer
    r"\bcustomer success\b",
    r"\bcustomer service\b",
    r"\bcustomer support\b",
    r"\bsupport specialist\b",
    r"\bsupport enablement\b",
    r"\bsupport engineer\b",        # technical support / database support
    r"\bcustomer reliability\b",
    # product / strategy / non-eng
    r"\bproduct manager\b",
    r"\bproduct lead\b",
    r"\bproduct marketing\b",
    r"\bstrategy\b",
    r"\banalytics\b",
    r"\bdata analyst\b",
    r"\bdata governance\b",
    r"\bresearch analyst\b",
    r"\buser researcher\b",
    r"\bdata science manager\b",
    # clearly non-software
    r"\bbroadcast\b",
    r"\bav engineer\b",             # audio/visual
    r"\bnetwork engineer\b",        # network ops ≠ software
    r"\bservicenow\b",              # IT service management platform
    r"\bsalesforce engineer\b",     # CRM admin ≠ software eng
    r"\bkyc\b",
    r"\bspecialist\b",
    r"\bpartnerships\b",
    r"\balliances\b",
    r"\bcommunity\b",
    r"\bsocial\b",
    r"\bpolicy\b",
    r"\bprocurement\b",
    r"\bsourcing\b",
    # irrelivant engineer
    r"\bsecurity engineer\b",
    r"\bprivacy engineer\b",
    r"\bblockchain\b",
    r"\bios engineer\b",
    r"\bandroid engineer\b",
    r"\bios software\b",
    r"\bandroid software\b",
    r"\bmobile engineer\b",
    r"\bweb engineer\b",
    r"\bdevops engineer\b",
    r"\bdevops\b",
]

RELEVANT_PRIMARY = [
    # explicit engineering titles
    r"\bsoftware engineer\b",
    r"\bbackend engineer\b",
    r"\bfrontend engineer\b",
    r"\bfull.?stack\b",
    r"\bplatform engineer\b",
    r"\binfrastructure engineer\b",
    r"\binfrastructure software\b",
    r"\bsite reliability\b",
    r"\bsre\b",
    r"\bcloud engineer\b",
    r"\bdata engineer\b",
    r"\bmachine learning engineer\b",
    r"\bml engineer\b",
    r"\bml systems\b",
    r"\bai engineer\b",
    r"\bapplied scientist\b",
    r"\bapplied ai\b",
    r"\bresearch engineer\b",
    r"\bresearch scientist\b",
    r"\bdata scientist\b",
    r"\bmlops\b",
    # broad catch-all — trust IRRELEVANT to block non-eng
    r"\bengineer\b",
    r"\bplatform\b",
    r"\binfrastructure\b",
    r"\bdistributed systems\b",
    # language/tech in primary title
    r"\bgolang\b",              # NOT \bgo\b — too noisy
    r"\brust\b",
    r"\bjava\b",
    r"\bpython\b",
    r"\belixir\b",
    r"\bllm\b",
    r"\bgenai\b",
    r"\bgenerative ai\b",
    r"\brag\b",
]



def _primary(title: str) -> str:
    part = re.split(r",|\s+-\s+", title)[0]
    return part.strip().lower()


def is_relevant(title: str) -> bool:
    full    = title.lower()
    primary = _primary(title)

    # 1. Seniority gate 
    for pat in EXCLUDE_SENIORITY:
        if re.search(pat, full):
            return False

    # 2. Role gate 
    for pat in IRRELEVANT_PRIMARY:
        if re.search(pat, primary):
            return False

    # 3. Keep recognisable engineering primary roles
    for pat in RELEVANT_PRIMARY:
        if re.search(pat, primary):
            return True

    return False

_US_SIGNALS = [
    r"\bUS\b", r"\bU\.S\b", r"United States",
    r"\bremote\b", r"\banywhere\b",
    r"\bSF\b", r"\bSEA\b", r"\bNYC\b", r"\bNY\b", r"\bCHI\b",
    r"\bATL\b", r"\bDC\b", r"\bLA\b",
    r"San Francisco", r"Seattle", r"New York", r"Chicago",
    r"Atlanta", r"Austin", r"Boston", r"Denver", r"Washington",
    r"California", r"Texas", r"Hawaii",
    r"\bNA\b", r"North America",
]

_NON_US_SIGNALS = [
    r"Dublin", r"London", r"Bengaluru", r"Bangalore", r"Toronto",
    r"Singapore", r"Tokyo", r"Sydney", r"Melbourne", r"Paris",
    r"Berlin", r"Munich", r"Amsterdam", r"Barcelona", r"Madrid",
    r"Stockholm", r"Luxembourg", r"Bucharest", r"Romania",
    r"Mexico City", r"CDMX",
    r"\bCanada\b", r"\bIndia\b", r"\bIreland\b", r"\bUK\b",
    r"\bGermany\b", r"\bFrance\b", r"\bSpain\b", r"\bJapan\b",
    r"\bAustralia\b", r"\bBrazil\b",
    r"\bEMEA\b", r"\bAPAC\b", r"\bLATAM\b",
    r"Mexico\b",
    # China
    r"\bChina\b", r"\bChinese\b",
    r"Beijing", r"Shanghai", r"Shenzhen", r"Guangzhou", r"Hangzhou",
    r"Chengdu", r"Wuhan", r"Xi'an", r"Nanjing", r"Suzhou",
    # Other Asia-Pacific
    r"\bKorea\b", r"\bSeoul\b", r"Taipei", r"\bTaiwan\b",
    r"Hong Kong", r"\bHK\b", r"Jakarta", r"\bIndonesia\b",
    r"Kuala Lumpur", r"\bMalaysia\b", r"Bangkok", r"\bThailand\b",
    r"Ho Chi Minh", r"Hanoi", r"\bVietnam\b",
    # Middle East
    r"Dubai", r"Abu Dhabi", r"\bUAE\b", r"Tel Aviv", r"\bIsrael\b",
    r"Riyadh", r"\bSaudi\b",
    # Eastern Europe
    r"Warsaw", r"\bPoland\b", r"Prague", r"\bCzech\b",
    r"Budapest", r"\bHungary\b", r"Kyiv", r"\bUkraine\b",
    r"Moscow", r"\bRussia\b",
]

_UNKNOWN_EXACT = {"", "n/a", "na", "location", "null", "tbd", "remote-us/ca"}

def is_us_location(location: str, remote: bool) -> bool:
    if remote:
        return True
    if not location:
        return True
    stripped = location.strip().lower()
    if stripped in _UNKNOWN_EXACT:
        return True
    for pat in _NON_US_SIGNALS:
        if re.search(pat, location, re.IGNORECASE):
            return False
    for pat in _US_SIGNALS:
        if re.search(pat, location, re.IGNORECASE):
            return True
    return True  # unknown — keep, let Gemini decide



def filter_jobs(jobs: list[dict], company_name: str) -> list[dict]:
    # stage 1: location
    us_jobs = [
        j for j in jobs
        if is_us_location(j.get("location", ""), j.get("remote", False))
    ]
    loc_dropped = len(jobs) - len(us_jobs)

    # stage 2: title relevance
    title_kept = [j for j in us_jobs if is_relevant(j.get("title", ""))]
    title_dropped = len(us_jobs) - len(title_kept)

    # stage 3: freshness
    fresh = [j for j in title_kept if is_fresh(j)]
    stale_dropped = len(title_kept) - len(fresh)

    # stage 4: sponsorship denial
    eligible = [j for j in fresh if not requires_sponsorship_denial(j)]
    sponsor_dropped = len(fresh) - len(eligible)

    logger.info(
        f"  {company_name}: {len(jobs)} total → "
        f"{loc_dropped} non-US → "
        f"{title_dropped} irrelevant title → "
        f"{stale_dropped} stale → "
        f"{sponsor_dropped} no-sponsorship → "
        f"{len(eligible)} eligible"
    )
    return eligible