"""
EOIR accredited-representative fuzzy name search.

All matching logic lives here. This module never prints, never formats
for a screen, and never decides what counts as "authorized" — it ranks
records by name similarity and hands the data back. cli.py (and later
app.py) turn the `status` value into words.

Run directly to print the top-5 recall score against test_cases.py:
    python search.py
"""

import json
import re
import unicodedata

from rapidfuzz import fuzz

DATA_PATH = "eoir_representatives.json"

TITLES_SUFFIXES = {
    "sr", "sra", "srta", "jr", "ii", "iii", "iv", "dr", "lic", "esq", "mr", "mrs", "ms",
}

MIN_QUERY_LEN = 3
CANDIDATE_FLOOR = 75  # below this, discard entirely
MAX_RESULTS = 5

STATE_NAME_TO_ABBR = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT",
    "delaware": "DE", "district of columbia": "DC", "florida": "FL",
    "georgia": "GA", "hawaii": "HI", "idaho": "ID", "illinois": "IL",
    "indiana": "IN", "iowa": "IA", "kansas": "KS", "kentucky": "KY",
    "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN",
    "mississippi": "MS", "missouri": "MO", "montana": "MT",
    "nebraska": "NE", "nevada": "NV", "new hampshire": "NH",
    "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
    "north carolina": "NC", "north dakota": "ND", "ohio": "OH",
    "oklahoma": "OK", "oregon": "OR", "pennsylvania": "PA",
    "rhode island": "RI", "south carolina": "SC", "south dakota": "SD",
    "tennessee": "TN", "texas": "TX", "utah": "UT", "vermont": "VT",
    "virginia": "VA", "washington": "WA", "west virginia": "WV",
    "wisconsin": "WI", "wyoming": "WY", "puerto rico": "PR",
    "guam": "GU", "virgin islands": "VI", "american samoa": "AS",
    "northern mariana islands": "MP",
}


# ---------------------------------------------------------------------------
# Normalization — the exact same function runs on the query and every
# stored name, so a query can never drift out of sync with the index.
# ---------------------------------------------------------------------------

def strip_accents(s):
    nfd = unicodedata.normalize("NFD", s)
    return "".join(ch for ch in nfd if unicodedata.category(ch) != "Mn")


def normalize_name(raw):
    """
    'García López, Jr. Juan Carlos' -> ['garcia', 'lopez', 'juan', 'carlos']
    """
    if not raw:
        return []
    s = raw.lower()
    s = strip_accents(s)
    s = re.sub(r"[.,\-'’]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    tokens = [t for t in s.split(" ") if t and t not in TITLES_SUFFIXES]
    return tokens


def normalize_query(raw):
    return normalize_name(raw)


def tokens_to_key(tokens):
    return " ".join(tokens)


# ---------------------------------------------------------------------------
# Index — loaded and normalized once at import time, never re-normalized
# inside a search() call.
# ---------------------------------------------------------------------------

class Index:
    def __init__(self, records):
        self.records = records
        for r in records:
            r["_search_key"] = tokens_to_key(normalize_name(r.get("name", "")))
            r["_org_search_key"] = tokens_to_key(normalize_name(r.get("org", "")))

        # secondary index: distinct orgs, each with its list of reps
        orgs = {}
        for r in records:
            key = r["_org_search_key"]
            if not key:
                continue
            orgs.setdefault(key, {"org": r.get("org"), "reps": []})
            orgs[key]["reps"].append(r)
        self.orgs = list(orgs.values())


_index = None


def load_index(path=DATA_PATH):
    global _index
    if _index is None:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        _index = Index(data["representatives"])
        _index.data_as_of = data.get("data_as_of")
    return _index


def get_data_as_of(path=DATA_PATH):
    """ISO date the underlying DOJ/EOIR PDFs were pulled, for display in a front end."""
    return load_index(path).data_as_of


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------

def _best_token_match_score(query_tokens, target_tokens):
    """
    Average, over each query token, of its best fuzz.ratio against any
    single target token. Catches "one surname misspelled" cases that
    token_set_ratio underscores, because token_set_ratio scores the
    *whole string* and gets dragged down by both the missing tokens
    (query is shorter than the stored name) and the misspelling at once.
    """
    if not query_tokens or not target_tokens:
        return 0
    scores = [
        max(fuzz.ratio(qt, tt) for tt in target_tokens)
        for qt in query_tokens
    ]
    return sum(scores) / len(scores)


def _score_candidates(query_key, keyed_items, key_fn):
    """keyed_items: list of arbitrary objects; key_fn(item) -> search key string."""
    query_tokens = query_key.split(" ")
    scored = []
    for item in keyed_items:
        key = key_fn(item)
        if not key:
            continue
        target_tokens = key.split(" ")
        recall_score = max(
            fuzz.token_set_ratio(query_key, key),
            _best_token_match_score(query_tokens, target_tokens),
        )
        if recall_score < CANDIDATE_FLOOR:
            continue
        precision_score = fuzz.token_sort_ratio(query_key, key)
        scored.append((item, recall_score, precision_score))
    scored.sort(key=lambda t: t[2], reverse=True)
    return scored


def search(query, path=DATA_PATH):
    """
    Search accredited representatives by name.

    Returns:
        {
          "query": str,
          "status": "candidates" | "too_many" | "too_short" | "none",
          "count": int,
          "results": [ {"score": int, "record": {...}, "matched_tokens": [...]} ]
        }
    """
    idx = load_index(path)
    tokens = normalize_query(query)

    if len(query.strip()) < MIN_QUERY_LEN:
        return {"query": query, "status": "too_short", "count": 0, "results": []}

    if not tokens:
        return {"query": query, "status": "too_short", "count": 0, "results": []}

    query_key = tokens_to_key(tokens)

    if len(tokens) == 1:
        matches = [r for r in idx.records if tokens[0] in r["_search_key"].split(" ")]
        if len(matches) > MAX_RESULTS:
            return {"query": query, "status": "too_many", "count": len(matches), "results": []}
        if not matches:
            return {"query": query, "status": "none", "count": 0, "results": []}
        results = [
            {"score": 100, "record": r, "matched_tokens": tokens}
            for r in matches
        ]
        return {"query": query, "status": "candidates", "count": len(results), "results": results}

    scored = _score_candidates(query_key, idx.records, lambda r: r["_search_key"])

    if not scored:
        return {"query": query, "status": "none", "count": 0, "results": []}

    top = scored[:MAX_RESULTS]
    results = [
        {
            "score": round(precision_score),
            "record": record,
            "matched_tokens": [t for t in tokens if t in record["_search_key"].split(" ")],
        }
        for record, _recall_score, precision_score in top
    ]
    return {"query": query, "status": "candidates", "count": len(results), "results": results}


def search_org(query, path=DATA_PATH):
    """
    Search recognized organizations by name. Returns each matching org
    plus its accredited representatives.

    Returns:
        {
          "query": str,
          "status": "candidates" | "too_short" | "none",
          "count": int,
          "results": [ {"score": int, "org": str, "reps": [record, ...]} ]
        }
    """
    idx = load_index(path)
    tokens = normalize_query(query)

    if len(query.strip()) < MIN_QUERY_LEN or not tokens:
        return {"query": query, "status": "too_short", "count": 0, "results": []}

    query_key = tokens_to_key(tokens)
    scored = _score_candidates(query_key, idx.orgs, lambda o: tokens_to_key(normalize_name(o["org"])))

    if not scored:
        return {"query": query, "status": "none", "count": 0, "results": []}

    top = scored[:MAX_RESULTS]
    results = [
        {"score": round(precision_score), "org": org["org"], "reps": org["reps"]}
        for org, _recall_score, precision_score in top
    ]
    return {"query": query, "status": "candidates", "count": len(results), "results": results}


def nearby_orgs(location, path=DATA_PATH, limit=5):
    """
    Recognized organizations near a free-text city/state, for the
    not-found path: someone didn't find who they were looking for, so
    point them at legitimate organizations near them instead.

    Returns: [{"org": str, "city": str, "state": str, "phone": str}, ...]
    City matches are ranked above state-only matches.
    """
    idx = load_index(path)
    loc = location.strip().lower()
    if not loc:
        return []
    target_state = STATE_NAME_TO_ABBR.get(loc) or (loc.upper() if len(loc) == 2 else None)

    matches = []
    for org in idx.orgs:
        located = next(
            (r for r in org["reps"] if r.get("org_city") and r.get("org_state")),
            None,
        )
        if not located:
            continue
        city, state = located["org_city"], located["org_state"]
        city_match = loc in city.lower()
        state_match = target_state is not None and state == target_state
        if not (city_match or state_match):
            continue
        matches.append({
            "org": org["org"],
            "city": city,
            "state": state,
            "phone": located.get("org_phone"),
            "_city_match": city_match,
        })

    matches.sort(key=lambda m: 0 if m["_city_match"] else 1)
    for m in matches:
        del m["_city_match"]
    return matches[:limit]


if __name__ == "__main__":
    from test_cases import CASES

    hits = 0
    failures = []
    for query, expected_name in CASES:
        result = search(query)
        names = [r["record"]["name"] for r in result["results"]]
        if expected_name in names:
            hits += 1
        else:
            failures.append(query)

    total = len(CASES)
    print(f"Top-5 recall: {hits}/{total} ({hits / total:.1%})")
    if failures:
        print(f"Failures: {', '.join(repr(f) for f in failures)}")
