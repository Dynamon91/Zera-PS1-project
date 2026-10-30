# Collisione verticale sopra la testa

Il salto nelle preview Dreary Valley e trampolino ora si arresta quando la
testa attraverserebbe una superficie dei collider originali. La velocità di
salita viene azzerata e il personaggio ricade sul piano inferiore. La query
seleziona la superficie più bassa sopra la testa, usando gli stessi triangoli
interi dei piani di appoggio, con interpolazione a 64 bit e bordi inclusi.

L'altezza provvisoria del corpo è 120 unità PS1, già usata dalle pareti; ora
è condivisa tramite `PLAYER_HEIGHT`. Non è una misura recuperata dal controller
Unity. Le frazioni della posizione della testa vengono arrotondate verso l'alto
per evitare agganci a superfici già superate. Il livello2 mantiene la sua
collisione precedente: i dati disponibili per quel percorso sono un heightfield.

## Prove eseguite

- Suite host completa con AddressSanitizer e UndefinedBehaviorSanitizer.
- Query su superfici sovrapposte, ordine dei vertici invertito, pendenze,
  bordi, triangoli verticali e coordinate limite dei dati short.
- Salto sotto un soffitto sintetico: arresto a quota 80, testa a quota 200,
  quindi ritorno a terra; verificata anche la testa inizialmente a contatto.
- Quota negativa frazionaria: intercettazione del soffitto senza attraversarlo.
- Query del collider originale a X=550, Z=0: superficie superiore a quota 261.
  La precedente fixture del giocatore in quel punto è stata rimossa: lo poneva
  dentro una parete inclinata, quindi non era una prova di salto valida.
  Il movimento contro i soffitti resta verificato con fixture sintetiche libere;
  vedere la [correzione della fixture](SLOPED_WALLS.md).
- Emulazione PCSX-ReARMed interpreter/software GPU, core
  `c8816799b50388e61cfe237fe2cdbb7d8175f20a`, BIOS HLE: percorso con controller
  fino a (500,0,0), salto libero fino a quota 153 e atterraggio, 1.250 frame
  video, zero respawn automatici e zero errori CD. È una regressione del salto
  libero, non una prova dell'urto contro un soffitto.
- Percorso nativo esistente da 5.700 frame: raccolta 1/3, 2/3, 3/3 con valori
  8, 16, 20; respawn conserva la raccolta, riavvio dell'area e ritorno al titolo
  la azzerano correttamente. Nessun errore CD osservato.
- Ricompilate con successo tutte e tre le immagini BIN/CUE.

I tentativi con controller verso i punti di sovrapposizione noti vengono
ostacolati dalle pareti conservative prima di raggiungere il punto di prova.
Non sono stati usati teletrasporti o scritture della RAM in emulazione. La
dimostrazione nativa di un urto sopra la testa resta da realizzare dopo aver
verificato un percorso adatto. [Evidenze della build corrente](../reports/ceiling_validation.json).

## Limiti e lavoro successivo

È un controllo verticale della testa lungo il salto, non una capsula completa:
restano da gestire ingresso orizzontale sotto soffitti bassi, ingombro laterale,
superfici mobili e collisioni continue durante i voli del trampolino. La query
usa soltanto i collider Walkable già convertiti nelle patch limitate. Non apre
nuovi livelli né abilita checkpoint o salvataggi.

Per ripetere la regressione nativa dopo la build:

```sh
python tools/capture_libretro.py /percorso/pcsx_rearmed_libretro.so build/zera_level3_preview.cue build/jump-preview tools/scenarios/level3_jump.json
python tools/check_jump_capture.py build/jump-preview
```

La CI esegue ora questo scenario e conserva le catture. HLE non certifica BIOS
reale, hardware o prestazioni. La stima di completamento resta provvisoria al 29%.
