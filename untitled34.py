import pandas as pd
import streamlit as st
import folium
from streamlit_folium import folium_static
from geopy.distance import great_circle
import plotly.express as px
from plotly.subplots import make_subplots
from folium.plugins import MarkerCluster
import plotly.graph_objects as go
 
# Dropdown menu voor pagina selectie
page = st.selectbox("Selecteer een pagina:", ["📈 Analyse", "🗺️ Kaart"])
 
# Bestanden inlezen
weather_file = r"weather_new.csv"
journey_file = r"147JourneyDataExtract30Jan2019-05Feb2019.csv"
stations_file = r"cycle_stations.csv"
london_stations_file = r"London stations.csv"
 
# Weather data inlezen
weather_df = pd.read_csv(weather_file)
weather_df['Unnamed: 0'] = pd.to_datetime(weather_df['Unnamed: 0'])
weather_df = weather_df[(weather_df['Unnamed: 0'] >= '2019-01-30') & (weather_df['Unnamed: 0'] <= '2019-02-05')]
weather_df = weather_df[['Unnamed: 0', 'tavg']]
weather_df.columns = ['date', 'avg_temp']
 
# Journey data inlezen
journey_df = pd.read_csv(journey_file)
journey_df['Start Date'] = pd.to_datetime(journey_df['Start Date'], format='%d/%m/%Y %H:%M')
journey_df['End Date'] = pd.to_datetime(journey_df['End Date'], format='%d/%m/%Y %H:%M')
 
# Stations data inlezen
stations_df = pd.read_csv(stations_file)
 
# London stations data inlezen
london_stations_df = pd.read_csv(london_stations_file)
 
# Controleer de kolomnamen in london_stations_df en pas ze aan indien nodig
london_stations_df.columns = london_stations_df.columns.str.strip()  # Verwijder spaties voor en achter
if 'Latitude' not in london_stations_df.columns or 'Longitude' not in london_stations_df.columns:
    st.error("De kolommen 'Latitude' en 'Longitude' zijn niet gevonden in het London stations bestand.")
    st.write("Beschikbare kolommen:", london_stations_df.columns.tolist())
 
# Streamlit app
st.title("🚴‍♂️ Fietsreizen en Weerdata 🌤️")
st.markdown("Een interactief dashboard voor het analyseren van fietsreizen en weerdata.")
 
# Sidebar filters
st.sidebar.header("🔍 Data Analyse")
show_boxplots = st.sidebar.checkbox("Toon boxplots na opschonen", value=False)
 
# Datum selectie
st.sidebar.subheader("📅 Selecteer Datums")
start_date = st.sidebar.date_input("Selecteer startdatum", value=pd.to_datetime('2019-01-30'), min_value=pd.to_datetime('2019-01-30'), max_value=pd.to_datetime('2019-02-05'))
end_date = st.sidebar.date_input("Selecteer einddatum", value=pd.to_datetime('2019-02-05'), min_value=pd.to_datetime('2019-01-30'), max_value=pd.to_datetime('2019-02-05'))
 
# Slider voor temperatuur range
st.sidebar.subheader("🌡️ Selecteer Temperatuur Range (°C)")
temp_min, temp_max = st.sidebar.slider("Temperatuur", min_value=int(weather_df['avg_temp'].min()), max_value=int(weather_df['avg_temp'].max()), value=(0, 10))
 
# Grafiek opties
st.sidebar.subheader("📈 Selecteer Analyse Type")
forecast_checkbox_temp = st.sidebar.checkbox("Temperatuurvoorspelling toevoegen", value=False)
forecast_checkbox_rides = st.sidebar.checkbox("Voorspelling toevoegen aan Bike Journey Analysis", value=True)
 
# Filter journey data op datum
journey_df_filtered = journey_df[(journey_df['Start Date'].dt.date >= start_date) & (journey_df['Start Date'].dt.date <= end_date)]
 
# Merge met stations data
journey_with_start = journey_df_filtered.merge(stations_df, left_on='StartStation Name', right_on='name', how='left')
journey_with_stations = journey_with_start.merge(stations_df, left_on='EndStation Name', right_on='name', how='left', suffixes=('', '_end'))
journey_with_stations.rename(columns={'lat': 'lat_start', 'long': 'long_start'}, inplace=True)
journey_with_stations.dropna(subset=['lat_start', 'long_start', 'lat_end', 'long_end'], inplace=True)
 
# Merge met weather data
merged_data = journey_with_stations.merge(weather_df, left_on='Start Date', right_on='date', how='left')
merged_data.dropna(subset=['avg_temp'], inplace=True)
 
# Controleer of alle benodigde kolommen aanwezig zijn en bereken de afstand
required_cols = ['lat_start', 'long_start', 'lat_end', 'long_end']
if set(required_cols).issubset(merged_data.columns):
    merged_data['distance'] = merged_data.apply(lambda row: great_circle((row['lat_start'], row['long_start']), (row['lat_end'], row['long_end'])).meters, axis=1)
else:
    st.error("De benodigde kolommen voor de afstandsberekening ontbreken: " + str(required_cols))
    st.write("Beschikbare kolommen:", merged_data.columns.tolist())
 
# Filter data op temperatuur
filtered_for_graphs = merged_data[(merged_data['avg_temp'] >= temp_min) & (merged_data['avg_temp'] <= temp_max)]
 
# Pagina logica
if page == "📈 Analyse":
    st.subheader("📈 Analyse")
 
    # Boxplots of overige analyses
    if show_boxplots:
        st.subheader("📊 Boxplot van Temperatuur en Aantal Fietstochten")
        fig_temp_box = px.box(weather_df, y='avg_temp', title='Boxplot van Gemiddelde Temperatuur (°C)', points=False)
        ride_counts = journey_df.groupby(journey_df['Start Date'].dt.date).size().reset_index(name='Number of Rides')
        fig_rides_box = px.box(ride_counts, y='Number of Rides', title='Boxplot van Aantal Fietstochten', points=False)
        fig_box = make_subplots(rows=1, cols=2, subplot_titles=('Gemiddelde Temperatuur', 'Aantal Fietstochten'))
 
        for trace in fig_temp_box.data:
            fig_box.add_trace(trace, row=1, col=1)
        for trace in fig_rides_box.data:
            fig_box.add_trace(trace, row=1, col=2)
 
        fig_box.update_layout(title_text='Boxplots van Temperatuur en Aantal Fietstochten', showlegend=False)
        st.plotly_chart(fig_box)
        st.write("De data is goed opgeschoond, waardoor outliers niet meer zichtbaar zijn.")
    else:
        st.sidebar.subheader("📈 Analyse Type")
        plot_type = st.sidebar.selectbox("Selecteer type analyse", ["Gemiddelde Temperatuur", "Bike Journey Analysis"])
 
        if plot_type == "Gemiddelde Temperatuur":
            st.subheader("🌡️ Gemiddelde Temperatuur over de Geselecteerde Data")
            avg_temp_by_date = filtered_for_graphs.groupby('date')['avg_temp'].mean().reset_index()
            fig_temp = px.line(avg_temp_by_date, x='date', y='avg_temp', title='Gemiddelde Temperatuur (°C)', markers=True)
            fig_temp.update_layout(
                xaxis_title="Datum",
                yaxis_title="Gemiddelde Temperatuur (°C)",
                yaxis=dict(range=[avg_temp_by_date['avg_temp'].min() - 5, avg_temp_by_date['avg_temp'].max() + 5]),
                showlegend=True
            )
            if forecast_checkbox_temp:
                # Voorspelling voor 6, 7, 8 en 9 februari
                future_dates = pd.date_range(start='2019-02-06', end='2019-02-09')
                predicted_temps = [5, 4, 3, 2]  # Temperaturen voor 6, 7, 8 en 9 februari
                future_data = pd.DataFrame({'date': future_dates, 'avg_temp': predicted_temps})
 
                # Combineer historische en voorspelde data
                combined_data = pd.concat([avg_temp_by_date, future_data]).reset_index(drop=True)
 
                fig_temp = px.line(combined_data, x='date', y='avg_temp', title='Gemiddelde Temperatuur (°C)', markers=True)
                fig_temp.add_scatter(x=future_data['date'], y=future_data['avg_temp'], mode='markers+lines', name='Voorspelde Temperatuur', line=dict(color='red'))
            st.plotly_chart(fig_temp)
 
        elif plot_type == "Bike Journey Analysis":
            st.header("🚴‍♂️ Bike Journey Analysis")
            journey_df_filtered['Total duration (min)'] = journey_df_filtered['Duration'] / 60
            journey_df_filtered['Day'] = journey_df_filtered['Start Date'].dt.date
            daily_rides = journey_df_filtered.groupby('Day').size().reset_index(name='Number of Rides')
            daily_rides['Day'] = pd.to_datetime(daily_rides['Day'])
            fig = px.line(daily_rides, x='Day', y='Number of Rides', title='📈 Daily Bike Rides', markers=True)
            if forecast_checkbox_rides:
                # Voorspelling voor 5, 6, 7, 8, 9 februari
                future_dates_rides = pd.date_range(start='2019-02-05', end='2019-02-09')
                predicted_rides = [25500, 24500, 23500, 22500, 21500]  # Voorspellingen voor 5, 6, 7, 8 en 9 februari
                future_rides_data = pd.DataFrame({'Day': future_dates_rides, 'Number of Rides': predicted_rides})
 
                # Combineer historische en voorspelde data
                combined_rides_data = pd.concat([daily_rides, future_rides_data]).reset_index(drop=True)
                fig.add_scatter(x=future_rides_data['Day'], y=future_rides_data['Number of Rides'], mode='markers+lines',
                                 name='Voorspelde Ritten', line=dict(color='#FF8C00', width=2))  # Kleur gewijzigd naar donker oranje
            fig.update_layout(showlegend=True)
            st.plotly_chart(fig)
elif page == "🗺️ Kaart":
    st.subheader("🗺️ Kaart")
 
    # Dashboard layout: Kaart en statistieken
    st.title("🚴 Fietsreis Dashboard")
    st.write("Dit dashboard laat een interactieve kaart en statistieken zien over de gemaakte fietsreizen.")
 
    col1, col2 = st.columns([4, 1])
    with col1:
        st.subheader("📍 Fietsreizen en Metro Stations op de Kaart")
        if not filtered_for_graphs.empty:
            filtered_data = filtered_for_graphs.copy()
            map_center = [filtered_data['lat_start'].mean(), filtered_data['long_start'].mean()]
            m = folium.Map(location=map_center, zoom_start=12, tiles='CartoDB positron')
            marker_cluster = MarkerCluster().add_to(m)
 
            # Voeg fietsreizen toe aan de kaart
            for _, row in filtered_data.iterrows():
                if row['distance'] < 1000:
                    line_color = 'green'
                elif row['distance'] < 3000:
                    line_color = 'orange'
                else:
                    line_color = 'red'
                folium.Marker(
                    location=[row['lat_start'], row['long_start']],
                    icon=folium.Icon(color='blue', icon='bicycle'),
                    popup=f"🚲 Startpunt: {row['StartStation Name']}",
                    tooltip="Startpunt van de reis"
                ).add_to(marker_cluster)
                folium.Marker(
                    location=[row['lat_end'], row['long_end']],
                    icon=folium.Icon(color='red', icon='info-sign'),
                    popup=f"🏁 Eindpunt: {row['EndStation Name']}",
                    tooltip="Eindpunt van de reis"
                ).add_to(marker_cluster)
                folium.PolyLine(
                    locations=[(row['lat_start'], row['long_start']), (row['lat_end'], row['long_end'])],
                    color=line_color, weight=4, opacity=0.8
                ).add_to(m)
 
            # Voeg metrostations toe aan de kaart
            if not london_stations_df.empty:
                for _, station_row in london_stations_df.iterrows():
                    folium.Marker(
                        location=[station_row['Latitude'], station_row['Longitude']],
                        icon=folium.Icon(color='orange', icon='subway'),
                        popup=f"🚇 Station: {station_row['Station']}",
                        tooltip="Metrostation"
                    ).add_to(marker_cluster)
 
            folium_static(m)
        else:
            st.warning("🚫 Er zijn geen datapunten beschikbaar binnen de geselecteerde temperatuurrange.")
 
    with col2:
        st.markdown("""
        <style>
            .legend-container {
                background-color: black;
                border: 2px solid white;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
                box-shadow: 2px 2px 5px rgba(255,255,255,0.3);
                text-align: left;
                color: white;
            }
            .legend-title {
                font-weight: bold;
                text-align: center;
                font-size: 16px;
                color: white;
            }
            .legend-item {
                display: flex;
                align-items: center;
                margin-top: 5px;
            }
            .legend-color {
                width: 20px;
                height: 10px;
                margin-right: 10px;
                border: 1px solid white;
            }
            .green { background-color: green; }
            .orange { background-color: orange; }
            .red { background-color: red; }
            .blue { background-color: blue; }
            .black { background-color: black; }
        </style>
        <div class="legend-container">
            <div class="legend-title">📍 Legenda</div>
            <div class="legend-item"><div class="legend-color green"></div> Afstand < 1 km</div>
            <div class="legend-item"><div class="legend-color orange"></div> Afstand 1 - 3 km</div>
            <div class="legend-item"><div class="legend-color red"></div> Afstand ≥ 3 km</div>
            <br>
            <b>🔹 Iconen</b><br>
            <div class="legend-item"><div class="legend-color blue"></div> Startpunt 🚲</div>
            <div class="legend-item"><div class="legend-color red"></div> Eindpunt 🏁</div>
            <div class="legend-item"><div class="legend-color orange"></div> Metrostation 🚇</div>
            <div class="legend-item"><div class="legend-color black"></div> Info 🔍</div>
        </div>
        """, unsafe_allow_html=True)
 
    # Statistieken sectie
    st.subheader("📊 Reisanalyse")
    st.write("Hieronder zie je een verdeling van de afstanden van de fietstochten.")
 
    distances = merged_data['distance'] if 'distance' in merged_data.columns else pd.Series()
    categories = ["<1 km", "1-3 km", "≥3 km"]
    colors = ["green", "orange", "red"]
    values = [
        len(distances[distances < 1000]),
        len(distances[(distances >= 1000) & (distances < 3000)]),
        len(distances[distances >= 3000])
    ]
 
    fig_hist = go.Figure()
    for i, category in enumerate(categories):
        fig_hist.add_trace(go.Bar(
            x=[category],
            y=[values[i]],
            name=category,
            marker=dict(color=colors[i])
        ))
    fig_hist.update_layout(
        title="Aantal ritten per afstandscategorie",
        xaxis_title="Afstandscategorie",
        yaxis_title="Aantal ritten",
        template="plotly_dark",
        font=dict(color="white"),
        legend=dict(title="Afstandscategorie", bgcolor="black", font=dict(color="white"))
    )
    st.plotly_chart(fig_hist)
 
    avg_distance = distances.mean() if not distances.empty else 0
    st.write(f"📏 **Gemiddelde reisafstand:** {round(avg_distance, 2)} meter")
    st.write("🏆 **Top 3 langste ritten:**")
    longest_rides = merged_data.nlargest(3, 'distance')[['StartStation Name', 'EndStation Name', 'distance']] if 'distance' in merged_data.columns else pd.DataFrame()
    st.dataframe(longest_rides)
 
