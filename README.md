https://github.com/Rakt-Seva/inspire-citation/releases

[![Releases](https://img.shields.io/github/v/release/Rakt-Seva/inspire-citation?label=Releases&style=for-the-badge)](https://github.com/Rakt-Seva/inspire-citation/releases)

# inspire-citation: Batch-sync BibTeX with InspireHEP CLI

🔁 📚 🔬 A command-line tool to update and sync your BibTeX file with records from InspireHEP. Designed for researchers in high-energy physics and related fields. Use it to refresh metadata, pull missing DOIs and arXiv IDs, and keep your bibliography clean and consistent.

[![Topics](https://img.shields.io/badge/topics-academic--tools%20%7C%20automation%20%7C%20bibliography--management%20%7C%20bibtex%20%7C%20cli%20%7C%20hep%20%7C%20inspirehep%20%7C%20python--blue?style=for-the-badge)](https://github.com/Rakt-Seva/inspire-citation)

- Repository: inspire-citation
- Purpose: Batch-update your BibTeX file to sync citations from InspireHEP.net
- Language: Python
- Topics: academic-tools, automation, bibliography-management, bibtex, cli, hep, high-energy-physics, inspirehep, python, research-tools

---

Table of Contents

- About
- Why this tool
- Key features
- How it works
- Install
- Releases and download
- Quick start
- Command reference
- Configuration file
- Field mapping and merge rules
- Deduplication and key management
- Examples and workflows
- Pre-commit and CI integration
- Error handling and logs
- Development and testing
- Contributing
- License
- Acknowledgements and links

About

inspire-citation scans a BibTeX file and looks up matching records on InspireHEP. It updates fields such as title, authors, journal, volume, pages, year, DOI, and arXiv identifiers. It can also add links and metadata that InspireHEP exposes. The tool aims to keep citation entries accurate and consistent across projects.

Why this tool

- Keep BibTeX entries accurate and consistent.
- Fix missing DOIs, arXiv IDs, and journal data.
- Merge authoritative data from InspireHEP while preserving local edits.
- Batch-process many entries in a single run.
- Integrate into pre-commit hooks or CI pipelines.
- Support common workflows of physicists and HEP researchers.

Key features

- CLI interface that takes input and output paths.
- Dry-run mode that shows changes without writing files.
- Backup of the original file on first write.
- Merge strategies: prefer-inspire, prefer-local, smart-merge.
- Deduplication by DOI, arXiv ID, or exact title match.
- Add/update INSPIRE fields like `eprint`, `eprinttype`, `doi`, `reportnumber`.
- Add a sync tag field for traceability (timestamp and source).
- Support for multiple BibTeX dialects (classic BibTeX, BibLaTeX field names).
- JSON output option that lists changes made.
- Config file support (YAML or TOML) for project defaults.
- Pre-commit hook template and CI snippets.

How it works

1. The CLI reads your BibTeX file.
2. It extracts candidate identifiers: DOI, arXiv ID, or title.
3. For each entry, it queries the InspireHEP API.
4. The tool computes a match score for candidates.
5. It applies the merge strategy you set.
6. It writes the updated entries to a new file or overwrites the input file.
7. It creates a backup file named <input>.backup.bib on first write.

The tool uses InspireHEP search by DOI, arXiv number, and title. It uses the InspireHEP REST endpoints and parses JSON responses. When multiple records match, it picks the best match by DOI or arXiv first, then by title and author overlap.

Install

Options: pip, source, release binary.

- From PyPI (if published)

  ```
  pip install inspire-citation
  ```

- From source

  ```
  git clone https://github.com/Rakt-Seva/inspire-citation.git
  cd inspire-citation
  python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  pip install -e .
  ```

- From releases

  The releases page contains packaged binaries and prebuilt wheels. Download and run the file listed on the Releases page. For example, if the release provides a binary named `inspire-citation-linux-x86_64.tar.gz`, download that file and extract it, then run the contained `inspire-citation` executable.

  Download and execute the release asset from:
  https://github.com/Rakt-Seva/inspire-citation/releases

Releases and download

The Releases page lists official releases, assets, and checksums. If you pick a release asset, download the file and execute it according to the platform instructions. The releases page also hosts signed artifacts.

https://github.com/Rakt-Seva/inspire-citation/releases

Quick start

- Basic update with overwrite:

  ```
  inspire-citation update --input references.bib --overwrite
  ```

- Dry run to preview changes:

  ```
  inspire-citation update --input references.bib --dry-run
  ```

- Update and write to a new file:

  ```
  inspire-citation update --input references.bib --output references.synced.bib
  ```

- Use a project config:

  ```
  inspire-citation update --config .inspirecitrc --input refs.bib
  ```

- Batch update multiple files:

  ```
  inspire-citation update --input refs/*.bib --output-dir synced/
  ```

Command reference

Main entry: inspire-citation

Subcommands:

- update: Update entries in one or more BibTeX files.
- check: Report which entries need updates without changing files.
- validate: Validate BibTeX syntax and common issues.
- config: Show or edit configuration settings.
- hook: Install a pre-commit hook or Git hook template.

Common flags:

- --input, -i: Path to input file or glob.
- --output, -o: Output file or pattern.
- --output-dir: Directory for multiple outputs.
- --overwrite: Overwrite the input file.
- --dry-run: Print proposed changes without writing files.
- --merge-strategy: Strategy to merge InspireHEP data. Options: prefer-inspire, prefer-local, smart-merge.
- --backup: Create a backup before writing.
- --threads: Number of concurrent API workers.
- --timeout: HTTP timeout in seconds.
- --api-url: Custom InspireHEP API URL (useful for testing).
- --api-key: API key if you have one (InspireHEP supports anonymous queries; an API key can raise rate limits).
- --format: Output format: bibtex or json.
- --verbose: Increase logging detail.
- --quiet: Reduce output.

Examples

1) Sync DOIs and arXiv IDs while keeping local notes

```
inspire-citation update -i myrefs.bib -o myrefs.synced.bib --merge-strategy smart-merge --backup
```

Behavior:

- For each entry, the tool updates DOI and arXiv fields if InspireHEP has them.
- It preserves local `note` and `abstract` fields unless you set `--merge-strategy prefer-inspire`.
- It writes a `.backup.bib` file first.

2) Force authoritative data from InspireHEP

```
inspire-citation update -i myrefs.bib --overwrite --merge-strategy prefer-inspire
```

Behavior:

- Replace conflicting fields with InspireHEP values.
- Keep local citation keys unless you opt for `--rewrite-keys`.

3) Dry-run and JSON report

```
inspire-citation update -i myrefs.bib --dry-run --format json > report.json
```

The JSON shows changes for each entry: fields added, fields updated, and match score.

Configuration file

Project settings live in `.inspirecitrc` or `pyproject.toml` under a `[tool.inspire-citation]` table. The config file can be YAML, TOML, or JSON. Example YAML:

```
# .inspirecitrc
api_url: "https://inspirehep.net/api"
api_key: ""
merge_strategy: "smart-merge"
backup: true
threads: 4
timeout: 10
fields:
  preserve:
    - note
    - abstract
    - keywords
  prefer_inspire:
    - title
    - journal
    - doi
    - eprint
dedupe:
  method: "doi_then_arxiv"
  resolution: "keep-first"
sync_tag_field: "inspire_synced"
sync_tag_value_template: "{source}:{timestamp}"
```

Field mapping and merge rules

The tool maps InspireHEP JSON to BibTeX fields. It understands common HEP metadata and maps them to standard BibTeX or BibLaTeX names.

Common mappings

- Inspire -> BibTeX
  - title -> title
  - authors -> author (format: "Last, First and ...")
  - journal_title -> journal
  - journal_volume -> volume
  - journal_issue -> number
  - page_start, page_end -> pages (merged as "start--end")
  - publication_year -> year
  - doi -> doi
  - arxiv eprint -> eprint / eprinttype=arXiv
  - reportnumber -> reportnumber
  - collaboration -> collaboration
  - abstract -> abstract
  - keywords -> keywords
  - url -> url

Merge strategies

- prefer-inspire: Replace local fields with InspireHEP values when available.
- prefer-local: Keep local fields when they exist and only add missing fields from InspireHEP.
- smart-merge (default): Update authoritative fields (doi, eprint, journal, year), preserve local annotation fields (note, keywords), and attempt to unify authors and titles while preserving formatting tweaks.

Conflict resolution

- DOI or arXiv conflicts trigger a review. If a DOI exists locally and InspireHEP returns a different DOI, the tool will flag the conflict. You can auto-resolve with:
  - --resolve-conflicts prefer-inspire
  - --resolve-conflicts prefer-local
  - --resolve-conflicts abort (stop on conflict)

Deduplication and key management

Deduplication methods

- doi_then_arxiv: Find duplicates by DOI first, then by arXiv ID.
- exact_title: Exact title match.
- fuzzy_title: Levenshtein distance on titles with a threshold.

Resolution strategies

- keep-first: Keep the first occurrence, drop others.
- merge: Merge entries into a single canonical entry.
- rename: Keep both entries and rename keys.

Citation key templates

You can set a key pattern in the config:

```
key_template: "{author_last}_{year}_{short_title}"
```

The tool can rewrite keys with `--rewrite-keys`. It provides a stable hash fallback to avoid collisions.

Examples and workflows

Workflow 1: Personal bibliography maintenance

- Keep a `references.bib` file in your research project.
- Run `inspire-citation update --input references.bib --dry-run` before major edits.
- Review the diff. Then run with `--overwrite --backup`.

Workflow 2: Lab or group bibliography

- Use a shared `group-refs.bib`.
- Add a CI job that runs `inspire-citation check` on pull requests.
- Use `--merge-strategy prefer-inspire` to enforce authoritative metadata.
- Use `--dedupe merge` to combine duplicates from multiple contributors.

Workflow 3: Pre-commit integration

- Install the pre-commit hook with:

  ```
  inspire-citation hook install --type pre-commit --path .git/hooks/pre-commit
  ```

- Add this sample `.pre-commit-config.yaml` entry:

  ```
  - repo: local
    hooks:
      - id: inspire-citation
        name: inspire-citation sync
        entry: inspire-citation update --input references.bib --dry-run
        language: system
        files: \.bib$
  ```

Pre-commit runs a dry-run check to avoid blocking commits for auto-changes. You can also run a full sync in CI after merges.

Advanced options

- Parallel queries: Use `--threads` to speed up network-bound lookups.
- Rate limits: Set `--timeout` and consider `--api-key` to increase rate limits if available.
- Custom API URL: Use `--api-url` to point to a test server or mirror.
- Log format: JSON log mode for machine parsing with `--format json`.
- Verbose logging: `--verbose` shows HTTP requests and raw InspireHEP responses.
- Output filters: Use `--only-fields` or `--exclude-fields` to limit updates to specific fields.

Example: update only DOIs and eprints

```
inspire-citation update -i refs.bib --merge-strategy prefer-inspire --only-fields doi,eprint
```

Error handling and logs

- The tool logs network errors and retries with exponential backoff.
- If the API returns multiple candidate records with low match scores, the tool lists them. You can set the threshold with `--min-match-score`.
- Use `--dry-run` to test a strategy and `--format json` to store the change list.
- When a conflict requires user input and you run in non-interactive mode, resolve using `--resolve-conflicts`.

Sample log output (verbose)

```
INFO  [0001] Reading input file: refs.bib
INFO  [0002] Found 128 entries
INFO  [0003] Querying InspireHEP for DOI: 10.1103/PhysRevD.58.014001
DEBUG [0003] API GET https://inspirehep.net/api/literature?q=doi:10.1103/PhysRevD.58.014001
INFO  [0003] Match found: 1234567 (score: 98)
INFO  [0003] Fields to update: doi (same), journal (updated), pages (updated)
INFO  [0004] Querying InspireHEP for title match: "Measurement of the Higgs boson mass"
WARN  [0004] Multiple candidates found (3). Best score: 60
DEBUG [0004] Candidate list: [...]
```

Development and testing

- Virtual environment

  ```
  python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements-dev.txt
  ```

- Run tests

  ```
  pytest tests/
  ```

- Lint and format

  ```
  black .
  ruff .
  isort .
  ```

- API mocking

  Use the built-in test fixtures that mock InspireHEP responses. The dev server runs at `http://localhost:5000/mock-inspire`.

- Run CLI locally

  ```
  python -m inspire_citation.cli update -i tests/fixtures/sample.bib --dry-run
  ```

Contributing

The project follows a simple workflow.

1. Fork the repo.
2. Create a feature branch.
3. Write tests for your change.
4. Run the test suite.
5. Open a pull request.

Guidelines

- Keep commits focused and small.
- Write descriptive commit messages with the template: `type(scope): short description`.
- Add unit tests for new logic.
- Keep code style consistent with Black and Ruff.

Issue templates

- Bug report: Include sample BibTeX, command used, and expected vs actual output.
- Feature request: Describe use case and expected behavior.

Maintainers

- Maintainer: Rakt-Seva (see repository for contact and maintainers list)
- Triage and review happen via PRs on the main repo.

License

- MIT License. See LICENSE file in the repository.

Acknowledgements and links

- InspireHEP API: https://inspirehep.net
- arXiv: https://arxiv.org
- BibTeX format reference: http://bibtex.org
- img.shields.io badges used for repository status and links.

Badges and visuals

- Releases badge (click to open releases):  
  [![Releases](https://img.shields.io/github/v/release/Rakt-Seva/inspire-citation?label=Releases&style=for-the-badge)](https://github.com/Rakt-Seva/inspire-citation/releases)

- Example image banner (inspired by HEP theme):

  ![HEP Banner](https://upload.wikimedia.org/wikipedia/commons/0/05/CERN_logo_(577x64).svg)

  (Use of a banner is optional. Replace with a project image if you have one.)

API and rate limits

- The default InspireHEP API allows anonymous queries with reasonable limits.
- If you expect heavy usage, request an API key from InspireHEP and pass it with `--api-key`.
- The CLI implements polite backoff and respects `Retry-After` headers.

Sample entry before and after

Before

```
@article{smith2012higgs,
  title = {Measurement of the Higgs boson mass},
  author = {Smith, John and Doe, Jane},
  year = {2012},
  note = {Personal copy}
}
```

After (smart-merge)

```
@article{smith_2012_measurement,
  title = {Measurement of the Higgs boson mass},
  author = {Smith, John and Doe, Jane and Collaboration, Example},
  journal = {Phys. Rev. D},
  volume = {85},
  pages = {012345},
  year = {2012},
  doi = {10.1103/PhysRevD.85.012345},
  eprint = {1204.12345},
  eprinttype = {arXiv},
  note = {Personal copy},
  inspire_synced = {inspire:2025-08-16T12:34:56Z}
}
```

Mapping notes

- The tool will add `eprinttype = {arXiv}` when it adds an arXiv eprint.
- It writes a `inspire_synced` field (or other tag as configured) for traceability.
- It avoids clobbering `note` and `abstract` unless you set `prefer-inspire`.

Security

- Do not commit API keys. Use environment variables or a config file excluded from the repo.
- The CLI reads `INSPIRE_CITATION_API_KEY` environment variable if set.
- Use the releases page to download signed artifacts when available.

Release assets and execution

The releases page hosts packaged artifacts. If a release contains an asset with a path or binary, download that file and execute it according to OS. For example:

- Linux tarball: download, extract, and run `./inspire-citation`.
- Windows ZIP: download, extract, and run `inspire-citation.exe`.
- Wheel: `pip install inspire_citation-<version>-py3-none-any.whl`.

Download and execute the release asset from:
https://github.com/Rakt-Seva/inspire-citation/releases

Resources and links

- InspireHEP API docs: https://inspirehep.net/info/hep/api
- arXiv identifier guide: https://arxiv.org/help/arxiv_identifier
- BibTeX reference: http://bibtex.org
- Example pre-commit hooks: https://pre-commit.com

Contact and support

- Open an issue on GitHub for bugs or feature requests.
- Use PRs for code contributions.
- For questions about usage, include a minimal example that reproduces the issue.

Changelog snippets (example)

- v1.2.0
  - Add smart-merge strategy.
  - Add JSON output for CI.
  - Improve author parsing and normalization.

- v1.1.0
  - Add deduplication by DOI and arXiv.
  - Add backup behavior.

- v1.0.0
  - Initial release with core update logic and CLI.

Common FAQs

Q: How does the tool match entries?
A: It prefers DOI or arXiv when available. When only a title exists, it uses normalized title matching and author overlap. You can set thresholds in the config.

Q: Will it change my citation keys?
A: Not by default. Use `--rewrite-keys` to rename keys based on the template.

Q: I use BibLaTeX. Will it work?
A: Yes. The tool maps to common BibLaTeX fields and respects `biblatex`-style fields when detected.

Q: Can I run this on many files?
A: Yes. Use glob patterns or pass a directory with `--output-dir`.

Q: Does the tool edit abstracts?
A: Only if you set the merge strategy to replace abstracts. By default it preserves local abstracts.

Sample CI job (GitHub Actions)

```
name: BibTeX check
on: [pull_request]
jobs:
  inspire-sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install inspire-citation
        run: pip install inspire-citation
      - name: Run dry-run update
        run: inspire-citation update --input references.bib --dry-run --format json > sync_report.json
      - name: Upload report
        uses: actions/upload-artifact@v4
        with:
          name: sync-report
          path: sync_report.json
```

Extending the tool

- Add a plugin for other bibliographic services (CrossRef, PubMed).
- Add a GUI front-end for manual review.
- Add more normalization rules for author names and diacritics.

Testing tips

- Use the `tests/fixtures` to simulate different states.
- Mock the InspireHEP API to avoid flakiness.
- Run tests in CI with network access disabled by default.

Files and structure (example)

- inspire_citation/
  - cli.py
  - core.py
  - api.py
  - bibparser.py
  - merge.py
  - dedupe.py
  - config.py
  - tests/
  - docs/

Contact points

- Use GitHub issues for bug reports.
- Submit PRs for fixes or features.
- Maintain a changelog in `CHANGELOG.md`.

Legal

- The project uses the MIT license.
- Respect InspireHEP terms when using their API.

Acknowledgements

- InspireHEP for metadata and API.
- arXiv and publishers for citation metadata.
- Many open-source libraries for BibTeX parsing and HTTP client code.

Images and emojis

- Use emojis to make sections clear: 🔁 (sync), 📚 (bibliography), 🔬 (HEP), ⚙️ (settings)
- Use an existing public image for a banner or logo. The README includes a CERN logo example for a HEP theme. Replace with a project logo if available.

Any release artifacts you download from the Releases page must be executed as appropriate for your platform. Check the release notes and checksums before running binaries. Download and execute the release asset from:
https://github.com/Rakt-Seva/inspire-citation/releases

Maintenance tips

- Run `inspire-citation check` as part of CI.
- Periodically run a full sync to catch updates.
- Keep backups of canonical bibliographies.

This README provides a complete guide to install, run, configure, and extend inspire-citation for HEP and research workflows.