"""
Re-pull reps.pdf / orgs.pdf / by_state.pdf from DOJ/EOIR and re-run the parser.

The DOJ reports page assigns each PDF a numeric media id that changes
whenever the file is replaced, so this looks the current links up by their
link text on https://www.justice.gov/eoir/recognition-accreditation-roster-reports
instead of hardcoding ids. justice.gov also 403s requests without a normal
browser User-Agent.

Run:  python fetch_eoir_pdfs.py
Need: pip install -r requirements-dev.txt
"""

import re
import sys
from urllib.parse import urljoin

import requests

import eoir_parser

REPORTS_PAGE = "https://www.justice.gov/eoir/recognition-accreditation-roster-reports"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
MIN_PDF_BYTES = 100_000  # sanity floor; a real roster PDF is ~1 MB

# link text on the reports page -> local file it corresponds to
LINK_TEXT_TO_FILE = {
    "Recognized Organizations List": eoir_parser.ORGS_PDF,
    "Accredited Representatives List": eoir_parser.REPS_PDF,
    "Organizations and Representatives, Listed by State": eoir_parser.BY_STATE_PDF,
}

ANCHOR_RE = re.compile(r'<a\s+[^>]*href="([^"]+)"[^>]*>([^<]*)</a>')


def find_pdf_links(html):
    """link text -> absolute URL, for every <a> on the reports page."""
    links = {}
    for href, text in ANCHOR_RE.findall(html):
        text = text.strip()
        if text in LINK_TEXT_TO_FILE:
            links[text] = urljoin(REPORTS_PAGE, href)
    return links


def download_pdf(url, dest_path, session):
    resp = session.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    resp.raise_for_status()
    content_type = resp.headers.get("Content-Type", "")
    if "pdf" not in content_type.lower():
        raise ValueError(f"{url} did not return a PDF (Content-Type: {content_type!r})")
    if len(resp.content) < MIN_PDF_BYTES:
        raise ValueError(f"{url} returned only {len(resp.content)} bytes, expected a full roster PDF")
    with open(dest_path, "wb") as f:
        f.write(resp.content)
    return len(resp.content)


def main():
    session = requests.Session()
    print(f"Fetching {REPORTS_PAGE} ...")
    resp = session.get(REPORTS_PAGE, headers={"User-Agent": USER_AGENT}, timeout=30)
    resp.raise_for_status()

    links = find_pdf_links(resp.text)
    missing = [text for text in LINK_TEXT_TO_FILE if text not in links]
    if missing:
        sys.exit(
            "Could not find a link for: " + ", ".join(missing) + "\n"
            "DOJ likely changed the reports page layout — update LINK_TEXT_TO_FILE "
            "in fetch_eoir_pdfs.py to match the new link text."
        )

    for text, dest_path in LINK_TEXT_TO_FILE.items():
        url = links[text]
        print(f"Downloading {text!r} -> {dest_path} ...")
        size = download_pdf(url, dest_path, session)
        print(f"  {size:,} bytes")

    print()
    eoir_parser.main()


if __name__ == "__main__":
    main()
