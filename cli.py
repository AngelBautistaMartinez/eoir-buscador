"""
EOIR accredited-representative search — terminal front end.

All matching lives in search.py. This file only turns `status` values
and records into Spanish-language terminal output. Every string a user
sees lives here, not in search.py, so app.py (Flask) can reuse the
exact same search() calls with its own display layer.

Run:  python cli.py
"""

from search import search, nearby_orgs, get_data_as_of

FIND_LEGAL_SERVICES_URL = "https://www.uscis.gov/scams-fraud-and-misconduct/avoid-scams/find-legal-services"

MESES_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def format_date_es(iso_date):
    if not iso_date:
        return None
    y, m, d = (int(p) for p in iso_date.split("-"))
    return f"{d} de {MESES_ES[m - 1]} de {y}"


def is_currently_authorized(r):
    """
    Per 8 CFR 1292.16, a timely-filed renewal keeps accreditation/recognition
    valid while EOIR reviews it — "pending renewal" is not a lapse. Both the
    representative's own status AND their organization's status must be
    Active; a rep can't act for an organization that has lost recognition.
    """
    return r.get("status") == "Active" and r.get("org_status") == "Active"


def format_record_line(idx, item):
    r = item["record"]
    scope_note = " (solo DHS)" if r["scope"] == "DHS_ONLY" else ""
    line1 = f"  [{idx}]  {r['name']:<45} {item['score']}%{scope_note}"
    org = r.get("org") or "(sin organización registrada)"
    city = r.get("org_city")
    state = r.get("org_state")
    loc = f" — {city}, {state}" if city and state else ""
    line2 = f"       {org}{loc}"
    phone = r.get("org_phone") or "(sin teléfono registrado)"
    line3 = f"       {phone}"
    return "\n".join([line1, line2, line3])


def print_full_record(r):
    print()
    print(f"Nombre:        {r['name']}")
    print(f"Alcance:       {'Solo DHS (no representa en corte)' if r['scope'] == 'DHS_ONLY' else 'Completo (corte y DHS)'}")
    print(f"Estatus:       {r.get('status') or 'desconocido'}")
    exp = r.get("expiration") or "sin fecha registrada"
    pending = "  (renovación pendiente)" if r.get("pending_renewal") else ""
    print(f"Vence:         {exp}{pending}")
    print(f"Organización:  {r.get('org') or 'sin organización registrada'}")
    if r.get("org_city") and r.get("org_state"):
        print(f"Ubicación:     {r['org_city']}, {r['org_state']}")
    print(f"Teléfono:      {r.get('org_phone') or 'sin teléfono registrado'}")
    print()
    if is_currently_authorized(r):
        print("¿Puede ayudarle ahora?  SÍ — según el registro del DOJ/EOIR, esta persona")
        print("está actualmente autorizada para representarle.")
        if r.get("pending_renewal") or r.get("org_pending_renewal"):
            print("Su renovación (o la de su organización) está en trámite, pero eso no le")
            print("quita validez: por ley (8 CFR 1292.16), sigue autorizada mientras EOIR")
            print("revisa la solicitud.")
    else:
        print("¿Puede ayudarle ahora?  No pudimos confirmarlo con los datos disponibles.")
        print("Verifique directamente con la organización o con EOIR antes de continuar.")
    print()
    print("Confirme que la organización y la ciudad coinciden con lo que le dijeron")
    print("antes de continuar. Un nombre parecido no es suficiente.")


def format_org_suggestion(org):
    loc = f" — {org['city']}, {org['state']}" if org.get("city") and org.get("state") else ""
    line = f"  • {org['org']}{loc}"
    if org.get("phone"):
        line += f"\n    {org['phone']}"
    return line


def not_found_flow(query):
    print()
    print(f"No encontramos a nadie parecido a '{query}' en la lista de representantes")
    print("acreditados por el DOJ/EOIR.")
    print()
    print("Esto NO es prueba de que sea un fraude. Puede pasar que:")
    print("  • Sea un abogado o abogada con licencia — los abogados no necesitan")
    print("    estar acreditados por el DOJ/EOIR, solo los representantes que no")
    print("    son abogados. Verifique su licencia con el colegio de abogados")
    print("    (State Bar) de su estado.")
    print("  • Haya un error de escritura en el nombre que buscó.")
    print("  • La persona use un nombre distinto al que está registrado.")
    print()
    print("Para verificar si alguien es abogado con licencia, o para encontrar")
    print("ayuda legal gratuita o de bajo costo, consulte el recurso oficial de USCIS:")
    print(f"  {FIND_LEGAL_SERVICES_URL}")

    city = input("\n¿En qué ciudad o estado vive? (Enter para omitir): ").strip()
    if not city:
        return
    suggestions = nearby_orgs(city)
    if not suggestions:
        print(f"\nNo encontramos organizaciones acreditadas registradas cerca de '{city}'.")
        return
    print(f"\nOrganizaciones acreditadas por el DOJ/EOIR cerca de '{city}':")
    print()
    for org in suggestions:
        print(format_org_suggestion(org))
    print()
    print("Confirme siempre que la persona con la que habla trabaje actualmente")
    print("para la organización antes de compartir información o pagar por servicios.")


def too_many_flow(query, count):
    print()
    print(f"Buscó solo un apellido. Encontramos {count} personas con el apellido '{query}'.")
    print("Agregue un nombre de pila o una ciudad para reducir la búsqueda.")


def too_short_flow(query):
    print()
    print(f"'{query}' es muy corto para buscar. Escriba al menos 3 letras.")


def run_search(query):
    result = search(query)

    if result["status"] == "too_short":
        too_short_flow(query)
        return
    if result["status"] == "none":
        not_found_flow(query)
        return
    if result["status"] == "too_many":
        too_many_flow(query, result["count"])
        return

    print()
    print(f"{result['count']} posible(s) coincidencia(s):")
    print()
    for i, item in enumerate(result["results"], start=1):
        print(format_record_line(i, item))
        print()
    print("  [0]  Ninguno de estos")
    print()

    choice = input("¿Cuál? ").strip()
    if choice == "0" or choice == "":
        not_found_flow(query)
        return
    try:
        n = int(choice)
        chosen = result["results"][n - 1]["record"]
    except (ValueError, IndexError):
        print("Opción no válida.")
        return
    print_full_record(chosen)


def main():
    print("Buscador de representantes acreditados — DOJ/EOIR")
    print("No es un sitio del gobierno. Es un proyecto gratuito de la comunidad.")
    print("No guardamos lo que usted busca.")
    fecha = format_date_es(get_data_as_of())
    if fecha:
        print(f"Datos del DOJ/EOIR actualizados al {fecha}.")
    query = input("\nBuscar: ").strip()
    run_search(query)


if __name__ == "__main__":
    main()
