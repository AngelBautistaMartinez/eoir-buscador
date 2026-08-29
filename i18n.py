"""
Short, reusable UI strings for the Flask front end (app.py / templates),
in Spanish and English. Long-form one-off content (consejos.html) is
branched directly in its template instead of living here — see that
file for why.

Usage: t(lang, key) -> str. Strings with {placeholders} are filled in
by the caller with Python's str.format, then printed normally in
Jinja so auto-escaping still applies to any interpolated user input.
"""

SUPPORTED_LANGS = ("es", "en")
DEFAULT_LANG = "es"

STRINGS = {
    "es": {
        # site chrome
        "brand": "Buscador de representantes acreditados",
        "subtitle": "DOJ/EOIR — verifique antes de confiar",
        "nav_consejos": "Consejos",
        "meta_description": "Verifique gratis si una persona u organización está acreditada por el DOJ/EOIR para ayudarle con su caso de inmigración. Gratis, sin cuentas, sin datos guardados.",
        "footer_intro": "Esta herramienta usa datos públicos del Departamento de Justicia (DOJ/EOIR). No es un servicio del gobierno ni sustituye asesoría legal.",
        "footer_updated": "Datos actualizados al {date}.",

        # index.html
        "hero_headline": "Verifique <em>antes</em> de confiar.",
        "hero_lede": "Compruebe en segundos si la persona u organización que le ofrece ayuda con su caso de inmigración está realmente autorizada por el gobierno de EE. UU.",
        "trust_independent": "Independiente, no es del gobierno",
        "trust_privacy": "Sin cuentas, nada guardado",
        "trust_free": "Gratis, siempre",
        "search_label": "Buscar por nombre",
        "search_placeholder": "Ej. Juan García",
        "search_button": "Buscar",
        "search_alt_org": "¿Busca una organización en vez de una persona?",
        "too_short": "'{query}' es muy corto para buscar. Escriba al menos 3 letras.",
        "too_many": "Buscó solo un apellido. Encontramos {count} personas con el apellido '{query}'. Agregue un nombre de pila o una ciudad para reducir la búsqueda.",
        "none_person": "No encontramos a nadie parecido a '{query}' en la lista de representantes acreditados por el DOJ/EOIR.",
        "not_fraud_proof": "Esto NO es prueba de que sea un fraude. Puede pasar que:",
        "reason_licensed_attorney": "Sea un abogado o abogada con licencia — los abogados no necesitan estar acreditados por el DOJ/EOIR, solo los representantes que no son abogados. Verifique su licencia con el colegio de abogados (State Bar) de su estado.",
        "reason_typo": "Haya un error de escritura en el nombre que buscó.",
        "reason_diff_name": "La persona use un nombre distinto al que está registrado.",
        "find_legal_help_intro": "Para verificar si alguien es abogado con licencia, o para encontrar ayuda legal gratuita o de bajo costo, consulte el recurso oficial de USCIS:",
        "location_question": "¿En qué ciudad o estado vive?",
        "location_placeholder": "Ej. San Diego o California",
        "location_button": "Buscar organizaciones cercanas",
        "nearby_heading": "Organizaciones acreditadas cerca de '{ubicacion}'",
        "nearby_none": "No encontramos organizaciones acreditadas registradas cerca de '{ubicacion}'.",
        "confirm_still_employed_warning": "Confirme siempre que la persona con la que habla trabaje actualmente para la organización antes de compartir información o pagar por servicios.",
        "results_count": "{count} posible(s) coincidencia(s)",
        "no_org_registered": "(sin organización registrada)",

        # representante.html
        "back_to_results": "Volver a los resultados",
        "badge_active": "Activo",
        "badge_pending": "Renovación pendiente",
        "badge_dhs_only": "Solo DHS",
        "auth_yes_headline": "¿Puede ayudarle ahora? Sí.",
        "auth_yes_body": "Según el registro del DOJ/EOIR, esta persona está actualmente autorizada para representarle.",
        "auth_yes_pending_note": "Su renovación (o la de su organización) está en trámite, pero eso no le quita validez: por ley (8 CFR 1292.16), sigue autorizada mientras EOIR revisa la solicitud.",
        "auth_unknown_headline": "¿Puede ayudarle ahora? No pudimos confirmarlo.",
        "auth_unknown_body": "Verifique directamente con la organización o con EOIR antes de continuar.",
        "label_scope": "Alcance",
        "scope_dhs_only_desc": "Solo DHS (no representa en corte)",
        "scope_full_desc": "Completo (corte y DHS)",
        "label_status": "Estatus",
        "status_unknown": "desconocido",
        "label_expires": "Vence",
        "no_expiration_on_file": "sin fecha registrada",
        "pending_renewal_suffix": " (renovación pendiente)",
        "label_org": "Organización",
        "no_org_on_file": "sin organización registrada",
        "label_location": "Ubicación",
        "label_org_phone": "Teléfono de la organización",
        "no_phone_on_file": "sin teléfono registrado",
        "confirm_org_city_warning": "Confirme que la organización y la ciudad coinciden con lo que le dijeron antes de continuar. Un nombre parecido no es suficiente.",

        # organizacion.html
        "title_org_search": "Buscar organización",
        "back_to_person_search": "Buscar por persona",
        "org_intro": "Busque el nombre de una organización para ver si está reconocida por el DOJ/EOIR, y quiénes son sus representantes acreditados.",
        "search_org_label": "Buscar organización",
        "search_org_placeholder": "Ej. Catholic Charities",
        "org_none": "No encontramos ninguna organización acreditada parecida a '{query}'. Esto NO es prueba de que sea un fraude — puede haber un error de escritura, o la organización puede operar bajo otro nombre.",

        # error.html
        "back_to_search": "Volver a la búsqueda",
        "error_404_title": "Página no encontrada",
        "error_404_message": "No encontramos esa página. Puede que el enlace esté mal escrito o haya caducado.",
        "error_500_title": "Error del servidor",
        "error_500_message": "Ocurrió un error inesperado de nuestra parte. Intente de nuevo en unos minutos.",
    },
    "en": {
        # site chrome
        "brand": "Accredited Representative Search",
        "subtitle": "DOJ/EOIR — verify before you trust",
        "nav_consejos": "Tips",
        "meta_description": "Check for free whether a person or organization is DOJ/EOIR-accredited to help with an immigration case. Free, no accounts, nothing saved.",
        "footer_intro": "This tool uses public data from the U.S. Department of Justice (DOJ/EOIR). It is not a government service and does not replace legal advice.",
        "footer_updated": "Data last updated {date}.",

        # index.html
        "hero_headline": "Verify <em>before</em> you trust.",
        "hero_lede": "Check in seconds whether the person or organization offering to help with your immigration case is actually authorized by the U.S. government to do so.",
        "trust_independent": "Independent, not government",
        "trust_privacy": "No accounts, nothing saved",
        "trust_free": "Free, always",
        "search_label": "Search by name",
        "search_placeholder": "e.g. Juan García",
        "search_button": "Search",
        "search_alt_org": "Looking for an organization instead of a person?",
        "too_short": "'{query}' is too short to search. Enter at least 3 letters.",
        "too_many": "You searched only a last name. We found {count} people with the last name '{query}'. Add a first name or city to narrow the search.",
        "none_person": "We couldn't find anyone matching '{query}' in the DOJ/EOIR list of accredited representatives.",
        "not_fraud_proof": "This is NOT proof of fraud. It's possible that:",
        "reason_licensed_attorney": "They're a licensed attorney — attorneys don't need to be DOJ/EOIR-accredited, only non-attorney representatives do. Verify their license with your state's bar association.",
        "reason_typo": "There's a typo in the name you searched.",
        "reason_diff_name": "The person uses a different name than the one on file.",
        "find_legal_help_intro": "To check whether someone is a licensed attorney, or to find free or low-cost legal help, see USCIS's official resource:",
        "location_question": "What city or state do you live in?",
        "location_placeholder": "e.g. San Diego or California",
        "location_button": "Search nearby organizations",
        "nearby_heading": "Accredited organizations near '{ubicacion}'",
        "nearby_none": "We didn't find any accredited organizations on file near '{ubicacion}'.",
        "confirm_still_employed_warning": "Always confirm that the person you're speaking with currently works for the organization before sharing information or paying for services.",
        "results_count": "{count} possible match(es)",
        "no_org_registered": "(no organization on file)",

        # representante.html
        "back_to_results": "Back to results",
        "badge_active": "Active",
        "badge_pending": "Pending renewal",
        "badge_dhs_only": "DHS only",
        "auth_yes_headline": "Can they help you right now? Yes.",
        "auth_yes_body": "According to the DOJ/EOIR record, this person is currently authorized to represent you.",
        "auth_yes_pending_note": "Their renewal (or their organization's) is in progress, but that doesn't affect its validity: by law (8 CFR 1292.16), it stays valid while EOIR reviews the request.",
        "auth_unknown_headline": "Can they help you right now? We couldn't confirm it.",
        "auth_unknown_body": "Verify directly with the organization or with EOIR before continuing.",
        "label_scope": "Scope",
        "scope_dhs_only_desc": "DHS only (cannot represent in court)",
        "scope_full_desc": "Full (court and DHS)",
        "label_status": "Status",
        "status_unknown": "unknown",
        "label_expires": "Expires",
        "no_expiration_on_file": "no date on file",
        "pending_renewal_suffix": " (pending renewal)",
        "label_org": "Organization",
        "no_org_on_file": "no organization on file",
        "label_location": "Location",
        "label_org_phone": "Organization's phone number",
        "no_phone_on_file": "no phone number on file",
        "confirm_org_city_warning": "Confirm that the organization and city match what you were told before continuing. A similar-sounding name is not enough.",

        # organizacion.html
        "title_org_search": "Search for an Organization",
        "back_to_person_search": "Search by person",
        "org_intro": "Search for an organization's name to see whether it's DOJ/EOIR-recognized, and who its accredited representatives are.",
        "search_org_label": "Search organization",
        "search_org_placeholder": "e.g. Catholic Charities",
        "org_none": "We couldn't find any accredited organization matching '{query}'. This is NOT proof of fraud — there may be a typo, or the organization may operate under a different name.",

        # error.html
        "back_to_search": "Back to search",
        "error_404_title": "Page not found",
        "error_404_message": "We couldn't find that page. The link may be broken or out of date.",
        "error_500_title": "Server error",
        "error_500_message": "Something unexpected went wrong on our end. Please try again in a few minutes.",
    },
}


def t(lang, key):
    return STRINGS.get(lang, STRINGS[DEFAULT_LANG]).get(key, key)
