import pandas as pd
import numpy as np
import ast
import pytz

def safeEvalDict(dictStr):
    try:
        return ast.literal_eval(dictStr)
    except (ValueError, SyntaxError):
        return {}

def processWeatherData(weatherFilePath):
    weatherData = []
    previousTemperature = None
    
    with open(weatherFilePath, 'r') as weatherFile:
        weatherLines = weatherFile.readlines()
    
    for line in weatherLines:
        if 'Time:' in line:
            parts = line.split(', ')
            timestamp = parts[0].split('Time: ')[1]
            dataStr = ', '.join(parts[2:])
            dataDict = safeEvalDict(dataStr.split('Data: ')[1])
            
            airTemperature = dataDict.get('Air temperature')
            
            if airTemperature is None or np.isnan(airTemperature):
                airTemperature = previousTemperature
            else:
                previousTemperature = airTemperature
            
            weatherData.append({'Timestamp': timestamp, 'Air temperature': airTemperature})

    return pd.DataFrame(weatherData)

def processRadiationData(filePath):
    radiationData = []
    with open(filePath, 'r') as file:
        for line in file:
            if 'Time:' in line:
                parts = line.split(', ')
                timestamp = parts[0].split('Time: ')[1]
                dataDict = {
                    keyVal.split(': ')[0]: max(0, float(keyVal.split(': ')[1]))
                    for keyVal in parts[2:] 
                    if any(x in keyVal for x in [
                        'Global radiation', 
                        'Direct solar radiation', 
                        'Reflected radiation', 
                        'Diffuse radiation'
                    ])
                }
                radiationData.append({'Timestamp': timestamp, **dataDict})
    
    return pd.DataFrame(radiationData)

def main(weatherFilePath, radiationFilePath, combinedOutputFile):
    # Määritetään Suomen aikavyöhyke
    FI_TZ = pytz.timezone('Europe/Helsinki')
    
    # Käsitellään molemmat datasetit
    weatherDf = processWeatherData(weatherFilePath)
    radiationDf = processRadiationData(radiationFilePath)
    
    # Muutetaan aikaleimat datetime-muotoon ja asetetaan aikavyöhykkeeksi UTC
    weatherDf['Timestamp'] = pd.to_datetime(weatherDf['Timestamp']).dt.tz_localize('UTC')
    radiationDf['Timestamp'] = pd.to_datetime(radiationDf['Timestamp']).dt.tz_localize('UTC')
    
    # Yhdistetään dataframet timestamp-sarakkeen perusteella
    combinedDf = pd.merge(radiationDf, weatherDf, on='Timestamp', how='outer')
    
    # Järjestetään aikaleiman mukaan
    combinedDf = combinedDf.sort_values('Timestamp')

    # Muunnetaan aikaleimat Suomen aikaan yhdistetyssä DataFramessa
    combinedDf['Timestamp'] = combinedDf['Timestamp'].dt.tz_convert(FI_TZ)

    # Muotoillaan aikaleima Exceliin sopivaksi
    combinedDf['Timestamp'] = combinedDf['Timestamp'].dt.strftime('%d.%m.%Y %H:%M')
    
    print(combinedDf)
    # Tallennetaan CSV-tiedostoon puolipisteellä erotettuna
    combinedDf.to_csv(combinedOutputFile, index=False, sep=';')
    print(f"Combined data has been saved to {combinedOutputFile}")

# Tiedostojen polut. Nämä pitää vaihtaa, kun ohjelma suoritetaan omalla koneella.
weatherFile = '/Users/ottosuominen/Tietotekniikka/Visualstudio/Kandi/weatherdata.txt'
radiationFile = '/Users/ottosuominen/Tietotekniikka/Visualstudio/Kandi/radiationdata.txt'
combinedOutputFile = '/Users/ottosuominen/Tietotekniikka/Visualstudio/Kandi/combinedweatherdata.csv'

# Ajetaan pääohjelma
main(weatherFile, radiationFile, combinedOutputFile)
