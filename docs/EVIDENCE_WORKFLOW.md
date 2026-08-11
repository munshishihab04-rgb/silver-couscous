# LicenzPol — workflow evidenze private

## Obiettivo

Nessun prodotto può essere pubblicato perché una casella è stata selezionata manualmente. Provenienza commerciale e diritti delle immagini richiedono un record completo, riferimenti a documenti privati e revisione nominativa.

## Dove conservare i documenti

I documenti reali non devono essere versionati nel repository pubblico. Conservarli in:

```text
.runtime/evidence/documents/
```

Il repository e MongoDB salvano esclusivamente riferimenti logici come:

```text
private://documents/contratto-fornitore-2026
```

Non inserire nel manifest password, chiavi, fatture con dati personali, coordinate bancarie o URL firmati.

## Provenienza commerciale

Per impostare `provenance_status=verified` servono tutti i campi:

- identità del fornitore;
- tipo: `manufacturer`, `authorized_distributor` oppure `documented_reseller`;
- almeno un riferimento `private://documents/...`;
- documento che dimostri il diritto a procurarsi e rivendere quello specifico prodotto o famiglia;
- revisore e timestamp, applicati dal server.

Una fattura isolata prova un acquisto, ma non sempre il diritto generale alla rivendita. Verificare anche termini del canale, territorio, edizione, trasferibilità e restrizioni della licenza.

## Diritti immagini

Ogni asset è identificato da percorso, SHA-256 e dimensioni. L'hash prova quale file è stato revisionato, non il diritto d'uso.

Per impostare `image_rights_approved=true` servono:

- base giuridica: `owned`, `licensed`, `manufacturer_authorized` o `public_domain`;
- almeno un riferimento documentale privato;
- fingerprint invariato dell'asset;
- revisore e timestamp applicati dal server.

Se il file cambia, rigenerare il manifest e ripetere la revisione. Il generatore azzera automaticamente l'approvazione quando cambia l'hash.

## Procedura

1. Collocare le prove nella directory privata.
2. Rigenerare i manifest:

   ```bash
   backend/.venv/bin/python backend/scripts/generate_evidence_manifests.py
   ```

3. Aprire **Admin → Merchant → modifica**.
4. Inserire fornitore, tipo di provenienza e riferimenti documentali.
5. Inserire base dei diritti immagine e riferimenti documentali.
6. Impostare gli stati verificati e salvare.
7. Controllare i contatori `Provenienza verificata` e `Diritti immagini`.
8. Procedere all'approvazione solamente dopo prezzo, stock, identificatore e categoria verificati.

## Fail-closed

Il backend rifiuta:

- provenienza verificata senza evidenze complete;
- diritti immagine approvati senza fingerprint e documenti;
- approvazioni singole o massive prive di evidenze;
- asset modificati dopo la revisione;
- riferimenti pubblici o HTTP al posto di riferimenti privati.
