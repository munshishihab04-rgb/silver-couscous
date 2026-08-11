# Fase 6 — Inventario licenze ed email transazionali

## Stato

La pipeline tecnica è completa e resta intenzionalmente fail-closed:

```text
COMMERCE_ENABLED=false
EMAIL_DELIVERY_MODE=dry-run
chiavi reali importate=0
email reali inviate=0
```

Le 200 unità dichiarate per ciascuno dei 20 prodotti non diventano disponibilità commerciale finché non esistono altrettante chiavi univoche nel database cifrato.

## Cifratura e deduplicazione

Le chiavi sono cifrate con Fernet usando esclusivamente:

```text
LICENSE_KEY_ENCRYPTION_KEY
```

La chiave di cifratura:

- è generata in `backend/.env`, che non è versionato;
- non deriva dal JWT;
- deve essere conservata nel sistema segreti/backup operativo;
- non deve essere ruotata senza una migrazione di decifratura e ricifratura;
- è obbligatoria quando il commercio viene abilitato.

Ogni licenza contiene soltanto:

- `key_encrypted`;
- fingerprint HMAC-SHA256 univoco;
- SKU;
- stato inventario;
- riferimenti ordine e audit.

Il plaintext non viene scritto in MongoDB, Git, audit o log.

## Fonte dello stock

`products.stock` è una proiezione del conteggio server-side:

```text
license_keys.status == available
```

Viene sincronizzato:

- dopo importazione;
- dopo prenotazione;
- dopo rilascio;
- a ogni avvio del backend.

Il seed pubblico non può sovrascrivere lo stock reale.

## Importazione privata

Template locale non versionato:

```text
.runtime/import/license_keys.csv
```

Formato:

```csv
sku,key,source
LP-EXAMPLE,AAAA-BBBB-CCCC-DDDD,supplier-batch-2026-08
```

Dry-run obbligatorio come primo passaggio:

```bash
backend/.venv/bin/python backend/scripts/import_license_inventory.py \
  .runtime/import/license_keys.csv
```

Applicazione esplicita:

```bash
backend/.venv/bin/python backend/scripts/import_license_inventory.py \
  .runtime/import/license_keys.csv --apply
```

Il comando:

- accetta input soltanto sotto `.runtime/`;
- blocca SKU sconosciuti e righe vuote;
- deduplica il file e il database;
- non stampa chiavi;
- cifra prima di persistere;
- aggiorna lo stock dal conteggio reale;
- registra soltanto conteggi nell'audit.

## Prenotazione e consegna

Flusso ordine:

```text
draft → payment_initializing → pending_payment → paid → fulfillment_processing → fulfilled
```

Errori recuperabili:

```text
fulfillment_processing → fulfillment_pending
```

Garanzie:

- prenotazione atomica di una chiave `available`;
- pagamento rifiutato se non esiste inventario consegnabile;
- rilascio delle prenotazioni su pagamento fallito o annullato;
- claim atomico della consegna;
- un solo worker può elaborare l'ordine;
- evento PSP univoco e idempotente;
- transizioni concorrenti protette con compare-and-set;
- nessuna chiave viene marcata `delivered` in modalità email dry-run.

## Email transazionali

Template disponibili:

1. ordine ricevuto;
2. pagamento confermato;
3. consegna licenza;
4. problema ordine.

Tutti i valori dinamici vengono sottoposti a escaping HTML.

Configurazione attuale:

```text
EMAIL_DELIVERY_MODE=dry-run
BREVO_API_KEY non configurata
```

Per l'attivazione reale:

1. verificare il mittente `supporto@licenzpol.it` su Brevo;
2. inserire `BREVO_API_KEY` esclusivamente in `backend/.env` o secret manager;
3. inviare un test a una casella controllata;
4. verificare message ID e consegna;
5. impostare `EMAIL_DELIVERY_MODE=live`;
6. riavviare e ripetere il test prima di abilitare il commercio.

## Outbox

La collezione `email_outbox` usa `event_key` univoco e gli stati:

```text
queued → sending → dry_run|sent|failed
```

Il contesto dell'outbox rifiuta campi con nomi sensibili come `key`, `secret`, `token`, `password` e `credential`.

La consegna della licenza registra nell'outbox soltanto il riferimento ordine. Il plaintext viene decifrato esclusivamente in memoria durante un invio live.

Un evento `sending`, `sent`, `dry_run` o `failed` non viene acquisito automaticamente una seconda volta: eventuali retry incerti richiedono revisione amministrativa, evitando doppie consegne.

## Gate di attivazione

Prima di `COMMERCE_ENABLED=true` devono risultare contemporaneamente:

- chiavi reali importate e riconciliate;
- prezzi e offerte approvati;
- provenienza e identificatori conformi alla politica scelta;
- Brevo in modalità live verificata;
- Nexi configurato e verificato separatamente;
- backup della chiave Fernet;
- test end-to-end di pagamento, assegnazione e consegna.
