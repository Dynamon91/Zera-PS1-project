# Port completo: riferimento e lavoro rimanente

Il riferimento disponibile è **Zera Myths Awaken Win 64 5.2 pre-release 5**.
Il 100% del port significa riprodurre i contenuti e i comportamenti di questa
build, con adattamenti documentati per PS1. Non implica recuperare contenuti
inediti o mancanti dalla build originale. La percentuale di raccolta mostrata
nel gioco è distinta dalla percentuale di sviluppo del port.

## Obiettivo concordato

Il risultato richiesto è **un gioco completo in un unico flusso**, dall'avvio
alla conclusione e al caricamento dei progressi. Le preview separate sono
strumenti di verifica: non costituiscono il prodotto finale.

| Ambito | Cosa deve includere il risultato finale | Stato attuale |
| --- | --- | --- |
| Avvio e intro | Loghi, sequenze e transizioni presenti nell'originale, audio sincronizzato e comportamento dei comandi | Logo originale con audio e titolo integrati in un nuovo disco; altre sequenze da recuperare |
| Menu | Titolo, nuova partita, caricamento, opzioni, pausa, comandi e crediti presenti nella build | Menu, crediti e changelog originali, volumi separati e impostazioni camera integrati; altre schermate e salvataggi da completare |
| Mondo e campagna | Scene originali, percorsi, passaggi tra livelli, requisiti, eventi e conclusione | Geometria statica delle sei scene del mondo nell'atlante; primi percorsi giocabili in Dreary Valley e Cosmic Core; collegamenti tra scene da integrare |
| Personaggi e modelli | Zera, personaggi secondari, nemici e oggetti, con forme, materiali, texture e animazioni coerenti con il riferimento | Scheletro di Zera corretto; gran parte degli altri attori da integrare |
| Interazioni e gameplay | Dialoghi, Kiwi/Gaia, abilità, danni, nemici, oggetti, raccolte, checkpoint e condizioni di completamento originali | Due reliquie, un checkpoint provvisorio e primo dialogo con Levium integrati; altre interazioni ancora da portare |
| Musiche e suoni | Brani nelle scene corrette, transizioni, loop, effetti e voci presenti, regolazioni del volume | Audio del logo, Glass Arp e sette effetti integrati; musiche dei livelli e altri suoni da collegare |
| Progressione e salvataggi | Stato globale e dei livelli, sblocchi, ripresa dopo riavvio, gestione memory card | Solo stato di sessione nel disco a settori |
| Qualità finale | Esperienza continua, risorse entro i limiti PS1, controlli e verifiche del contenuto completo | Verifiche locali su singole milestone; nessuna certificazione del gioco completo |

Grafica, codifiche audio/video e caricamenti richiedono adattamenti ai limiti
PS1. Ogni adattamento deve conservare contenuti e funzioni del riferimento e
riportare le differenze effettive. L'estrazione di un asset o la sua presenza
su CD non dimostrano che funzioni correttamente nel gioco.

**Prossima milestone:** animazioni originali Idle/Talking di Levium, con controlli
su rig e materiali. Il primo incontro è documentato in
[LEVIUM_DIALOGUE.md](LEVIUM_DIALOGUE.md). Menu ampliato e primo percorso
sono documentati in [CAMPAIGN_ENTRY.md](CAMPAIGN_ENTRY.md). Il primo avvio integrato
è documentato con screenshot e limiti in [FRONTEND.md](FRONTEND.md).
Il trampolino di Dreary Valley resta nel piano successivo, insieme al
completamento del gameplay e della campagna.

### Primo recupero dell'avvio

[Rapporto originale](../reports/frontend_recovery.json): due scene di avvio,
47 metodi relativi a titolo/menu/impostazioni e riferimenti audio/video.
SplashLoad contiene il VideoClip `logo`, con 425 frame e risorsa esterna
`sharedassets0.resource`. È il filmato del logo; questo dato non dimostra il
recupero di tutte le eventuali sequenze narrative. La rigenerazione del rapporto
è verificata sui file originali. Testi, immagini, eventi dei pulsanti, timeline
e coroutines richiedono ancora ricostruzione. Nessuna nuova schermata PS1 è
stata implementata con questa analisi.

## Originale ricevuto e verificato

Le cinque parti da 30 MiB sono state ricomposte nell'archivio Data:

`SHA-256: 4bc9e08960a3d2b86e7a0745f87e554a5f05988cdfb910d88d77b5bfc8626b87`

Verifica CRC completata su 142 voci. I file originali sono conservati fuori
dal checkout, in `/workspace/zera-original`; non sono inclusi nei nuovi report.
La rigenerazione del recupero della progressione coincide integralmente con
`reports/progression_recovery.json` già presente nel progetto.

Il nuovo [recupero del gameplay](../reports/gameplay_recovery.json) registra
nomi e ordine delle scene dai BuildSettings originali, componenti per scena,
hash dei file, schemi dei salvataggi e istruzioni IL di 20 metodi selezionati.
L'analisi non esegue il gioco Windows e non deserializza i salvataggi binari.

| Scena originale | Stato PS1 verificato prima di questa analisi |
| --- | --- |
| SplashLoad | Nessuna equivalenza completa verificata |
| Main Menu | Menu PS1 provvisorio, equivalenza non verificata |
| Cosmic Core | Patch limitata level2 |
| Dreary Valley | Patch iniziale e area separata del trampolino |
| Crystal Rift | Nessun livello giocabile integrato |
| Mystic Towers | Nessun livello giocabile integrato |
| Frigid Bluffs | Nessun livello giocabile integrato |
| Secret | Nessuna equivalenza verificata |

Inventario della build: 788 Mesh, 240 Texture2D, 97 AudioClip e 164
AnimationClip. Questi sono oggetti serializzati, non quantità di contenuti
unici, utilizzati o già convertiti. Lo stesso vale per i 193 componenti reliquia,
20 essenze e 13 checkpoint: contenitori e oggetti creati durante il gioco
possono generare altro contenuto.

## Regole originali che incidono sul port

- `GameControl.checkArrays` verifica gli oggetti ancora esistenti negli array
  `relics`, `essences`, `enemytype1`, `enemytype2`, `snappies`, `containers`.
  Imposta `everythingCollected` quando non ne trova. Le sole tre reliquie della
  preview non provano il completamento di Dreary Valley.
- `getLevelComplete.Update` attiva schermata/evento di completamento e chiama
  `GameControl.Save`. L'interazione con eventi e dialoghi va riprodotta.
- La coroutine del checkpoint assegna sia lo spawn del personaggio sia quello
  della telecamera. Il trigger avvia un'interazione con Kiwi: sostituirlo con
  un semplice respawn al centro della patch non riproduce questa logica.
- La variante `GaiaQuickSave` aggiorna entrambi gli spawn e successivamente
  imposta la salute a 3. Nome e trigger non dimostrano da soli un salvataggio
  su disco: le chiamate effettive vanno seguite.
- Il salvataggio originale separa `MasterSave.Axobat` e `Saves/<scena>.Axobat`:
  dati globali con BinaryFormatter e dati scena con JSON. Il port deve conservare
  le informazioni equivalenti in un formato PS1; non deve eseguire o importare
  automaticamente BinaryFormatter.
- `DisplayPercentage` legge `WholeGameRelicCount / 10000 * 100` dal salvataggio.
  Non è una formula valida per stimare quanto codice del port è completo.

Queste osservazioni provengono dai metodi conservati nel report, non da una
sessione di gioco originale. Eventi Unity, coroutines, oggetti generati,
contenuti dei contenitori e percorsi effettivi richiedono ulteriore ricostruzione.

## Ordine di sviluppo e criteri di completamento

0. **Avvio e menu integrati.** Ricostruire logo/intro, titolo, eventi dei pulsanti,
   nuova partita e impostazioni dai dati originali. Collegarli al disco giocabile
   e gestire letture CD e audio senza interrompere la riproduzione. Caricamento
   e ripresa diventeranno completi insieme alla memory card.
1. **Dreary Valley dall'inizio all'uscita.** Recuperare terreno completo e
   collisioni, attraversamenti, collezionabili e contenuti dei contenitori.
   Verificare un percorso continuo senza teletrasporti o modifiche della RAM.
2. **Meccaniche originali.** Integrare salute, danni, nemici, abilità,
   interazioni con Kiwi/Gaia, checkpoint, dialoghi ed eventi necessari ai percorsi.
   Ogni comportamento richiede una prova mirata e un confronto con l'originale.
3. **Progressione e memory card.** Conservare oggetti raccolti/distrutti,
   sblocchi e stato globale; verificare un riavvio dell'emulatore e il recupero
   dei progressi, oltre a carta assente, piena e dati danneggiati.
4. **Campagna completa.** Collegare Cosmic Core, Crystal Rift, Mystic Towers,
   Frigid Bluffs e Secret rispettando accessi, requisiti, ritorni e finali
   effettivamente presenti nella build fornita. Completare anche menu,
   impostazioni, audio, dialoghi e sequenze presenti nel riferimento.
5. **Compatibilità PS1.** Misurare RAM, VRAM, primitive, letture CD e tempi dei
   frame; verificare build Release, avvio con BIOS reale autorizzato e, quando
   disponibile, hardware. Un test HLE non certifica hardware o prestazioni.

Una voce è completata solo con implementazione e prove, non con l'estrazione
di dati. Questa analisi non modifica il gameplay PS1 e non aumenta la stima
provvisoria del 29%.

## Riprodurre l'analisi

Dal checkout, con le dipendenze di `requirements.txt` installate:

```sh
python tools/recover_gameplay.py "/workspace/zera-original/Zera Myths Awaken_Data"
python tools/recover_gameplay.py "/workspace/zera-original/Zera Myths Awaken_Data" --check
python tools/check_gameplay_recovery.py
```

`--check` ripete l'analisi sull'originale e rifiuta differenze. Il controllo
senza originali verifica coerenza con il recupero della progressione, metadati,
destinazioni dei salti IL e riferimenti importanti; non esegue il gameplay.
