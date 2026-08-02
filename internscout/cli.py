import argparse
import logging
import sys
from .models import UserQuery, Filters
from .config import load_config, has_llm
from .pipeline import run
from .render import render_table, export

def _setup_logging(verbose: bool) -> None:
    """Quiet by default; --verbose shows per-request and per-source detail.

    Scrapling logs one INFO line per HTTP request, which buries the results table
    under a wall of `Fetched (200) <GET ...>`. Silencing it needs a filter, not a
    level: scrapling builds its logger lazily on first import and hard-sets the
    level to INFO, clobbering anything we set up front. Filters survive that,
    because setLevel/addHandler don't touch them, and a logger is a singleton by
    name so we can attach ours before scrapling is ever imported.
    """
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")

    scrapling_log = logging.getLogger("scrapling")
    scrapling_log.addFilter(lambda record: verbose or record.levelno >= logging.WARNING)
    # it installs its own handler, so let it print once instead of twice via root
    scrapling_log.propagate = False

    logging.getLogger("internscout").setLevel(level)

def build_query(args) -> UserQuery:
    locs = [s.strip() for s in (args.locations or "").split(",") if s.strip()]
    # Default geography for this tool: India-based or remote roles. Remote jobs
    # always pass the location filter, so ["India"] means "in India or remote".
    if not locs:
        locs = ["India"]
    return UserQuery(
        prompt=args.prompt,
        filters=Filters(remote=args.remote, locations=locs,
                        grad_year=args.grad_year, max_results=args.limit),
    )

def _ask(prompt: str) -> str:
    """input() that turns Ctrl+C / Ctrl+D / a piped-empty stdin into a clean exit
    instead of an EOFError or KeyboardInterrupt traceback."""
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.", file=sys.stderr)
        raise SystemExit(130)

def _interactive(args):
    args.prompt = _ask("What kind of internship are you looking for? ")
    if not args.prompt:
        print("Need a prompt to search for - try: internscout --prompt "
              "\"backend internship at an early-stage AI startup\"", file=sys.stderr)
        raise SystemExit(2)
    r = _ask("Remote / onsite / any? [any] ").lower() or "any"
    args.remote = r if r in ("remote", "onsite", "any") else "any"
    args.locations = _ask("Preferred locations (comma-separated, blank = India or remote): ")
    gy = _ask("Graduation year (blank to skip): ")
    args.grad_year = int(gy) if gy.isdigit() else None
    lim = _ask("How many results? [25] ")
    args.limit = int(lim) if lim.isdigit() and int(lim) > 0 else 25
    return args

def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="internscout", description="Find internships that match you.")
    p.add_argument("--prompt")
    p.add_argument("--remote", choices=["remote", "onsite", "any"], default="any")
    p.add_argument("--locations", default="")
    p.add_argument("--grad-year", dest="grad_year", type=int, default=None)
    p.add_argument("--limit", type=int, default=25)
    p.add_argument("--export", choices=["csv", "md"], default=None)
    p.add_argument("-v", "--verbose", action="store_true",
                   help="show per-request and per-source logs (for debugging)")
    args = p.parse_args(argv)
    if args.limit < 1:
        p.error("--limit must be 1 or more")
    _setup_logging(args.verbose)

    cfg = load_config()
    if not (args.prompt or "").strip():
        args = _interactive(args)
    if not has_llm(cfg):
        print("(no GROQ_API_KEY set - running in keyword-only mode)\n", file=sys.stderr)

    query = build_query(args)
    print("Scraping sources... this can take a minute.", file=sys.stderr)
    try:
        ranked = run(query, cfg)
    except KeyboardInterrupt:
        # the scrape is the long part; Ctrl+C here is expected, not a crash
        print("\nStopped.", file=sys.stderr)
        return 130
    if not ranked:
        print("No matching internships found. Try fewer filters or a broader prompt - "
              "some sources may also be temporarily blocked.", file=sys.stderr)
        return 0
    render_table(ranked)
    if args.export:
        try:
            path = export(ranked, args.export, None)
        except OSError as e:
            # e.g. results.csv still open in Excel on Windows - don't throw away
            # a scrape that already succeeded and is on screen above
            print(f"\nCould not write the export file: {e}", file=sys.stderr)
            return 1
        print(f"\nSaved {len(ranked)} results to {path}", file=sys.stderr)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
