"""Migrate the CSV-loaded catalog into MongoDB on first boot.
After migration, MongoDB is the source of truth and PRODUCTS list is refreshed
from DB by the server.

This module also handles idempotent backfilling of merchant fields onto legacy
product documents that predate the merchant-authoritative schema.
"""

from datetime import datetime, timezone
from typing import List

MERCHANT_FIELD_DEFAULTS = {
    "sku": None,
    "gtin": None,
    "gtin_status": None,
    "mpn": None,
    "condition": "new",
    "selling_price_eur": None,
    "availability_status": "PendingReview",
    "stock": 0,
    "merchant_approved": False,
    "image_rights_approved": False,
    "provenance_status": "unverified",
    "status": "draft",
    "google_product_category": None,
    "risk_score": None,
}


async def migrate_products_if_empty(db, seed_products: List[dict]) -> int:
    """If db.products is empty, insert all seed_products. Returns number inserted."""
    count = await db.products.estimated_document_count()
    if count > 0:
        # DB already populated — backfill merchant fields idempotently.
        await backfill_merchant_fields(db, seed_products)
        return 0
    if not seed_products:
        return 0
    docs = []
    for p in seed_products:
        d = dict(p)
        d["_id"] = d["slug"]
        docs.append(d)
    await db.products.insert_many(docs)
    return len(docs)


async def backfill_merchant_fields(db, seed_products: List[dict]) -> int:
    """Backfill merchant fields on existing product docs.

    Reads authoritative values from the seed (which comes from catalog.csv) and
    writes them onto existing DB docs ONLY when the field is missing or None.
    Never overwrites human-approved fields like `merchant_approved=True`.
    """
    seed_by_slug = {p["slug"]: p for p in seed_products}
    updated = 0
    async for doc in db.products.find({}):
        slug = doc.get("slug")
        seed = seed_by_slug.get(slug, {})
        patch = {}
        for key, default in MERCHANT_FIELD_DEFAULTS.items():
            if key not in doc:
                patch[key] = seed.get(key, default)
        if patch:
            await db.products.update_one({"_id": doc["_id"]}, {"$set": patch})
            updated += 1
    return updated


async def load_products_from_db(db) -> List[dict]:
    """Return all products as plain dicts, without Mongo's _id."""
    out = []
    async for p in db.products.find({}):
        p.pop("_id", None)
        out.append(p)
    return out


# ---------- Legal / CMS pages (generated per Italian best practices) --------

LEGAL_PAGES = {
    "privacy": {
        "title_it": "Informativa Privacy",
        "title_en": "Privacy Policy",
        "content_it": """# Informativa Privacy (ai sensi del Regolamento UE 2016/679)

> **Nota di lavorazione:** questa informativa è redatta secondo le best practice del GDPR ma deve essere revisionata da un legale prima della pubblicazione in produzione.

## Titolare del trattamento
DIGITALSOFT DI MUNSHI SHIHAB — Via Aldo Pio Manuzio 24, 40132 Bologna (BO) — P.IVA 04358941203 — REA 588058.
Contatto privacy: supporto@licenzpol.it.

## Dati trattati
- Dati identificativi (nome, cognome, email, telefono) forniti durante il checkout e nella richiesta di supporto.
- Dati di fatturazione (indirizzo, P.IVA, codice fiscale se necessario).
- Dati di traffico anonimi (indirizzo IP mascherato, user-agent) per finalità di sicurezza e analisi aggregata.
- Log di comunicazione (ticket, email transazionali).

## Finalità e basi giuridiche
- Esecuzione del contratto di vendita (art. 6.1.b GDPR).
- Adempimento di obblighi legali/fiscali (art. 6.1.c).
- Legittimo interesse per la prevenzione delle frodi e la sicurezza (art. 6.1.f).
- Consenso esplicito per comunicazioni commerciali facoltative (art. 6.1.a).

## Destinatari
Fornitori tecnici in qualità di responsabili del trattamento: hosting cloud, provider di posta transazionale (Brevo), gateway di pagamento (Nexi XPay), servizio contabile.

## Trasferimenti extra-UE
Nessun trasferimento sistematico. Eventuali trasferimenti avvengono solo sulla base di clausole contrattuali standard (SCC) approvate dalla Commissione Europea.

## Conservazione
- Dati ordine e fatturazione: 10 anni (obblighi fiscali).
- Log tecnici: massimo 12 mesi.
- Ticket di supporto: 24 mesi dalla chiusura.

## Diritti dell'interessato
Accesso, rettifica, cancellazione, limitazione, opposizione, portabilità e reclamo al Garante Privacy (garanteprivacy.it). Scrivi a supporto@licenzpol.it.

## Cookie
Vedi la [Cookie policy](/legal/cookies).

_Ultimo aggiornamento: automatico._""",
        "content_en": "# Privacy Policy\n\nEnglish version to be reviewed and translated before production launch.",
    },
    "terms": {
        "title_it": "Termini e Condizioni di Vendita",
        "title_en": "Sales Terms",
        "content_it": """# Termini e Condizioni di Vendita

> **Nota:** documento redatto secondo il Codice del Consumo e la direttiva UE 2011/83/UE. Da confermare con un legale prima della go-live.

## 1. Venditore
DIGITALSOFT DI MUNSHI SHIHAB — Via Aldo Pio Manuzio 24, 40132 Bologna (BO) — P.IVA 04358941203 — REA 588058 — supporto@licenzpol.it.

## 2. Oggetto
Vendita di licenze software originali in formato digitale. Ogni prodotto pubblicato riporta prezzo (IVA inclusa), disponibilità e caratteristiche.

## 3. Conclusione del contratto
Il contratto si perfeziona con la ricezione dell'email di conferma d'ordine dopo il pagamento andato a buon fine. Il prezzo è quello indicato al momento dell'ordine.

## 4. Pagamenti
Pagamenti in EUR gestiti dal circuito **Nexi XPay** con protocollo 3D Secure. Non tratteniamo dati di carta.

## 5. Consegna
La chiave di licenza viene inviata via email all'indirizzo indicato in fase d'ordine, di norma entro 5 minuti dall'incasso e comunque entro 24 ore lavorative.

## 6. Diritto di recesso
Le licenze digitali sono contenuto digitale non fornito su supporto materiale (art. 59 lett. o) Codice del Consumo). L'utente al checkout dichiara di consentire l'inizio immediato dell'esecuzione e riconosce di **perdere il diritto di recesso** una volta che la chiave gli è stata trasmessa. Vedi la pagina [Diritto di recesso](/legal/withdrawal).

## 7. Garanzia
Le licenze sono garantite conformi alla descrizione. In caso di problemi di attivazione contatta supporto@licenzpol.it entro 30 giorni: forniamo assistenza o sostituzione della chiave.

## 8. Foro competente
Per il consumatore, il foro è quello di residenza dell'acquirente (art. 66-bis Codice del Consumo).

_Versione: 2026-08-11._""",
        "content_en": "# Sales Terms\n\nEnglish version to be translated and legally reviewed.",
    },
    "cookies": {
        "title_it": "Cookie Policy",
        "title_en": "Cookies Policy",
        "content_it": """# Cookie policy

## Cookie tecnici (obbligatori)
Utilizziamo cookie di sessione strettamente necessari al funzionamento del sito (autenticazione admin, carrello). Non richiedono consenso.

## Cookie analitici e di terze parti
Attivi solo dopo il consenso esplicito prestato tramite il banner cookie. Puoi revocare il consenso in qualsiasi momento.

## Come gestire i cookie
Puoi modificare le preferenze cookie cliccando sull'apposito link in fondo alla pagina.

_Versione: 2026-08-11._""",
        "content_en": "# Cookies Policy\n\nEnglish version pending review.",
    },
    "withdrawal": {
        "title_it": "Diritto di recesso digitale",
        "title_en": "Digital withdrawal right",
        "content_it": """# Diritto di recesso — contenuto digitale

Ai sensi degli articoli 52 e seguenti del Codice del Consumo, l'utente consumatore ha diritto di recedere entro 14 giorni dalla conclusione del contratto senza fornire motivazione.

## Perdita del diritto per contenuto digitale
Per i prodotti digitali non forniti su supporto materiale (chiavi software), il diritto di recesso si perde quando l'esecuzione ha avuto inizio con il consenso espresso dell'utente e con la sua accettazione della conseguente perdita del diritto stesso (art. 59 lett. o).

Al momento del checkout raccogliamo:
1. Consenso espresso all'inizio immediato della fornitura digitale.
2. Presa d'atto della perdita del diritto di recesso una volta trasmessa la chiave.

Entrambi i consensi vengono registrati, versionati e archiviati insieme all'ordine.

## Come esercitare il recesso (prima della consegna)
Fino a quando la chiave non è stata inviata, puoi recedere scrivendo a supporto@licenzpol.it indicando il numero d'ordine. Rimborso entro 14 giorni con lo stesso metodo di pagamento.""",
        "content_en": "# Digital withdrawal\n\nEnglish version pending.",
    },
    "delivery": {
        "title_it": "Consegna digitale",
        "title_en": "Digital delivery",
        "content_it": """# Consegna digitale

Le chiavi di licenza vengono inviate via email all'indirizzo indicato all'atto dell'ordine.

- **Tempo medio:** entro 5 minuti dall'incasso del pagamento.
- **Tempo massimo garantito:** 24 ore lavorative.
- **Se non ricevi l'email:** controlla lo spam e scrivi a supporto@licenzpol.it entro 48 ore.

Ogni chiave viene rilasciata una sola volta. In caso di smarrimento della mail forniamo copia previa verifica dell'ordine.""",
        "content_en": "# Digital delivery\n\nEnglish version pending.",
    },
    "refunds": {
        "title_it": "Rimborsi e reclami",
        "title_en": "Refunds and complaints",
        "content_it": """# Rimborsi e reclami

## Prima della consegna
Rimborso integrale entro 14 giorni dalla conclusione del contratto, se la chiave non è ancora stata inviata.

## Dopo la consegna
La chiave non è rimborsabile perché l'esecuzione è stata immediata (vedi [Diritto di recesso](/legal/withdrawal)). Tuttavia se:
- la chiave non funziona,
- la chiave risulta già utilizzata,
- il prodotto consegnato non corrisponde a quanto ordinato,

interveniamo con **sostituzione gratuita** o rimborso integrale. Contatta supporto@licenzpol.it entro 30 giorni dall'ordine allegando screenshot dell'errore.

## Reclami / ADR
Per i reclami non risolti entro 30 giorni, il consumatore può rivolgersi alla piattaforma ODR della Commissione Europea: https://ec.europa.eu/consumers/odr.""",
        "content_en": "# Refunds\n\nEnglish version pending.",
    },
    "transparency": {
        "title_it": "Trasparenza",
        "title_en": "Transparency",
        "content_it": """# Trasparenza

## Chi siamo
DIGITALSOFT DI MUNSHI SHIHAB — impresa individuale iscritta al Registro Imprese di Bologna, REA 588058, P.IVA 04358941203, sede in Via Aldo Pio Manuzio 24, 40132 Bologna (BO).

## Come lavoriamo
- Vendiamo licenze software originali con documentazione di provenienza tracciata.
- Ogni offerta pubblicata sul sito è **approvata manualmente** dal team dopo verifica del fornitore, del prezzo e della disponibilità.
- Le chiavi vengono consegnate via email in modo automatico dopo l'incasso.

## Contatti
- Assistenza: supporto@licenzpol.it
- Telefono: +39 393 684 1051
- PEC: da comunicare""",
        "content_en": "# Transparency\n\nEnglish version pending.",
    },
}


async def ensure_default_pages(db):
    """Seed CMS pages if not present."""
    for slug, doc in LEGAL_PAGES.items():
        existing = await db.pages.find_one({"slug": slug})
        if not existing:
            await db.pages.insert_one({"slug": slug, **doc,
                                        "created_at": datetime.now(timezone.utc).isoformat()})


DEFAULT_SETTINGS = {
    "key": "site",
    "logo_text": "LicenzPøl",
    "logo_url": "",
    "site_title": "LicenzPøl — Software originale, chiavi verificate, consegna via email",
    "site_description": "Licenze software originali (Microsoft, Adobe, Autodesk e altri). Consegna via email, fattura UE, assistenza in italiano.",
    # Business identity — DIGITALSOFT DI MUNSHI SHIHAB
    "business_legal_name": "DIGITALSOFT DI MUNSHI SHIHAB",
    "business_address": "Via Aldo Pio Manuzio 24, 40132 Bologna (BO)",
    "business_vat": "04358941203",
    "business_rea": "588058",
    "business_email": "supporto@licenzpol.it",
    "business_phone": "+39 393 684 1051",
    "primary_email": "supporto@licenzpol.it",
    "ga4_measurement_id": "",
    "gtm_container_id": "",
    "meta_pixel_id": "",
    "custom_head_html": "",
    "custom_body_html": "",
    "demo_banner": True,  # true in staging/dev, false in production
}


async def ensure_default_settings(db):
    existing = await db.settings.find_one({"key": "site"})
    if not existing:
        await db.settings.insert_one(dict(DEFAULT_SETTINGS))
    else:
        # ensure any new default keys are present without overwriting existing values
        missing = {k: v for k, v in DEFAULT_SETTINGS.items() if k not in existing}
        if missing:
            await db.settings.update_one({"key": "site"}, {"$set": missing})
