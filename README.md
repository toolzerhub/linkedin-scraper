# LinkedIn Scraper (Python)

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Last verified](https://img.shields.io/badge/last%20verified-2026--10--13-brightgreen.svg)](#how-we-keep-it-working)

Scrape public LinkedIn jobs, companies, profiles and posts with Python. No login, no API key, one file.

> **Need this at scale?** The script is for learning and small jobs. The [ToolzerHub LinkedIn API](https://toolzerhub.com/apis/linkedin?utm_source=github&utm_medium=readme&utm_campaign=linkedin-scraper) returns the same data and more (Ad Library search, a company's recent updates and its affiliated pages) as JSON from any server, with no blocks to handle. 100 free credits a month, no card needed.

## What it scrapes

| Command | What you get |
|---|---|
| `jobs <keywords>` | Public job search: title, company, location, post date and salary when shown. Filter by place and age (LinkedIn often ignores the workplace filter) |
| `job <id or url>...` | One job posting with its full description, seniority, employment type, industries and applicant hint |
| `company <name>...` | A company page: about text, website, size, headquarters, specialties, follower and employee counts, similar companies |
| `profile <name>...` | A public profile: name, headline, location, about, follower count, work history, education and a few recent posts |
| `post <url>...` | One public post: text, date, author, like and comment counts, and optionally the first page of comments |

## Quick start

```bash
git clone https://github.com/toolzerhub/linkedin-scraper.git
cd linkedin-scraper
pip install -r requirements.txt
python linkedin_scraper.py company microsoft
```

More examples:

```bash
python linkedin_scraper.py jobs "data analyst" --location London --limit 20 -o jobs.json
python linkedin_scraper.py jobs "teacher" --location Sydney --posted week --workplace hybrid
python linkedin_scraper.py job 4476983365
python linkedin_scraper.py company nasa -o nasa.json
python linkedin_scraper.py profile williamhgates
python linkedin_scraper.py post https://www.linkedin.com/posts/williamhgates_for-an-affordable-climate-win-look-to-the-activity-7515504308268810240-k1KI --comments
```

Every command takes `-o file.json` to save the result and `--proxy URL` to route through a proxy. The script also reads `HTTPS_PROXY`. You can pass several companies, profiles or posts to one command, but see Limits. A company or profile can be the name from its URL (`microsoft`, `williamhgates`) or the full page URL. A job can be its numeric id or its URL. `--posted` takes `day`, `week` or `month`, and `--workplace` takes `onsite`, `remote` or `hybrid`.

## Example output

`python linkedin_scraper.py jobs "data analyst" --location London --limit 10` (two jobs shown)

```json
[
  {
    "job_id": "4476590411",
    "url": "https://www.linkedin.com/jobs/view/4476590411",
    "title": "Data Analyst",
    "company": "Searchability NS&D",
    "company_url": "https://www.linkedin.com/company/searchability-ns-d",
    "location": "London Area, United Kingdom",
    "posted_date": "2026-10-07",
    "salary": null,
    "actively_hiring": true
  },
  {
    "job_id": "4472176709",
    "url": "https://www.linkedin.com/jobs/view/4472176709",
    "title": "Data Analyst - Up to £80k + Benefits + Bonus",
    "company": "Oliver Bernard",
    "company_url": "https://www.linkedin.com/company/oliverbernard",
    "location": "London Area, United Kingdom",
    "posted_date": "2026-09-30",
    "salary": null,
    "actively_hiring": true
  }
]
```

`python linkedin_scraper.py job 4476983365`

```json
{
  "job_id": "4476983365",
  "url": "https://www.linkedin.com/jobs/view/4476983365",
  "title": "Software Engineer II (Java/AWS)",
  "company": "JPMorganChase",
  "company_url": "https://www.linkedin.com/company/jpmorganchase",
  "location": "New York, NY",
  "posted_ago": "5 days ago",
  "applicants": "162 applicants",
  "salary": "$123,500.00/yr - $150,000.00/yr",
  "is_open": true,
  "seniority_level": "Not Applicable",
  "employment_type": "Full-time",
  "industries": "Financial Services",
  "description": "Job Description\n\nYou're ready to gain the skills and experience needed to grow within your role and advance yo..."
}
```

`python linkedin_scraper.py company microsoft` (lists shortened)

```json
{
  "slug": "microsoft",
  "url": "https://www.linkedin.com/company/microsoft",
  "company_id": "1035",
  "name": "Microsoft",
  "industry": "Software Development",
  "description": "Every company has a mission. What's ours? To empower every person and every organization to achieve more. We b...",
  "website": "https://news.microsoft.com/",
  "company_size": "10,001+ employees",
  "employee_count": 231136,
  "followers_count": 29287243,
  "type": "Public Company",
  "founded": null,
  "specialties": [
    "Business Software",
    "Developer Tools",
    "Home & Educational Software",
    "Tablets"
  ],
  "headquarters": "Redmond, Washington",
  "address": {
    "street": "1 Microsoft Way",
    "city": "Redmond",
    "region": "Washington",
    "postal_code": "98052",
    "country": "US"
  },
  "logo_url": "https://media.licdn.com/dms/image/v2/D560BAQH32RJQCl3dDQ/company-logo_200_200/B56ZYQ0mrGGoAM-/0/1744038948046/...",
  "similar_companies": [
    "google",
    "amazon",
    "apple",
    "meta"
  ]
}
```

`python linkedin_scraper.py profile williamhgates` (one recent post shown)

```json
{
  "slug": "williamhgates",
  "url": "https://www.linkedin.com/in/williamhgates",
  "name": "Bill Gates",
  "headline": "Chair, Gates Foundation and Founder, Breakthrough Energy",
  "location": "Seattle, Washington, United States",
  "country": "US",
  "about": "Chair of the Gates Foundation. Founder of Breakthrough Energy. Co-founder of Microsoft. Voracious reader. Avid...",
  "badges": "Creator, Top Voice",
  "followers_count": 40727634,
  "photo_url": "https://media.licdn.com/dms/image/v2/D5603AQF-RYZP55jmXA/profile-displayphoto-shrink_200_200/B56ZRi8g.aGsAY-/0...",
  "experience": [
    {
      "title": "Co-chair",
      "company": "Gates Foundation",
      "company_url": "https://www.linkedin.com/company/gates-foundation",
      "start": "2000",
      "end": null,
      "is_current": true
    },
    {
      "title": "Founder",
      "company": "Breakthrough Energy",
      "company_url": "https://www.linkedin.com/company/breakthrough-energy",
      "start": "2015",
      "end": null,
      "is_current": true
    },
    {
      "title": "Co-founder",
      "company": "Microsoft",
      "company_url": "https://www.linkedin.com/company/microsoft",
      "start": "1975",
      "end": null,
      "is_current": true
    }
  ],
  "education": [
    {
      "school": "Harvard University",
      "school_url": "https://www.linkedin.com/school/harvard-university",
      "start_year": 1973,
      "end_year": 1975
    }
  ],
  "recent_posts": [
    {
      "url": "https://www.linkedin.com/posts/williamhgates_child-malnutrition-is-one-of-africas-biggest-activity-7514893923710984192-ZuIL",
      "published_at": "2026-10-11T03:45:31+00:00",
      "text": "Tackling malnutrition requires more than a steady supply of nutritious food. Access to healthcare, clean water, and safe sanitation are just as essential to growing up healthy. ",
      "like_count": 1424
    }
  ]
}
```

`python linkedin_scraper.py post https://www.linkedin.com/posts/williamhgates_for-an-affordable-climate-win-look-to-the-activity-7515504308268810240-k1KI`

```json
{
  "id": "7515504308268810240",
  "url": "https://www.linkedin.com/posts/williamhgates_for-an-affordable-climate-win-look-to-the-activity-75155043082688...",
  "published_at": "2026-10-12T20:10:58+00:00",
  "text": "To prevent the majority of warming contrails—the cloud-like lines we sometimes see form behind planes—we would...",
  "author_name": "Bill Gates",
  "author_url": "https://www.linkedin.com/in/williamhgates",
  "author_followers": 40727634,
  "like_count": 2850,
  "comment_count": 476,
  "shared_link": "https://www.linkedin.com/pulse/affordable-climate-win-look-sky-bill-gates-eoj7e",
  "image_url": "https://dms.licdn.com/playlist/vid/v2/D4E12AQFXSlhYCq-GVA/thumbnail-with-play-button-overlay-low/B4EaExtVeFJIC..."
}
```

Long text and links are shortened here. The full outputs for every command are in [examples/](examples).

## Fields

### jobs

| Field | Description |
|---|---|
| job_id, url | LinkedIn's job id and a short link to the posting |
| title | Job title |
| company, company_url | The employer and its page |
| location | Place as LinkedIn shows it |
| posted_date | Day it was posted, `YYYY-MM-DD` |
| salary | Pay range when the card shows one, otherwise null |
| actively_hiring | True when the card has the "Actively Hiring" badge |

### job

| Field | Description |
|---|---|
| job_id, url, title | Same as `jobs` |
| company, company_url, location | Same as `jobs` |
| posted_ago | How long ago it was posted, as text ("5 days ago") |
| applicants | The applicant hint LinkedIn shows ("162 applicants", "Over 200 applicants") |
| salary | Pay range when the posting shows one, otherwise null |
| is_open | False when LinkedIn marks the job as closed |
| seniority_level, employment_type, industries | The criteria LinkedIn lists. A missing one is null |
| description | The full description as plain text, one line per paragraph or bullet |

### company

| Field | Description |
|---|---|
| slug, url | The name in the company URL, and the page link |
| company_id | LinkedIn's numeric company id |
| name, industry, description | Basics from the page |
| website | The company's own site |
| company_size | Size band ("10,001+ employees") |
| employee_count | Employee number LinkedIn reports, as an integer |
| followers_count | Followers as an integer |
| type | Public company, nonprofit and so on |
| founded | Year, or null when the page does not list it |
| specialties | List of specialties |
| headquarters | Headquarters as text |
| address | Street, city, region, postal code and country code |
| logo_url | Logo link (signed, it expires) |
| similar_companies | Names from the "similar pages" list, as URL names |

### profile

| Field | Description |
|---|---|
| slug, url | The name in the profile URL, and the page link |
| name, headline | Name and headline |
| location, country | Place text and country code |
| about | The about text |
| badges | Badges such as "Creator, Top Voice", or null |
| followers_count | Followers as an integer |
| photo_url | Profile photo link (signed, it expires) |
| experience | Title, company, company_url, start year, end year and is_current |
| education | School, school_url, start_year and end_year |
| recent_posts | A few recent posts: url, published_at, text and like_count |

### post

| Field | Description |
|---|---|
| id, url | Activity id and post link |
| published_at | ISO 8601 UTC |
| text | The full post text |
| author_name, author_url, author_followers | The author |
| like_count, comment_count | Counts as integers |
| shared_link | Link to a shared article, or null |
| image_url | Cover image link (signed, it expires) |
| comments | Only with `--comments`: text, published_at, like_count and author_name for the first page of comments |

## How it works

1. `jobs` and `job` call the same small public endpoints LinkedIn's own job pages use (`/jobs-guest/jobs/api/seeMoreJobPostings/search` and `/jobs-guest/jobs/api/jobPosting/<id>`). They answer with HTML fragments, and `jobs` pages through them 10 at a time. The requests look like Chrome (`curl_cffi` copies its network fingerprint).
2. `company`, `profile` and `post` ask for the public page (`/company/<name>`, `/in/<name>`, `/posts/<slug>`). Each page holds a `<script type="application/ld+json">` block with the main facts, and the page itself holds the rest (company details, work history). Only the job requests send a `Referer` header. On the pages it makes LinkedIn answer HTTP 999.
3. Each reply is cleaned with BeautifulSoup into the fields above. Counts become integers, times become ISO 8601 UTC, tracking parameters are cut from links, and the raw HTML is dropped.

## Limits

- Public data only.
- Only what a signed-out visitor sees. That means no full employee lists, no connections, no skills, no contact details, and only a few recent posts on a profile. `comments` returns the first page (8 in our 2026-10-17 runs) of a post's comments, not all of them.
- `jobs` pages through results and can stop early when LinkedIn limits the next page. The script then prints a warning and returns the jobs it already has.
- LinkedIn is strict with repeat requests. The job commands cope better, but they also slow down on long runs. Several names in one page command (`company`, `profile`, `post`) often end with HTTP 429 or 999 and a "rate-limited or blocked" error, and the command saves nothing. Run one page per command and pause between commands. HTTP 999 is also what an unknown profile name gets, so check the spelling first. Run it from a home connection, or pass `--proxy` (a sticky residential proxy works best).
- No concurrency. The script waits 2 seconds between requests and retries a 429 once. That is all, so it stays short enough to read in one sitting.
- It breaks when LinkedIn changes its pages. See "How we keep it working".

## Scaling up

The script is for learning and small jobs. At scale you run into blocks, changing page formats and proxy costs. The [ToolzerHub LinkedIn API](https://toolzerhub.com/apis/linkedin?utm_source=github&utm_medium=readme&utm_campaign=linkedin-scraper) handles all of that:

| | This script | ToolzerHub API |
|---|---|---|
| Data | Jobs, company pages, public profiles and posts | 20 LinkedIn endpoints: those, plus location search, Ad Library search, company updates and affiliated pages |
| Blocks and proxies | Your problem | Handled |
| When LinkedIn changes | Wait for a fix here | Fixed on our side |
| Cost | Free, plus your proxy | 100 free credits a month, then from $0.99 per 1,000 calls |

## How we keep it working

Every command is run against live LinkedIn pages before each update, and the "last verified" badge shows the last day they all passed. If something breaks, [open an issue](https://github.com/toolzerhub/linkedin-scraper/issues).

## FAQ

**Is scraping LinkedIn legal?**
Scraping publicly available data is generally allowed in many places, but it depends on your country, what you collect and how you use it. Read the Legal section below.

**Why am I getting blocked?**
LinkedIn refuses clients that ask for many pages in a row. On 2026-10-17 one page per command worked from a datacenter IP, while several companies in one command got HTTP 999. Run one page per command and slow down.

**Can it get a company's employee list or a profile's skills?**
No. A signed-out visitor does not see them.

## Related scrapers

- [instagram-scraper](https://github.com/toolzerhub/instagram-scraper): public Instagram profiles, posts, comments and search
- [tiktok-scraper](https://github.com/toolzerhub/tiktok-scraper): public TikTok profiles, videos, comments and hashtags
- [threads-scraper](https://github.com/toolzerhub/threads-scraper): public Threads profiles, posts, replies and search
- [reddit-scraper](https://github.com/toolzerhub/reddit-scraper): public subreddits, posts, comments, search and user posts
- [google-maps-scraper](https://github.com/toolzerhub/google-maps-scraper): public Google Maps places, details and reviews
- [facebook-ad-library-scraper](https://github.com/toolzerhub/facebook-ad-library-scraper): public Meta Ad Library ads by keyword or advertiser, with their videos and images
- [zillow-scraper](https://github.com/toolzerhub/zillow-scraper): public Zillow listings, property details, Zestimates and price history

## Legal and responsible use

This project is for education and for collecting **publicly available** data. You are responsible for how you use it.

- **Public data only.** The script reads pages anyone can see without an account. Do not use it to get around logins, paywalls, CAPTCHAs or other access controls.
- **Terms and robots rules.** LinkedIn's terms of service may restrict automated access. Read them and decide for yourself; following them is your responsibility.
- **Personal data.** Profiles and comments can contain personal data. Laws such as the GDPR (EU and UK) and the CCPA (California) may apply. Collect only what you need, have a lawful basis, keep it secure, delete it when you no longer need it, and respect people's requests to access or erase their data.
- **Copyright.** Posts, images and videos belong to their creators. Do not republish them without permission.
- **Be gentle.** Keep request rates low and do not disrupt the service.
- **No warranty.** The software is provided "as is" under the MIT License, without warranty of any kind. The authors are not liable for any claim or damage arising from its use.
- **Not affiliated.** This project is not affiliated with, endorsed by or sponsored by LinkedIn Corporation. LinkedIn is a trademark of LinkedIn Corporation.
- **Takedown requests.** If you own rights in something here and want it changed or removed, email contact@toolzerhub.com.

This section is not legal advice. If you are unsure, talk to a lawyer.

## License

[MIT](LICENSE) © ToolzerHub
