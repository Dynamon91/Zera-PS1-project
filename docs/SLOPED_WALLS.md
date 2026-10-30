# Pareti inclinate: collisione all'altezza del corpo

Il movimento delle tre preview level3 usa ora i triangoli ripidi dei collider
originali, ritagliati alla fascia verticale del personaggio: piedi+8 fino alla
testa. La proiezione X/Z della porzione rimasta determina il contatto e lo
scorrimento. Una parete triangolare alta non blocca più automaticamente tutto
il rettangolo tra i suoi estremi. La telecamera mantiene i proxy precedenti;
la collisione del level2 mantiene il proprio modello.

## Caso originale verificato

Un muro vicino allo spawn passa da X=574 alla base a X=547 a quota 265. Il
vecchio proxy usava X=547 a tutte le altezze; con una testa a quota 120, la
porzione pertinente arriva invece a circa X=562.

Con lo stesso scenario del controller da 1.100 frame, la build precedente si
arrestava a **X=522**, quella attuale a **X=537**. Entrambe bloccano il muro,
ma la nuova permette 15 unità PS1 aggiuntive di avvicinamento alla superficie
inclinata. Il raggio del corpo rimane 24. Il vecchio risultato è stato verificato
contro l'hash del BIN conservato nello ZIP della build precedente.

I test host verificano anche un'apertura sotto una faccia triangolare: il
rettangolo precedente la bloccava, mentre il ritaglio all'altezza del corpo la
lascia libera. Si tratta di una fixture sintetica, non della prova di un nuovo
sottopassaggio percorribile nel livello originale.

## Test e correzione di una fixture precedente

Suite host con sanitizer: pareti verticali e inclinate, sotto/sopra la faccia,
ordine dei vertici invertito, interno della proiezione, bordi e coordinate short
estese. La radice e i prodotti delle distanze usano ora 64 bit dove necessario.

La vecchia prova del salto con il giocatore inizializzato a X=550,Z=0 piazzava
il corpo **dentro questa parete inclinata**. È stata rimossa come prova di salto
valida. Rimangono le query dei collider originali e i test del movimento contro
soffitti sintetici in uno spazio libero; non si afferma un urto nativo sopra la
testa. Le vecchie evidenze di quel posizionamento non vanno usate come prova di
un sottopassaggio raggiungibile.

Il passo fisico calcola inoltre i risultati in uno stato locale e li pubblica
al termine, evitando che il collaudo legga la posizione temporanea prima della
risoluzione dei contatti durante un frame video.

Regressioni native: muro inclinato, salto libero, checkpoint e raccolta 3/3.
PCSX-ReARMed HLE interpreter/software GPU; nessun BIOS reale o hardware verificato.
[Evidenze](../reports/sloped_wall_validation.json).

## Limiti e prossima milestone

Questo è un ritaglio verticale e una risoluzione per triangolo della proiezione,
non uno sweep continuo di capsula. Giunzioni fra triangoli, ingresso orizzontale
sotto soffitti, collider dinamici e robustezza a velocità elevate richiedono
ancora lavoro. La camera conserva le approssimazioni precedenti.

La reliquia 6606 è ora [raccolta nel corridoio](CORRIDOR_RELIC.md).
Ora è raccolta anche la [reliquia inferiore 6898](TWO_CORRIDOR_RELICS.md).
Il [checkpoint 6752 è ora collegato](CONNECTED_CHECKPOINT.md).
**Prossima milestone:** recuperare e visualizzare la sua pianta originale.
