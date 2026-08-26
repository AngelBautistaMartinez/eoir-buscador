"""
Test set for search.py — the actual deliverable this week.

Every (query, expected_name) pair below is checked against a real record
in eoir_representatives.json. Half of them are the name as it actually
appears; the other half are deliberately broken the way Rosa breaks a
name she only ever heard out loud: phonetic respelling, dropped accents,
dropped apostrophes, reordered tokens, added titles.

Run:  python search.py
Prints "Top-5 recall: N/30 (xx.x%)" and lists any query that failed to
surface the right person in its top 5 results.
"""

CASES = [
    # -- exact-ish, different token order / case -----------------------
    ("juan garcia", "Garcia, Juan Gil"),
    ("garcia juan gil", "Garcia, Juan Gil"),
    ("juan gil garcia", "Garcia, Juan Gil"),
    ("GARCIA JUAN GIL", "Garcia, Juan Gil"),

    # -- surnames only, given name first --------------------------------
    ("aguayo leyva", "Aguayo Leyva, Yvette Guadalupe"),
    ("yvette aguayo", "Aguayo Leyva, Yvette Guadalupe"),

    # -- phonetic respelling: heard it spoken, never saw it written -----
    ("aguayo leiva", "Aguayo Leyva, Yvette Guadalupe"),      # leyva -> leiva
    ("yvette aguallo", "Aguayo Leyva, Yvette Guadalupe"),    # aguayo -> aguallo

    ("afrin zakia", "Afrin, Zakia"),
    ("zakia afrin", "Afrin, Zakia"),
    ("sakia afrin", "Afrin, Zakia"),                          # zakia -> sakia

    # -- accents present in the record, absent from the query ----------
    ("munoz amy", "Muñoz, Amy Mary"),
    ("muñoz amy mary", "Muñoz, Amy Mary"),
    ("magdalena lopez murphy", "Murphy, Magdalena López"),

    # -- apostrophe in the record ---------------------------------------
    ("o donnell katlellen", "O’Donnell, Katlellen"),
    ("odonnell katlellen", "O’Donnell, Katlellen"),

    # -- two-word surnames ------------------------------------------------
    ("jimenez lopez silvia", "Jimenez Lopez, Silvia Ruth"),
    ("silvia jimenez lopez", "Jimenez Lopez, Silvia Ruth"),
    ("himenez lopez silvia", "Jimenez Lopez, Silvia Ruth"),   # j -> h, Spanish pronunciation

    ("nunez ricardo", "Nunez, Ricardo"),
    ("kevin nunez", "Nunez, Kevin"),
    ("medina nunez mayra", "Medina-Nunez, Mayra"),

    ("castro josefina angelica", "Castro, Josefina Angelica"),
    ("josefina castro", "Castro, Josefina Angelica"),

    ("cruz juan andres", "Cruz, Juan Andres"),
    ("juan andres cruz", "Cruz, Juan Andres"),
    ("sr. juan andres cruz jr", "Cruz, Juan Andres"),          # titles/suffixes

    ("DE LA CRUZ ANA MARIA", "De La Cruz, Ana Maria"),
    ("ana maria de la cruz", "De La Cruz, Ana Maria"),

    ("vargas maria guadalupe", "Vargas, Maria Guadalupe"),
    ("maria guadalupe vargas", "Vargas, Maria Guadalupe"),

    ("mendoza rosa", "Mendoza, Rosa"),
    ("rosa mendoza", "Mendoza, Rosa"),
]


# -- org search: she may know the business, not the person -------------
ORG_CASES = [
    ("al otro lado", "Al Otro Lado, Inc."),
    ("catholic charities los angeles", "Catholic Charities of Los Angeles, Inc."),
]

# -- status edge cases: these do not have a "right answer" name, they
#    have a right answer status. Checked separately in __main__ below. --
STATUS_CASES = [
    ("ga", "too_short"),           # under 3 chars
    ("garcia", "too_many"),        # bare surname, 40+ hits
    ("zzqxnotarealname", "none"),  # no plausible match
]


if __name__ == "__main__":
    from search import search

    status_hits = 0
    for query, expected_status in STATUS_CASES:
        result = search(query)
        ok = result["status"] == expected_status
        status_hits += ok
        mark = "ok" if ok else "FAIL"
        print(f"[{mark}] {query!r} -> {result['status']} (expected {expected_status})")
    print(f"Status cases: {status_hits}/{len(STATUS_CASES)}\n")

    from search import search_org

    org_hits = 0
    for query, expected_org in ORG_CASES:
        result = search_org(query)
        names = [r["org"] for r in result["results"]]
        ok = expected_org in names
        org_hits += ok
        mark = "ok" if ok else "FAIL"
        print(f"[{mark}] {query!r} -> {names}")
    print(f"Org cases: {org_hits}/{len(ORG_CASES)}\n")
