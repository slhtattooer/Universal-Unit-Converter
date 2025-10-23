=====================================
     UNIVERSAL UNIT CONVERTER
=====================================

Applicazione Flask per convertire qualsiasi unità di misura:
- Lunghezza, massa, volume, tempo, velocità, pressione, temperatura, dati, angoli e altro.
- Tutti i calcoli vengono eseguiti lato server, 100% in Python.

-------------------------------------
INSTALLAZIONE LOCALE
-------------------------------------

1. (Facoltativo ma consigliato)
   Crea un ambiente virtuale:
       python -m venv venv
       source venv/bin/activate        # Linux/Mac
       venv\Scripts\activate           # Windows

2. Installa le dipendenze:
       pip install -r requirements.txt

3. Avvia l’applicazione:
       python unit_converter.py

4. Apri il browser e visita:
       http://127.0.0.1:5000

-------------------------------------
DEPLOY (Heroku / Render / Railway)
-------------------------------------

Assicurati di avere questi file:
   - unit_converter.py
   - requirements.txt
   - Procfile

Imposta una chiave segreta come variabile d’ambiente:
   FLASK_SECRET_KEY=<chiave_randomica>

Esegui l’app con:
   gunicorn unit_converter:app

-------------------------------------
NOTE TECNICHE
-------------------------------------
- Framework: Flask
- Nessun database richiesto
- Tutti i calcoli avvengono in memoria
- Sessioni Flask firmate via cookie
- Porta configurabile tramite variabile d’ambiente PORT
- Interfaccia responsive basata su Bootstrap (HTML/CSS inline)
- Nessuna dipendenza esterna lato client: funziona ovunque

-------------------------------------
AUTORE
-------------------------------------
Creato da Andrea Buda (SLH Tattooer)
per divertimento e sperimentazione con Flask.

