"""Scrape public LinkedIn jobs, companies, profiles and posts with Python. No login, one file."""
import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from urllib.parse import parse_qs, unquote, urlparse

from bs4 import BeautifulSoup
from curl_cffi import requests

BASE = "https://www.linkedin.com"
JOBS_SEARCH = BASE + "/jobs-guest/jobs/api/seeMoreJobPostings/search"
JOB_DETAIL = BASE + "/jobs-guest/jobs/api/jobPosting/"

# Filter values the public job search understands (f_TPR is "posted within N seconds").
POSTED = {"day": "r86400", "week": "r604800", "month": "r2592000"}
WORKPLACE = {"onsite": "1", "remote": "2", "hybrid": "3"}


class ScrapeError(Exception):
    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


def text_of(node):
    return " ".join(node.get_text(" ", strip=True).split()) if node else None


def to_int(value):
    digits = re.sub(r"[^\d]", "", str(value or ""))
    return int(digits) if digits else None


def iso(value):
    """Turn LinkedIn's '2026-10-12T20:10:58.408Z' into '2026-10-12T20:10:58+00:00'."""
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def clean_url(url):
    """Drop tracking parameters and country subdomains (uk.linkedin.com -> www.linkedin.com)."""
    if not url:
        return None
    parts = urlparse(url)
    return f"{BASE}{parts.path}".rstrip("/")


def last_segment(value, marker):
    """'https://www.linkedin.com/company/microsoft/?x=1' -> 'microsoft'."""
    m = re.search(rf"/{marker}/([^/?#]+)", value)
    return unquote(m.group(1)) if m else value.strip().strip("/")


def job_id_of(value):
    m = re.search(r"currentJobId=(\d+)", value) or re.search(r"(\d{6,})(?!.*\d{6,})", value)
    return m.group(1) if m else None


def ld_json(soup):
    """All JSON-LD nodes on the page, with '@graph' wrappers flattened."""
    nodes = []
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
        except ValueError:
            continue
        nodes.extend(data.get("@graph", [data]) if isinstance(data, dict) else data)
    return nodes


def like_count(node):
    stats = node.get("interactionStatistic") or []
    for stat in stats if isinstance(stats, list) else [stats]:
        if "LikeAction" in str(stat.get("interactionType")):
            return stat.get("userInteractionCount")
    return None


def follower_count(node):
    stat = node.get("interactionStatistic") or {}
    return stat.get("userInteractionCount") if "FollowAction" in str(stat.get("interactionType")) else None


class LinkedIn:
    """Plain logged-out requests that look like Chrome. No session setup is needed.

    Only the job endpoints get a Referer. On the public pages it triggers HTTP 999.
    """

    def __init__(self, proxy=None):
        self.http = requests.Session(impersonate="chrome", proxies={"http": proxy, "https": proxy} if proxy else None)
        self.last_call = 0.0

    def get(self, url, params=None, referer=None):
        headers = {"Accept-Language": "en-US,en;q=0.9", **({"Referer": referer} if referer else {})}
        for attempt in range(4):
            # Stay slow: LinkedIn answers a quick burst from one IP with 429 or 999.
            time.sleep(max(0, 2 - (time.time() - self.last_call)))
            try:
                resp = self.http.get(url, params=params, headers=headers, timeout=30, allow_redirects=False)
            except requests.RequestsError as exc:
                raise ScrapeError(f"Network error: {exc}") from exc
            self.last_call = time.time()
            where = resp.headers.get("location", "")
            if resp.status_code in (301, 302) and "linkedin.com" in where and "authwall" not in where:
                url, params = where, None  # a renamed page or a country site
                continue
            if resp.status_code == 429 and attempt == 0:
                time.sleep(4)  # the job endpoints often clear after a short pause
                continue
            break
        status = resp.status_code
        if status in (301, 302, 401, 403, 429, 999):
            raise ScrapeError(
                f"LinkedIn answered HTTP {status}: rate-limited or blocked. "
                "Datacenter IPs are blocked most; try a home connection or --proxy, and wait a minute.",
                status,
            )
        if status == 404:
            raise ScrapeError("Not found.")
        if status != 200:
            raise ScrapeError(f"Unexpected HTTP {status} from LinkedIn.")
        return resp

    # --- jobs ------------------------------------------------------------

    def jobs(self, keywords, location=None, posted=None, workplace=None, limit=10):
        params = {"keywords": keywords}
        if location:
            params["location"] = location
        if posted:
            params["f_TPR"] = POSTED[posted]
        if workplace:
            params["f_WT"] = WORKPLACE[workplace]
        jobs = []
        while len(jobs) < limit:
            try:
                html = self.get(JOBS_SEARCH, {**params, "start": len(jobs)}, BASE + "/jobs/search").text
            except ScrapeError:
                if jobs:  # keep the pages we already have
                    print(f"Warning: stopped at {len(jobs)} jobs: LinkedIn limited the next page.", file=sys.stderr)
                    break
                raise
            cards = BeautifulSoup(html, "html.parser").select("li div.base-card")
            if not cards:
                break
            for card in cards:
                urn = card.get("data-entity-urn", "")
                company = card.select_one("h4.base-search-card__subtitle a")
                posted_on = card.select_one("time")
                jobs.append({
                    "job_id": urn.split(":")[-1],
                    "url": f"{BASE}/jobs/view/{urn.split(':')[-1]}",
                    "title": text_of(card.select_one("h3.base-search-card__title")),
                    "company": text_of(company) or text_of(card.select_one("h4.base-search-card__subtitle")),
                    "company_url": clean_url(company["href"]) if company else None,
                    "location": text_of(card.select_one("span.job-search-card__location")),
                    "posted_date": posted_on.get("datetime") if posted_on else None,
                    "salary": text_of(card.select_one(".job-search-card__salary-info")),
                    "actively_hiring": "Actively Hiring" in card.get_text(),
                })
        # Pages can overlap a little, so de-duplicate by id.
        seen, unique = set(), []
        for job in jobs:
            if job["job_id"] not in seen:
                seen.add(job["job_id"])
                unique.append(job)
        return unique[:limit]

    def job(self, value):
        job_id = job_id_of(value)
        if not job_id:
            raise ScrapeError(f"Could not find a job id in: {value}")
        soup = BeautifulSoup(self.get(JOB_DETAIL + job_id, referer=f"{BASE}/jobs/view/{job_id}").text, "html.parser")
        title = soup.select_one("h2.top-card-layout__title, h2.topcard__title")
        if not title:
            raise ScrapeError(f"Job not found: {job_id}")
        criteria = {}
        for item in soup.select("li.description__job-criteria-item"):
            criteria[text_of(item.select_one("h3"))] = text_of(item.select_one("span"))
        company = soup.select_one("a.topcard__org-name-link")
        return {
            "job_id": job_id,
            "url": f"{BASE}/jobs/view/{job_id}",
            "title": text_of(title),
            "company": text_of(company),
            "company_url": clean_url(company["href"]) if company else None,
            "location": text_of(soup.select_one(".topcard__flavor--bullet")),
            "posted_ago": text_of(soup.select_one(".posted-time-ago__text")),
            "applicants": text_of(soup.select_one(".num-applicants__caption")),
            "salary": text_of(soup.select_one(".compensation__salary")),
            "is_open": soup.select_one(".closed-job__flavor--closed") is None,
            "seniority_level": criteria.get("Seniority level"),
            "employment_type": criteria.get("Employment type"),
            "industries": criteria.get("Industries"),
            "description": description_text(soup.select_one(".show-more-less-html__markup")),
        }

    # --- company ---------------------------------------------------------

    def company(self, value):
        slug = last_segment(value, "company")
        raw = self.get(f"{BASE}/company/{slug}").text
        soup = BeautifulSoup(raw, "html.parser")
        org = next((n for n in ld_json(soup) if n.get("@type") == "Organization"), None)
        if not org:
            raise ScrapeError(f"No company data on the page for {slug}. It may not exist.")

        def about(key):
            return text_of(soup.select_one(f'[data-test-id="about-us__{key}"] dd'))

        website = soup.select_one('[data-test-id="about-us__website"] dd a')
        if website and "redirect?url=" in website["href"]:  # LinkedIn wraps outside links
            site = unquote(parse_qs(urlparse(website["href"]).query)["url"][0])
        else:
            site = about("website")
        followers = re.search(r"([\d,]+)\s+followers", text_of(soup.select_one(".top-card-layout__first-subline")) or "")
        address = org.get("address") or {}
        org_id = re.search(r"urn:li:organization:(\d+)", raw)
        similar = soup.select('section[data-test-id="similar-pages"] a[href*="/company/"]')
        specialties = about("specialties")
        return {
            "slug": slug,
            "url": f"{BASE}/company/{slug}",
            "company_id": org_id.group(1) if org_id else None,
            "name": org.get("name"),
            "industry": about("industry"),
            "description": org.get("description"),
            "website": site,
            "company_size": about("size"),
            "employee_count": (org.get("numberOfEmployees") or {}).get("value"),
            "followers_count": to_int(followers.group(1)) if followers else None,
            "type": about("organizationType"),
            "founded": to_int(about("founded")),
            "specialties": [s.strip() for s in specialties.split(",")] if specialties else [],
            "headquarters": about("headquarters"),
            "address": {
                "street": address.get("streetAddress"),
                "city": address.get("addressLocality"),
                "region": address.get("addressRegion"),
                "postal_code": address.get("postalCode"),
                "country": address.get("addressCountry"),
            },
            "logo_url": (org.get("logo") or {}).get("contentUrl"),
            "similar_companies": list(dict.fromkeys(last_segment(a["href"], "company") for a in similar)),
        }

    # --- profile ---------------------------------------------------------

    def profile(self, value):
        slug = last_segment(value, "in")
        try:
            page = self.get(f"{BASE}/in/{slug}")
        except ScrapeError as exc:
            if exc.status == 999:  # LinkedIn sends the same 999 for unknown profiles and blocked IPs
                raise ScrapeError(f"LinkedIn answered HTTP 999 for {slug}: the profile does not exist, or this IP is blocked. Check the name, then try --proxy.") from exc
            raise
        soup = BeautifulSoup(page.text, "html.parser")
        nodes = ld_json(soup)
        person = next((n for n in nodes if n.get("@type") == "Person"), None)
        if not person:
            raise ScrapeError(f"No public profile data for {slug}. The profile may not exist or may be private.")
        experience = []
        for item in soup.select("li.experience-item"):
            company = item.select_one(".experience-item__subtitle")
            link = item.select_one("a[href*='/company/']")
            dates = text_of(item.select_one(".date-range")) or ""
            years = [text_of(t) for t in item.select(".date-range time")]
            experience.append({
                "title": text_of(item.select_one(".experience-item__title")),
                "company": text_of(company),
                "company_url": clean_url(link["href"]) if link else None,
                "start": years[0] if years else None,
                "end": years[1] if len(years) > 1 else None,
                "is_current": "Present" in dates,
            })
        education = [{
            "school": e.get("name"),
            "school_url": clean_url(e.get("url")),
            "start_year": (e.get("member") or {}).get("startDate"),
            "end_year": (e.get("member") or {}).get("endDate"),
        } for e in person.get("alumniOf") or []]
        address = person.get("address") or {}
        posts = [{
            "url": clean_url(n.get("url")),
            "published_at": iso(n.get("datePublished")),
            "text": n.get("text"),
            "like_count": like_count(n),
        } for n in nodes if n.get("@type") == "DiscussionForumPosting"]
        return {
            "slug": slug,
            "url": f"{BASE}/in/{slug}",
            "name": person.get("name"),
            "headline": text_of(soup.select_one(".top-card-layout__headline")),
            "location": address.get("addressLocality"),
            "country": address.get("addressCountry"),
            "about": person.get("description"),
            "badges": person.get("disambiguatingDescription"),
            "followers_count": follower_count(person),
            "photo_url": (person.get("image") or {}).get("contentUrl"),
            "experience": experience,
            "education": education,
            "recent_posts": posts,
        }

    # --- post ------------------------------------------------------------

    def post(self, value, comments=False):
        url = value if "/posts/" in value else f"{BASE}/posts/{value}"
        soup = BeautifulSoup(self.get(clean_url(url)).text, "html.parser")
        post = next((n for n in ld_json(soup) if n.get("@type") in ("SocialMediaPosting", "VideoObject", "DiscussionForumPosting")), None)
        if not post:
            raise ScrapeError(f"No post data on the page for {value}. The post may not exist or may be private.")
        author = post.get("author") or post.get("creator") or {}
        activity = re.search(r"activity-(\d+)", url)
        article = soup.select_one('[data-test-id="article-content"]')
        out = {
            "id": activity.group(1) if activity else None,
            "url": clean_url(post.get("@id") or url),
            "published_at": iso(post.get("datePublished")),
            "text": post.get("articleBody") or post.get("description") or post.get("text") or post.get("headline"),
            "author_name": author.get("name"),
            "author_url": clean_url(author.get("url")),
            "author_followers": follower_count(author),
            "like_count": like_count(post),
            "comment_count": post.get("commentCount"),
            "shared_link": clean_url(article["href"]) if article else None,
            "image_url": (post.get("image") or {}).get("url") or post.get("thumbnailUrl"),
        }
        if comments:
            out["comments"] = [{
                "text": c.get("text"),
                "published_at": iso(c.get("datePublished")),
                "like_count": like_count(c),
                "author_name": (c.get("author") or c.get("creator") or {}).get("name"),
            } for c in post.get("comment") or []]
        return out


def description_text(node):
    """Job description HTML as plain text with one line per paragraph or bullet."""
    if not node:
        return None
    for br in node.find_all("br"):
        br.replace_with("\n")
    for li in node.find_all("li"):
        li.insert(0, "- ")
    for block in node.find_all(["p", "li", "ul", "div", "h1", "h2", "h3", "h4"]):
        block.append("\n")
    text = re.sub(r"[ \t]+", " ", node.get_text())
    return re.sub(r"\n\s*\n+", "\n\n", re.sub(r" ?\n ?", "\n", text)).strip() or None


def main():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--proxy", default=os.environ.get("HTTPS_PROXY"), help="proxy URL, e.g. http://user:pass@host:port")
    common.add_argument("-o", "--output", help="write JSON to this file")
    parser = argparse.ArgumentParser(description="Scrape public LinkedIn data. No login.")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("jobs", parents=[common], help="search public job postings")
    p.add_argument("keywords", help='for example "data analyst"')
    p.add_argument("--location", help='for example "London"')
    p.add_argument("--posted", choices=POSTED, help="only jobs posted in this period")
    p.add_argument("--workplace", choices=WORKPLACE)
    p.add_argument("--limit", type=int, default=10, help="how many jobs to return (default 10)")
    sub.add_parser("job", parents=[common], help="one job posting").add_argument("jobs", nargs="+", help="job URL or id")
    sub.add_parser("company", parents=[common], help="public company page").add_argument("companies", nargs="+", help="name in the URL, like microsoft, or the page URL")
    sub.add_parser("profile", parents=[common], help="public profile").add_argument("profiles", nargs="+", help="name in the URL, like williamhgates, or the page URL")
    p = sub.add_parser("post", parents=[common], help="one public post")
    p.add_argument("posts", nargs="+", help="post URL")
    p.add_argument("--comments", action="store_true", help="also return the first page of comments")
    args = parser.parse_args()

    try:
        li = LinkedIn(args.proxy)
        if args.command == "jobs":
            data = li.jobs(args.keywords, args.location, args.posted, args.workplace, args.limit)
        elif args.command == "job":
            data = [li.job(j) for j in args.jobs]
        elif args.command == "company":
            data = [li.company(c) for c in args.companies]
        elif args.command == "profile":
            data = [li.profile(p) for p in args.profiles]
        else:
            data = [li.post(p, args.comments) for p in args.posts]
    except ScrapeError as exc:
        sys.exit(f"Error: {exc}")

    if args.command != "jobs" and len(data) == 1:
        data = data[0]
    text = json.dumps(data, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(f"Saved to {args.output}")
    else:
        print(text)


if __name__ == "__main__":
    main()
