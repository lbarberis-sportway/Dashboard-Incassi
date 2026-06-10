# Dashboard Analisi Incassi Retail 📊

Questa repository contiene una dashboard interattiva sviluppata in Python tramite [Streamlit](https://streamlit.io/). L'obiettivo principale dell'applicazione è fornire un'analisi dettagliata degli incassi dei negozi, applicando le migliori pratiche del mondo retail per il confronto dei dati storici.

## 🔍 Logica dell'Analisi (Like-for-Like)

L'analisi va oltre il semplice confronto di date di calendario gregoriano (che spesso sfalserebbe i dati a causa dei diversi giorni della settimana da un anno all'altro). L'app implementa nativamente:

1. **Allineamento per Settimana ISO**: I confronti Year-to-Date (YTD) e i grafici di tendenza allineano automaticamente i giorni della settimana (es. il 1° Lunedì di Maggio 2024 viene confrontato in automatico con il corrispondente 1° Lunedì di Maggio 2023).
2. **Analisi Eventi e Saldi Relativi**: Permette di selezionare un periodo promozionale nell'anno in corso (es. "Saldi Estivi") e mappare la stessa durata in giorni a partire da una data di inizio dell'anno precedente, permettendo un vero confronto "Giorno 1 vs Giorno 1".
3. **Matrici di Sintesi (Pivot)**: Genera tabelle dinamiche per l'analisi macro per Anno (con crescita Delta % YoY) e per Mese, raggruppate per punto vendita, con scale di colore in stile heatmap.

## 🛠️ Come usare e testare l'app in locale (Per Sviluppatori)

### Prerequisiti
Assicurati di avere **Python 3.8+** installato sul tuo sistema.

### Installazione

1. Clona questa repository ed entra nella cartella del progetto:
   ```bash
   git clone <url-della-repo>
   cd <nome-cartella-repo>
   ```

2. *(Opzionale ma altamente consigliato)* Crea e attiva un ambiente virtuale (virtualenv) per isolare le dipendenze:
   ```bash
   python -m venv venv
   
   # Su Windows:
   venv\Scripts\activate
   # Su macOS/Linux:
   source venv/bin/activate
   ```

3. Installa le librerie Python richieste:
   ```bash
   pip install -r requirements.txt
   ```

### Avvio della Dashboard

Per lanciare il server locale di Streamlit, esegui il seguente comando dalla root del progetto:

```bash
streamlit run app.py
```

L'applicazione si aprirà automaticamente nel tuo browser predefinito all'indirizzo locale: `http://localhost:8501`. Qualsiasi modifica salvata al file `app.py` verrà applicata istantaneamente ricaricando la pagina del browser.

## 📁 Formato e Struttura dei Dati

Allo stato attuale, l'applicazione interroga i dati leggendoli da un file Excel locale inserito nella root.

- **Nome file atteso:** `INCASSI_NEGOZI_ANALISI.xlsx`
- **Foglio di lavoro (Sheet):** L'app cerca esplicitamente un foglio nominato `Dati`.
- **Colonne necessarie:**
  - `Data` (formato datetime)
  - `Negozio` (stringa)
  - `Incasso` (numerico float/int)
  - `Mese` (numerico)
  - `Settimana` (numerico ISO)
