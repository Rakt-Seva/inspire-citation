# Usage examples:
#   python inspire-citation.py myrefs.bib
#   python inspire-citation.py -v myrefs.bib
#   python inspire-citation.py myrefs.bib --replace ./paper
#   python inspire-citation.py --replace ./paper
#     (uses citation_key_changes.log from a previous run, no .bib processing)
#   python inspire-citation.py --replace ./paper/main.tex
#     (replaces citations only in that file)

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
parser.add_argument("bibfile", nargs="?", help="input/output .bib filename (omit if only using --replace)")
parser.add_argument("--replace", metavar="PATH", help="replace citation keys in a single .tex file or in all .tex files under PATH if it is a directory")
args = parser.parse_args()

if not args.bibfile and not args.replace:
    parser.error("You must specify a .bib file unless using --replace only.")


def vlog(msg):
    if args.verbose:
        tqdm.write(msg)

# --- Citation key replacement helpers ---
def load_changes_from_log(log_path):
    mapping = {}
    if not os.path.exists(log_path):
        return mapping
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or "-->" not in line:
                continue
            old, new = line.split("-->")
            old = old.strip()
            new = new.strip()
            if old and new:
                mapping[old] = new
    return mapping

_CITE_CMD_RE = re.compile(r"\\(cite|citet|citep|citealp|citealt|parencite|textcite|autocite|footcite|footcitetext|nocite)\\*?\s*(?:\[[^\]]*\]\s*){0,2}\{([^}]*)\}")

def _replace_keys_in_block(keys_block, key_map):
    # Split by commas, trim spaces, replace if present in map, then rejoin with a single space after comma
    parts = [p.strip() for p in keys_block.split(",")]
    replaced = []
    changed = False
    for k in parts:
        newk = key_map.get(k, k)
        if newk != k:
            changed = True
        replaced.append(newk)
    return ", ".join(replaced), changed

def replace_citations_in_text(text, key_map):
    changed_any = False
    def _sub(m):
        nonlocal changed_any
        keys_block = m.group(2)
        new_block, changed = _replace_keys_in_block(keys_block, key_map)
        if changed:
            changed_any = True
        # Rebuild the match, keeping the original command and any optional args intact
        full_match = m.group(0)
        # Find the start of the keys block within the full match and replace only inside the braces
        prefix = full_match[:full_match.rfind('{') + 1]
        suffix = full_match[full_match.rfind('}'):]
        return prefix + new_block + suffix

    new_text = _CITE_CMD_RE.sub(_sub, text)
    return new_text, changed_any


# Helper to process a single .tex file
def _process_single_tex_file(path, key_map):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            original = f.read()
        updated, changed = replace_citations_in_text(original, key_map)
        if not changed:
            vlog(f"{CYAN}No citation key changes needed in{RESET} {path}")
            return False
        base, ext = os.path.splitext(path)
        backup = f"{base}-old{ext}"
        if os.path.exists(backup):
            os.remove(backup)
        os.rename(path, backup)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(updated)
        print(f"{GREEN}{ICON_OK} Updated citations in{RESET} {path}  {YELLOW}(backup:{RESET} {backup}{YELLOW}){RESET}")
        return True
    except Exception as e:
        print(f"{RED}{ICON_FAIL} Failed to update{RESET} {path}: {e}")
        return False

# General function to replace citations in either a single file or all .tex files under a directory
def replace_in_tex_dir(root_path, key_map):
    # If a single .tex file was provided, process it directly
    if os.path.isfile(root_path):
        if root_path.endswith('.tex'):
            _process_single_tex_file(root_path, key_map)
        else:
            print(f"{YELLOW}Provided path is a file but not .tex, skipping:{RESET} {root_path}")
        return

    # Otherwise, treat as directory and recurse
    tex_files = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        for fn in filenames:
            if fn.endswith('.tex') and not fn.endswith('-old.tex'):
                tex_files.append(os.path.join(dirpath, fn))
    if not tex_files:
        print(f"{YELLOW}No .tex files found under{RESET} {root_path}")
        return

    for path in tex_files:
        _process_single_tex_file(path, key_map)


citation_key_map = {}
not_found = []

if args.bibfile:
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
        logf = os.path.join(os.path.dirname(os.path.abspath(out_bib)), "citation_key_changes.log")
        print(f"\n{CYAN}==== Citation key changes (old --> new) ===={RESET}")
        for old, new in citation_key_map.items():
            print(f"{old} --> {GREEN}{new}{RESET}")
        with open(logf, "w") as f:
            for old, new in citation_key_map.items():
                f.write(f"{old} --> {new}\n")
        print(f"\n{CYAN}==> Citation key changes have been logged to {BOLD}{logf}{RESET}")

# If requested, perform in-place citation key replacement in .tex files
if args.replace:
    # Prefer in-memory map from the current run, fallback to log file
    mapping = dict(citation_key_map)
    if not mapping:
        if args.bibfile:
            logf = os.path.join(os.path.dirname(os.path.abspath(args.bibfile)), "citation_key_changes.log")
        else:
            logf = "citation_key_changes.log"
        mapping = load_changes_from_log(logf)
    if not mapping:
        print(f"{YELLOW}No citation key changes available to apply. Skipping replacement.{RESET}")
    else:
        print(f"\n{CYAN}==== Replacing citation keys in .tex files under:{RESET} {args.replace}")
        replace_in_tex_dir(args.replace, mapping)
