#!/usr/bin/python

import datetime
import sys
import os
import logging
from weather_providers import openweathermap, dwd
from utility import get_formatted_time, update_svg, configure_logging, configure_locale
import textwrap

configure_locale()
configure_logging()


def format_weather_description(weather_description):
    if len(weather_description) < 20:
        return {1: weather_description, 2: ''}

    splits = textwrap.fill(weather_description, 20, break_long_words=False,
                           max_lines=2, placeholder='...').split('\n')
    weather_dict = {1: splits[0]}
    weather_dict[2] = splits[1] if len(splits) > 1 else ''
    return weather_dict


def get_weather(location_lat, location_long, units):

    # gather relevant environment configs
    openweathermap_apikey = os.getenv("OPENWEATHERMAP_APIKEY")
    dwd_station_id = os.getenv("DWD_STATION_ID")

    openweathermap_weather = None
    dwd_weather = None

    if (
        not openweathermap_apikey
        and not dwd_station_id
    ):
        logging.error("No weather provider has been configured (OpenWeatherMap)")
        sys.exit(1)

    if openweathermap_apikey:
        logging.info("Getting weather from OpenWeatherMap")
        weather_provider = openweathermap.OpenWeatherMap(openweathermap_apikey,
                                                         location_lat,
                                                         location_long,
                                                         units)
        openweathermap_weather = weather_provider.get_weather()
    if dwd_station_id:
        logging.info("Getting weather from DWD")
        weather_provider = dwd.DWD(dwd_station_id,
                                   units)
        dwd_weather = weather_provider.get_weather()

    # merge weather icon from openweathermap with data from DWD
    if dwd_weather is not None and openweathermap_weather is not None:
        dwd_weather["current"]["icon"] = openweathermap_weather["current"]["icon"]

        for i in range(0, min(len(dwd_weather["hourly"]), len(openweathermap_weather["hourly"]))-1):
            dwd_weather["hourly"][i]["icon"] = openweathermap_weather["hourly"][i]["icon"]

        for i in range(0,min(len(dwd_weather["daily"]),len(openweathermap_weather["daily"]))-1):
            dwd_weather["daily"][i]["icon"] = openweathermap_weather["daily"][i]["icon"]

        weather = dwd_weather

    elif dwd_weather is not None:
        weather = dwd_weather

    elif openweathermap_weather is not None:
        weather = openweathermap_weather

    logging.info("weather - {}".format(weather))

    return weather


def main():

    template_name = os.getenv("SCREEN_LAYOUT", "1")
    location_lat = os.getenv("WEATHER_LATITUDE", "51.5077")
    location_long = os.getenv("WEATHER_LONGITUDE", "-0.1277")
    weather_format = os.getenv("WEATHER_FORMAT", "CELSIUS")

    if (weather_format == "CELSIUS"):
        units = "metric"
        degrees = "°C"
    else:
        units = "imperial"
        degrees = "°F"

    weather = get_weather(location_lat, location_long, units)

    if not weather:
        logging.error("Unable to fetch weather payload. SVG will not be updated.")
        return

    weather_desc = format_weather_description(weather["current"]["description"])

    time_now = get_formatted_time(datetime.datetime.now())
    time_now_font_size = "100px"

    if len(time_now) > 6:
        time_now_font_size = str(100 - (len(time_now)-5) * 5) + "px"

    output_dict = {
        'LOW_ONE': "{}{}".format(str(round(weather["current"]['temperatureMin'])), degrees),
        'HIGH_ONE': "{}{}".format(str(round(weather["current"]['temperatureMax'])), degrees),
        'ICON_ONE': weather["current"]["icon"],
        'WEATHER_DESC_1': weather_desc[1],
        'WEATHER_DESC_2': weather_desc[2],
        'TIME_NOW_FONT_SIZE': time_now_font_size,
        'TIME_NOW': datetime.datetime.now().strftime("%H:%M"),
        'HOUR_NOW': datetime.datetime.now().strftime("%H"),
        'DAY_ONE': datetime.datetime.now().strftime("%b %-d, %Y"),
        'DAY_NAME': datetime.datetime.now().strftime("%A"),
        'ALERT_MESSAGE_VISIBILITY': "hidden"}

    for i in range(1, 13):
        output_dict['WEATHER_HOUR_DATETIME_{:X}'.format(i)] = datetime.datetime.fromtimestamp(weather["hourly"][i]["dt"]).strftime("%H")
        output_dict['W_HOUR_TEMP_{:X}'.format(i)] =  "{}{}".format(str(round(weather["hourly"][i]["temperature"])), degrees)
        output_dict['W_HOUR_CLOUDS_{:X}'.format(i)] = "{}%".format(str(round(weather["hourly"][i]["clouds"])))
        output_dict['W_HOUR_POP_{:X}'.format(i)] = "{}%".format(str(round(weather["hourly"][i]["pop"]*100)))
        output_dict['W_HOUR_WIND_SPEED_{:X}'.format(i)] = "{}m/s".format(str(round(weather["hourly"][i]["wind_speed"])))
        output_dict['W_HOUR_WIND_DIR_{:X}'.format(i)] = weather["hourly"][i]["wind_direction"]
        output_dict['W_HOUR_ICON_{:X}'.format(i)] = weather["hourly"][i]["icon"]
        output_dict['WEATHER_HOUR_DESC_{:X}'.format(i)] = weather["hourly"][i]["description"]

    for i in range(1,8):
        output_dict['WEATHER_DAY_DATETIME_{}'.format(i)] = datetime.datetime.fromtimestamp(weather["daily"][i]["dt"]).strftime("%a %d")
        output_dict['W_DAY_TEMP_MIN_{}'.format(i)] = "{}{}".format(str(round(weather["daily"][i]["temperatureMin"])), degrees)
        output_dict['W_DAY_TEMP_MAX_{}'.format(i)] = "{}{}".format(str(round(weather["daily"][i]["temperatureMax"])), degrees)
        output_dict['W_DAY_CLOUDS_{}'.format(i)] = "{}%".format(str(round(weather["daily"][i]["clouds"])))
        output_dict['W_DAY_POP_{}'.format(i)] = "{}%".format(str(round(weather["daily"][i]["pop"]*100)))
        output_dict['W_DAY_WIND_SPEED_{}'.format(i)] = "{}m/s".format(str(round(weather["daily"][i]["wind_speed"])))
        output_dict['W_DAY_WIND_DIR_{}'.format(i)] = weather["daily"][i]["wind_direction"]
        output_dict['W_DAY_ICON_{}'.format(i)] = weather["daily"][i]["icon"]
        output_dict['WEATHER_DAY_DESC_{}'.format(i)] = weather["daily"][i]["description"]

    logging.debug(output_dict)

    logging.info("Updating SVG")

    template_svg_filename = f'screen-template.{template_name}.svg'
    output_svg_filename = 'screen-output-weather.svg'
    update_svg(template_svg_filename, output_svg_filename, output_dict)

if __name__ == "__main__":
    main()
