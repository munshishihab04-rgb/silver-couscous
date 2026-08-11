"""Reviewed business-policy drafts used by the CMS seed.

These texts are operational drafts, not a substitute for advice from an Italian
consumer/privacy professional. They deliberately describe the current staging
state and must be re-approved when payment and fulfillment are activated.
"""

IDENTITY_IT = (
    "Titolare e venditore: DIGITALSOFT DI MUNSHI SHIHAB, Via Aldo Pio Manuzio 24, "
    "40132 Bologna (BO), Italia; P.IVA 04358941203; REA BO-588058; "
    "email supporto@licenzpol.it; telefono +39 393 684 1051."
)
IDENTITY_EN = (
    "Controller and seller: DIGITALSOFT DI MUNSHI SHIHAB, Via Aldo Pio Manuzio 24, "
    "40132 Bologna (BO), Italy; VAT 04358941203; REA BO-588058; "
    "email supporto@licenzpol.it; phone +39 393 684 1051."
)

LEGAL_PAGES = {
    "privacy": {
        "title_it": "Informativa privacy",
        "title_en": "Privacy notice",
        "content_it": f"""Ultimo aggiornamento: 11 agosto 2026.

{IDENTITY_IT}

Trattiamo i dati forniti tramite assistenza, checkout e amministrazione per rispondere alle richieste, eseguire misure precontrattuali, gestire ordini, obblighi fiscali, sicurezza e contestazioni. I dati possono comprendere nome, contatti, dati di fatturazione, contenuto delle richieste e dati tecnici strettamente necessari alla sicurezza. Le basi giuridiche sono esecuzione contrattuale o precontrattuale, obbligo legale, interesse legittimo alla sicurezza e consenso per strumenti statistici non essenziali.

Non vendiamo dati personali. Fornitori tecnici, hosting, email, consulenti e futuro prestatore di pagamento ricevono solo i dati necessari e sono scelti con adeguate garanzie. I dati di pagamento completi non devono essere conservati da LicenzPol: saranno gestiti dal prestatore di pagamento selezionato.

Conserviamo richieste e dati contrattuali per il tempo necessario e per i termini fiscali o di difesa applicabili; gli eventi statistici non essenziali sono raccolti solo dopo consenso e con retention documentata. Puoi chiedere accesso, rettifica, cancellazione, limitazione, portabilità od opposizione scrivendo a supporto@licenzpol.it e puoi presentare reclamo al Garante per la protezione dei dati personali.

Il sito di staging non accetta pagamenti reali. Questa informativa sarà aggiornata indicando nominativamente hosting, email e prestatore di pagamento prima dell'attivazione commerciale.""",
        "content_en": f"""Last updated: 11 August 2026.

{IDENTITY_EN}

We process information submitted through support, checkout and administration to answer requests, take pre-contractual steps, manage future orders, meet tax duties, maintain security and resolve disputes. Data may include identity, contact and billing details, support content and technical information strictly needed for security. Legal bases include contract or pre-contract steps, legal obligation, legitimate security interests and consent for non-essential analytics.

We do not sell personal data. Technical, hosting, email, professional and future payment providers receive only necessary data under appropriate safeguards. Full payment credentials must not be stored by LicenzPol and will be handled by the selected payment provider.

Data is retained only as needed and for applicable tax or legal-defence periods. Non-essential analytics is collected only after consent. Contact supporto@licenzpol.it to exercise access, rectification, deletion, restriction, portability or objection rights, or complain to the competent data-protection authority. The staging site does not process real payments; provider details will be added before commercial activation.""",
    },
    "terms": {
        "title_it": "Termini di vendita",
        "title_en": "Terms of sale",
        "content_it": f"""Ultimo aggiornamento: 11 agosto 2026.

{IDENTITY_IT}

Il sito attuale è un ambiente di staging: catalogo, prezzi e disponibilità sono in revisione, il checkout è dimostrativo e non si perfeziona alcun contratto né pagamento. Un prodotto potrà essere acquistato solo quando contrassegnato come disponibile, con prezzo IVA inclusa, caratteristiche, durata, dispositivi compatibili, modalità di consegna e pulsante di pagamento reale.

Prima dell'ordine il cliente dovrà verificare edizione, piattaforma, territorio, requisiti tecnici e tipo di licenza. Il contratto si concluderà soltanto dopo conferma del pagamento e invio della conferma d'ordine. In caso di indisponibilità o errore evidente il pagamento sarà annullato o rimborsato senza consegna sostitutiva non concordata.

Le chiavi e i link di download saranno forniti solo per offerte con provenienza verificata. Non dichiariamo affiliazioni, certificazioni o autorizzazioni dei produttori se non documentate. È vietato rivendere, condividere o utilizzare le licenze oltre i diritti indicati nella singola scheda e nelle condizioni del produttore.

Prezzi, imposte, pagamento, consegna, assistenza, recesso e rimborso saranno mostrati prima dell'acquisto. Il cliente può contattarci a supporto@licenzpol.it. La legge applicabile e il foro non limitano le tutele inderogabili del consumatore residente nell'Unione europea.""",
        "content_en": f"""Last updated: 11 August 2026.

{IDENTITY_EN}

The current website is a staging environment: catalogue, prices and availability are under review, checkout is demonstrative and no contract or payment is completed. A product may be purchased only when marked available with VAT-inclusive price, licence scope, duration, compatible devices, delivery method and a real payment action.

Before ordering, customers must review edition, platform, territory, technical requirements and licence type. A contract will be formed only after payment confirmation and the order confirmation. If an item is unavailable or an obvious error is found, payment will be cancelled or refunded without an unagreed substitute.

Keys and download links will be supplied only for offers with verified provenance. We do not claim manufacturer affiliation, certification or authorisation without evidence. Licences may not be resold, shared or used beyond the rights on the product page and manufacturer terms.

Prices, taxes, payment, delivery, assistance, withdrawal and refund terms will be displayed before purchase. Contact supporto@licenzpol.it. Applicable law and venue do not restrict mandatory EU consumer protections.""",
    },
    "cookies": {
        "title_it": "Cookie policy",
        "title_en": "Cookie policy",
        "content_it": f"""Ultimo aggiornamento: 11 agosto 2026.

{IDENTITY_IT}

Il sito usa memoria locale e cookie tecnici necessari per carrello, lingua, sessione amministrativa, sicurezza e memorizzazione della scelta privacy. Questi strumenti non richiedono consenso quando sono strettamente necessari.

Analytics, Google Tag Manager, Meta Pixel o strumenti equivalenti restano disattivati finché l'utente non seleziona “Accetta statistiche”. Il rifiuto non impedisce la navigazione. La scelta è conservata nel browser e può essere modificata cancellando i dati del sito; prima del lancio sarà disponibile anche un controllo permanente per riaprire le preferenze.

La versione di staging non deve caricare PostHog, session recording o script Emergent. Eventuali futuri fornitori, durata dei cookie e trasferimenti internazionali saranno elencati qui prima dell'attivazione. Per domande o esercizio dei diritti scrivere a supporto@licenzpol.it.""",
        "content_en": f"""Last updated: 11 August 2026.

{IDENTITY_EN}

The site uses local storage and essential cookies for cart, language, admin session, security and privacy-choice storage. These are used only when strictly necessary. Analytics, Google Tag Manager, Meta Pixel or equivalent tools remain disabled until the visitor selects “Accept analytics”. Refusal does not prevent browsing.

The choice is stored in the browser and can be changed by clearing site data; a permanent preference control will be available before launch. Staging must not load PostHog, session recording or Emergent scripts. Future vendors, cookie duration and international transfers will be listed before activation. Contact supporto@licenzpol.it for questions or rights requests.""",
    },
    "withdrawal": {
        "title_it": "Diritto di recesso per contenuti digitali",
        "title_en": "Withdrawal right for digital content",
        "content_it": f"""Ultimo aggiornamento: 11 agosto 2026.

{IDENTITY_IT}

Il sito di staging non accetta pagamenti e non consegna licenze. Prima dell'attivazione commerciale, il checkout informerà il consumatore del diritto di recedere entro quattordici giorni quando applicabile e distinguerà chiaramente la richiesta di consegna digitale immediata.

La fornitura anticipata di contenuto digitale potrà iniziare solo dopo una richiesta espressa. L'eventuale perdita del diritto di recesso avverrà esclusivamente nei casi e con i requisiti previsti dalla normativa applicabile, dopo consenso espresso all'inizio dell'esecuzione e separata presa d'atto della conseguenza. Consenso, versione del testo, data e ordine saranno registrati e confermati su supporto durevole.

Prima dell'inizio della fornitura il consumatore potrà comunicare il recesso a supporto@licenzpol.it indicando il riferimento dell'ordine. Questa disciplina non limita i rimedi per mancata consegna o difetto di conformità descritti nella policy Resi e rimborsi. Il testo sarà sottoposto a revisione legale prima dell'attivazione dei pagamenti.""",
        "content_en": f"""Last updated: 11 August 2026.

{IDENTITY_EN}

Staging accepts no payment and delivers no licence. Before commercial activation, checkout will explain the consumer's fourteen-day withdrawal right where applicable and clearly distinguish a request for immediate digital delivery.

Early digital supply may begin only after an express request. Any loss of the withdrawal right will apply only where permitted by law, after express consent to begin performance and a separate acknowledgement of the consequence. Consent text version, timestamp and order will be recorded and confirmed on a durable medium.

Before supply begins, consumers may notify withdrawal at supporto@licenzpol.it with the order reference. This does not restrict remedies for non-delivery or lack of conformity in the Returns and refunds policy. The final text must receive legal review before payments are enabled.""",
    },
    "refunds": {
        "title_it": "Resi, recesso e rimborsi",
        "title_en": "Returns, withdrawal and refunds",
        "content_it": f"""Ultimo aggiornamento: 11 agosto 2026.

{IDENTITY_IT}

Il sito di staging non accetta ancora ordini o pagamenti. Prima del lancio, il checkout distinguerà chiaramente tra richiesta di consegna differita e richiesta di fornitura digitale immediata. Per i consumatori, l'eventuale perdita del diritto di recesso dopo l'inizio della fornitura di contenuto digitale avverrà solo con consenso espresso e presa d'atto separata, registrata nell'ordine, nei limiti previsti dalla legge.

Se la chiave non viene consegnata, è già utilizzata, non corrisponde all'offerta o non può essere attivata per causa imputabile al venditore, il cliente deve contattare supporto@licenzpol.it indicando riferimento ordine e messaggio d'errore senza pubblicare la chiave. Dopo verifica sarà proposta correzione, sostituzione equivalente concordata o rimborso sul metodo originario.

Non sono esclusi i rimedi legali per difetto di conformità. Le richieste saranno registrate e confermate per email. Tempi operativi e metodo di rimborso saranno mostrati al checkout prima dell'attivazione dei pagamenti e dovranno coincidere con le impostazioni di Google Merchant Center.""",
        "content_en": f"""Last updated: 11 August 2026.

{IDENTITY_EN}

Staging does not yet accept orders or payments. Before launch, checkout will clearly distinguish deferred delivery from a request for immediate digital supply. For consumers, any loss of the withdrawal right after digital supply begins will occur only after separate express consent and acknowledgement recorded with the order, within applicable law.

If a key is not delivered, already used, materially different or cannot be activated for a seller-caused reason, contact supporto@licenzpol.it with the order reference and error message without publishing the key. After verification, LicenzPol will provide correction, an agreed equivalent replacement or refund to the original payment method. Statutory conformity remedies remain available. Operational times will be published before payments and must match Merchant Center settings.""",
    },
    "delivery": {
        "title_it": "Consegna digitale",
        "title_en": "Digital delivery",
        "content_it": f"""Ultimo aggiornamento: 11 agosto 2026.

{IDENTITY_IT}

Tutti i prodotti sono digitali: non viene spedito alcun pacco fisico e non sono addebitati costi di spedizione fisica. Il sito di staging non consegna chiavi. Prima del lancio, ogni scheda indicherà contenuto fornito, territorio, piattaforma, durata, numero di dispositivi, disponibilità e tempo di evasione reale.

Dopo conferma irrevocabile del pagamento, il sistema assegnerà una licenza disponibile una sola volta e invierà conferma e istruzioni all'indirizzo email dell'ordine. Se il controllo antifrode o l'evasione richiedono verifica manuale, il cliente ne sarà informato senza promettere tempi non garantiti. Nessuna chiave sarà consegnata prima dello stato pagato.

Il cliente deve verificare l'email e contattare supporto@licenzpol.it senza condividere pubblicamente la chiave. Problemi di consegna, chiave già usata o prodotto difforme seguono la policy Resi e rimborsi. Disponibilità sul sito, feed Google e checkout devono provenire dallo stesso inventario autorevole.""",
        "content_en": f"""Last updated: 11 August 2026.

{IDENTITY_EN}

All products are digital: no physical parcel is shipped and no physical shipping fee is charged. Staging does not deliver keys. Before launch, each offer will state supplied content, territory, platform, term, devices, live availability and actual fulfilment timing.

After irrevocable payment confirmation, the system will allocate one available licence once and send confirmation and instructions to the order email. Manual fraud or fulfilment review will be disclosed without unsupported timing promises. No key will be delivered before paid status.

Customers should check their email and contact supporto@licenzpol.it without publicly sharing a key. Non-delivery, already-used keys or mismatched products follow the Returns and refunds policy. Website, Google feed and checkout availability must come from the same authoritative inventory.""",
    },
    "transparency": {
        "title_it": "Trasparenza",
        "title_en": "Transparency",
        "content_it": f"""Ultimo aggiornamento: 11 agosto 2026.

{IDENTITY_IT}

LicenzPol è in preparazione al lancio. Catalogo e checkout sono staging, non accettano pagamenti e non costituiscono disponibilità commerciale. Ogni offerta resta nascosta dai feed promozionali finché prezzo, stock, provenienza, identificatori, diritti immagine, copy e processo di consegna non sono verificati.

Non dichiariamo di essere rivenditore autorizzato o partner di un produttore senza documentazione. Marchi e nomi dei prodotti identificano compatibilità e titolarità dei rispettivi proprietari. Segnalazioni su catalogo o proprietà intellettuale possono essere inviate a supporto@licenzpol.it.

Prima del lancio, sito, checkout, dati strutturati e feed Google saranno riconciliati automaticamente. Gli acquisti reali verranno abilitati solo dopo integrazione e verifica congiunta del prestatore di pagamento.""",
        "content_en": f"""Last updated: 11 August 2026.

{IDENTITY_EN}

LicenzPol is preparing for launch. Catalogue and checkout are staging, accept no payment and do not represent commercial availability. Every offer stays out of promotional feeds until price, stock, provenance, identifiers, image rights, copy and delivery are verified.

We do not claim authorised-reseller or partner status without documentation. Trademarks identify compatibility and belong to their owners. Catalogue or intellectual-property notices can be sent to supporto@licenzpol.it. Before launch, website, checkout, structured data and Google feed will be reconciled automatically. Real purchasing will be enabled only after joint payment-provider integration and verification.""",
    },
}
