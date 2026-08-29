"""
EOIR accredited-representative search — web front end.

All matching lives in search.py. This file only turns `status` values
and records into Spanish-language HTML, the same way cli.py turns them
into Spanish-language terminal output. Neither front end contains any
matching logic.

Local dev:   python app.py            (debug off unless FLASK_DEBUG=1)
Production:  gunicorn wsgi:app        (see wsgi.py / Procfile)
Need:        pip install -r requirements.txt
"""

import os
from urllib.parse import urlencode

from flask import Flask, render_template, request, abort, g

from search import search, search_org, nearby_orgs, get_data_as_of
from i18n import SUPPORTED_LANGS, DEFAULT_LANG, t

FIND_LEGAL_SERVICES_URL = "https://www.uscis.gov/scams-fraud-and-misconduct/avoid-scams/find-legal-services"

MESES_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]
MESES_EN = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

app = Flask(__name__)


def format_date(iso_date, lang):
    if not iso_date:
        return None
    y, m, d = (int(p) for p in iso_date.split("-"))
    if lang == "en":
        return f"{MESES_EN[m - 1]} {d}, {y}"
    return f"{d} de {MESES_ES[m - 1]} de {y}"


@app.before_request
def set_lang():
    lang = request.args.get("lang")
    if lang not in SUPPORTED_LANGS:
        lang = request.cookies.get("lang")
    if lang not in SUPPORTED_LANGS:
        lang = DEFAULT_LANG
    g.lang = lang


def lang_switch_url(new_lang):
    """Current path with `lang` swapped — not url_for(request.endpoint, ...),
    since request.endpoint is None on a 404/unmatched route."""
    args = request.args.to_dict(flat=True)
    args["lang"] = new_lang
    return f"{request.path}?{urlencode(args)}"


def is_currently_authorized(r):
    """
    Per 8 CFR 1292.16, a timely-filed renewal keeps accreditation/recognition
    valid while EOIR reviews it — "pending renewal" is not a lapse. Both the
    representative's own status AND their organization's status must be
    Active; a rep can't act for an organization that has lost recognition.
    """
    return r.get("status") == "Active" and r.get("org_status") == "Active"


@app.context_processor
def inject_i18n():
    return {
        "lang": g.lang,
        "t": lambda key: t(g.lang, key),
        "lang_switch_url": lang_switch_url,
        "data_as_of_line": (
            t(g.lang, "footer_updated").format(date=format_date(get_data_as_of(), g.lang))
            if get_data_as_of() else None
        ),
    }


@app.after_request
def set_security_headers(response):
    if request.args.get("lang") in SUPPORTED_LANGS:
        response.set_cookie(
            "lang", g.lang, max_age=60 * 60 * 24 * 365, samesite="Lax"
        )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.route("/")
def index():
    query = request.args.get("q", "").strip()
    ubicacion = request.args.get("ubicacion", "").strip()

    result = search(query) if query else None
    nearby = nearby_orgs(ubicacion) if ubicacion else None

    return render_template(
        "index.html",
        query=query,
        result=result,
        ubicacion=ubicacion,
        nearby=nearby,
        legal_services_url=FIND_LEGAL_SERVICES_URL,
    )


@app.route("/representante")
def representante():
    query = request.args.get("q", "")
    index_param = request.args.get("i", type=int)

    result = search(query)
    if (
        result["status"] != "candidates"
        or index_param is None
        or not (0 <= index_param < len(result["results"]))
    ):
        abort(404)

    record = result["results"][index_param]["record"]
    return render_template(
        "representante.html",
        record=record,
        query=query,
        autorizado=is_currently_authorized(record),
    )


@app.route("/organizacion")
def organizacion():
    query = request.args.get("q", "").strip()
    result = search_org(query) if query else None

    results = None
    if result and result["status"] == "candidates":
        results = []
        for item in result["results"]:
            reps = item["reps"]
            location = next(
                (r for r in reps if r.get("org_city") and r.get("org_state")), None
            )
            results.append({
                "org": item["org"],
                "location": location,
                "reps": [
                    {"record": r, "autorizado": is_currently_authorized(r)}
                    for r in reps
                ],
            })

    return render_template(
        "organizacion.html",
        query=query,
        result=result,
        results=results,
    )


@app.route("/consejos")
def consejos():
    return render_template("consejos.html")


@app.errorhandler(404)
def not_found(e):
    return render_template(
        "error.html",
        title=t(g.lang, "error_404_title"),
        message=t(g.lang, "error_404_message"),
    ), 404


@app.errorhandler(500)
def server_error(e):
    return render_template(
        "error.html",
        title=t(g.lang, "error_500_title"),
        message=t(g.lang, "error_500_message"),
    ), 500


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(os.environ.get("PORT", 5000)),
        debug=os.environ.get("FLASK_DEBUG") == "1",
    )
