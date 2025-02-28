import streamlit as st
import pandas as pd
import numpy as np
#import folium
#from streamlit_folium import folium_static
import requests
#from bs4 import BeautifulSoup
#from playwright.sync_api import sync_playwright
#from geopy.geocoders import Nominatim
#import matplotlib.pyplot as plt
import webbrowser
import io

def get_lat_lon(address):
    geolocator = Nominatim(user_agent="house_rental_estimator")
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude
    return None, None

def open_new_tab(link):
    webbrowser.open_new_tab(link)

def calcola_ricavi(tariffa, occupazione, mesi=12):
    return tariffa * occupazione * mesi

def calcola_netto(prezzo_airbnb, occupazione, costi_mensili, tasse):
    # Basic price per night
    prezzo_notte = prezzo_airbnb / 30
    stagionalita = {"novembre": 0.75, "dicembre": 1, "gennaio": 0.75, "febbraio": 0.75, "agosto": 0.75}
    ricavi_mensili = {}
    
    # Compute monthly revenue considering seasonality and occupancy
    for mese in ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]:
        riduzione = stagionalita.get(mese, 1)  # Get seasonality adjustment
        ricavi_mensili[mese] = (prezzo_notte * riduzione) * occupazione  # Adjusted price per night and occupancy
    
    # Compute netto with dynamic tax calculation per month
    data = []
    for mese, ricavo in ricavi_mensili.items():
        riduzione = stagionalita.get(mese, 1)
        prezzo_notte_aggiustato = prezzo_notte * riduzione  # Adjusted nightly price for each month
        tassa_mese = (ricavo * tasse) / 100  # Monthly tax calculation
        netto = ricavo - tassa_mese - costi_mensili  # Net income
        
        data.append({
            "Mese": mese,
            "Ricavi Netti": netto,
            "%Netto": netto / ricavo * 100,  # Percentage of net income relative to gross
            "Ricavi Lordi": ricavo,
            "Ricavi a Notte": prezzo_notte_aggiustato,  # Adjusted nightly price
            "Occupazione (gg)": occupazione,
            "Costi Mensili (€)": costi_mensili,
            "Tasse (€)": tassa_mese,
        })
    
    # Create DataFrame
    df_netto = pd.DataFrame(data)
    # Calculate netto mensile (monthly net income) for each month
    netto_mensile = {mese: (ricavo - (ricavo * tasse) - costi_mensili) for mese, ricavo in ricavi_mensili.items()}
    return df_netto, netto_mensile

# Funzione per simulare il netto modificando l'occupazione (giorni di affitto per mese)
def simulate_occupazione(df, occ, tax_rate=10):
    # Calcola il nuovo ricavo lordo per ogni mese: prezzo a notte aggiustato * nuovi giorni di affitto
    nuovo_ricavo = df["Ricavi a Notte"] * occ  
    # Calcola la tassa per ogni mese (assumendo una percentuale fissa, ad esempio 10%)
    nuova_tassa = nuovo_ricavo * (tax_rate / 100)
    # Calcola il nuovo netto: ricavo lordo - tassa - costi mensili
    nuovo_netto = nuovo_ricavo - nuova_tassa - df["Costi Mensili (€)"]
    return nuovo_ricavo.sum(), nuovo_netto.sum()



######################################### APP

# *SIDEBAR
st.sidebar.image("logo.png", width=100)
st.sidebar.header("Porta Metronia Case Vacanze")
st.sidebar.divider()
st.sidebar.subheader("Steps:")
st.sidebar.markdown('''
1. 🏠 **Stima i ricavi** per la tua casa con i dati di Airbnb
2. 💲**Stima il netto** mensile e annuale per la tua casa
3. 🌙 **Compara le metriche** per il numero di notti affittate al mese
''')
st.sidebar.divider()
if st.sidebar.button("Torna al sito"):
    open_new_tab("https://4nemo0220.github.io/porta-metronia/servizi.html")


# *PAGE
st.title("Stima dei Ricavi per Casa Vacanze a Roma")
st.markdown('''
Vuoi scoprire se affittare la tua casa vacanze è davvero **conveniente**?
:rainbow[Ti aiutiamo noi!]

Con pochi semplici passi, stimeremo i tuoi ricavi lordi con i **dati di mercato** più aggiornati di **:red[Airbnb]**. Poi calcoleremo insieme il **netto**, considerando tutti i **costi fissi e variabili** di una casa vacanze Romana DOC.
Pront* per iniziare? 🚀''')
st.divider()

# *STEP1 - Airbnb
st.subheader("🏠 Step 1. Stima i ricavi per la tua casa con i dati di Airbnb")
st.markdown('''
Clicca sul bottone \"Apri Airbnb\" per navigare alla pagina Airbnb dedicata alla stima dei ricavi. 
Su **Airbnb**:
1. Inserisci l'**indirizzo** della tua casa
2. Seleziona si tratta di una **Stanza Privata** o di un **Alloggio Intero**
3. Inserisci il **numero di stanze** da letto
4. Seleziona **30 notti** sul cursore
5. **Torna su questa pagina per stimare il netto con noi**
''')
airbnb_button = st.button("Apri Airbnb", type="primary")
if airbnb_button:
    open_new_tab("https://www.airbnb.it/host/homes")
st.markdown('''\n*:red[Utilizziamo il calcolatore di Airbnb poiché poggia su dati di mercato **realistici** e **sempre aggiornati** e su **modelli predittivi** di **Intelligenza Artificiale** che permettono una stima sempre accurata]*''')
st.divider()

# STEP 2. Stima Netto
st.subheader("💲Step 2. Stima il netto mensile e annuale per la tua casa")
st.text("Ora facciamo una stima realistica del netto considerando costi fissi e variabili. Su Airbnb questa funzione non è disponibile")
prezzo_airbnb = st.number_input("Inserisci la stima riportata da Airbnb per 30 giorni", min_value=0, value=2000)
occupazione= st.slider("Inserisci il numero di giorni occupati al mese", min_value=0, value=25, max_value=30)
costi_mensili = st.number_input("Inserisci i costi mensili (acqua, luce, gas, wifi)", min_value=0, value=350)
tasse = st.number_input("Inserisci la percentuale di tasse applicata (cedolare secca 21%)", min_value=0, value=21, max_value=100)

calcola_netto_btn = st.button("Calcola Netto", type="primary")

# Button Calcolo
if calcola_netto_btn:
    st.text("")
    ricavi_annui = calcola_ricavi(tariffa=prezzo_airbnb/30, occupazione=occupazione)
    df_netto, netto_mensile = calcola_netto(prezzo_airbnb, occupazione, costi_mensili, tasse)

    # Calcolo delle metriche principali aggregando i dati per anno (ogni riga è un mese)
    total_lordo   = df_netto["Ricavi Lordi"].sum()
    total_netto   = df_netto["Ricavi Netti"].sum()
    active_months = len(df_netto)  # normalmente 12 mesi
    total_notti   = df_netto["Occupazione (gg)"].sum()  # totale notti occupate nell'anno
    avg_notti     = df_netto["Occupazione (gg)"].mean()

    # Calcolo delle percentuali
    perc_tasse      = (df_netto["Tasse (€)"].sum() / total_lordo * 100) if total_lordo != 0 else 0
    perc_netto    = (total_netto / total_lordo * 100) if total_lordo != 0 else 0
    perc_costi    = (df_netto["Costi Mensili (€)"].sum() / total_lordo * 100) if total_lordo != 0 else 0

    # Simulazione del netto con occupazione costante a 20, 25 e 30 giorni per mese
    ricavo_20, netto_20 = simulate_occupazione(df_netto, 20)
    ricavo_25, netto_25 = simulate_occupazione(df_netto, 25)
    ricavo_30, netto_30 = simulate_occupazione(df_netto, 30)
    
    # *STATISTICHE MESE
    st.markdown("**📆 Statistiche :orange-background[Mensili]**")
    col1, col2, col3, col4 = st.columns(4, gap="medium")
    col1.metric("Lordo Medio Mese", round(df_netto["Ricavi Lordi"].mean()))
    col2.metric("Netto Medio Mese", round(df_netto["Ricavi Netti"].mean()))
    col3.metric("Tasse Medie Mese", round(df_netto["Tasse (€)"].mean()))
    col4.metric("Costi Medi Mese", round(df_netto["Costi Mensili (€)"].mean()))

    # *STATISTICHE ANNO
    st.markdown("**📆 Statistiche :red-background[Annuali]**")
    col5, col6, col7, col8 = st.columns(4, gap="medium")

    # Colonna 5: Ricavi e informazioni sui mesi
    col5.metric("Totale Lordo", round(total_lordo))
    col5.metric("Totale Notti (anno)", round(total_notti))

    # Colonna 6: Dati relativi alle fees (tasse) e all'occupazione media
    col6.metric("Totale Netto", round(total_netto))
    col6.metric("% Netto su Lordo", f"{round(perc_netto)}%")
    
    # Colonna 7: Dati sul netto bonificato e simulazioni per diversi scenari di occupazione
    col7.metric("Totale Tasse (€)", round(df_netto["Tasse (€)"].sum()))
    col7.metric("% Tasse su Lordo", f"{round(perc_tasse)}%")

    # Colonna 8: Informazioni sui costi
    col8.metric("Totale Costi (anno)", round(df_netto["Costi Mensili (€)"].sum()))
    col8.metric("% Costi su Lordo", f"{round(perc_costi)}%")

    st.markdown("**📈 Scarica il :blue-background[Report]**")
    st.write(df_netto)


    # Convertire in Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_netto.to_excel(writer, index=False, sheet_name="Simulazione_Anno")

    excel_data = output.getvalue()

    # Bottone per scaricare Excel
    st.download_button(
        label=f"📥 Scarica Report {occupazione} giorni in Excel",
        data=excel_data,
        file_name=f"stima_casavacanze_{occupazione}_giorni_porta_metronia.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary"
    )
    st.markdown('''*:red[Aggiorna i giorni e calcola nuovamente il netto o prosegui a **comparare le metriche per 20/25/30 giorni**]*''')
    
        
    # fig, ax = plt.subplots()
    # ax.plot(list(netto_mensile.keys()), list(netto_mensile.values()), marker='o', linestyle='-', label='Netto Mensile')
    # ax.set_xlabel("Mese")
    # ax.set_ylabel("Ricavi Netti (€)")
    # ax.set_title("Trend dei Ricavi Netti")
    # ax.legend()
    # st.pyplot(fig)

    st.divider()
    # *STEP 3. Comparazione per tassi di occupazione
    st.subheader("🌙 Step 3. Compara le metriche per il numero di notti affittate al mese")
    st.text("Compara i ricavi e il netto per occupazione di 20/25/30 giorni al mese")

    col9, col10, col11= st.columns(3, gap="large")
    col9.metric("Notti", 20)
    col10.metric("Notti", 25)
    col11.metric("Notti", 30)

    col9.metric("Lordo (20 gg/mese)", round(ricavo_20))
    col10.metric("Lordo (25 gg/mese)", round(ricavo_25))
    col11.metric("Lordo (30 gg/mese)", round(ricavo_30))

    col9.metric("Netto (20 gg/mese)", round(netto_20))
    col10.metric("Netto (25 gg/mese)", round(netto_25))
    col11.metric("Netto (30 gg/mese)", round(netto_30))

    col9.metric("% Netto su Lordo (20 gg/mese)", round(netto_20/ricavo_20*100))
    col10.metric("% Netto su Lordo (25 gg/mese)", round(netto_25/ricavo_25*100))
    col11.metric("% Netto su Lordo (30 gg/mese)", round(netto_30/ricavo_30*100))

    st.markdown('''*:red[All'aumentare dei ricavi il netto sale in percentuale poiché i costi rimangono fissi]*''')
    st.divider()

    st.subheader("🔎 Come Calcoliamo il Netto")
    st.markdown(f"""
    1. **Calcoliamo il prezzo base per notte:** dividiamo il prezzo mensile indicato da Airbnb per 30.
    2. **Adeguiamo per stagionalità:** applichiamo una riduzione del 25% del prezzo a notte nei mesi di bassa stagione (Novembre, Dicembre, Gennaio, Febbraio ed Agosto).
    3. **Stimiamo i ricavi lordi mensili:** moltiplichiamo il prezzo per notte adeguato in base alla stagione per il numero previsto di notti occupate nel mese.
    4. **Calcoliamo le tasse mensili:** determiniamo le tasse come percentuale dei ricavi lordi mensili, applicando di base un 21% di cedolare secca.
    5. **Determiniamo il guadagno netto mensile:** sottraendo dai ricavi lordi mensili sia le tasse sia i costi fissi mensili (manutenzione, utenze, ecc.).
    """)
    st.subheader("Extra da Considerare")
    st.markdown("""
    - **Pulizie**: Costi di pulizia a ogni cambio ospite
    - **Danni**: Possibili costi di riparazione
    - **Late arrivals**: Supplementi per arrivi tardivi
    """)

    st.divider()
    st.subheader("Vuoi avviare la tua casa autonomamente?")
    st.markdown("Torna sul sito di **Porta Metronia** cliccando sul bottone nella sidebar e 📤 :red[**Scarica la Guida** dalla nostra **pagina di Servizi**]")

# *STEP4 - Map
#indirizzo = st.text_input("Inserisci indirizzo o zona:")
#if indirizzo:
#    lat, lon = get_lat_lon(indirizzo)
#    if lat and lon:
#        mappa = folium.Map(location=[lat, lon], zoom_start=14)
#        folium.Marker([lat, lon], popup=indirizzo).add_to(mappa)
#        folium_static(mappa)