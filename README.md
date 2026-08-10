# LicenzPol

Storefront React con API FastAPI, pannello amministrativo e catalogo MongoDB.

## Contenuto

- `frontend/`: storefront e pannello admin React/CRACO.
- `backend/`: API FastAPI, autenticazione amministrativa e strumenti di importazione.
- `frontend/public/products/`: immagini prodotto WebP ospitate localmente.
- `database/seed/`: seed pubblico e riproducibile di prodotti, pagine CMS e impostazioni.

Le collezioni operative sensibili (`admin_users`, `analytics_events`, `login_attempts`, `orders`) non sono incluse nel repository pubblico. Gli amministratori vengono creati dalle variabili d'ambiente al primo avvio.

## Requisiti

- Node.js 20+
- Python 3.12+
- MongoDB 7/8

## Configurazione

```bash
cp backend/.env.example backend/.env
cp frontend/.env.production.example frontend/.env.production
```

Impostare valori sicuri in `backend/.env`, soprattutto `JWT_SECRET` e `ADMIN_PASSWORD`.

## Backend

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/restore_seed.py
.venv/bin/uvicorn server:app --host 127.0.0.1 --port 8000
```

## Frontend di sviluppo

```bash
cd frontend
npm install --legacy-peer-deps
REACT_APP_BACKEND_URL=http://127.0.0.1:8000 npm start
```

## Build e deployment unico

`deploy_app.py` serve API e build React dallo stesso processo:

```bash
cd frontend
npm install --legacy-peer-deps
npm run build
cd ../backend
.venv/bin/uvicorn deploy_app:app --host 0.0.0.0 --port 8000
```

Con `REACT_APP_BACKEND_URL=` il frontend usa l'API same-origin su `/api`.

## Database seed

Il seed contiene:

- 397 prodotti con immagini locali;
- 4 pagine CMS;
- 1 configurazione pubblica del sito.

Ripristino idempotente:

```bash
cd backend
.venv/bin/python scripts/restore_seed.py
```

## Immagini

`backend/data/product_images.json` collega ogni slug al relativo file locale. Il manifest non usa hotlink esterni. Lo script `backend/scripts/import_product_images.py` permette di rigenerare gli asset da un export strutturato autorizzato.
