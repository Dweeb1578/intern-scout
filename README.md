# Intern Scout

Find internships that match what you actually want to do. Describe the role in plain
English, add a couple of filters, and Intern Scout scrapes startup ATS boards, YC, and
(best-effort) LinkedIn/Indeed, then ranks the most relevant openings - and the companies
behind them.

> **Using an AI coding agent (Codex, Cursor, GLM, Claude Code)?** It will read
> [`AGENTS.md`](AGENTS.md) automatically — that file tells your agent how to set this up
> and run internship searches *for* you. Just point it at this repo and say "help me find
> an internship."

## Setup

1. Install Python 3.11+.
2. Clone this repo and install (this pulls Scrapling + its browser engine):
   ```bash
   pip install -e .
   python -m scrapling install   # one-time: downloads the stealth browser
   ```
3. (Optional but recommended) copy `.env.example` to `.env` and add a free Groq API key
   for smarter ranking. Without it, the tool runs in keyword-only mode.
   ```bash
   cp .env.example .env
   ```

## Use

Interactive:
```bash
internscout
```

One-shot:
```bash
internscout --prompt "backend internship at an early-stage AI startup" \
  --remote any --locations "India, Remote" --limit 25 --export csv
```

Flags: `--prompt`, `--remote remote|onsite|any`, `--locations "A, B"`, `--grad-year`,
`--limit`, `--export csv|md`.

## Location

By default Intern Scout only returns roles that are **in India or remote** — leave
`--locations` blank (or pass `"India"`) and it keeps Indian roles (recognizing major
cities like Bengaluru, Gurgaon, Hyderabad, Pune… not just the literal word "India")
plus any remote role. Remote roles always pass regardless of where the company is.

To search elsewhere, pass explicit cities/countries, e.g. `--locations "London, Berlin"`.

## Roles it understands

Works for engineering internships **and** business/early-career roles — operations,
GTM (sales / marketing / growth / business development), supply chain (procurement,
logistics, fulfillment), and management/strategy (founder's office, chief of staff,
business analyst, management trainee). India often labels these "Management Trainee" or
"Graduate Programme" rather than "Intern" — those are recognized too. Just describe the
role in your prompt; with a Groq key the matching is sharper, but keyword mode handles
these domains out of the box.

## Notes

- LinkedIn/Indeed are best-effort and may return little or nothing when they block bots;
  ATS boards and YC are the reliable core.
- ATS coverage is Greenhouse / Lever / Ashby. Many large Indian consumer/logistics firms
  (Swiggy, Flipkart, Delhivery…) use other systems (Darwinbox, Workday) and aren't
  reachable yet — see the seed list for the companies that are.
- Each person runs their own scrapes locally, so there's no shared server to rate-limit.
- Add more companies in `internscout/data/seed_companies.json`.
