# Intern Scout

Find internships that match what you actually want to do. Describe the role in plain
English, add a couple of filters, and Intern Scout searches startup job boards, YC,
LinkedIn and Indeed, then ranks the openings that fit best.

It runs entirely on your own computer. There is no server, no account, and no cost.

```
internscout --prompt "operations internship at a logistics startup"
```

```
| # | Score | Title                                | Company   | Location                   | Source     |
|---|-------|--------------------------------------|-----------|----------------------------|------------|
| 1 | 2.0   | Intern - Industrial Trainee          | inmobi    | Bangalore                  | greenhouse |
| 2 | 2.0   | Supply Chain and Logistics - Intern  | Raptee.HV | Chennai, Tamil Nadu, India | linkedin   |
| 3 | 2.0   | Operations Intern (Startup)          | FXN India | Kochi, Kerala              | indeed     |
```

---

## Setup

This takes about ten minutes, most of which is waiting for a download. You will be
typing commands into a terminal, but you do not need to know how to code.

### Step 1: Install Python

Download Python 3.11 or newer from [python.org/downloads](https://www.python.org/downloads/).

**On Windows, tick the box that says "Add python.exe to PATH"** on the first screen of
the installer. It is easy to miss and nothing below will work without it.

To check it worked, open a terminal (Command Prompt or PowerShell on Windows, Terminal
on macOS) and run:

```bash
python --version
```

You should see `Python 3.11.x` or higher. If Windows says the command was not found,
reinstall Python with the PATH box ticked. On macOS you may need `python3` instead of
`python` in every command below.

### Step 2: Download Intern Scout

If you have `git`:

```bash
git clone https://github.com/Dweeb1578/intern-scout.git
cd intern-scout
```

If you do not, click the green **Code** button on the GitHub page, choose **Download
ZIP**, unzip it, then open a terminal in the unzipped folder. On Windows you can
shift-right-click inside the folder and pick "Open PowerShell window here".

### Step 3: Create a private workspace for it

This keeps Intern Scout's dependencies separate from the rest of your computer, so
nothing else breaks. Run this inside the `intern-scout` folder:

```bash
python -m venv .venv
```

Then activate it. **Windows (PowerShell):**

```powershell
.venv\Scripts\Activate.ps1
```

**macOS or Linux:**

```bash
source .venv/bin/activate
```

Your prompt should now start with `(.venv)`. You need to run this activate command
every time you open a new terminal to use Intern Scout.

> If PowerShell refuses with "running scripts is disabled on this system", run
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, answer `Y`, and try again.

### Step 4: Install it

```bash
pip install -e .
```

Then install the browser it uses to read LinkedIn, Indeed and YC:

```bash
scrapling install
```

This one downloads a few hundred megabytes and can take several minutes. You only ever
do it once. It is safe to re-run if it gets interrupted.

### Step 5 (optional): Add a free Groq key for smarter ranking

Without a key, Intern Scout matches on keywords, which works fine. With one, it reads
the job descriptions and ranks them more accurately.

1. Make a free account at [console.groq.com/keys](https://console.groq.com/keys).
2. Click **Create API Key** and copy it.
3. Copy the example config file:

   ```bash
   cp .env.example .env
   ```

   On Windows PowerShell, use `Copy-Item .env.example .env` instead.

4. Open `.env` in any text editor and paste your key after `GROQ_API_KEY=`, so the line
   reads `GROQ_API_KEY=gsk_yourkeyhere`. Save the file.

Never share your `.env` file or commit it. It is already excluded from git.

---

## Using it

The simplest way is to run it with no arguments and answer the questions:

```bash
internscout
```

Or say everything up front:

```bash
internscout --prompt "backend internship at an early-stage AI startup" --limit 25 --export csv
```

Describe the role the way you would to a friend. "Marketing intern at a consumer
startup" works better than a list of keywords.

### Options

| Option | What it does |
|--------|--------------|
| `--prompt "..."` | Plain-English description of the role you want |
| `--remote remote\|onsite\|any` | Work arrangement (default: any) |
| `--locations "A, B"` | Cities or countries. Leave blank for India or remote |
| `--grad-year 2027` | Only roles asking for that graduation year |
| `--limit 25` | How many results to show (default: 25) |
| `--export csv` or `--export md` | Also save the results to a file |
| `--verbose` | Show what it is doing, for when something looks wrong |

### Where results are saved

`--export csv` writes **results.csv** into the folder you ran the command from. It opens
directly in Excel or Google Sheets. `--export md` writes **results.md**, a table you can
paste into Notion or a doc. Each run overwrites the previous file, so rename it if you
want to keep it.

---

## How the location filter works

By default Intern Scout returns roles that are **in India or remote**. Leave
`--locations` blank, or pass `"India"`, and it keeps Indian roles plus remote ones. It
recognizes major cities (Bengaluru, Gurgaon, Hyderabad, Pune and so on), not just the
literal word "India".

Remote roles normally pass no matter where the company is. The one exception is a
posting that names its own hiring region: "fully remote (within the U.S.)" is not
actually open to someone searching from India, so it gets filtered out. This only
happens when the posting is explicit. A plain "Remote", a "Remote (anywhere)", or any
wording the tool cannot read confidently all stay in your results, because a role you
never see costs you more than one you skip past.

To search somewhere else, name the places:

```bash
internscout --prompt "product design intern" --locations "London, Berlin"
```

## What kinds of roles it understands

Engineering internships and business or early-career roles: operations, GTM (sales,
marketing, growth, business development), supply chain (procurement, logistics,
fulfillment), and management or strategy (founder's office, chief of staff, business
analyst, management trainee).

Indian companies often label these "Management Trainee" or "Graduate Programme" rather
than "Intern", and those are recognized too.

---

## If something goes wrong

**`internscout: command not found`**
Your virtual environment is probably not active. Run the activate command from Step 3
again. Check your prompt starts with `(.venv)`.

**`pip` is not recognized (Windows)**
Python was installed without being added to PATH. Reinstall it and tick "Add python.exe
to PATH".

**"No matching internships found"**
Try a broader prompt, raise `--limit`, or drop `--grad-year`. Job boards also block
automated visits sometimes, so a re-run a few minutes later often returns more.

**A source seems to return nothing**
Run the same command with `--verbose` to see each request and any failures. LinkedIn and
Indeed block bots intermittently, which is normal and temporary.

**It feels slow**
A full run takes roughly 30 to 60 seconds because it visits several job boards and loads
LinkedIn, Indeed and YC in a real browser.

---

## Notes and limits

- LinkedIn and Indeed are best effort. They block bots and will sometimes return little
  or nothing. The company job boards are the dependable core.
- **YC returns very few results, and that is expected.** Work at a Startup ignores the
  search query for logged-out visitors, so Intern Scout only sees its default job list
  and keeps the intern roles in it. Often that is one or two. Nothing is broken; the
  site just does not search without an account.
- Company job board coverage is Greenhouse, Lever and Ashby. Several large Indian firms
  (Swiggy, Flipkart, Delhivery and others) use Darwinbox or Workday and are not reachable
  yet. See the seed list for who is covered.
- Everyone runs their own searches locally, so there is no shared server to rate-limit.
- To add companies, edit `internscout/data/seed_companies.json`.

## Using an AI coding agent

If you use Codex, Cursor, GLM or Claude Code, this repo ships an
[`AGENTS.md`](AGENTS.md) that your agent reads automatically. It explains how to set the
tool up and run searches for you. Point the agent at this folder and say "help me find
an internship". You do not need any of this to use Intern Scout yourself.
