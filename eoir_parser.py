"""
EOIR roster parser — reps.pdf + orgs.pdf + by_state.pdf -> one clean JSON
per accredited representative.

Run:  python eoir_parser.py
Need: pip install pdfplumber
"""

import datetime
import json
import os
import re
import pdfplumber

REPS_PDF = "reps.pdf"
ORGS_PDF = "orgs.pdf"
BY_STATE_PDF = "by_state.pdf"
OUT_JSON = "eoir_representatives.json"

US_STATES = {
    "ALABAMA", "ALASKA", "ARIZONA", "ARKANSAS", "CALIFORNIA", "COLORADO",
    "CONNECTICUT", "DELAWARE", "DISTRICT OF COLUMBIA", "FLORIDA", "GEORGIA",
    "HAWAII", "IDAHO", "ILLINOIS", "INDIANA", "IOWA", "KANSAS", "KENTUCKY",
    "LOUISIANA", "MAINE", "MARYLAND", "MASSACHUSETTS", "MICHIGAN",
    "MINNESOTA", "MISSISSIPPI", "MISSOURI", "MONTANA", "NEBRASKA", "NEVADA",
    "NEW HAMPSHIRE", "NEW JERSEY", "NEW MEXICO", "NEW YORK",
    "NORTH CAROLINA", "NORTH DAKOTA", "OHIO", "OKLAHOMA", "OREGON",
    "PENNSYLVANIA", "RHODE ISLAND", "SOUTH CAROLINA", "SOUTH DAKOTA",
    "TENNESSEE", "TEXAS", "UTAH", "VERMONT", "VIRGINIA", "WASHINGTON",
    "WEST VIRGINIA", "WISCONSIN", "WYOMING", "PUERTO RICO", "GUAM",
    "VIRGIN ISLANDS", "AMERICAN SAMOA", "NORTHERN MARIANA ISLANDS",
}

PHONE_RE = re.compile(r"\(\d{3}\)\s?\d{3}-\d{4}")
CITY_STATE_ZIP_RE = re.compile(
    r"^(?P<city>.+?),\s*(?P<state>[A-Z]{2})\s+(?P<zip>\d{5}(?:-\d{4})?)\s*$"
)
DATE_RE = re.compile(r"(\d{2})/(\d{2})/(\d{2})")
OFFICE_LABEL_RE = re.compile(r"^(Principal Office|.+ Extension Office)$")


def norm_ws(s):
    """Collapse embedded newlines / whitespace runs into single spaces."""
    if s is None:
        return ""
    return re.sub(r"\s+", " ", s).strip()


def norm_key(s):
    """Lowercase, punctuation-stripped key for joining/searching names."""
    s = re.sub(r"[^a-z0-9]+", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def two_digit_year_to_iso(mm, dd, yy):
    yy = int(yy)
    year = 1900 + yy if yy >= 69 else 2000 + yy
    return f"{year:04d}-{mm}-{dd}"


def parse_date_field(raw):
    """
    '10/18/25*\\n(Pending\\nRenewal)' -> ('2025-10-18', True)
    '11/01/26'                        -> ('2026-11-01', False)
    ''  / None                        -> (None, False)
    """
    text = norm_ws(raw)
    if not text:
        return None, False
    pending = "pending renewal" in text.lower() or "*" in text
    m = DATE_RE.search(text)
    if not m:
        return None, pending
    mm, dd, yy = m.groups()
    return two_digit_year_to_iso(mm, dd, yy), pending


def parse_name_field(raw):
    """
    'Abdelnabi, Elfatih\\n(DHS only)' -> ('Abdelnabi, Elfatih', 'DHS_ONLY')
    'Adonis, Guerly'                  -> ('Adonis, Guerly', 'FULL')
    """
    text = norm_ws(raw)
    scope = "FULL"
    m = re.search(r"\(DHS only\)\s*$", text, re.IGNORECASE)
    if m:
        scope = "DHS_ONLY"
        text = text[: m.start()].strip().rstrip(",").strip()
        # re-attach: names never end with a dangling comma after strip
    return text, scope


def is_header_or_junk_row(row, org_first):
    """Section-letter rows ('A', None,...) and repeated header rows."""
    c0 = norm_ws(row[0]) if row[0] else ""
    if not c0:
        return True
    if len(c0) <= 2 and all(not norm_ws(c) for c in row[1:]):
        return True  # e.g. 'A' section divider
    header_markers = ("Accredited", "Recognized\nOrganization", "Recognized Organization")
    if row[0] and any(h in row[0] for h in header_markers):
        return True
    return False


# ---------------------------------------------------------------------------
# reps.pdf  /  orgs.pdf  ->  base rep-org records
# ---------------------------------------------------------------------------

def parse_reps_pdf(path):
    """columns: rep name, rep exp, rep status, org, org recognized, org exp, org status"""
    records = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                for row in table:
                    if len(row) != 7 or is_header_or_junk_row(row, org_first=False):
                        continue
                    if not row[0]:
                        continue
                    name, scope = parse_name_field(row[0])
                    if not name:
                        continue
                    exp_iso, pending = parse_date_field(row[1])
                    org_exp_iso, org_pending = parse_date_field(row[5])
                    records.append({
                        "name": name,
                        "name_normalized": norm_key(name),
                        "scope": scope,
                        "expiration": exp_iso,
                        "pending_renewal": pending,
                        "status": norm_ws(row[2]) or None,
                        "org": norm_ws(row[3]) or None,
                        "org_recognized": parse_date_field(row[4])[0],
                        "org_expiration": org_exp_iso,
                        "org_pending_renewal": org_pending,
                        "org_status": norm_ws(row[6]) or None,
                    })
    return records


def parse_orgs_pdf(path):
    """columns: org, recognized, exp, status, rep name, rep exp, rep status
    org fields are blank/None on continuation rows -> forward-fill."""
    records = []
    cur = {"org": None, "org_recognized": None, "org_expiration": None,
           "org_pending_renewal": False, "org_status": None}
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                for row in table:
                    if len(row) != 7:
                        continue
                    c0 = norm_ws(row[0]) if row[0] else ""
                    header_markers = ("Recognized\nOrganization", "Recognized Organization")
                    if row[0] and any(h in row[0] for h in header_markers):
                        continue
                    if len(c0) <= 2 and c0 and all(not norm_ws(c) for c in row[1:]):
                        continue  # section-letter divider

                    if row[0]:  # new org starts here -> update forward-fill context
                        org_exp_iso, org_pending = parse_date_field(row[2])
                        cur = {
                            "org": norm_ws(row[0]) or None,
                            "org_recognized": parse_date_field(row[1])[0],
                            "org_expiration": org_exp_iso,
                            "org_pending_renewal": org_pending,
                            "org_status": norm_ws(row[3]) or None,
                        }

                    if not row[4]:  # no rep on this row (shouldn't normally happen)
                        continue
                    name, scope = parse_name_field(row[4])
                    if not name:
                        continue
                    exp_iso, pending = parse_date_field(row[5])
                    records.append({
                        "name": name,
                        "name_normalized": norm_key(name),
                        "scope": scope,
                        "expiration": exp_iso,
                        "pending_renewal": pending,
                        "status": norm_ws(row[6]) or None,
                        **cur,
                    })
    return records


# ---------------------------------------------------------------------------
# by_state.pdf  ->  org address book
# ---------------------------------------------------------------------------

def split_org_cell_into_locations(cell_text):
    """
    A single table cell can contain ONE or MORE physical-office blocks
    concatenated with \\n (PDF extraction quirk), each shaped:
        <org name line(s)>
        Principal Office | <...> Extension Office
        <address line(s), last one 'City, ST ZIP'>
        <(phone) line>            <- optional
    Returns a list of dicts: org_name, office_label, city, state, zip, phone.
    """
    lines = [l for l in cell_text.split("\n")]
    blocks = []
    i = 0
    n = len(lines)
    while i < n:
        name_lines = []
        while i < n and not OFFICE_LABEL_RE.match(lines[i].strip()):
            if lines[i].strip():
                name_lines.append(lines[i].strip())
            i += 1
        if i >= n:
            # no office label found for trailing text -> not a real block
            break
        office_label = lines[i].strip()
        i += 1
        addr_lines = []
        city = state = zipc = None
        while i < n:
            line = lines[i].strip()
            m = CITY_STATE_ZIP_RE.match(line)
            if m:
                addr_lines.append(line)
                city, state, zipc = m.group("city"), m.group("state"), m.group("zip")
                i += 1
                break
            addr_lines.append(line)
            i += 1
        phone = None
        if i < n and PHONE_RE.match(lines[i].strip()):
            phone = lines[i].strip()
            i += 1
        blocks.append({
            "org_name": norm_ws(" ".join(name_lines)),
            "office_label": office_label,
            "org_address": " | ".join(addr_lines),
            "org_city": city,
            "org_state": state,
            "org_zip": zipc,
            "org_phone": phone,
        })
    return blocks


def parse_by_state_pdf(path):
    """Returns dict: normalized org name -> list of location dicts."""
    org_locations = {}
    cur_state = None
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                for row in table:
                    if len(row) != 4:
                        continue
                    c0 = row[0].strip() if row[0] else ""
                    others_blank = all(not norm_ws(c) for c in row[1:])

                    if not c0:
                        continue
                    if others_blank and c0.upper() == c0 and c0 in US_STATES:
                        cur_state = c0
                        continue
                    if "Recognized" in c0 and "Organization" in c0:
                        continue  # column header row
                    if others_blank:
                        continue  # city header row; address itself carries city

                    # actual org/address row
                    for loc in split_org_cell_into_locations(row[0]):
                        loc["state_header"] = cur_state
                        key = norm_key(loc["org_name"])
                        if not key:
                            continue
                        org_locations.setdefault(key, []).append(loc)
    return org_locations


# ---------------------------------------------------------------------------
# merge + join
# ---------------------------------------------------------------------------

def merge_rep_sources(reps_records, orgs_records):
    """Union on name_normalized; prefer reps.pdf, fill any gaps from orgs.pdf."""
    by_key = {}
    for r in reps_records:
        by_key[r["name_normalized"]] = r
    added = 0
    for r in orgs_records:
        if r["name_normalized"] not in by_key:
            by_key[r["name_normalized"]] = r
            added += 1
    return list(by_key.values()), added


def attach_address(rep, org_locations):
    key = norm_key(rep["org"] or "")
    locs = org_locations.get(key)
    if not locs:
        rep["org_city"] = None
        rep["org_state"] = None
        rep["org_phone"] = None
        rep["org_address_match"] = False
        return
    principal = next((l for l in locs if l["office_label"] == "Principal Office"), locs[0])
    rep["org_city"] = principal["org_city"]
    rep["org_state"] = principal["org_state"]
    rep["org_phone"] = principal["org_phone"]
    rep["org_address_match"] = True


def source_pdfs_data_as_of():
    """
    The DOJ/EOIR list is only as fresh as the day these PDFs were pulled
    from justice.gov — not the day the parser happened to run. Use the
    newest of the three source files' mtimes as that download date.
    """
    newest = max(os.path.getmtime(p) for p in (REPS_PDF, ORGS_PDF, BY_STATE_PDF))
    return datetime.date.fromtimestamp(newest).isoformat()


def main():
    print("Parsing reps.pdf ...")
    reps_records = parse_reps_pdf(REPS_PDF)
    print(f"  {len(reps_records)} rep rows")

    print("Parsing orgs.pdf ...")
    orgs_records = parse_orgs_pdf(ORGS_PDF)
    print(f"  {len(orgs_records)} rep rows")

    merged, added = merge_rep_sources(reps_records, orgs_records)
    print(f"Merged: {len(merged)} unique reps ({added} added only from orgs.pdf)")

    print("Parsing by_state.pdf ...")
    org_locations = parse_by_state_pdf(BY_STATE_PDF)
    total_locs = sum(len(v) for v in org_locations.values())
    print(f"  {len(org_locations)} unique org keys, {total_locs} physical locations")

    for rep in merged:
        attach_address(rep, org_locations)

    matched = sum(1 for r in merged if r["org_address_match"])
    dhs_only = sum(1 for r in merged if r["scope"] == "DHS_ONLY")
    pending = sum(1 for r in merged if r["pending_renewal"])
    print(f"\nAddress match: {matched}/{len(merged)} ({matched/len(merged):.1%})")
    print(f"DHS_ONLY scope: {dhs_only}/{len(merged)} ({dhs_only/len(merged):.1%})")
    print(f"Pending renewal: {pending}/{len(merged)} ({pending/len(merged):.1%})")

    data_as_of = source_pdfs_data_as_of()
    output = {
        "data_as_of": data_as_of,
        "generated_at": datetime.date.today().isoformat(),
        "representatives": merged,
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nWrote {OUT_JSON} (data_as_of: {data_as_of})")

    print("\n--- sample records ---")
    for r in merged[:3]:
        print(json.dumps(r, indent=2, ensure_ascii=False))

    # spot checks called out explicitly by the task
    print("\n--- spot checks ---")
    for r in merged:
        if r["name_normalized"].startswith("aganga williams"):
            print("Aganga-Williams (expect Active, DHS_ONLY, pending_renewal True):")
            print(json.dumps(r, indent=2, ensure_ascii=False))
            break
    for r in merged:
        if "catholic charities of santa clara" == norm_key(r["org"] or ""):
            print(f"Catholic Charities Santa Clara org_recognized (expect 1976-xx-xx): {r['org_recognized']}")
            break


if __name__ == "__main__":
    main()
