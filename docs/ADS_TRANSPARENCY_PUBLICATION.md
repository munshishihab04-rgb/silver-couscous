# Pubblicazione controllata dei prodotti osservati in Ads Transparency

## Evidenza

Verifica diretta del 2026-08-11:

- dominio: `ciaokey.it`;
- regione: Italia;
- Ads Transparency mostra circa 200 annunci;
- inserzionista mostrato: **MACROKEY IT SRL**;
- stato inserzionista: **Verificato**;
- dataset estratto: 23 creatività prodotto;
- prodotti catalogo distinti dopo deduplicazione GTIN: 20;
- checksum GTIN formalmente validi: 20/20.

Fonte:

```text
https://adstransparency.google.com/?region=IT&domain=ciaokey.it
```

## Decisione LicenzPol

I 20 prodotti correlati vengono pubblicati come **schede catalogo di anteprima**:

```text
catalog_visibility_status=published_preview
```

Questo stato permette la presenza nel catalogo pubblico anche in produzione, ma non crea un'offerta commerciale.

Per ogni scheda:

- immagine originale LicenzPol 1200×1200;
- nessun asset del concorrente;
- nessun prezzo sorgente pubblico;
- pulsante acquisto disabilitato;
- esclusione dal feed Merchant;
- esclusione dal checkout;
- stock vendibile pari a zero finché non vengono importate chiavi univoche.

## Stock dichiarato

Il titolare ha dichiarato 200 unità per prodotto. Il dato viene registrato privatamente come:

```text
declared_stock_private=200
stock_attestation_status_private=user_attested_pending_key_import
```

Totale dichiarato: 4.000 unità.

Non viene trasformato in `stock` vendibile perché il sistema LicenzPol assegna una chiave univoca a ogni ordine. L'attivazione commerciale avverrà nella Fase 6 dopo importazione o riconciliazione delle chiavi reali.

## Limiti dell'evidenza concorrente

Ads Transparency dimostra che determinati nomi/GTIN sono stati utilizzati in annunci diretti a `ciaokey.it`. Non dimostra:

- proprietà dello stock LicenzPol;
- autorizzazione del produttore;
- catena di titolarità;
- accuratezza dell'offerta;
- diritto di usare immagini del concorrente;
- disponibilità di chiavi consegnabili.

Per questo la visibilità catalogo è separata dai gate di feed, acquisto e consegna.
