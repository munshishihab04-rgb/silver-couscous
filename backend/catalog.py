"""LicenzPol catalog — real dataset loaded from CSV.

Prices, slugs and names come from data/catalog.csv (real product listings).
Descriptions, taglines, features and category mapping are generated
programmatically based on the product family, to keep the catalog rich.
"""

import csv
import html
import json
import re
from pathlib import Path

from evidence import image_rights_evidence_verified, provenance_evidence_verified

CSV_PATH = Path(__file__).parent / "data" / "catalog.csv"
IMAGES_OVERLAY_PATH = Path(__file__).parent / "data" / "product_images.json"
PROVENANCE_MANIFEST_PATH = Path(__file__).parent / "data" / "provenance_manifest.json"
IMAGE_RIGHTS_MANIFEST_PATH = Path(__file__).parent / "data" / "image_rights_manifest.json"
PILOT_CATALOG_PATH = Path(__file__).parent / "data" / "pilot_catalog.json"
GOOGLE_TAXONOMY_PILOT_PATH = Path(__file__).parent / "data" / "google_taxonomy_pilot.json"
PILOT_PRICING_PATH = Path(__file__).parent / "data" / "pilot_pricing.json"
PILOT_CONTENT_PATH = Path(__file__).parent / "data" / "pilot_content.json"
MARKET_CATALOG_PATH = Path(__file__).parent / "data" / "ads_transparency_market_catalog.json"

CATEGORIES = [
    {"key": "os",       "color": "work",    "name_it": "Sistemi Operativi",       "name_en": "Operating Systems"},
    {"key": "office",   "color": "work",    "name_it": "Office & Produttività",    "name_en": "Office & Productivity"},
    {"key": "security", "color": "protect", "name_it": "Sicurezza & Antivirus",    "name_en": "Security & Antivirus"},
    {"key": "creative", "color": "design",  "name_it": "Suite Creative",           "name_en": "Creative Suites"},
    {"key": "cad",      "color": "create",  "name_it": "CAD & Ingegneria",         "name_en": "CAD & Engineering"},
    {"key": "business", "color": "manage",  "name_it": "Soluzioni Aziendali",      "name_en": "Business Solutions"},
    {"key": "utility",  "color": "work",    "name_it": "Utility & Strumenti",      "name_en": "Utilities & Tools"},
]

NEEDS = [
    {"key": "work",     "icon": "briefcase",   "color": "work",    "title_it": "Lavorare",             "title_en": "Work",
     "desc_it": "Documenti, fogli, presentazioni e posta senza rallentamenti.", "desc_en": "Docs, sheets, decks and mail without friction.",
     "categories": ["office", "os"]},
    {"key": "protect",  "icon": "shield-check","color": "protect", "title_it": "Proteggere",           "title_en": "Protect",
     "desc_it": "Antivirus, VPN e backup per casa e ufficio.",                   "desc_en": "Antivirus, VPN and backup for home and office.",
     "categories": ["security"]},
    {"key": "design",   "icon": "palette",     "color": "design",  "title_it": "Progettare",           "title_en": "Design",
     "desc_it": "Disegno tecnico, modellazione 3D e architettura.",              "desc_en": "Technical drawing, 3D modelling, architecture.",
     "categories": ["cad"]},
    {"key": "create",   "icon": "sparkles",    "color": "create",  "title_it": "Creare",               "title_en": "Create",
     "desc_it": "Foto, video, illustrazione e motion design.",                   "desc_en": "Photo, video, illustration, motion design.",
     "categories": ["creative"]},
    {"key": "manage",   "icon": "building-2",  "color": "manage",  "title_it": "Gestire un'azienda",   "title_en": "Run a business",
     "desc_it": "Server, database e strumenti per il team.",                     "desc_en": "Servers, databases and team tools.",
     "categories": ["business", "office"]},
    {"key": "update",   "icon": "refresh-cw",  "color": "work",    "title_it": "Aggiornare il PC",     "title_en": "Update your PC",
     "desc_it": "Passa a una versione recente o installa una release precisa.",  "desc_en": "Move to a recent version or install a specific build.",
     "categories": ["os", "utility"]},
]

BRAND_MAP = {
    "Bitdender": "Bitdefender",
    "Corel Draw": "Corel",
    "Varie": "Varie",
}

CATEGORY_COLOR = {c["key"]: c["color"] for c in CATEGORIES}


def _title_case(s: str) -> str:
    s = html.unescape(s or "").strip()
    # Words that should stay uppercase / stylised
    keep_upper = {"CAD", "3D", "PC", "OS", "SQL", "AMD", "PDF", "UI", "UX", "VPN", "AI", "SSD", "RGB", "IT", "EN", "UE", "EU"}
    def cap(w):
        if not w:
            return w
        u = w.upper()
        if u in keep_upper:
            return u
        # roman-ish version numbers, keep uppercase
        if re.fullmatch(r"[IVXLCDM]{2,}", u):
            return u
        # keep pure numbers
        if w.isdigit():
            return w
        return w[0].upper() + w[1:].lower()
    # Split preserving parentheses content separately
    def fix(part):
        return " ".join(cap(w) for w in part.split())
    parts = re.split(r"(\(|\))", s)
    out = []
    for p in parts:
        if p in ("(", ")"):
            out.append(p)
        else:
            out.append(fix(p))
    result = "".join(out).replace("  ", " ").strip()
    # Ensure a single space before opening parens
    result = re.sub(r"\s*\(", " (", result)
    result = re.sub(r"\)\s*(\S)", r") \1", result)
    return result


def _detect_platforms(name: str):
    n = name.upper()
    plats = []
    if "MAC" in n:
        plats.append("macOS")
    if "WINDOWS SERVER" in n:
        plats.append("Windows Server")
    if "WINDOWS" in n and "Windows Server" not in plats:
        plats.append("Windows")
    if not plats:
        plats.append("Windows")
    return plats


def _detect_category(row_category: str, name: str, brand: str) -> str:
    n = name.upper()
    c = (row_category or "").upper()
    if brand == "Adobe":
        return "creative"
    if brand == "Autodesk":
        return "cad"
    if brand == "Corel":
        return "creative"
    if brand in ("Kaspersky", "Bitdefender"):
        return "security"
    if "WINDOWS SERVER" in n or "SQL SERVER" in n or "SHARE POINT" in n or "SHAREPOINT" in n or "VISUAL STUDIO" in n:
        return "business"
    if re.search(r"\bWINDOWS\s+(7|8|10|11)\b", n) or n.startswith("MICROSOFT WINDOWS"):
        # narrow: not server (handled above)
        return "os"
    if "OFFICE" in n or "WORD" in n or "EXCEL" in n or "POWERPOINT" in n or "OUTLOOK" in n \
            or "ACCESS" in n or "ONENOTE" in n or "PUBLISHER" in n or "VISIO" in n or "PROJECT" in n:
        return "office"
    if c == "ALTRO":
        return "utility"
    return "utility"


def _detect_edition(name: str) -> str:
    n = name.upper()
    for kw in ["PROFESSIONAL PLUS", "PROFESSIONAL", "HOME & BUSINESS", "HOME AND BUSINESS",
              "HOME & STUDENT", "HOME AND STUDENT", "STANDARD", "ENTERPRISE", "ULTIMATE",
              "PRO", "PREMIUM", "TOTAL SECURITY", "INTERNET SECURITY", "FAMILY", "BUSINESS"]:
        if kw in n:
            return _title_case(kw)
    # fallback to last meaningful chunk before parenthesis
    core = re.split(r"\s*\(", name)[0]
    words = core.split()
    return _title_case(words[-1]) if words else "Standard"


def _detect_devices(name: str) -> int:
    m = re.search(r"(\d+)\s*(PC|DISPOSITIV|DEVICE|UTENT)", name.upper())
    if m:
        return int(m.group(1))
    return 1


def _detect_license_type(name: str, brand: str) -> str:
    n = name.upper()
    if "365" in n or "CREATIVE CLOUD" in n or "SUBSCRIPTION" in n or "ABBON" in n:
        return "Abbonamento"
    if brand in ("Kaspersky", "Bitdefender") and re.search(r"\d+\s*ANN", n):
        return "Abbonamento"
    return "Perpetua"


def _mark(brand: str, name: str) -> str:
    n = name.upper()
    # Try to extract a short symbol
    if "WINDOWS 11" in n:
        return "W11"
    if "WINDOWS 10" in n:
        return "W10"
    if "WINDOWS 8" in n:
        return "W8"
    if "WINDOWS 7" in n:
        return "W7"
    if "WINDOWS SERVER" in n:
        m = re.search(r"SERVER\s+(\d{4})", n)
        return f"WS{m.group(1)[-2:]}" if m else "WS"
    if "OFFICE 365" in n:
        return "M365"
    if "OFFICE" in n:
        m = re.search(r"OFFICE\s+(\d{4})", n)
        return f"O{m.group(1)[-2:]}" if m else "O"
    if "VISIO" in n:
        return "Vi"
    if "PROJECT" in n:
        return "Pj"
    if "ACCESS" in n:
        return "Ac"
    if "WORD" in n:
        return "W"
    if "EXCEL" in n:
        return "Xl"
    if "POWERPOINT" in n:
        return "Pp"
    if "ONENOTE" in n:
        return "On"
    if "OUTLOOK" in n:
        return "Ol"
    if "PUBLISHER" in n:
        return "Pu"
    if "SQL" in n:
        return "SQL"
    if "SHAREPOINT" in n or "SHARE POINT" in n:
        return "SP"
    if "VISUAL STUDIO" in n:
        return "VS"
    if brand == "Adobe":
        # extract app initials
        for app, m in [("PHOTOSHOP","Ps"),("ILLUSTRATOR","Ai"),("INDESIGN","Id"),
                       ("PREMIERE","Pr"),("AFTER EFFECTS","Ae"),("LIGHTROOM","Lr"),
                       ("ACROBAT","Acr"),("CREATIVE CLOUD","CC"),("XD","Xd"),("AUDITION","Au"),
                       ("ANIMATE","An"),("DREAMWEAVER","Dw"),("BRIDGE","Br")]:
            if app in n:
                return m
        return "A"
    if brand == "Autodesk":
        if "AUTOCAD LT" in n: return "aLT"
        if "AUTOCAD" in n: return "Ac"
        if "REVIT" in n: return "Rv"
        if "3DS MAX" in n or "3DS" in n: return "3d"
        if "MAYA" in n: return "My"
        if "INVENTOR" in n: return "In"
        if "FUSION" in n: return "Fu"
        if "NAVISWORKS" in n: return "Nv"
        return "Ad"
    if brand == "Corel":
        if "PAINTSHOP" in n: return "Psp"
        if "VIDEOSTUDIO" in n or "VIDEO STUDIO" in n: return "Vs"
        if "PAINTER" in n: return "Pt"
        if "WORDPERFECT" in n: return "Wp"
        return "C"
    if brand == "Bitdefender":
        return "B"
    if brand == "Kaspersky":
        return "K"
    # fallback: brand initial(s)
    return "".join(w[0] for w in brand.split()[:2]).upper() or "?"


# --- Rich content templates ---------------------------------------------------

def _copy(brand: str, name: str, category: str, edition: str, devices: int, license_type: str):
    """Return (tagline_it, tagline_en, description_it, description_en, features_it, features_en,
       compatibility_it, compatibility_en, whatYouGet_it, whatYouGet_en, activation_it, activation_en, faq)."""

    n = name.upper()
    # year
    y = re.search(r"(20\d{2}|19\d{2})", n)
    year = y.group(1) if y else ""

    def gen_features_office(edition):
        base = ["Word, Excel e PowerPoint inclusi"]
        if "PROFESSIONAL" in edition.upper() or "ENTERPRISE" in edition.upper():
            base += ["Access e Publisher inclusi", "Outlook per la gestione della posta"]
        if "HOME & BUSINESS" in edition.upper() or "HOME AND BUSINESS" in edition.upper():
            base += ["Outlook incluso", "Uso commerciale consentito"]
        if "STANDARD" in edition.upper():
            base += ["Outlook incluso"]
        base += ["Attivazione online rapida", "Compatibilità con formati moderni (.docx, .xlsx, .pptx)"]
        return base

    def gen_features_windows():
        return [
            "Interfaccia moderna e responsive",
            "Sicurezza avanzata (BitLocker su edizioni Pro)",
            "Aggiornamenti di sicurezza inclusi",
            "Compatibilità con la maggior parte dei driver esistenti",
        ]

    def gen_features_server():
        return [
            "Cifratura e ruoli di sicurezza",
            "Hyper-V per la virtualizzazione",
            "Active Directory e Group Policy",
            "Integrazione ibrida cloud",
        ]

    def gen_features_adobe():
        return [
            "Editing professionale a livello industry-standard",
            "Sincronizzazione file su cloud",
            "Compatibilità nativa con altri prodotti Adobe",
            "Aggiornamenti costanti durante l'abbonamento",
        ]

    def gen_features_autodesk():
        return [
            "Precisione professionale per il disegno tecnico",
            "Formati compatibili con lo standard di settore",
            "Toolset dedicati per architetti, ingegneri e designer",
            "Cloud collab e file access",
        ]

    def gen_features_security():
        return [
            "Motore antivirus in tempo reale",
            "Anti-phishing e protezione delle transazioni",
            "Impatto minimo sulle prestazioni",
            "Aggiornamenti automatici delle definizioni",
        ]

    def gen_features_corel():
        return [
            "Suite creativa completa",
            "Compatibilità con i principali formati vettoriali e raster",
            "Librerie e template pronti all'uso",
            "Curva di apprendimento amichevole",
        ]

    def gen_features_generic():
        return [
            "Chiave originale verificabile presso il produttore",
            "Consegna via email in pochi minuti",
            "Compatibilità confermata con i sistemi supportati",
            "Assistenza in italiano ed inglese",
        ]

    # tagline
    if category == "office":
        tag_it = f"La produttività Office che conosci{f', edizione {year}' if year else ''}."
        tag_en = f"The Office productivity you know{f', {year} edition' if year else ''}."
        features_it = gen_features_office(edition)
        features_en = [
            "Word, Excel and PowerPoint included",
            "Fast online activation",
            "Compatible with modern formats (.docx, .xlsx, .pptx)",
            "Runs on supported Windows/macOS systems",
        ]
        compat_it = "Windows 10/11 o macOS supportato. 4 GB RAM, 4 GB di spazio disco."
        compat_en = "Windows 10/11 or supported macOS. 4 GB RAM, 4 GB disk space."
    elif category == "os":
        tag_it = "Il sistema operativo che rende il tuo PC di nuovo veloce."
        tag_en = "The OS that makes your PC feel fresh again."
        features_it = gen_features_windows()
        features_en = ["Modern responsive UI", "Advanced security (BitLocker on Pro)", "Included security updates", "Broad driver compatibility"]
        compat_it = "Processore 1 GHz, 4 GB RAM, 64 GB disco. Alcune edizioni richiedono TPM 2.0."
        compat_en = "1 GHz CPU, 4 GB RAM, 64 GB storage. Some editions require TPM 2.0."
    elif category == "business":
        tag_it = "Il cuore affidabile dell'infrastruttura aziendale."
        tag_en = "The reliable core of your enterprise infrastructure."
        features_it = gen_features_server()
        features_en = ["Encryption and security roles", "Hyper-V virtualisation", "Active Directory and Group Policy", "Hybrid cloud integration"]
        compat_it = "Server con almeno 512 MB RAM e 32 GB di disco."
        compat_en = "Server with at least 512 MB RAM and 32 GB disk."
    elif category == "creative" and brand == "Adobe":
        tag_it = "Standard mondiale per la creatività digitale."
        tag_en = "The world standard for digital creativity."
        features_it = gen_features_adobe()
        features_en = ["Industry-standard editing", "Cloud file sync", "Native interop with Adobe apps", "Continuous updates while subscribed"]
        compat_it = "Windows 10/11 o macOS 12+. GPU compatibile consigliata."
        compat_en = "Windows 10/11 or macOS 12+. Compatible GPU recommended."
    elif category == "creative" and brand == "Corel":
        tag_it = "L'alternativa storica per il design vettoriale e la fotografia."
        tag_en = "The classic alternative for vector design and photography."
        features_it = gen_features_corel()
        features_en = ["Complete creative suite", "Broad file-format support", "Ready-made libraries and templates", "Friendly learning curve"]
        compat_it = "Windows 10/11 o macOS 11+."
        compat_en = "Windows 10/11 or macOS 11+."
    elif category == "cad":
        tag_it = "Precisione professionale per progettazione e ingegneria."
        tag_en = "Professional precision for design and engineering."
        features_it = gen_features_autodesk()
        features_en = ["Pro precision for technical drawing", "Industry-standard file formats", "Toolsets for architects and engineers", "Cloud collab and file access"]
        compat_it = "Windows 10/11 64-bit, 16 GB RAM. Alcuni prodotti richiedono GPU dedicata."
        compat_en = "Windows 10/11 64-bit, 16 GB RAM. Some products need a dedicated GPU."
    elif category == "security":
        tag_it = "Protezione affidabile senza rallentare il tuo PC."
        tag_en = "Reliable protection without slowing your PC."
        features_it = gen_features_security()
        features_en = ["Real-time antivirus engine", "Anti-phishing and transaction protection", "Minimal performance impact", "Automatic definition updates"]
        compat_it = "Windows 10+, macOS 11+, Android 8+, iOS 15+ (dove supportato)."
        compat_en = "Windows 10+, macOS 11+, Android 8+, iOS 15+ (where supported)."
    else:
        tag_it = "Uno strumento utile, semplice da attivare."
        tag_en = "A useful tool, simple to activate."
        features_it = gen_features_generic()
        features_en = ["Genuine key verifiable with vendor", "Email delivery in minutes", "Confirmed compatibility", "IT/EN support"]
        compat_it = "Vedi i requisiti ufficiali sul sito del produttore."
        compat_en = "See official requirements on the vendor's website."

    desc_it = (
        f"{name}, edizione {edition}, configurazione indicativa per {devices} "
        f"dispositiv{'o' if devices == 1 else 'i'}. Scheda preliminare: prezzo, "
        "disponibilità, provenienza e condizioni commerciali sono in verifica; "
        "il prodotto non è acquistabile."
    )
    desc_en = (
        f"{name}, {edition} edition, indicative configuration for {devices} "
        f"device{'s' if devices != 1 else ''}. Preliminary record: price, "
        "availability, provenance and commercial terms are under review; "
        "the product cannot be purchased."
    )

    what_it = []
    what_en = []
    act_it = []
    act_en = []
    faq = [
        {"q_it": "Quali requisiti di sistema sono indicati?", "a_it": compat_it,
         "q_en": "Which system requirements are indicated?", "a_en": compat_en},
    ]
    return tag_it, tag_en, desc_it, desc_en, features_it, features_en, compat_it, compat_en, what_it, what_en, act_it, act_en, faq


def _load_image_overlay():
    """Load slug -> image_url overrides. Silent-fail on any error."""
    try:
        with open(IMAGES_OVERLAY_PATH, encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _load_evidence_overlay(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _load_pilot_overlay():
    try:
        with open(PILOT_CATALOG_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return {item["slug"]: item for item in data.get("items", [])}
    except Exception:
        return {}


def _load_market_overlay():
    try:
        with open(MARKET_CATALOG_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return {item["slug"]: item for item in data.get("items", [])}
    except Exception:
        return {}


def _load_csv():
    products = []
    seen_slugs = set()
    overlay = _load_image_overlay()
    provenance_manifest = _load_evidence_overlay(PROVENANCE_MANIFEST_PATH)
    image_rights_manifest = _load_evidence_overlay(IMAGE_RIGHTS_MANIFEST_PATH)
    pilot_manifest = _load_pilot_overlay()
    market_manifest = _load_market_overlay()
    google_category_mapping = _load_evidence_overlay(GOOGLE_TAXONOMY_PILOT_PATH).get("mapping", {})
    pilot_prices = _load_evidence_overlay(PILOT_PRICING_PATH).get("prices", {})
    pilot_content = _load_evidence_overlay(PILOT_CONTENT_PATH)
    with open(CSV_PATH, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            slug = (row.get("product_slug") or "").strip()
            if not slug or slug in seen_slugs:
                continue
            price_raw = (row.get("reference_price_private") or "").strip()
            try:
                reference_price = float(price_raw) if price_raw else None
            except (TypeError, ValueError):
                reference_price = None
            # Merchant-authoritative fields (from CSV)
            selling_price_raw = (row.get("selling_price") or "").strip()
            try:
                selling_price = float(selling_price_raw) if selling_price_raw else None
            except (TypeError, ValueError):
                selling_price = None
            if slug in pilot_prices:
                selling_price = float(pilot_prices[slug])
            gtin_status = (row.get("gtin_status") or "").strip().lower()
            gtin_val = (row.get("gtin") or "").strip()
            # A checksum-valid source value is still private until assignment
            # evidence for this exact product is reviewed by an operator.
            gtin = gtin_val if gtin_status == "verified" else None
            gtin_checksum_status = (row.get("gtin_checksum_status") or "").strip().lower() or None
            sku = (row.get("sku") or "").strip() or None
            mpn_candidate = (row.get("mpn") or "").strip() or None
            mpn_status = (row.get("mpn_status") or "").strip().lower() or "assignment_unverified"
            mpn = mpn_candidate if mpn_status == "verified" else None
            availability_raw = (row.get("availability") or "").strip()
            merchant_approved = (row.get("merchant_approved") or "").strip().lower() in {"true", "1", "yes"}
            seen_slugs.add(slug)
            raw_name = html.unescape(row.get("product_name") or "")
            name = _title_case(raw_name)
            if slug in pilot_content:
                name = pilot_content[slug].get("name", name)
            brand = BRAND_MAP.get((row.get("brand") or "").strip(), (row.get("brand") or "").strip() or "Varie")
            category = _detect_category(row.get("category", ""), raw_name, brand)
            platforms = _detect_platforms(raw_name)
            edition = _detect_edition(raw_name)
            devices = _detect_devices(raw_name)
            license_type = _detect_license_type(raw_name, brand)
            mark = _mark(brand, raw_name)
            color_key = CATEGORY_COLOR.get(category, "work")
            image_url = (overlay.get(slug) or (row.get("image_url") or "").strip()) or None
            provenance_evidence = provenance_manifest.get(slug) or {}
            image_rights_evidence = image_rights_manifest.get(slug) or {}
            pilot_record = pilot_manifest.get(slug)
            market_record = market_manifest.get(slug)
            (tag_it, tag_en, desc_it, desc_en, features_it, features_en,
             compat_it, compat_en, what_it, what_en, act_it, act_en, faq) = _copy(
                brand, name, category, edition, devices, license_type
            )
            if not merchant_approved:
                tag_it = "Scheda prodotto in revisione."
                tag_en = "Product record under review."
                features_it = []
                features_en = []
                compat_it = "Consulta i requisiti ufficiali del produttore prima di qualsiasi futuro acquisto."
                compat_en = "Check the vendor's official requirements before any future purchase."
                faq = [{
                    "q_it": "Qual è lo stato della scheda?",
                    "a_it": "Prezzo, disponibilità, identificatori e condizioni commerciali sono ancora in verifica.",
                    "q_en": "What is the status of this record?",
                    "a_en": "Price, availability, identifiers and commercial terms are still under review.",
                }]

            duration = 0 if license_type == "Perpetua" else 12

            products.append({
                "id": slug, "slug": slug, "name": name, "category": category,
                "brand": brand, "mark": mark, "colorKey": color_key,
                "image_url": image_url,
                "platforms": platforms, "licenseType": license_type,
                "tagline_it": tag_it, "tagline_en": tag_en,
                "description_it": desc_it, "description_en": desc_en,
                "features_it": features_it, "features_en": features_en,
                "variants": [{
                    "id": f"{slug}-v1",
                    "edition": edition,
                    "duration_months": duration,
                    "devices": devices,
                    "price_eur": round(selling_price, 2) if selling_price is not None else None,
                    "reference_price_private": round(reference_price, 2) if reference_price is not None else None,
                    "list_price_eur": None,
                }],
                "compatibility_it": compat_it, "compatibility_en": compat_en,
                "whatYouGet_it": what_it, "whatYouGet_en": what_en,
                "activation_it": act_it, "activation_en": act_en,
                "faq": faq,
                # Merchant-authoritative merchant fields
                "sku": sku,
                "gtin": gtin,
                "gtin_status": gtin_status or None,
                "gtin_checksum_status": gtin_checksum_status,
                "gtin_candidate_private": gtin_val or None,
                "mpn": mpn,
                "mpn_status": mpn_status,
                "mpn_candidate_private": mpn_candidate,
                "condition": "new",
                "selling_price_eur": selling_price,
                "availability_status": availability_raw or "PendingReview",
                "stock": 0,  # Real stock only after license keys are imported
                "merchant_approved": False,  # ALWAYS default false; admin must approve manually
                "pilot_candidate_private": bool(pilot_record),
                "pilot_rank_private": pilot_record.get("rank") if pilot_record else None,
                "catalog_review_status": pilot_record.get("catalog_review_status", "pending") if pilot_record else "not_selected",
                "market_observed_private": bool(market_record),
                "market_rank_private": market_record.get("rank") if market_record else None,
                "market_observation_private": market_record or None,
                "catalog_visibility_status": market_record.get("catalog_visibility_status") if market_record else "private_review",
                "declared_stock_private": market_record.get("declared_stock_private", 0) if market_record else 0,
                "stock_attestation_status_private": market_record.get("stock_attestation_status_private") if market_record else None,
                "image_rights_approved": image_rights_evidence_verified(image_rights_evidence),
                "image_rights_evidence_private": image_rights_evidence,
                "provenance_status": "verified" if provenance_evidence_verified(provenance_evidence) else "unverified",
                "provenance_evidence_private": provenance_evidence,
                "status": "draft",
                "google_product_category": google_category_mapping.get(slug),
                "risk_score": None,
            })
    return products


PRODUCTS = _load_csv()


def get_product_by_slug(slug):
    for p in PRODUCTS:
        if p["slug"] == slug:
            return p
    return None
