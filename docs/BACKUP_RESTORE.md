# Backup e ripristino MongoDB

## Obiettivo

I backup contengono ordini, supporto e altri dati personali. Per questo non vengono mai scritti in chiaro né versionati.

Formato:

```text
Extended JSON BSON → gzip → Fernet
```

Percorso privato:

```text
.runtime/backups/
```

Permessi file: `0600`.

## Chiave

Generare una chiave distinta da JWT e inventario:

```bash
backend/.venv/bin/python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```

Salvarla esclusivamente nel secret manager o in `backend/.env`:

```env
BACKUP_ENCRYPTION_KEY=...
```

La perdita della chiave rende i backup irrecuperabili. La sua esposizione rende leggibili dati personali e ordini.

## Backup manuale

```bash
backend/.venv/bin/python backend/scripts/backup_mongodb.py
```

Lo script:

1. verifica MongoDB con `ping`;
2. esporta tutte le collezioni non di sistema;
3. comprime;
4. cifra;
5. salva con permessi `0600`;
6. decifra e valida immediatamente il file;
7. conserva gli ultimi 14 backup.

Wrapper operativo:

```bash
backend/scripts/run_backup.sh
```

## Backup automatico

Il backend avvia un task giornaliero in-process quando `BACKUP_ENCRYPTION_KEY` è configurata. Il task parte dopo l’avvio e crea un backup ogni 24 ore.

Questa modalità è adatta al deployment attuale a singola istanza. Su un’infrastruttura multi-worker deve essere sostituita da un job esterno singleton.

Il tentativo di installare un crontab utente sulla VM è fallito perché `/var/spool/cron` non è scrivibile per l’utente applicativo; non viene quindi dichiarato alcun cron di sistema attivo.

## Ripristino isolato

Il restore rifiuta database che non iniziano con `licenzpol_restore_`:

```bash
backend/.venv/bin/python backend/scripts/restore_mongodb.py \
  .runtime/backups/licenzpol-YYYYMMDDTHHMMSSZ.json.gz.fernet \
  --target-database licenzpol_restore_verifica
```

Il comando:

1. decifra e decomprime;
2. verifica il formato;
3. elimina soltanto il database target isolato;
4. reinserisce i documenti;
5. confronta i conteggi di ogni collezione;
6. restituisce `verified: true` soltanto in caso di corrispondenza.

Gli indici applicativi vengono ricreati dal normale startup del backend; il formato corrente salva i documenti, non gli indici.

## Procedura disaster recovery

1. fermare il traffico applicativo;
2. copiare backup e chiave in un ambiente isolato;
3. eseguire restore in `licenzpol_restore_<ticket>`;
4. verificare conteggi, ordini e inventario;
5. avviare il backend contro il database isolato per ricreare gli indici;
6. eseguire test health/readiness e login amministrativo;
7. promuovere il database soltanto dopo approvazione manuale;
8. registrare data, operatore e hash del file senza registrare la chiave.

## Verifica Fase 7

Il backup reale di staging è stato:

- creato;
- cifrato;
- decifrato per verifica;
- ripristinato in un database isolato;
- confrontato su 10 collezioni e 529 documenti;
- eliminato dopo il test di restore.
