import datetime
import json
import logging
import time
import pandas as pd
from  zipfile import ZipFile
from io import StringIO, BytesIO
from lxml import etree
from weather_providers.base_provider import BaseWeatherProvider

try:  # Python 3
    from urllib.request import urlopen
except ImportError:
    logging.error("Python 2 is not supported!")

# Doc on fields:
# https://opendata.dwd.de/weather/lib/MetElementDefinition.xml


class DWD(BaseWeatherProvider):
    def __init__(self, dwd_location_id, units):
        self.location_id = dwd_location_id
        self.units = units

        self.station_list_url = 'https://www.dwd.de/DE/leistungen/klimadatendeutschland/statliste/statlex_html.html?view=nasPublication&nn=16102'
        self.station_list_cache_days = 1
        self.station_list_df = None
        self.forecasts_all_url = 'https://opendata.dwd.de/weather/local_forecasts/mos/MOSMIX_L/all_stations/kml/MOSMIX_L_LATEST.kmz'
        self.forecast_station_url = 'https://opendata.dwd.de/weather/local_forecasts/mos/MOSMIX_L/single_stations/{0}/kml/MOSMIX_L_LATEST_{0}.kmz'
        self.forecast_max_cache_secs = 3600

    # Build the URL for the API call
    def get_url(self):
        url = (self.forecast_station_url
               .format(self.location_id))

        return url

    def _download_unpack(self, url):
        try:
            logging.debug(f'Downloading: {url}')
            resp = urlopen(url)
            zfile = ZipFile(BytesIO(resp.read()))
            iodata = zfile.open(
                zfile.namelist()[0]).read()
        except Exception as e:
            logging.error(f'Unable to download {url}: {e}')
            return None
        return iodata

    def _download_station_forecast_raw(self):
        dl_url = self.get_url()
        return self._download_unpack(dl_url)

    def station_forecast(self):
        xml_data = self.get_response_xml(self.get_url(), None, True)
        if xml_data is None:
            return None
        logging.debug(f"Starting to parse station {self.location_id} xml...")

        # XML parsen
        root = xml_data #etree.fromstring(xml_data)
        ns = {
            'kml': 'http://www.opengis.net/kml/2.2',
            'dwd': 'https://opendata.dwd.de/weather/lib/pointforecast_dwd_extension_V1_0.xsd'
        }

        # Name der Station herausfinden
        station_name = None
        for placemark in root.findall('.//kml:Placemark', ns):
            loc = placemark.find('kml:name', ns)
            if loc is not None and loc.text == str(self.location_id):
                station_name = placemark.find('kml:description', ns).text
                break

        if not station_name:
            raise ValueError(f"Station mit ID {self.location_id} nicht gefunden.")

        # Zeitstempel extrahieren
        time_steps = root.find('.//dwd:ProductDefinition/dwd:ForecastTimeSteps', ns)
        times = [pd.to_datetime(t.text) for t in time_steps.findall('dwd:TimeStep', ns)]

        # Vorhersagewerte für die Zielstation extrahieren
        forecasts = []
        for location in root.findall('.//kml:Placemark', ns):
            if location.find('kml:name', ns).text != str(self.location_id):
                continue
            for param in location.findall('kml:ExtendedData/dwd:Forecast', ns):
                variable = param.attrib['{https://opendata.dwd.de/weather/lib/pointforecast_dwd_extension_V1_0.xsd}elementName']
                param_value = param.find('dwd:value',ns)
                values = [float(v) if v not in ('NaN', '-') else None for v in param_value.text.strip().split()]
                for i in range(0, len(values)-1):
                    forecasts.append({
                        'station_id': self.location_id,
                        'station_name': station_name,
                        'time': times[i],
                        'variable': variable,
                        'value': values[i]
                    })

        df = pd.DataFrame(forecasts)
        return df

    def get_weather(self):
        weather = {}
        #weather["current"] = self.get_current_weather()
        weather["hourly"] = self.get_hourly_forecast()
        #weather["daily"] = self.get_daily_forecast()

        return weather

    def get_hourly_forecast(self):
        df = self.station_forecast()
        records = df.set_index('time').to_dict('records')

        forecast = []
        for i in records.index[0:12]:
            entry = {}
            entry["dt"] = datetime.datetime.fromisoformat(str(i)).timestamp()
            entry["temperature"] = records[i].get('PPP')
            entry["wind_speed"] = records[i].get('FF')
            entry["wind_direction"] = records[i].get('DD')
            entry["clouds"] = records[i].get('N')
            entry["pop"] = records[i].get('wwP')

            #entry["feels_like"] = hour_entry["feels_like"]
            #entry["icon"] = self.get_icon_from_openweathermap_weathercode(hour_entry["weather"][0]["id"],
            #                                                              self.is_daytime(self.location_lat,
            #                                                                              self.location_long))
            #entry["description"] = hour_entry["weather"][0]["description"].title()

            forecast.append(entry)

        return forecast

    def get_daily_forecast(self):
        return {}

def main():
    weather = DWD(10853, "metric").get_weather()

    print(weather)

if __name__ == "__main__":
    main()
