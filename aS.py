import ephem
import math
import csv
import pytz
from datetime import datetime, timedelta, timezone

# Suomen aikavyöhyke
FI_TZ = pytz.timezone('Europe/Helsinki')

# Määritellään tarkasteltava aikaväli
startDate = datetime(2024, 5, 20, 21, 0, 0, tzinfo=timezone.utc)  # Aloituspäivämäärä UTC-ajassa
endDate = datetime(2024, 5, 28, 23, 59, 59, tzinfo=timezone.utc)  # Lopetuspäivämäärä UTC-ajassa

# Paneelin asetukset
SETTINGS = {
    'latitude': '60.192059',  # Leveyspiiri
    'longitude': '24.945831',  # Pituuspiiri
    'panelTilt': 40,  # Paneelin kallistuskulma (astetta)
    'panelAzimuth': 177  # Paneelin atsimuuttikulma (astetta)
}

def calculatePhysicalIAM(angleOfIncidence, n=1.526, K=4, L=0.002):
    """
    Laskee IAM (Incident Angle Modifier) -arvon tulokulmalle
    :param angleOfIncidence: Tulokulma asteina
    :param n: Lasin taitekerroin (oletus 1.526)
    :param K: Lasin absorptiokerroin (oletus 4)
    :param L: Lasin paksuus (oletus 0.002)
    :return: IAM-arvo (välillä 0–1)
    """
    thetaRad = math.radians(angleOfIncidence)
    thetaRefracted = math.asin(math.sin(thetaRad) / n)
    
    tauTheta = math.exp(-K * L / math.cos(thetaRefracted)) * (
        1 - 0.5 * (
            (math.sin(thetaRefracted - thetaRad) ** 2 / math.sin(thetaRefracted + thetaRad) ** 2) +
            (math.tan(thetaRefracted - thetaRad) ** 2 / math.tan(thetaRefracted + thetaRad) ** 2)
        )
    )
    return max(0, min(1, tauTheta / math.exp(-K * L) * (1 + ((1 - n) / (1 + n)) ** 2)))

def calculateSolarData(currentDate):
    """Laskee auringon ja paneelin parametrit annetulle ajanhetkelle"""
    observer = ephem.Observer()
    observer.lat, observer.lon = SETTINGS['latitude'], SETTINGS['longitude']
    observer.date = currentDate

    sun = ephem.Sun(observer)
    solarAltitude = math.degrees(sun.alt)
    solarAzimuth = math.degrees(sun.az)

    # Tulokulman laskenta
    cosTheta = (
        math.sin(math.radians(solarAltitude)) * math.cos(math.radians(SETTINGS['panelTilt'])) +
        math.cos(math.radians(solarAltitude)) * math.sin(math.radians(SETTINGS['panelTilt'])) * 
        math.cos(math.radians(solarAzimuth) - math.radians(SETTINGS['panelAzimuth']))
    )
    
    angleOfIncidence = math.degrees(math.acos(max(-1, min(1, cosTheta))))
    
    return {
        'date': currentDate.astimezone(FI_TZ).strftime('%d.%m.%Y %H:%M'),
        'solarAltitude': f"{solarAltitude:.4f}",
        'solarAzimuth': f"{solarAzimuth:.4f}",
        'angleOfIncidence': f"{angleOfIncidence:.4f}",
        'cosineFactor': f"{math.cos(math.radians(angleOfIncidence)):.4f}",
        'IAM': f"{calculatePhysicalIAM(angleOfIncidence):.4f}"
    }

# Tiedoston kirjoitus
with open("solarPositionData.csv", 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["date", "solarAltitude", "solarAzimuth", "angleOfIncidence", "cosineFactor", "IAM"])
    
    currentDate = startDate
    while currentDate <= endDate:
        writer.writerow(calculateSolarData(currentDate).values())
        currentDate += timedelta(minutes=15)

print("CSV file created: solarPositionData.csv")
