import argparse
import sys
from .models import UserQuery, Filters
from .config import load_config, has_llm
from .pipeline import run
from .render import render_table, export

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

def _interactive(args):
    args.prompt = input("What kind of internship are you looking for? ").strip()
    r = input("Remote / onsite / any? [any] ").strip().lower() or "any"
    args.remote = r if r in ("remote", "onsite", "any") else "any"
    args.locations = input("Preferred locations (comma-separated, blank = India or remote): ").strip()
    gy = input("Graduation year (blank to skip): ").strip()
    args.grad_year = int(gy) if gy.isdigit() else None
    lim = input("How many results? [25] ").strip()
    args.limit = int(lim) if lim.isdigit() else 25
    return args

def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="internscout", description="Find internships that match you.")
    p.add_argument("--prompt")
    p.add_argument("--remote", choices=["remote", "onsite", "any"], default="any")
    p.add_argument("--locations", default="")
    p.add_argument("--grad-year", dest="grad_year", type=int, default=None)
    p.add_argument("--limit", type=int, default=25)
    p.add_argument("--export", choices=["csv", "md"], default=None)
    args = p.parse_args(argv)

    cfg = load_config()
    if not args.prompt:
        args = _interactive(args)
    if not has_llm(cfg):
        print("(no GROQ_API_KEY set - running in keyword-only mode)\n", file=sys.stderr)

    query = build_query(args)
    print("Scraping sources... this can take a minute.", file=sys.stderr)
    ranked = run(query, cfg)
    if not ranked:
        print("No matching internships found. Try fewer filters or a broader prompt - "
              "some sources may also be temporarily blocked.", file=sys.stderr)
        return 0
    render_table(ranked)
    if args.export:
        path = export(ranked, args.export, None)
        print(f"\nSaved {len(ranked)} results to {path}", file=sys.stderr)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
