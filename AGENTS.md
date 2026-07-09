# AGENTS.md — how to run Intern Scout for your human

**You are an AI coding agent (Codex, Cursor, GLM, Claude, etc.). Your job here is simple:
help the person you're working with land an internship using this repo.** You are an
*operator* of this tool, not a contributor to it. Do **not** refactor, restructure, or
"improve" the code. Just set it up, run searches, and hand back real openings.

Intern Scout scrapes startup ATS boards (Greenhouse / Lever / Ashby), Y Combinator, and
(best-effort) LinkedIn / Indeed, then ranks the internships that match what your human
actually wants to do. It defaults to roles **in India or remote**.

---

## Do this, in order

### 1. Set it up (once)

```bash
pip install -e .
python -m scrapling install     # one-time: downloads the stealth browser it scrapes with
```

Optional but makes ranking noticeably smarter — a free [Groq](https://console.groq.com)
API key. Without it the tool still works in keyword-only mode.

```bash
cp .env.example .env            # then put GROQ_API_KEY=... in .env
```

If you skip the key, that's fine — just tell your human the ranking is keyword-only.

### 2. Ask your human what they want

Get four things from them before searching:

- **What kind of internship?** (e.g. "backend at an early-stage AI startup", "operations
  intern", "product design"). This becomes the `--prompt` — a plain-English sentence, not
  keywords.
- **Remote, onsite, or any?**
- **Which locations?** Any Indian cities they prefer (Bengaluru, Gurgaon, Pune…), or leave
  blank for "anywhere in India, plus remote."
- **How many results?** (default 25 is fine.)

### 3. Run the search

Fill their answers into one command:

```bash
internscout --prompt "operations internship at a logistics startup" \
  --remote any --locations "Bengaluru, Remote" --limit 25 --export csv
```

Flags:

| Flag | Meaning |
|------|---------|
| `--prompt "..."` | Plain-English description of the role (required) |
| `--remote remote\|onsite\|any` | Work arrangement |
| `--locations "A, B"` | Comma-separated cities/countries. **Blank = India or remote.** |
| `--grad-year 2027` | Optional graduation-year filter |
| `--limit 25` | How many results |
| `--export csv` | Also writes the results to a file (see below) |

You can also just run `internscout` with no flags for an interactive Q&A prompt — but
since you're driving it, passing flags is cleaner.

### 4. Deliver the results

- `--export csv` writes **`results.csv`** in the current directory. It opens directly in
  Excel or Google Sheets. (`--export md` writes `results.md` instead — a Markdown table.)
- On top of the file, **summarize in chat**: the top 5–8 matches (title · company ·
  location · why it matched · link) and the standout companies. Your human shouldn't have
  to open a spreadsheet to see the best hits.
- Then offer the obvious next step: *"Want me to draft an application or a cold email to
  any of these?"*

### 5. Be honest when a source is blocked

LinkedIn and Indeed actively block bots and will sometimes return little or nothing. The
ATS boards and YC are the reliable core. If a run comes back thin:

- **Say so plainly** — "LinkedIn was blocked this run, so these are from the ATS boards and
  YC." Never invent or pad results.
- Suggest a fix: broaden the prompt, drop a filter, add a Groq key, or just re-run (blocks
  are often temporary).

---

## Guardrails

- **Don't edit the code to change what it returns.** No new filters, no tweaking scrapers
  to "get more results." If coverage is genuinely missing, tell your human — don't fake it.
- **Only report internships the tool actually found.** Every row in the output is a real
  scraped posting with a real URL. Keep it that way.
- The one file worth editing is `internscout/data/seed_companies.json` — if your human
  names a specific company whose careers page runs on Greenhouse/Lever/Ashby, you can add
  its board slug there so future runs include it. That's operating the tool, not rewriting
  it.

---

## Coverage, honestly

- **Reliable:** Greenhouse, Lever, Ashby ATS boards + Y Combinator.
- **Best-effort:** LinkedIn, Indeed (may be blocked).
- **Not reachable yet:** many large Indian consumer/logistics firms (Swiggy, Flipkart,
  Delhivery…) run on Darwinbox / Keka / Workday, which this tool doesn't scrape. The seed
  list (`internscout/data/seed_companies.json`) is the set of companies it can reach today.

If your human needs more, the honest answer is "this tool covers X; for company Y you'd
apply directly on their careers page" — not a scraper hack.
