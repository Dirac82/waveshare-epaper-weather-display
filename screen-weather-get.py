#!/usr/bin/python

import datetime
import sys
import os
import logging
from weather_providers import openweathermap
from utility import get_formatted_time, update_svg, configure_logging, configure_locale
import textwrap
import html

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

    if (
        not openweathermap_apikey
    ):
        logging.error("No weather provider has been configured (OpenWeatherMap)")
        sys.exit(1)

    if openweathermap_apikey:
        logging.info("Getting weather from OpenWeatherMap")
        weather_provider = openweathermap.OpenWeatherMap(openweathermap_apikey,
                                                         location_lat,
                                                         location_long,
                                                         units)
        hourly_weather = weather_provider.get_hourly_forecast()
        logging.info("hourly_forecast[{}] - {}".format(len(hourly_weather), hourly_weather[0:12]))
        daily_weather = weather_provider.get_daily_forecast()
        logging.info("daily_forecast[{}] - {}".format(len(daily_weather), daily_weather))

    weather = weather_provider.get_weather()
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
        'TIME_NOW': time_now,
        'HOUR_NOW': datetime.datetime.now().strftime("%-I %p"),
        'DAY_ONE': datetime.datetime.now().strftime("%b %-d, %Y"),
        'DAY_NAME': datetime.datetime.now().strftime("%A"),
        'ALERT_MESSAGE_VISIBILITY': "hidden",

        'WEATHER_HOUR_DATETIME_1': datetime.datetime.fromtimestamp(weather["hourly"][1]["dt"]).strftime("%I %p"),
        'W_HOUR_TEMP_1': "{}{}".format(str(round(weather["hourly"][1]["temperature"])), degrees),
        'W_HOUR_FEEL_1': "{}{}".format(str(round(weather["hourly"][1]["feels_like"])), degrees),
        'W_HOUR_CLOUDS_1': "{}%".format(str(round(weather["hourly"][1]["clouds"]))),
        'W_HOUR_POP_1': "{}%".format(str(round(weather["hourly"][1]["pop"]*100))),
        'WEATHER_HOUR_DESC_1': weather["hourly"][1]["description"],

        'WEATHER_HOUR_DATETIME_2': datetime.datetime.fromtimestamp(weather["hourly"][2]["dt"]).strftime("%I %p"),
        'W_HOUR_TEMP_2': "{}{}".format(str(round(weather["hourly"][2]["temperature"])), degrees),
        'W_HOUR_FEEL_2': "{}{}".format(str(round(weather["hourly"][2]["feels_like"])), degrees),
        'W_HOUR_CLOUDS_2': "{}%".format(str(round(weather["hourly"][2]["clouds"]))),
        'W_HOUR_POP_2': "{}%".format(str(round(weather["hourly"][2]["pop"]*100))),
        'WEATHER_HOUR_DESC_2': weather["hourly"][2]["description"],

        'WEATHER_HOUR_DATETIME_3': datetime.datetime.fromtimestamp(weather["hourly"][3]["dt"]).strftime("%I %p"),
        'W_HOUR_TEMP_3': "{}{}".format(str(round(weather["hourly"][3]["temperature"])), degrees),
        'W_HOUR_FEEL_3': "{}{}".format(str(round(weather["hourly"][3]["feels_like"])), degrees),
        'W_HOUR_CLOUDS_3': "{}%".format(str(round(weather["hourly"][3]["clouds"]))),
        'W_HOUR_POP_3': "{}%".format(str(round(weather["hourly"][3]["pop"]*100))),
        'WEATHER_HOUR_DESC_3': weather["hourly"][3]["description"],

        'WEATHER_HOUR_DATETIME_4': datetime.datetime.fromtimestamp(weather["hourly"][4]["dt"]).strftime("%I %p"),
        'W_HOUR_TEMP_4': "{}{}".format(str(round(weather["hourly"][4]["temperature"])), degrees),
        'W_HOUR_FEEL_4': "{}{}".format(str(round(weather["hourly"][4]["feels_like"])), degrees),
        'W_HOUR_CLOUDS_4': "{}%".format(str(round(weather["hourly"][4]["clouds"]))),
        'W_HOUR_POP_4': "{}%".format(str(round(weather["hourly"][4]["pop"]*100))),
        'WEATHER_HOUR_DESC_4': weather["hourly"][4]["description"],

        'WEATHER_HOUR_DATETIME_5': datetime.datetime.fromtimestamp(weather["hourly"][5]["dt"]).strftime("%I %p"),
        'W_HOUR_TEMP_5': "{}{}".format(str(round(weather["hourly"][5]["temperature"])), degrees),
        'W_HOUR_FEEL_5': "{}{}".format(str(round(weather["hourly"][5]["feels_like"])), degrees),
        'W_HOUR_CLOUDS_5': "{}%".format(str(round(weather["hourly"][5]["clouds"]))),
        'W_HOUR_POP_5': "{}%".format(str(round(weather["hourly"][5]["pop"]*100))),
        'WEATHER_HOUR_DESC_5': weather["hourly"][5]["description"],

        'WEATHER_HOUR_DATETIME_6': datetime.datetime.fromtimestamp(weather["hourly"][6]["dt"]).strftime("%I %p"),
        'W_HOUR_TEMP_6': "{}{}".format(str(round(weather["hourly"][6]["temperature"])), degrees),
        'W_HOUR_FEEL_6': "{}{}".format(str(round(weather["hourly"][6]["feels_like"])), degrees),
        'W_HOUR_CLOUDS_6': "{}%".format(str(round(weather["hourly"][6]["clouds"]))),
        'W_HOUR_POP_6': "{}%".format(str(round(weather["hourly"][6]["pop"]*100))),
        'WEATHER_HOUR_DESC_6': weather["hourly"][6]["description"],

        'WEATHER_HOUR_DATETIME_7': datetime.datetime.fromtimestamp(weather["hourly"][7]["dt"]).strftime("%I %p"),
        'W_HOUR_TEMP_7': "{}{}".format(str(round(weather["hourly"][7]["temperature"])), degrees),
        'W_HOUR_FEEL_7': "{}{}".format(str(round(weather["hourly"][7]["feels_like"])), degrees),
        'W_HOUR_CLOUDS_7': "{}%".format(str(round(weather["hourly"][7]["clouds"]))),
        'W_HOUR_POP_7': "{}%".format(str(round(weather["hourly"][7]["pop"]*100))),
        'WEATHER_HOUR_DESC_7': weather["hourly"][7]["description"],

        'WEATHER_HOUR_DATETIME_8': datetime.datetime.fromtimestamp(weather["hourly"][8]["dt"]).strftime("%I %p"),
        'W_HOUR_TEMP_8': "{}{}".format(str(round(weather["hourly"][8]["temperature"])), degrees),
        'W_HOUR_FEEL_8': "{}{}".format(str(round(weather["hourly"][8]["feels_like"])), degrees),
        'W_HOUR_CLOUDS_8': "{}%".format(str(round(weather["hourly"][8]["clouds"]))),
        'W_HOUR_POP_8': "{}%".format(str(round(weather["hourly"][8]["pop"]*100))),
        'WEATHER_HOUR_DESC_8': weather["hourly"][8]["description"],

        'WEATHER_HOUR_DATETIME_9': datetime.datetime.fromtimestamp(weather["hourly"][9]["dt"]).strftime("%I %p"),
        'W_HOUR_TEMP_9': "{}{}".format(str(round(weather["hourly"][9]["temperature"])), degrees),
        'W_HOUR_FEEL_9': "{}{}".format(str(round(weather["hourly"][9]["feels_like"])), degrees),
        'W_HOUR_CLOUDS_9': "{}%".format(str(round(weather["hourly"][9]["clouds"]))),
        'W_HOUR_POP_9': "{}%".format(str(round(weather["hourly"][9]["pop"]*100))),
        'WEATHER_HOUR_DESC_9': weather["hourly"][9]["description"],

        'WEATHER_HOUR_DATETIME_10': datetime.datetime.fromtimestamp(weather["hourly"][10]["dt"]).strftime("%I %p"),
        'W_HOUR_TEMP_10': "{}{}".format(str(round(weather["hourly"][10]["temperature"])), degrees),
        'W_HOUR_FEEL_10': "{}{}".format(str(round(weather["hourly"][10]["feels_like"])), degrees),
        'W_HOUR_CLOUDS_10': "{}%".format(str(round(weather["hourly"][10]["clouds"]))),
        'W_HOUR_POP_10': "{}%".format(str(round(weather["hourly"][10]["pop"]*100))),
        'WEATHER_HOUR_DESC_10': weather["hourly"][10]["description"],

        'WEATHER_HOUR_DATETIME_11': datetime.datetime.fromtimestamp(weather["hourly"][11]["dt"]).strftime("%I %p"),
        'W_HOUR_TEMP_11': "{}{}".format(str(round(weather["hourly"][11]["temperature"])), degrees),
        'W_HOUR_FEEL_11': "{}{}".format(str(round(weather["hourly"][11]["feels_like"])), degrees),
        'W_HOUR_CLOUDS_11': "{}%".format(str(round(weather["hourly"][11]["clouds"]))),
        'W_HOUR_POP_11': "{}%".format(str(round(weather["hourly"][11]["pop"]*100))),
        'WEATHER_HOUR_DESC_11': weather["hourly"][11]["description"],

        'WEATHER_DAY_DATETIME_1': datetime.datetime.fromtimestamp(weather["daily"][1]["dt"]).strftime("%a %d"),
        'W_DAY_TEMP_MIN_1': "{}{}".format(str(round(weather["daily"][1]["temperatureMin"])), degrees),
        'W_DAY_TEMP_MAX_1': "{}{}".format(str(round(weather["daily"][1]["temperatureMax"])), degrees),
        'W_DAY_CLOUDS_1': "{}%".format(str(round(weather["daily"][1]["clouds"]))),
        'W_DAY_POP_1': "{}%".format(str(round(weather["daily"][1]["pop"]*100))),
        'WEATHER_DAY_DESC_1': weather["daily"][1]["description"],

        'WEATHER_DAY_DATETIME_2': datetime.datetime.fromtimestamp(weather["daily"][2]["dt"]).strftime("%a %d"),
        'W_DAY_TEMP_MIN_2': "{}{}".format(str(round(weather["daily"][2]["temperatureMin"])), degrees),
        'W_DAY_TEMP_MAX_2': "{}{}".format(str(round(weather["daily"][2]["temperatureMax"])), degrees),
        'W_DAY_CLOUDS_2': "{}%".format(str(round(weather["daily"][2]["clouds"]))),
        'W_DAY_POP_2': "{}%".format(str(round(weather["daily"][2]["pop"]*100))),
        'WEATHER_DAY_DESC_2': weather["daily"][2]["description"],

        'WEATHER_DAY_DATETIME_3': datetime.datetime.fromtimestamp(weather["daily"][3]["dt"]).strftime("%a %d"),
        'W_DAY_TEMP_MIN_3': "{}{}".format(str(round(weather["daily"][3]["temperatureMin"])), degrees),
        'W_DAY_TEMP_MAX_3': "{}{}".format(str(round(weather["daily"][3]["temperatureMax"])), degrees),
        'W_DAY_CLOUDS_3': "{}%".format(str(round(weather["daily"][3]["clouds"]))),
        'W_DAY_POP_3': "{}%".format(str(round(weather["daily"][3]["pop"]*100))),
        'WEATHER_DAY_DESC_3': weather["daily"][3]["description"],

        'WEATHER_DAY_DATETIME_4': datetime.datetime.fromtimestamp(weather["daily"][4]["dt"]).strftime("%a %d"),
        'W_DAY_TEMP_MIN_4': "{}{}".format(str(round(weather["daily"][4]["temperatureMin"])), degrees),
        'W_DAY_TEMP_MAX_4': "{}{}".format(str(round(weather["daily"][4]["temperatureMax"])), degrees),
        'W_DAY_CLOUDS_4': "{}%".format(str(round(weather["daily"][4]["clouds"]))),
        'W_DAY_POP_4': "{}%".format(str(round(weather["daily"][4]["pop"]*100))),
        'WEATHER_DAY_DESC_4': weather["daily"][4]["description"],

        'WEATHER_DAY_DATETIME_5': datetime.datetime.fromtimestamp(weather["daily"][5]["dt"]).strftime("%a %d"),
        'W_DAY_TEMP_MIN_5': "{}{}".format(str(round(weather["daily"][5]["temperatureMin"])), degrees),
        'W_DAY_TEMP_MAX_5': "{}{}".format(str(round(weather["daily"][5]["temperatureMax"])), degrees),
        'W_DAY_CLOUDS_5': "{}%".format(str(round(weather["daily"][5]["clouds"]))),
        'W_DAY_POP_5': "{}%".format(str(round(weather["daily"][5]["pop"]*100))),
        'WEATHER_DAY_DESC_5': weather["daily"][5]["description"],

        'WEATHER_DAY_DATETIME_6': datetime.datetime.fromtimestamp(weather["daily"][6]["dt"]).strftime("%a %d"),
        'W_DAY_TEMP_MIN_6': "{}{}".format(str(round(weather["daily"][6]["temperatureMin"])), degrees),
        'W_DAY_TEMP_MAX_6': "{}{}".format(str(round(weather["daily"][6]["temperatureMax"])), degrees),
        'W_DAY_CLOUDS_6': "{}%".format(str(round(weather["daily"][6]["clouds"]))),
        'W_DAY_POP_6': "{}%".format(str(round(weather["daily"][6]["pop"]*100))),
        'WEATHER_DAY_DESC_6': weather["daily"][6]["description"],

        'WEATHER_DAY_DATETIME_7': datetime.datetime.fromtimestamp(weather["daily"][7]["dt"]).strftime("%a %d"),
        'W_DAY_TEMP_MIN_7': "{}{}".format(str(round(weather["daily"][7]["temperatureMin"])), degrees),
        'W_DAY_TEMP_MAX_7': "{}{}".format(str(round(weather["daily"][7]["temperatureMax"])), degrees),
        'W_DAY_CLOUDS_7': "{}%".format(str(round(weather["daily"][7]["clouds"]))),
        'W_DAY_POP_7': "{}%".format(str(round(weather["daily"][7]["pop"]*100))),
        'WEATHER_DAY_DESC_7': weather["daily"][7]["description"]
    }

    logging.info(output_dict)

    logging.info("Updating SVG")

    template_svg_filename = f'screen-template.{template_name}.svg'
    output_svg_filename = 'screen-output-weather.svg'
    update_svg(template_svg_filename, output_svg_filename, output_dict)


if __name__ == "__main__":
    main()
