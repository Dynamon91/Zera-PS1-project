# Pareti dai collider originali

Nota di versione: la tabella seguente descrive il primo passaggio ai collider
originali, prima dell'ampliamento del corridoio. Il movimento attuale ritaglia
le facce all'altezza del corpo ([pareti inclinate](SLOPED_WALLS.md)); i proxy
verticali restano per la camera. La patch iniziale è ora il [corridoio esteso](DREARY_CORRIDOR.md).

La conversione delle tre preview level3 ora usa le **MeshCollider originali**
per i muri. Prima, `world_walls.h` veniva ricavato dai triangoli ripidi del
render, mentre l'estrazione dei collider accettava principalmente `Walkable.*`.
Questo escludeva `Walls.*` originali e faceva dipendere gli ostacoli da dettagli
della grafica, che possono differire dalla geometria fisica Unity.

Il convertitore considera i collider solidi attivi sotto `DrearyValley` e,
nella preview trampolino, quelli del suo oggetto originale. Esclude lava,
trigger, componenti disabilitati e gerarchie inattive. Applica le trasformazioni
originali del collider, senza usare le trasformazioni dei batch di rendering.
La selezione dei collider di appoggio rimane separata da quella delle pareti.

| Area | Proxy precedenti dal render | Proxy dai collider | Collider sorgente considerati |
| --- | ---: | ---: | ---: |
| Inizio Dreary Valley | 156 | 157 | 6 |
| Trampolino | 553 | 542 | 20 |
| Checkpoint | 91 | 90 | 10 |

Il conteggio dei proxy non è una misura di completezza del livello. I collider
considerati includono superfici Walkable che possono non generare alcun muro.
Render, suddivisione in celle, colori e piani di appoggio delle patch iniziale e
trampolino sono stati confrontati con i dati già committati e risultano invariati.

## Verifiche eseguite

- Dati originali: verificati gli hash dei file, il tipo MeshCollider, stato
  abilitato, assenza di trigger, gerarchia attiva, riferimenti mesh e matrice
  world dei 36 record sorgente delle tre aree. Non si tratta necessariamente
  di 36 collider unici, perché le patch possono sovrapporsi.
- Dati generati: corrispondenza tra report, array JSON, conteggio e header C;
  coordinate short valide e riferimenti alla scena originale corretti.
- Suite host con AddressSanitizer e UndefinedBehaviorSanitizer, inclusa la
  pressione continua contro la parete originale a X=547: il personaggio si
  arresta a X=522–523 con raggio 24, senza attraversarla.
- Stessa prova con controller in emulazione per **1.100 frame**: pressione a
  destra mantenuta contro il muro, personaggio a terra, zero respawn e zero
  errori CD osservati. Le tolleranze di un'unità derivano dalle proiezioni intere.
- Regressioni native: salto libero e atterraggio, checkpoint con ritorno da
  Select/menu e azzeramento al titolo, raccolta delle tre reliquie con valore
  totale 20, riavvio dell'area e ritorno al titolo.

Emulatore: PCSX-ReARMed `c8816799b50388e61cfe237fe2cdbb7d8175f20a`, HLE,
interpreter/software GPU. Il collaudo applica input del controller e legge lo
stato; non scrive la RAM. Nessuna verifica su BIOS reale o hardware.

[Evidenze e hash](../reports/wall_collider_validation.json).

## Limiti

Ogni triangolo ripido produce ancora un proxy verticale conservativo: lato X/Z
più lungo e intervallo Y. Non è una collisione esatta triangolo/capsula e può
ancora bloccare un passaggio. Non sono stati aggiunti BoxCollider, CapsuleCollider,
collisioni dinamiche, lava o attori fuori dalla selezione statica. La collisione
del livello2 resta quella precedente.

La correzione rende verificabile l'origine fisica dei muri; **non dimostra
ancora un percorso continuo dallo spawn di Dreary Valley al primo checkpoint**.
Le patch e la preview separata del checkpoint rimangono parziali.

## Riprodurre

```sh
python tools/check_wall_sources.py
python tools/check_wall_sources.py "/percorso/Zera Myths Awaken_Data"
sh tools/run_host_checks.sh
cmake --build build --parallel 4
python tools/capture_libretro.py /percorso/pcsx_rearmed_libretro.so build/zera_level3_preview.cue build/wall-collider-preview tools/scenarios/level3_wall.json
python tools/check_wall_capture.py build/wall-collider-preview
```

Il primo controllo funziona senza originali o dipendenze Unity. Il secondo
ricontrolla i record direttamente nei file originali. La CI esegue ora il
controllo dei dati e lo scenario nativo contro il muro.
