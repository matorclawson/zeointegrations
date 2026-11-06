"""Bounded openweather operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import WeatherClient


class Client(BaseClient):
    provider = "openweather"
    implementation = WeatherClient
    origins = ("https://api.openweathermap.org",)
    operations = ("get_weather_by_city", "get_forecast_by_city")
