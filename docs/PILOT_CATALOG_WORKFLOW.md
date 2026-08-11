# Fase 5 — Catalogo pilota

## Stato

Il catalogo pilota contiene 10 candidati. **Candidato non significa approvato**. Tutte le schede restano `catalog_review_status=pending`, non acquistabili e non incluse nel feed.

## Candidati

1. Microsoft Office 2024 Home & Business (Mac)
2. Microsoft Office 2024 Home & Business (Windows)
3. Microsoft Windows 11 Professional
4. Microsoft Windows 11 Home
5. Bitdefender Antivirus Plus — 1 PC / 1 anno
6. Bitdefender Antivirus Plus — 3 PC / 1 anno
7. Bitdefender Antivirus Plus — 5 PC / 1 anno
8. Bitdefender Total Security — 3 dispositivi / 1 anno
9. Bitdefender Total Security — 5 dispositivi / 1 anno
10. Bitdefender Total Security — 10 dispositivi / 1 anno

La shortlist esclude GTIN duplicati o con checksum non valido, asset mancanti e immagini con lato inferiore a 500 px. Questa selezione tecnica non dimostra autenticità, disponibilità o diritto di rivendita.

La ricerca ufficiale ha inoltre escluso Office 2019 (lifecycle concluso), CorelCAD 2020 (la pagina storica reindirizza alla Technical Suite corrente) e Photoshop 2022 (l'offerta Adobe corrente è Creative Cloud/subscription). Il registro è `backend/data/pilot_selection_research.json`.

## Dati creati e validati autonomamente

- prezzi pre-lancio LicenzPol IVA inclusa, separati dai prezzi sorgente;
- categorie Google tratte dalla tassonomia ufficiale Google;
- immagini originali LicenzPol 1200×1200, generate senza loghi, package art o asset esterni;
- SHA-256 e ricevuta di generazione per ogni immagine;
- audit dei GTIN candidati, lasciati non verificati perché non è stata trovata un'associazione ufficiale.

## Dati ancora necessari per ogni scheda

Il file `backend/data/pilot_review_template.csv` è già compilato per prezzo, categoria e immagini. Restano:

- GTIN oppure MPN verificato per quello specifico prodotto;
- riferimento privato alla prova dell'identificatore;
- nome del fornitore;
- tipo di provenienza;
- riferimento privato ai documenti di approvvigionamento/rivendita;
- decisione `approved` solamente dopo revisione dei documenti autentici.

I riferimenti devono avere questa forma:

```text
private://documents/nome-documento
```

I documenti reali vanno conservati fuori da Git in:

```text
.runtime/evidence/documents/
```

## Validazione

```bash
backend/.venv/bin/python backend/scripts/validate_pilot_review.py
```

Il comando è fail-closed:

- exit code `0`: tutte le 12 righe sono formalmente complete;
- exit code `1`: almeno una riga è bloccata;
- report: `backend/data/pilot_review_report.json`.

La validazione dello schema non prova l'autenticità dei documenti. Il revisore deve aprire e controllare ogni documento privato.

## Approvazione dal pannello

1. Aprire **Admin → Merchant**.
2. Lasciare attivo **Solo catalogo pilota**.
3. Aprire `modifica` sul prodotto.
4. Inserire prezzo, categoria, identificatore ed evidenze.
5. Impostare provenienza e diritti immagini come verificati.
6. Impostare **Revisione catalogo pilota → approved**.
7. Salvare.

Il backend rifiuta l'approvazione se manca un requisito. Lo stock non è richiesto per la revisione catalogo: sarà importato nella Fase 6. `merchant_approved` e pubblicazione restano bloccati fino allo stock reale.
