# Progresso Zera PS1

**Obiettivo: port completo da Unity a PlayStation 1.**

**Completamento stimato: 29% · WIP09 · 30 ottobre 2026**

- Personaggio giocabile con animazioni, movimento e musica.
- Scheletro corretto: ordine delle rotazioni Euler recuperate riparato, eliminando una torsione del bacino di circa 114°. Personaggio nuovamente eretto; [confronto e preview ravvicinata](docs/CHARACTER_RIG_FIX.md).
- Rendering del personaggio corretto: facce interne escluse e triangoli ordinati per profondità precisa; corpo, testa e dettagli più leggibili. Quattro animazioni e regressioni di checkpoint/trampolino verificate in emulazione. [Screenshot e preview](docs/CHARACTER_MODEL_FIX.md).
- Tre aree di prova giocabili.
- Nuova camminata nella mappa a settori di Dreary Valley: collider originali attivi su 723 settori, primo percorso a Z=-2000 verificato, cambio settore in salto/planata senza perdere posizione o velocità. [Preview e limiti](docs/STREAMED_WALK.md).
- Nuovo atlante separato con tutte le sei scene del mondo presenti nell'originale: 248.369 triangoli sorgente e 3.437 settori caricati da CD. Esplorazione a volo libero; fisica e gameplay completi ancora da integrare. [Mappe, screenshot e limiti](docs/WORLD_ATLAS.md).
- Trampolino originale con atterraggio e telecamera migliorata.
- Raccolta delle tre reliquie nelle posizioni originali; tutte e tre raccolte in emulazione, totale 20.
- Corpo originale delle reliquie e colori di base ciano/verde; shader ancora in lavorazione.
- Messaggio di area completata e riavvio con Quadrato dopo 3/3 reliquie.
- Prossimi passi: altri percorsi, progressione completa e salvataggio.
- Corridoio Dreary Valley ampliato con terreno originale: tratto continuo dallo spawn a `(0,-16,-2000)`, oltre il vecchio confine Z=-1280, verificato senza respawn in emulazione. [Prove e limiti](docs/DREARY_CORRIDOR.md).
- Pareti inclinate: il movimento ora ritaglia i triangoli originali all'altezza del corpo invece di usare rettangoli verticali pieni. [Prove](docs/SLOPED_WALLS.md).
- Reliquia originale 6606 attiva nel corridoio: modello e posizione originali, salto/planata fino alla raccolta, valore 1, respawn conserva il progresso e titolo lo azzera. [Prove e screenshot](docs/CORRIDOR_RELIC.md).
- Seconda reliquia inferiore 6898 attiva: percorso continuo dallo spawn con entrambe raccolte, totale **2/2 e valore 17**, modelli/posizioni originali e progressi conservati al respawn. [Preview e prove](docs/TWO_CORRIDOR_RELICS.md).
- Checkpoint 6752 collegato nel disco principale: dallo spawn si raccolgono le due reliquie, si raggiunge il checkpoint e Select/Respawn conservano il valore 17. [Percorso e prove](docs/CONNECTED_CHECKPOINT.md). Attivazione per prossimità ancora provvisoria.
- Due reliquie e checkpoint 6752 collegati alla camminata a settori: percorso continuo, valore 17, ritorno con Select e nuova partita verificati in emulazione. [Screenshot e limiti](docs/STREAMED_PROGRESS.md).
- Obiettivo confermato: gioco completo con intro, menu, interazioni, modelli, animazioni, musiche, effetti e salvataggi in un unico flusso. [Ambiti e criteri](docs/PORT_COMPLETO.md).
- Avvio originale: recuperati riferimenti audio/video e 47 metodi di titolo/menu/impostazioni. È analisi verificata sui file originali, non nuova implementazione PS1.
- Nuovo disco integrato: filmato originale del logo con audio, texture originale del titolo, musica Glass Arp, nuova partita, pausa/ripresa, opzioni audio, comandi e ritorno al titolo. Otto scenari nativi locali passati, incluso il percorso delle due reliquie e del checkpoint. Modelli corretti preservati. [Preview e limiti](docs/FRONTEND.md).
- Play collegato allo spawn originale di Cosmic Core: primo percorso con 548 settori fisici, salto/planata e passaggio di settore verificati. Menu ampliato con crediti e changelog originali, volumi separati e camera automatica/manuale con sensibilità. [Screenshot e limiti](docs/CAMPAIGN_ENTRY.md).
- Primo incontro con Levium collegato al percorso di Cosmic Core: modello originale, sei battute, frase successiva, avvicinamento autore, pausa e stato di sessione verificati. Posa statica; animazioni NPC ancora da integrare. [Preview e limiti](docs/LEVIUM_DIALOGUE.md).
- **Prossima milestone:** animazioni originali Idle/Talking di Levium, con controlli su rig, materiali e resa in gioco.
- Pareti delle preview level3 corrette: ora derivano dai collider solidi originali `Walls.*`/`Walkable.*`, non dalla sola grafica. Provenienza verificata sull'originale, test di blocco contro un muro e regressioni native passati; [dettagli](docs/WALL_COLLIDERS.md). Percorso completo ancora da collegare.
- Collisioni verticali: il salto ora si arresta contro le superfici sopra la testa nelle preview level3/trampolino. Test host sui collider originali e regressioni in emulazione su salto libero e raccolta 3/3; [dettagli e limiti](docs/CEILINGS.md).
- Nuova preview separata del checkpoint originale 6752: attivazione di prossimità provvisoria, respawn da Select/menu e ripristino della direzione camera. Stato di sessione azzerato al titolo; [prove e limiti](docs/CHECKPOINTS.md). Interazione con Kiwi e memory card ancora assenti.
- Originale ricevuto e verificato: inventario delle 8 scene e recupero di 20 metodi di progressione/checkpoint/salvataggio. [Riferimento e criteri per il port completo](docs/PORT_COMPLETO.md). È lavoro di analisi, non nuovo gameplay; stima invariata.

[Screenshot prima e dopo e download del WIP](README.md)
