"""Product families — curated landing pages for the biggest catalog groups.

A family is a hand-picked slice of the catalog (by brand + optional filters)
that deserves its own hero, story and grouped grid. Not every catalog row
belongs to a family: families are for depth and discovery, not exhaustive
listing.
"""

FAMILIES = [
    {
        "slug": "microsoft-windows",
        "brand": "Microsoft",
        "match": {"category": "os"},
        "mark": "W",
        "colorKey": "work",
        "name_it": "Microsoft Windows",
        "name_en": "Microsoft Windows",
        "tagline_it": "Il sistema operativo, in tutte le sue edizioni.",
        "tagline_en": "The operating system, across every edition.",
        "story_it": (
            "Da Windows 7 fino a Windows 11: scegli la versione giusta per il tuo hardware "
            "e la tua produttività. Ogni licenza è perpetua e ti accompagna a lungo."
        ),
        "story_en": (
            "From Windows 7 to Windows 11: pick the right version for your hardware and "
            "workflow. Every licence is perpetual and stays with you."
        ),
        "group_by": "windows_version",
    },
    {
        "slug": "microsoft-office",
        "brand": "Microsoft",
        "match": {"category": "office"},
        "mark": "O",
        "colorKey": "work",
        "name_it": "Microsoft Office",
        "name_en": "Microsoft Office",
        "tagline_it": "La suite di produttività più diffusa al mondo.",
        "tagline_en": "The world's most-used productivity suite.",
        "story_it": (
            "Word, Excel, PowerPoint e gli strumenti Microsoft che conosci. "
            "Trova l'edizione giusta per lavoro, studio o famiglia."
        ),
        "story_en": (
            "Word, Excel, PowerPoint and the Microsoft tools you know. "
            "Find the right edition for work, study or family."
        ),
        "group_by": "office_year",
    },
    {
        "slug": "adobe",
        "brand": "Adobe",
        "match": {},
        "mark": "A",
        "colorKey": "design",
        "name_it": "Adobe",
        "name_en": "Adobe",
        "tagline_it": "Lo standard creativo, foto, video e design.",
        "tagline_en": "The creative standard, photo, video and design.",
        "story_it": (
            "Photoshop, Illustrator, Premiere Pro, Acrobat e la suite Creative Cloud. "
            "Strumenti pensati per professionisti che vivono di visione."
        ),
        "story_en": (
            "Photoshop, Illustrator, Premiere Pro, Acrobat and the Creative Cloud suite. "
            "Tools built for professionals who live on vision."
        ),
        "group_by": "adobe_app",
    },
    {
        "slug": "autodesk",
        "brand": "Autodesk",
        "match": {},
        "mark": "Ad",
        "colorKey": "create",
        "name_it": "Autodesk",
        "name_en": "Autodesk",
        "tagline_it": "Precisione millimetrica per chi progetta.",
        "tagline_en": "Millimetre precision for those who design.",
        "story_it": (
            "AutoCAD, Revit, 3ds Max, Maya e Inventor. Le suite Autodesk per architettura, "
            "ingegneria e visualizzazione, con file compatibili con lo standard di settore."
        ),
        "story_en": (
            "AutoCAD, Revit, 3ds Max, Maya and Inventor. The Autodesk suites for architecture, "
            "engineering and visualisation, with industry-standard file compatibility."
        ),
        "group_by": "autodesk_product",
    },
]


def get_family(slug):
    for f in FAMILIES:
        if f["slug"] == slug:
            return f
    return None
