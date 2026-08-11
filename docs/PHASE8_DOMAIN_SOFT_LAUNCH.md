# Fase 8 — Dominio definitivo e soft launch

## Stato iniziale verificato il 2026-08-11

Dominio:

```text
licenzpol.it
www.licenzpol.it
```

Stato osservato:

- entrambi risolvono verso `13.248.243.5` e `76.223.105.230`;
- il server HTTP dichiara `DPS/2.0.0`, infrastruttura GoDaddy Website Builder;
- `www` reindirizza all'apex;
- la pagina pubblicata è un placeholder “Lancio imminente”, non l'applicazione LicenzPol;
- il dominio ha già HSTS GoDaddy;
- la VM applicativa è `hermes-fresh-vm`, resource group `HERMES-AGENT-RG`, regione `ItalyNorth`, rete privata `10.42.1.5`;
- Azure IMDS non riporta alcun Public IP associato alla NIC;
- `172.213.246.119` è stato osservato soltanto come indirizzo di uscita/NAT e **non deve essere usato come record A**;
- sulla VM non sono in ascolto le porte 80/443;
- l'utente applicativo non dispone di `sudo` non interattivo;
- Azure CLI non risulta autenticata e la VM non dispone di managed identity utilizzabile;
- non sono disponibili credenziali delegate DNS/GoDaddy/Cloudflare.

Di conseguenza il DNS non è stato modificato: puntare ora il dominio alla VM provocherebbe downtime.

## Artefatti preparati

- `deploy/production.env.example`: configurazione produzione fail-closed;
- `deploy/Caddyfile`: TLS automatico, redirect `www` e reverse proxy verso `127.0.0.1:8002`;
- `deploy/licenzpol.service`: servizio systemd con hardening e restart automatico;
- `deploy/cloudflared-config.yml.example` e `deploy/licenzpol-cloudflared.service`: percorso raccomandato per tunnel nominato persistente senza esporre ingress diretto sulla VM;
- `.runtime/bin/cloudflared`: binario locale non versionato, versione verificata `2026.7.3`;
- `backend/scripts/check_soft_launch.py`: QA del dominio definitivo;
- `SEARCH_INDEXING_ENABLED=false`: gate indipendente per mantenere il soft launch `noindex` anche con `APP_ENV=production`.

## Stato previsto al primo soft launch

```text
APP_ENV=production
COMMERCE_ENABLED=false
EMAIL_DELIVERY_MODE=dry-run
SEARCH_INDEXING_ENABLED=false
CATALOG_PREVIEW_SCOPE=market
```

Quindi:

- 20 schede informative visibili;
- zero offerte acquistabili;
- zero feed Merchant;
- zero pagamenti reali;
- zero email live;
- robots `Disallow: /`;
- sitemap vuota;
- HSTS attivo soltanto dopo conferma HTTPS persistente sul dominio definitivo.

L'indicizzazione sarà abilitata in un passaggio separato impostando esplicitamente:

```text
SEARCH_INDEXING_ENABLED=true
```

## Piano di attivazione senza downtime

Poiché la NIC non ha un Public IP, il percorso raccomandato è un **Cloudflare Tunnel nominato**:

1. Aggiungere `licenzpol.it` a Cloudflare e completare la delega nameserver dal pannello GoDaddy.
2. Creare un tunnel nominato dedicato; salvare il JSON credenziali solo sotto `.runtime/cloudflared/` con permessi `0600`.
3. Derivare la configurazione privata da `deploy/cloudflared-config.yml.example`.
4. Installare `licenzpol.service` e `licenzpol-cloudflared.service` tramite l'amministratore della VM.
5. Avviare l'applicazione su `127.0.0.1:8002` e verificare health/readiness localmente.
6. Pubblicare prima un hostname QA nella zona Cloudflare e completare lo smoke test fail-closed.
7. Instradare apex e `www` al tunnel soltanto dopo il QA; l'applicazione applica il redirect canonico `www → apex`.
8. Verificare certificato, CSP, HSTS, health, catalogo, robots noindex e gate commerciali.
9. Rimuovere il Quick Tunnel e il placeholder GoDaddy soltanto dopo il QA del dominio definitivo.

Percorso alternativo: assegnare alla NIC un Public IP statico, aprire NSG 80/443 e usare Caddy. Questo richiede controllo Azure e privilegi amministrativi; l'indirizzo NAT di uscita osservato non è utilizzabile.

## QA

Staging attuale:

```bash
backend/.venv/bin/python backend/scripts/check_soft_launch.py \
  https://sku-wesley-driver-currencies.trycloudflare.com --staging
```

Soft launch definitivo, ancora noindex:

```bash
backend/.venv/bin/python backend/scripts/check_soft_launch.py https://licenzpol.it
```

Dopo l'abilitazione esplicita dell'indicizzazione:

```bash
backend/.venv/bin/python backend/scripts/check_soft_launch.py \
  https://licenzpol.it --indexable
```

## Accesso necessario per completare il cutover

Serve uno dei seguenti percorsi:

### Percorso VM + Caddy

- accesso amministrativo alla VM o intervento del proprietario per installare Caddy/systemd;
- accesso Azure sufficiente a verificare IP statico e NSG;
- accesso delegato GoDaddy DNS.

### Percorso Cloudflare Tunnel nominato

- zona DNS trasferita o delegata a Cloudflare;
- token di un tunnel nominato;
- record DNS gestito da Cloudflare.

Non inviare password o token in chat. Usare accesso delegato o secret manager. Il Quick Tunnel `trycloudflare.com` non viene considerato produzione.
