import sys
import os
import re
import argparse
import bibtexparser
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# ANSI color codes for terminal output
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
BOLD = "\033[1m"
RESET = "\033[0m"
ICON_SEARCH = "🔎"
ICON_OK = "✅"
ICON_WARN = "⚠️"
ICON_FAIL = "❌"

# parse args
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", action="store_true", help="enable per-entry logs (🔎/✅/❌)")
parser.add_argument("bibfile", help="input/output .bib filename")
args = parser.parse_args()


def vlog(msg):
    if args.verbose:
        tqdm.write(msg)


# HTTP session with retries
session = requests.Session()
retry = Retry(total=3, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retry))

# prepare filenames
out_bib = args.bibfile
base, ext = os.path.splitext(out_bib)
old_bib = f"{base}-old{ext}"
if os.path.exists(out_bib):
    os.rename(out_bib, old_bib)
in_bib = old_bib

# load entries
with open(in_bib) as f:
    parser = bibtexparser.bparser.BibTexParser(interpolate_strings=False)
    bib_db = bibtexparser.load(f, parser=parser)
entries = bib_db.entries

citation_key_map = {}
not_found = []


def query_entry(entry):
    key = entry.get("ID", "")
    year = entry.get("year", "").strip()
    title = re.sub(r"[{}\n]", "", entry.get("title", "")).strip().lower()

    searches = []
    if "arxiv" in entry or "eprint" in entry:
        aid = entry.get("arxiv", entry.get("eprint", "")).replace("arXiv:", "").split()[0]
        searches.append(("arxiv", f"https://inspirehep.net/api/literature?q=arxiv:{aid}&format=bibtex"))
    if "doi" in entry:
        searches.append(("doi", f"https://inspirehep.net/api/literature?q=doi:{entry['doi']}&format=bibtex"))
    if title:
        q = requests.utils.quote(title)
        searches.append(("title", f'https://inspirehep.net/api/literature?q=title:"{q}"&format=bibtex'))

    for stype, url in searches:
        vlog(f"{CYAN}{ICON_SEARCH} Trying [{stype}] for key [{key}]{RESET}")
        try:
            r = session.get(url, timeout=10)
            txt = r.text.strip()
            if r.status_code == 200 and txt.startswith("@"):
                insp = bibtexparser.loads(txt).entries
                for ie in insp:
                    it = re.sub(r"[{}\n]", "", ie.get("title", "")).strip().lower()
                    iy = ie.get("year", "").strip()
                    ok = (stype in ("arxiv", "doi")) or (it == title and iy == year)
                    if ok:
                        new_id = ie.get("ID", key)
                        if new_id != key:
                            citation_key_map[key] = new_id
                            vlog(f"{YELLOW}{ICON_WARN} Key changed: {key} → {new_id}{RESET}")
                        vlog(f"{GREEN}{ICON_OK} Success: {key} updated ({stype} match){RESET}\n")
                        return ie
        except Exception:
            pass

    not_found.append(key)
    vlog(f"{RED}{ICON_FAIL} Not found: {key} (keeping original){RESET}\n")
    return entry


# parallel update with progress bar
with ThreadPoolExecutor(max_workers=8) as ex:
    futures = {ex.submit(query_entry, e): e for e in entries}
    new_entries = []
    for f in tqdm(as_completed(futures), total=len(entries), desc="Updating BibTeX", leave=True, position=0):
        new_entries.append(f.result())

# write updated file
new_db = bibtexparser.bibdatabase.BibDatabase()
new_db.entries = new_entries
with open(out_bib, "w") as f:
    bibtexparser.dump(new_db, f)

# summary: not found
if not_found:
    print(f"\n{YELLOW}==== Summary: Not found on InspireHEP ===={RESET}")
    print(f"Make sure the entry(entries) below has at least an arXiv or DOI.\n")
    for k in not_found:
        print(f"{RED}{ICON_FAIL} {k}{RESET}")

# summary: key changes
if citation_key_map:
    logf = "citation_key_changes.log"
    print(f"\n{CYAN}==== Citation key changes (old --> new) ===={RESET}")
    for old, new in citation_key_map.items():
        print(f"{old} --> {GREEN}{new}{RESET}")
    with open(logf, "w") as f:
        for old, new in citation_key_map.items():
            f.write(f"{old} --> {new}\n")
    print(f"\n{CYAN}==> Citation key changes have been logged to {BOLD}{logf}{RESET}")
