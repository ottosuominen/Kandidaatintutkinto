import datetime as dt
from fmiopendata.wfs import download_stored_query
import os

# Muuntaa päivämäärän ISO8601-muotoon (sekunnintarkkuudella) ja lisää 'Z'-merkinnän UTC-aikavyöhykkeen osoittamiseksi
def formatDateToIso(date):
    return date.isoformat(timespec="seconds") + 'Z'

# Hakee säätietoja annetulta asemalta ja aikaväliltä
def getWeatherData(stationId, storedQueryId, startTime, endTime):
    try:
        result = download_stored_query(storedQueryId, args=[
            f'bbox=60,23,61,24',  # Määritetty koordinaatiston alue
            f'fmisid={stationId}',  # Aseman tunnus
            f'starttime={startTime}',  # Aloitusaika ISO8601-muodossa
            f'endtime={endTime}',  # Lopetusaika ISO8601-muodossa
            'timestep=15'  # Aikaväli: data haetaan 15 minuutin välein
        ])

        featureCollection = result.data
        if not featureCollection:
            print('No data found in the response.')
            return

        output = ""  # Ei lisätä otsikkoa

        # Käydään läpi datat aikaleiman ja aseman mukaan
        for tstep in sorted(featureCollection.keys()):
            stationData = {}  # Tallennetaan eri parametrien arvot yhteen paikkaan
            for station in featureCollection[tstep]:
                for param, val in featureCollection[tstep][station].items():
                    value = val.get('value', 'N/A')
                    stationData[param] = value  # Tallennetaan parametrin nimi ja arvo
                
                # Tallennetaan kaikki parametrit yhteen riviin, jotta ne eivät mene sekaisin
                output += f"Time: {tstep}, Station: {station}, Data: {stationData}\n"
        
        return output  # Palautetaan data, ei kirjoiteta tiedostoon suoraan

    except Exception as e:
        print('Error fetching data:', e)

# Hakee dataa viikoittaisissa jaksoissa annetulta aikaväliltä
def fetchDataInWeeklyIntervals(stationId, storedQueryId, startDate, endDate):
    allData = ""  # Kaikki data tallennetaan ensin tähän muuttujaan
    currentStartDate = startDate
    while currentStartDate < endDate:
        currentEndDate = currentStartDate + dt.timedelta(days=7)
        if currentEndDate > endDate:
            currentEndDate = endDate

        startTime = formatDateToIso(currentStartDate)
        endTime = formatDateToIso(currentEndDate)

        weatherData = getWeatherData(stationId, storedQueryId, startTime, endTime)
        if weatherData:
            allData += weatherData  # Lisätään haettu data muistiin

        currentStartDate = currentEndDate + dt.timedelta(seconds=1)
    
    return allData  # Palautetaan kaikki haettu data

# Määritetään asematunnus ja aikaväli
stationId = '101104'  # Asema: Jokioinen
startDate = dt.datetime(2024, 5, 11, 21, 0, 0)  # Aikavälin aloitus
endDate = dt.datetime(2024, 6, 11, 0, 0, 0)  # Aikavälin loppu

# Haetaan säädataa kahdesta eri kategoriasta ja tallennetaan muistiin
weatherData = fetchDataInWeeklyIntervals(stationId, 'fmi::observations::weather::multipointcoverage', startDate, endDate)
radiationData = fetchDataInWeeklyIntervals(stationId, 'fmi::observations::radiation::multipointcoverage', startDate, endDate)

# Kun kaikki data on haettu, kirjoitetaan tiedosto
with open('weatherdata.txt', 'w') as file:
    file.write(weatherData)

with open('radiationdata.txt', 'w') as file:
    file.write(radiationData)

print("All data has been written to files successfully.")
