import datetime
import logging
import pandas as pd
from zipfile import ZipFile
from io import BytesIO
import pytz
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

        self.df = None

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
        param_map = {"TTT": "temperature", "FF": "wind_speed", "DD": "wind_direction", "N": "clouds", "wwP": "pop"}
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

        weather_data = {}
        weather_data['times'] = times

        # Vorhersagewerte für die Zielstation extrahieren
        forecasts = []
        for location in root.findall('.//kml:Placemark', ns):
            if location.find('kml:name', ns).text != str(self.location_id):
                continue
            for param in location.findall('kml:ExtendedData/dwd:Forecast', ns):
                variable = param.attrib['{https://opendata.dwd.de/weather/lib/pointforecast_dwd_extension_V1_0.xsd}elementName']
                if variable in ("TTT", "FF", "DD", "N", "wwP"):
                    param_value = param.find('dwd:value',ns)
                    values = [float(v) if v not in ('NaN', '-') else None for v in param_value.text.strip().split()]
                    weather_data[param_map[variable]] = values

        df = pd.DataFrame(weather_data)
        return df

    def get_weather(self):
        self.df = self.station_forecast()

        weather = {}
        weather["current"] = self.get_current_weather()
        weather["hourly"] = self.get_hourly_forecast()
        weather["daily"] = self.get_daily_forecast()

        return weather

    def get_icon(self):
        '''TODO'''
        return "climacell_clear_day"

    def get_current_weather(self):
        weather_data = self.df.sort_values(by='times').groupby(by=self.df['times'].dt.date, group_keys=True).agg(
            {
                'temperature': ['min', 'max'],
                'wind_speed': ['min', 'max', 'mean', 'median'],
                'wind_direction': ['mean', 'median'],
                'clouds': ['min', 'max', 'mean', 'median'],
                'pop': ['min', 'max', 'mean', 'median']
            }
        ).head(1)

        weather = {}
        weather["temperatureMin"] = self.k_to_c(weather_data["temperature", "min"].values[0])
        weather["temperatureMax"] = self.k_to_c(weather_data["temperature", "max"].values[0])
        weather["icon"] = self.get_icon()
        weather["description"] = ""
        logging.debug(weather)
        return weather

    def get_hourly_forecast(self):
        hourly = self.df.sort_values(by ='times')

        # check for first entry that is not in the past
        start = 0
        time_now = pd.to_datetime(datetime.datetime.now(tz=pytz.timezone("Europe/Berlin")))
        for i in hourly.index:
            if hourly["times"][i] > time_now:
                break
            start = i

        forecast = []
        for i in range(start, start+13):
            entry = {}
            entry["dt"] = datetime.datetime.timestamp(hourly["times"][i])
            entry["temperature"] = self.k_to_c(hourly["temperature"][i])
            entry["wind_speed"] = hourly["wind_speed"][i]
            entry["wind_direction"] = self.wind_deg2txt(hourly["wind_direction"][i])
            entry["clouds"] = hourly["clouds"][i]
            entry["pop"] = hourly["pop"][i]/100.0
            entry["icon"] = self.get_icon()
            entry["description"] = ""

            forecast.append(entry)

        return forecast

    def get_daily_forecast(self):
        daily = self.df.sort_values(by = 'times').groupby(by=self.df['times'].dt.date, group_keys = True).agg(
            {
                'temperature': ['min', 'max'],
                'wind_speed': ['min', 'max', 'mean', 'median'],
                'wind_direction': ['mean', 'median'],
                'clouds': ['min', 'max', 'mean', 'median'],
                'pop': ['min', 'max', 'mean', 'median']
            }
        )

        daily_dict = daily.to_dict()

        forecast = []
        for day_index in daily.index:
            entry = {}
            entry["dt"] = datetime.datetime.timestamp(datetime.datetime.combine(day_index, datetime.time.fromisoformat("00:00:00")))
            entry["temperatureMin"] = self.k_to_c(daily_dict['temperature', 'min'][day_index])
            entry["temperatureMax"] = self.k_to_c(daily_dict['temperature', 'max'][day_index])
            entry["pop"] = daily_dict['pop', 'mean'][day_index]/100.0
            entry["wind_speed"] = daily_dict['wind_speed', 'mean'][day_index]
            entry["wind_direction"] = self.wind_deg2txt(daily_dict['wind_direction', 'mean'][day_index])
            entry["clouds"] = daily_dict['clouds', 'mean'][day_index]
            entry["icon"] = self.get_icon()
            entry["description"] = ""
            logging.debug(entry)
            forecast.append(entry)

        return forecast
