import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta

def format_euro(val):
    if pd.isna(val):
        return "-"
    return f"€ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_perc(val):
    if pd.isna(val):
        return "-"
    return f"{val:+.1%}".replace(".", ",")

st.set_page_config(page_title="Dashboard Incassi Negozi", layout="wide", page_icon="logo.png")

@st.cache_data
def load_data():
    # Carichiamo i dati
    df = pd.read_excel('INCASSI_NEGOZI_ANALISI.xlsx', sheet_name='Dati')
    # Assicuriamoci che Data sia datetime
    df['Data'] = pd.to_datetime(df['Data'])
    
    # Estraiamo informazioni temporali chiave
    df['Anno'] = df['Data'].dt.year
    df['Mese'] = df['Data'].dt.month
    df['Settimana'] = df['Data'].dt.isocalendar().week
    df['GiornoSettimana'] = df['Data'].dt.dayofweek # 0=Lunedì, 6=Domenica
    
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Errore nel caricamento del file Excel: {e}")
    st.stop()

st.title("Dashboard Incassi Negozi")
st.markdown("Analisi basata sul confronto tra settimane e giorni omologhi.")

# --- SIDEBAR FILTRI GLOBALI ---
st.sidebar.header("Filtri Principali")

negozi_disponibili = df['Negozio'].unique()
negozi_selezionati = st.sidebar.multiselect("Seleziona Negozio/i", negozi_disponibili, default=negozi_disponibili)

anni_disponibili = sorted(df['Anno'].dropna().unique(), reverse=True)
if len(anni_disponibili) >= 2:
    anno_corrente = st.sidebar.selectbox("Anno di Riferimento", anni_disponibili, index=0)
    anno_confronto = st.sidebar.selectbox("Anno di Confronto", anni_disponibili, index=1)
else:
    anno_corrente = anni_disponibili[0] if anni_disponibili else None
    anno_confronto = anni_disponibili[0] if anni_disponibili else None
    st.sidebar.warning("Non ci sono abbastanza anni per il confronto.")

# Applica filtro negozio
if negozi_selezionati:
    df_filtered = df[df['Negozio'].isin(negozi_selezionati)]
else:
    df_filtered = df.copy()

st.divider()

if anno_corrente and anno_confronto:
    # --- SEZIONE 1: KPI YTD (Year To Date) Like-for-Like ---
    st.header(f"YTD: {anno_corrente} vs {anno_confronto}")
    st.caption("Questo grafico mostra come si posiziona l'anno corrente rispetto all'anno precedente, tenendo conto che ci si può fermare in qualunque giorno.")
    
    df_curr = df_filtered[df_filtered['Anno'] == anno_corrente]
    df_prev = df_filtered[df_filtered['Anno'] == anno_confronto]
    
    if not df_curr.empty:
        # Trova l'ultimo record dell'anno corrente per capire fin dove calcolare il YTD
        ultima_data_curr = df_curr['Data'].max()
        
        # Filtriamo df_curr per prendere i dati del giorno massimo
        latest_day_data = df_curr[df_curr['Data'] == ultima_data_curr]
        ultima_settimana_curr = latest_day_data['Settimana'].values[0]
        ultimo_giorno_sett_curr = latest_day_data['GiornoSettimana'].values[0]
        
        # YTD Anno Corrente: tutto l'anno fino ad oggi
        ytd_curr = df_curr['Incasso'].sum()
        
        # YTD Anno Confronto (Allineato)
        # Prendiamo tutte le settimane fino all'ultima settimana. 
        # Per l'ultima settimana considerata, ci fermiamo al giorno della settimana corrispondente.
        mask_prev_ytd = (
            (df_prev['Settimana'] < ultima_settimana_curr) | 
            ((df_prev['Settimana'] == ultima_settimana_curr) & (df_prev['GiornoSettimana'] <= ultimo_giorno_sett_curr))
        )
        ytd_prev = df_prev[mask_prev_ytd]['Incasso'].sum()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(f"Incasso YTD {anno_corrente}", format_euro(ytd_curr))
        with col2:
            st.metric(f"Incasso YTD {anno_confronto} (Allineato)", format_euro(ytd_prev))
        with col3:
            delta = ytd_curr - ytd_prev
            if ytd_prev > 0:
                delta_perc = (delta / ytd_prev) * 100
            else:
                delta_perc = 0
            st.metric("Delta (Valore / %)", format_euro(delta), f"{delta_perc:+.2f}%".replace(".", ","))
            
    else:
        st.warning(f"Nessun dato trovato per l'anno {anno_corrente}.")

    st.divider()
    
    # --- SEZIONE 2: ANDAMENTO SETTIMANALE ---
    st.header("Andamento per Settimana dell'Anno")
    st.caption("Confronto delle curve di incasso allineando la Settimana dell'anno (da 1 a 52/53).")
    
    # Raggruppamento per settimana
    groupby_curr = df_curr.groupby('Settimana')['Incasso'].sum().reset_index()
    groupby_prev = df_prev.groupby('Settimana')['Incasso'].sum().reset_index()
    
    groupby_curr['Anno'] = str(anno_corrente)
    groupby_prev['Anno'] = str(anno_confronto)
    
    df_trend = pd.concat([groupby_curr, groupby_prev])
    
    if not df_trend.empty:
        fig_trend = px.line(df_trend, x='Settimana', y='Incasso', color='Anno', markers=True,
                            title="Incasso per Settimana ISO",
                            labels={"Incasso": "Incasso (€)", "Settimana": "Settimana dell'Anno"})
        fig_trend.update_layout(xaxis=dict(tickmode='linear', dtick=1))
        st.plotly_chart(fig_trend, use_container_width=True)

    # --- MATRICE SETTIMANALE YTD (INTERATTIVA) ---
    if not df_curr.empty and not df_prev.empty:
        ultima_data_curr = df_curr['Data'].max()
        latest_day_data = df_curr[df_curr['Data'] == ultima_data_curr]
        ultima_settimana_curr = latest_day_data['Settimana'].values[0]
        ultimo_giorno_sett_curr = latest_day_data['GiornoSettimana'].values[0]

        mask_prev_aligned = (
            (df_prev['Settimana'] < ultima_settimana_curr) |
            ((df_prev['Settimana'] == ultima_settimana_curr) & (df_prev['GiornoSettimana'] <= ultimo_giorno_sett_curr))
        )
        df_prev_aligned = df_prev[mask_prev_aligned]

        weekly_curr = df_curr.groupby('Settimana')['Incasso'].sum().reset_index()
        weekly_curr.columns = ['Settimana', f'Incasso {anno_corrente}']

        weekly_prev = df_prev_aligned.groupby('Settimana')['Incasso'].sum().reset_index()
        weekly_prev.columns = ['Settimana', f'Incasso {anno_confronto}']

        ytd_matrix = weekly_curr.merge(weekly_prev, on='Settimana', how='left')
        ytd_matrix = ytd_matrix.sort_values('Settimana').reset_index(drop=True)
        ytd_matrix = ytd_matrix.fillna(0)

        ytd_matrix[f'Cumulato {anno_corrente}'] = ytd_matrix[f'Incasso {anno_corrente}'].cumsum()
        ytd_matrix[f'Cumulato {anno_confronto}'] = ytd_matrix[f'Incasso {anno_confronto}'].cumsum()

        ytd_matrix['Delta %'] = 0.0
        mask_valid = ytd_matrix[f'Incasso {anno_confronto}'] > 0
        ytd_matrix.loc[mask_valid, 'Delta %'] = (
            (ytd_matrix.loc[mask_valid, f'Incasso {anno_corrente}'] - ytd_matrix.loc[mask_valid, f'Incasso {anno_confronto}'])
            / ytd_matrix.loc[mask_valid, f'Incasso {anno_confronto}']
        )

        col_inc_curr = f'Incasso {anno_corrente}'
        col_inc_prev = f'Incasso {anno_confronto}'
        col_cum_curr = f'Cumulato {anno_corrente}'
        col_cum_prev = f'Cumulato {anno_confronto}'

        ytd_matrix.set_index('Settimana', inplace=True)

        st.subheader(f"Matrice Settimanale YTD ({anno_corrente} vs {anno_confronto})")
        st.caption("Dettaglio settimana per settimana con cumulato e delta %")

        # Stile DataFrame
        format_dict = {
            col_inc_curr: format_euro,
            col_cum_curr: format_euro,
            col_inc_prev: format_euro,
            col_cum_prev: format_euro,
            'Delta %': format_perc
        }
        
        styled_matrix = ytd_matrix.style.format(format_dict, na_rep="-")
        styled_matrix = styled_matrix.background_gradient(cmap='RdYlGn', subset=['Delta %'], vmin=-0.3, vmax=0.3)
        
        st.dataframe(styled_matrix, use_container_width=True)

    st.divider()
    
    # --- SEZIONE 3: CONFRONTO PERIODI CUSTOM (ES. SALDI) ---
    st.header("Analisi Periodi Personalizzati")
    st.caption("Confronto periodo specifico di quest'anno con i giorni corrispondenti dell'anno passato.")
    
    colA, colB = st.columns(2)
    
    with colA:
        st.subheader(f"Periodo A ({anno_corrente})")
        # Default al primo dell'anno per evitare errori se non ci sono date
        min_date_curr = df_curr['Data'].min().date() if not df_curr.empty else pd.to_datetime(f"{anno_corrente}-01-01").date()
        data_inizio_A = st.date_input(f"Inizio Periodo {anno_corrente}", min_date_curr, format="DD/MM/YYYY")
        # Default a un mese dopo, o max date
        data_fine_A = st.date_input(f"Fine Periodo {anno_corrente}", min_date_curr + timedelta(days=30), format="DD/MM/YYYY")
        
    with colB:
        st.subheader(f"Periodo B di Confronto ({anno_confronto})")
        min_date_prev = df_prev['Data'].min().date() if not df_prev.empty else pd.to_datetime(f"{anno_confronto}-01-01").date()

        # Allineamento YTD: stessa settimana ISO e stesso giorno della settimana di Periodo A
        ts_a = pd.Timestamp(data_inizio_A)
        iso_week, iso_weekday = ts_a.isocalendar()[1], ts_a.isocalendar()[2]  # 1-53, 1=Mon..7=Sun
        jan4_prev = pd.Timestamp(anno_confronto, 1, 4)
        lun_sett1_prev = jan4_prev - pd.Timedelta(days=jan4_prev.dayofweek)
        data_inizio_B_default = (lun_sett1_prev + pd.Timedelta(weeks=iso_week - 1, days=iso_weekday - 1)).date()

        data_inizio_B = st.date_input(
            f"Inizio Periodo {anno_confronto}",
            value=data_inizio_B_default,
            min_value=min_date_prev,
            key=f"inizio_B_{anno_confronto}_{data_inizio_A.isoformat()}",
            format="DD/MM/YYYY"
        )
        st.caption(f"Data auto-allineata come YTD (stessa Settimana ISO e giorno di {data_inizio_A.strftime('%d/%m/%Y')}). Modificabile manualmente.")
        st.info("La data di fine viene calcolata in automatico per combaciare con la durata di analisi del Periodo A.")
        
    if data_inizio_A <= data_fine_A:
        durata_giorni = (data_fine_A - data_inizio_A).days
        data_fine_B = data_inizio_B + timedelta(days=durata_giorni)
        
        st.write(f"**Durata Analisi:** {durata_giorni + 1} giorni. Il Periodo B calcolato è dal `{data_inizio_B.strftime('%d/%m/%Y')}` al `{data_fine_B.strftime('%d/%m/%Y')}`.")
        
        # Filtriamo i dataframe per le date specificate
        mask_A = (df_curr['Data'].dt.date >= data_inizio_A) & (df_curr['Data'].dt.date <= data_fine_A)
        df_saldi_A = df_curr[mask_A].copy()
        
        mask_B = (df_prev['Data'].dt.date >= data_inizio_B) & (df_prev['Data'].dt.date <= data_fine_B)
        df_saldi_B = df_prev[mask_B].copy()
        
        if not df_saldi_A.empty and not df_saldi_B.empty:
            # Calcoliamo il "Giorno N" relativo per poter sovrapporre le curve sul grafico
            df_saldi_A['Giorno_Relativo'] = (df_saldi_A['Data'] - pd.to_datetime(data_inizio_A)).dt.days + 1
            df_saldi_B['Giorno_Relativo'] = (df_saldi_B['Data'] - pd.to_datetime(data_inizio_B)).dt.days + 1
            
            # Aggreghiamo
            agg_A = df_saldi_A.groupby('Giorno_Relativo')['Incasso'].sum().reset_index()
            agg_A['Serie'] = f"{anno_corrente} (dal {data_inizio_A.strftime('%d/%m')})"
            
            agg_B = df_saldi_B.groupby('Giorno_Relativo')['Incasso'].sum().reset_index()
            agg_B['Serie'] = f"{anno_confronto} (dal {data_inizio_B.strftime('%d/%m')})"
            
            df_saldi_confronto = pd.concat([agg_A, agg_B])
            
            # Grafico
            fig_saldi = px.line(df_saldi_confronto, x='Giorno_Relativo', y='Incasso', color='Serie',
                                title=f"Andamento Giornaliero - {durata_giorni + 1} giorni a confronto", markers=True,
                                labels={"Giorno_Relativo": "Giorno rel. (1 = Giorno di Inizio)", "Incasso": "Incasso (€)"})
            st.plotly_chart(fig_saldi, use_container_width=True)
            
            # KPI Totali
            tot_A = agg_A['Incasso'].sum()
            tot_B = agg_B['Incasso'].sum()
            delta_saldi = tot_A - tot_B
            delta_saldi_perc = (delta_saldi / tot_B * 100) if tot_B > 0 else 0
            
            st.success(f"**Totale {anno_corrente}:** {format_euro(tot_A)} | **Totale {anno_confronto}:** {format_euro(tot_B)} | **Delta:** {f'{delta_saldi_perc:+.2f}%'.replace('.', ',')}")
        else:
            st.warning("Non ci sono abbastanza dati nei periodi selezionati per mostrare il grafico.")
    else:
        st.error("La data di fine del Periodo A deve essere successiva o uguale alla data di inizio.")

    # --- SEZIONE 4: DATI DI SINTESI (MATRICI) ---
    st.divider()
    st.header("Dati di Sintesi")
    
    tab_anno, tab_mese = st.tabs(["📅 Analisi x Anno", "📆 Analisi x Mese"])
    
    with tab_anno:
        st.subheader("Incasso Assoluto per Anno e Negozio")
        # Raggruppa l'intero dataframe per Anno e Negozio
        pivot_anno = df_filtered.pivot_table(index='Anno', columns='Negozio', values='Incasso', aggfunc='sum')
        pivot_anno['Totale Anno'] = pivot_anno.sum(axis=1)
        
        # Formattazione
        st.dataframe(
            pivot_anno.style.format(format_euro).background_gradient(cmap='Greens', axis=0), 
            use_container_width=True
        )
        
        st.subheader("Crescita % Anno su Anno (YoY)")
        # Calcolo del Delta percentuale
        pivot_anno_delta = pivot_anno.pct_change()
        st.dataframe(
            pivot_anno_delta.style.format(format_perc).background_gradient(cmap='RdYlGn', axis=0, vmin=-0.3, vmax=0.3), 
            use_container_width=True
        )
        
        if not df_curr.empty:
            ultima_data_str = df_curr['Data'].max().strftime('%d/%m/%Y')
            st.info(f"Attenzione: l'anno corrente ({anno_corrente}) è ancora in corso, i dati arrivano fino al giorno {ultima_data_str}.")
        
    with tab_mese:
        st.subheader(f"Incasso per Mese e Negozio (Anno selezionato: {anno_corrente})")
        # Raggruppa solo per l'anno corrente
        pivot_mese = df_curr.pivot_table(index='Mese', columns='Negozio', values='Incasso', aggfunc='sum')
        
        if not pivot_mese.empty:
            pivot_mese['Totale Mese'] = pivot_mese.sum(axis=1)
            
            # Mappiamo i numeri dei mesi in nomi per renderli più leggibili
            mesi_nomi = {1:'Gen', 2:'Feb', 3:'Mar', 4:'Apr', 5:'Mag', 6:'Giu', 
                         7:'Lug', 8:'Ago', 9:'Set', 10:'Ott', 11:'Nov', 12:'Dic'}
            pivot_mese.index = pivot_mese.index.map(lambda x: mesi_nomi.get(x, str(x)))
            
            # Aggiungiamo la riga dei totali per colonna (in fondo)
            pivot_mese.loc['Totale'] = pivot_mese.sum(axis=0)
            
            # Escludiamo l'ultima riga ('Totale') dal calcolo dei colori per non sballare la scala
            subset_rows = pivot_mese.index[:-1]
            
            st.dataframe(
                pivot_mese.style.format(format_euro).background_gradient(cmap='Blues', axis=0, subset=(subset_rows, pivot_mese.columns)), 
                use_container_width=True
            )
        else:
            st.info(f"Nessun dato mensile disponibile per il {anno_corrente}.")
