# LicenzPol — avanzamento pre-lancio

Ultimo aggiornamento: 2026-08-11

Questo file è il riferimento persistente tra sessioni. Ogni fase viene conclusa, verificata, pubblicata e riepilogata prima di iniziare la successiva.

## Stato delle fasi

- [x] **Fase 1 — Privacy, legalità e telemetria**
  - 7 policy IT/EN sincronizzate tra codice, seed e MongoDB.
  - Identità e contatti aziendali pubblicati.
  - PostHog, session recording ed Emergent rimossi.
  - Analytics solo dopo consenso; IP e user-agent non salvati.
  - Cookie banner con accettazione, rifiuto e riapertura preferenze.
  - Staging `noindex,nofollow` e comunicazione pubblica pre-lancio.
  - Verifica: 6 test backend + 8 test frontend passati; build riuscita.

- [x] **Fase 2 — Gate produzione per catalogo, sitemap e feed Merchant**
  - Un'unica regola fail-closed governa storefront, pagine prodotto, famiglie, correlati, sitemap e feed.
  - In produzione sono pubblicabili solo offerte approvate con provenienza verificata, diritti immagine, prezzo di vendita, stock, SKU, disponibilità e identificatore valido.
  - In staging i prodotti restano visibili per revisione ma sono marcati `purchasable=false`.
  - Feed Merchant sempre vuoto fuori produzione.
  - Sitemap staging vuota e `robots.txt` con `Disallow: /`.
  - Prezzo pubblico delle offerte approvate deriva da `selling_price_eur`, non dal prezzo sorgente.
  - Verifica: 18 test backend passati; build riuscita; QA locale e pubblico completato.
- [x] **Fase 3 — Bonifica dati prodotto e identificatori**
  - Catalogo riconciliato a 398 prodotti con slug e SKU LicenzPol univoci.
  - GTIN riclassificati con algoritmo GS1 corretto: 374 checksum-validi ma assegnazione non verificata, 20 in conflitto per duplicazione, 1 checksum errato, 3 mancanti.
  - MPN importati trattati come candidati privati finché non verificati contro produttore/fornitore.
  - Prezzi sorgente spostati in `reference_price_private`; zero prezzi pubblici o commerciali impliciti.
  - Campi `_private` rimossi da ogni risposta API pubblica.
  - MongoDB e seed riproducibile riallineati a 398 prodotti; stock e approvazioni restano a zero.
  - Copy delle bozze reso prudente: nessuna promessa di originalità, consegna, fattura o attivazione.
  - Dettaglio, card, confronto e bundle mostrano “In verifica” e non consentono acquisti.
  - Approvazione singola e massiva bloccata lato server finché identificatori e tutti gli altri requisiti non sono verificati.
  - Verifica: 30 test backend mirati + 10 test frontend passati; build riuscita; QA API e browser pubblico completato.
- [x] **Fase 4 — Provenienza e diritti immagini**
  - Creati manifest persistenti per 398 record di provenienza e 398 asset immagine.
  - Tutte le immagini hanno percorso, SHA-256 e dimensioni; 0 mancanti, 0 orfane, 1 sotto 500 px.
  - Nessun fornitore o diritto è stato inventato: 398 provenienze non verificate e 0 immagini approvate.
  - Il gate richiede evidenze private complete oltre ai flag di approvazione.
  - Il server vincola la revisione dell'immagine al fingerprint reale e rifiuta hash sostituiti dal client.
  - L'editor prodotto generico non può modificare campi Merchant o campi `_private`.
  - Le revisioni manuali sopravvivono alla riconciliazione e ai riavvii.
  - Pannello Merchant esteso con fornitore, tipo fonte, documenti, base diritti, hash e dimensioni.
  - Workflow documentato in `docs/EVIDENCE_WORKFLOW.md`; documenti reali esclusi dal repository pubblico.
  - Verifica: 42 test backend mirati + 10 test frontend passati; build e QA API completati.
- [x] **Fase 5 — Catalogo pubblico controllato** — completata nel perimetro concordato
  - Shortlist autonoma revisionata a 10 prodotti correnti Microsoft/Bitdefender; rimossi Office 2019, CorelCAD 2020 e Photoshop 2022 dopo ricerca su fonti ufficiali.
  - 10 prezzi LicenzPol IVA inclusa creati; rimangono invisibili al pubblico finché il gate non è superato.
  - 10 categorie Google assegnate dalla tassonomia ufficiale verificata.
  - 10 immagini originali LicenzPol 1200×1200 generate senza asset esterni, fingerprintate e approvate con base `owned`.
  - GTIN candidati verificati formalmente ma 0 associazioni ufficiali trovate; nessun GTIN/MPN promosso a verificato.
  - Microsoft CSP e Bitdefender Partner Advantage individuati come canali ufficiali, ma non costituiscono prova di iscrizione o diritto specifico di LicenzPol.
  - Restano soltanto `identifier_assignment_unverified` e `provenance_evidence_missing` per tutti i 10 prodotti.
  - Su richiesta del titolare è stato aggiunto un livello meno restrittivo di visibilità catalogo: 20 prodotti osservati negli annunci `ciaokey.it` sono `published_preview`, con immagini originali e senza offerta acquistabile.
  - Ads Transparency mostrava circa 200 annunci di MACROKEY IT SRL (verificato); il dataset contiene 23 creatività riconducibili a 20 GTIN distinti con checksum valido.
  - Lo stock dichiarato dal titolare (200 per prodotto, 4.000 totale) è registrato privatamente ma non diventa stock vendibile fino all'importazione delle chiavi reali.
  - La fase è chiusa per la pubblicazione catalogo concordata; conversione dello stock dichiarato in chiavi disponibili, feed Merchant e acquisto restano esplicitamente nella Fase 6.
- [x] **Fase 6 — Inventario licenze ed email** — pipeline tecnica completata in modalità fail-closed
  - Cifratura Fernet con chiave dedicata separata dal JWT; fingerprint HMAC e indice univoco impediscono doppie importazioni.
  - Import CSV privato dry-run/apply confinato a `.runtime/`, con validazione SKU, audit per conteggi e nessuna chiave nei log.
  - Stock derivato esclusivamente dalle chiavi `available`, sincronizzato dopo importazione/prenotazione/rilascio e a ogni avvio.
  - Prenotazione, rilascio e claim consegna atomici; eventi PSP e ordini idempotenti; transizioni protette da compare-and-set.
  - Outbox email idempotente e template escaped per ordine ricevuto, pagamento, consegna e problema.
  - `EMAIL_DELIVERY_MODE=dry-run`: nessun invio simulato consuma inventario o marca chiavi come consegnate.
  - Stato esterno reale: 0 chiavi importate e Brevo non configurato; attivazione commerciale resta bloccata fino alla fornitura delle chiavi e delle credenziali.
  - Workflow operativo: `docs/INVENTORY_EMAIL_WORKFLOW.md`.
  - Verifica: 70 test backend locali passati, 10 test frontend passati, build completata e QA locale/pubblico superato.
- [ ] **Fase 7 — Sicurezza, test e infrastruttura**
- [ ] **Fase 8 — Dominio definitivo e soft launch**
- [ ] **Fase 9 — Pagamento Nexi con l'utente**
- [ ] **Fase 10 — Google Merchant Center**

## Regole permanenti

- Pagamento reale per ultimo e insieme all'utente.
- Nessuna offerta nel feed senza approvazione, prezzo, stock, provenienza e diritti immagine verificati.
- Staging sempre non indicizzabile.
- Ogni fase deve avere test, verifica pubblica, commit e riepilogo.
