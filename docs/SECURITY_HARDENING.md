# Fase 7 — Security hardening

## Stato e principi

Il backend resta fail-closed:

```text
APP_ENV=staging
COMMERCE_ENABLED=false
EMAIL_DELIVERY_MODE=dry-run
```

I controlli di questa fase non trasformano le schede informative in offerte acquistabili e non modificano i gate Merchant.

## Superfici protette

### Header HTTP

Ogni risposta applicativa riceve:

- `Content-Security-Policy`;
- `X-Content-Type-Options: nosniff`;
- `X-Frame-Options: DENY`;
- `Referrer-Policy: strict-origin-when-cross-origin`;
- `Permissions-Policy` restrittiva;
- `Cross-Origin-Opener-Policy: same-origin`;
- `X-Permitted-Cross-Domain-Policies: none`;
- `X-Request-ID` casuale.

Le API amministrative, ordini e pagamenti ricevono `Cache-Control: no-store`.

HSTS viene aggiunto **solo** quando `APP_ENV=production` e la richiesta risulta HTTPS. Non viene attivato nello staging Quick Tunnel.

### Host, proxy e CORS

- `TrustedHostMiddleware` accetta soltanto `ALLOWED_HOSTS` e gli host locali necessari ai test.
- In staging l’host temporaneo Cloudflare è esplicitamente elencato.
- Gli IP inoltrati vengono considerati soltanto quando il peer diretto è loopback.
- CORS espone soltanto metodi e header necessari.
- Le credenziali CORS vengono disabilitate quando l’origine è wildcard.
- Il servizio deve continuare a essere esposto su `127.0.0.1`, dietro proxy HTTPS.

### Payload e input

- body HTTP dichiarato massimo: 1 MiB;
- limiti Pydantic per email, nomi, messaggi, query, righe ordine, quantità e idempotency key;
- eventi analytics ammessi tramite allowlist;
- campo `extra` analytics limitato;
- regex amministrative costruite con `re.escape`;
- paginazione pubblica e amministrativa limitata.

### Rate limiting e anti-automazione

Rate limiter sliding-window applicato a:

- ordini;
- supporto;
- analytics;
- anteprima bundle;
- emissione challenge form.

I form supporto e checkout richiedono inoltre:

- challenge HMAC firmata e legata allo scopo;
- nonce casuale e single-use tramite inserimento atomico MongoDB;
- età minima;
- scadenza 30 minuti;
- honeypot invisibile;
- rate limiting per IP.

La challenge è consumata atomicamente in MongoDB. Prima di scalare su più processi o VM, il rate limiter in-memory deve essere spostato su Redis/MongoDB o sostituito con Cloudflare Turnstile.

### Ordini e pagamenti

- ogni ordine riceve un token cliente casuale;
- nel database viene conservato soltanto SHA-256 del token;
- lettura ordine, inizializzazione pagamento e polling richiedono `X-Order-Token`;
- il frontend conserva il token in `sessionStorage`;
- idempotency key checkout casuale, senza email o dati personali;
- claim pagamento e fulfillment atomici;
- prenotazioni rilasciate e stato ripristinato su qualsiasi errore provider o transizione concorrente;
- webhook Nexi autenticati con confronto constant-time del security token;
- eventi PSP idempotenti tramite indice univoco;
- nei documenti PSP viene salvata soltanto una allowlist di ID, tipo e risultato, mai il payload completo.

### Autenticazione amministrativa

- JWT HS256 con secret almeno 32 caratteri;
- durata predefinita: 240 minuti;
- `jti` casuale;
- `token_version` verificato a ogni richiesta;
- cambio password incrementa `token_version` e revoca i token esistenti;
- lockout dopo tentativi falliti;
- tentativi salvati come datetime e rimossi tramite indice TTL;
- il bootstrap crea il primo amministratore ma non sovrascrive più password già esistenti al riavvio.

Endpoint di rotazione:

```text
POST /api/admin/auth/change-password
```

Richiede token amministrativo, password corrente e nuova password di almeno 12 caratteri.

### Logging ed errori

- log JSON strutturati;
- correlation ID per richiesta;
- nessun body Brevo/Nexi;
- nessun destinatario, token, chiave licenza o response payload provider;
- gli errori non gestiti restituiscono un messaggio generico;
- nei log viene registrato soltanto il tipo dell’eccezione.

### Health e readiness

```text
GET /api/health/live   # processo vivo
GET /api/health        # readiness con ping MongoDB
```

La readiness restituisce `503` se MongoDB non risponde.

## Configurazione

```env
ALLOWED_HOSTS=shop.example.com,localhost,127.0.0.1
JWT_ACCESS_TTL_MINUTES=240
BACKUP_ENCRYPTION_KEY=<chiave Fernet separata>
```

## Vincoli operativi

- HSTS resta disattivato fino al dominio HTTPS definitivo.
- Non impostare `ALLOWED_HOSTS=*` in produzione.
- Non esporre Uvicorn su `0.0.0.0` senza firewall e reverse proxy verificato.
- La password amministrativa esposta durante lo sviluppo è stata ruotata al consolidamento della Fase 7; ruotare ancora dopo la prima consegna sicura.
- Il PAT GitHub esposto deve essere revocato dal proprietario dell'account: l'applicazione non dispone dell'accesso necessario alla gestione token.
- Nexi resta disabilitato fino alla Fase 9 condivisa.
