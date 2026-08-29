# Buscador de representantes acreditados

A free, Spanish/English tool to check whether the person or organization offering to
help with an immigration case is actually accredited by the U.S. Department of
Justice's Executive Office for Immigration Review (DOJ/EOIR) — before you pay them or
hand over documents.

**Live:** https://eoir-buscador.onrender.com

Independent project. Not affiliated with or endorsed by DOJ, EOIR, or USCIS.

## What it does

- Search a person's name (fuzzy matching tolerates typos/misspellings) or an
  organization's name, and see their current DOJ/EOIR accreditation status.
- Correctly applies 8 CFR 1292.16: a pending renewal doesn't mean someone lost their
  accreditation, and a representative can't act for an organization that has.
- No match doesn't mean a dead end — surfaces real, nearby accredited organizations
  instead of just saying "not found."
- [`/consejos`](https://eoir-buscador.onrender.com/consejos) — fraud-prevention tips
  grounded in current scam tactics (fake AI-generated hearings, cloned social-media
  profiles, fake-detention bail calls), not generic advice.
- No login, no accounts, nothing tracked or stored.

## How the data stays current

DOJ republishes its accredited-representative rosters as three PDFs
(`reps.pdf` / `orgs.pdf` / `by_state.pdf`). `fetch_eoir_pdfs.py` re-downloads them
directly from justice.gov (looked up by link text on the DOJ reports page, since the
underlying file IDs change whenever DOJ replaces a file) and re-runs `eoir_parser.py`
to rebuild `eoir_representatives.json`. A [scheduled GitHub Action](.github/workflows/refresh-eoir-data.yml)
runs this weekly and commits the result if the data changed; the PDFs themselves
aren't tracked in git since they're fully regenerable.

## Running locally

```
pip install -r requirements.txt
python app.py            # http://127.0.0.1:5000
```

To re-pull and re-parse the source data yourself:

```
pip install -r requirements-dev.txt
python fetch_eoir_pdfs.py
```

## Project layout

| File | Purpose |
|---|---|
| `app.py` | Flask web front end |
| `cli.py` | Terminal front end (same `search.py`, no matching logic of its own) |
| `search.py` | All fuzzy-matching logic — the only place either front end reads from |
| `eoir_parser.py` | Parses the three source PDFs into `eoir_representatives.json` |
| `fetch_eoir_pdfs.py` | Downloads the current PDFs from DOJ, then runs the parser |
| `i18n.py` | Spanish/English UI strings |
| `test_cases.py` | Search recall test cases, run via `python search.py` |

## Contact

angelbautistamartinez.tech@gmail.com
