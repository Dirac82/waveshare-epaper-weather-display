import json
import logging
import time
from  zipfile import ZipFile
from io import StringIO, BytesIO
import xml.etree.cElementTree as et
from weather_providers.base_provider import BaseWeatherProvider

try:  # Python 3
    from urllib.request import urlopen
except ImportError:
    logging.error("Python 2 is not supported!")

# Doc on fields:
# https://opendata.dwd.de/weather/lib/MetElementDefinition.xml


class DWD(BaseWeatherProvider):
    def __init__(self, dwd_location_id, units):
        self.location_id = dwd_locagion_id
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
        iodata = self.get_response_xml(self.get_url(), None, True)
        if iodata is None:
            return None
        logging.debug(f"Starting to parse station {self.location_id} xml...")
        xmlroot = et.fromstring(iodata)
        logging.debug("parsed xml")
        timesteps = []
        locations = []
        dfd = None
        for node in xmlroot:
            tag = self._filter_tag(node.tag)
            att = self._filter_attrib_dict(node.attrib)
            location = None
            for node2 in node:
                tag = self._filter_tag(node2.tag)
                att = self._filter_attrib_dict(node2.attrib)
                if tag == "Placemark":
                    location = {}
                    dfd = pd.DataFrame({'time': timesteps})
                    dfd.index = pd.to_datetime(dfd.pop('time'))
                for node3 in node2:
                    tag = self._filter_tag(node3.tag)
                    att = self._filter_attrib_dict(node3.attrib)
                    for node4 in node3:
                        tag = self._filter_tag(node4.tag)
                        att = self._filter_attrib_dict(node4.attrib)
                        if tag == 'Forecast':
                            key = att['elementName']
                        for node5 in node4:
                            data = None
                            tag = self._filter_tag(node5.tag)
                            att = self._filter_attrib_dict(node5.attrib)
                            text = node5.text
                            if tag == 'TimeStep':
                                timesteps.append(text)
                                text = None
                            if text is not None:
                                data = text.split()
                            if data is not None and tag == 'value':
                                dfd[key] = pd.to_numeric(
                                    pd.Series(data, index=dfd.index), errors='coerce')
                            else:
                                data = None
            if location is not None:
                dfd.index = dfd.index.tz_convert(tz=None)
                location['forecast'] = dfd
                locations.append(location)
                location = None

        try:
            all_forecasts = {'timestamp': time.time(),
                             locations: []}
            forecasts = json.loads(locations.to_json())
            forecast['timestamp'] = time.time()
        except Exception as e:
            self.log.warning(f'Failed to convert forecast to json: {e}')
            return dfd
        try:
            with open(forecast_cache_file, 'w') as f:
                json.dump(forecast, f)
        except Exception as e:
            self.log.warning(f'Failed to write forecast cache file {forecast_cache_file}: {e}')

    if station_id is None:
        return locations
    else:
        return dfd
