**Aufgabe Lab3 A2.1 Request-Reply:** 
 1. Experiment: 
   Client sendet 1. Nachricht und wartet anschließend auf Antwort vom Server. Erst wenn Bestätigung ankommt wird nächste Nachricht verschickt

 2. Experiment: 
   Beide Clients senden 1.Nachrichten und warten auf Antwort. Server antwortet zuerst ausschließlich dem Client, der als erstes gesendet hat und danach erst dem anderen Client.

 **Aufgabe Lab3.2:**
 1. Experiment:
   Beide Clients subscriben sich jeweils auf die Antworten die DATE oder TIME enthalten und printen diese aus. Der Server wird jedoch nicht gestoppt. Er sendet alle 5sec erneut Zeit und Datum.

 2. Experiment unterscheidet sich nicht vom 1.?

 **Aufgabe Lab3.3:**
 1. Experiment:
    Zuerst werden zwei Farmer gestartet, dann ein worker. Der Worker empfängt Nachrichten von beiden Farmern. Insgesamt also 200 Stück. Die Nachrichten werden abwechselnd empfangen.
 2. Experiment: 
    Zuerst werden zwei Worker gestartet, dann ein Farmer. Beide Worker empfangen empfangen jeweils 50 Nachrichten von dem Farmer. Da der Farmer insgesamt 100 verschickt, werden diese gleichmäßig aufgeteilt.