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
- [ ] **Fase 3 — Bonifica dati prodotto e identificatori**
- [ ] **Fase 4 — Provenienza e diritti immagini**
- [ ] **Fase 5 — Catalogo pilota approvato**
- [ ] **Fase 6 — Inventario licenze ed email**
- [ ] **Fase 7 — Sicurezza, test e infrastruttura**
- [ ] **Fase 8 — Dominio definitivo e soft launch**
- [ ] **Fase 9 — Pagamento Nexi con l'utente**
- [ ] **Fase 10 — Google Merchant Center**

## Regole permanenti

- Pagamento reale per ultimo e insieme all'utente.
- Nessuna offerta nel feed senza approvazione, prezzo, stock, provenienza e diritti immagine verificati.
- Staging sempre non indicizzabile.
- Ogni fase deve avere test, verifica pubblica, commit e riepilogo.
