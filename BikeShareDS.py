import pandas as pd

"""
    Bike share data:
    https://s3.amazonaws.com/capitalbikeshare-data/index.html

    Weather data:
    https://open-meteo.com/en/docs/historical-weather-api#latitude=52.54&longitude=13.44&start_date=2011-02-16&end_date=2023-03-18&hourly=temperature_2m
"""

class BikeShareDS:

    ds = None
    color_reg = '#037ffc'
    color_cas = '#cc0000'
    weekday_order = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
    weather_colors = {
        'clear': '#037ffc',
        'mist': '#cc0000',
        'light_rain': '#ffcc00',
        'heavy_rain': '#000000'
    }
    weather_color_palette = [
        weather_colors['clear'],
        weather_colors['mist'],
        weather_colors['light_rain'],
        weather_colors['heavy_rain']
    ]

    def __init__(self):
        self.load_data()

    def load_data(self):
        self.ds = pd.read_csv('data/capital-bike-share-2010-2023-no-text-fields.csv')

        self.update_data_format(self.ds)


    def transform_fields(self, ds):
        pass


    def update_data_format(self, ds):
        pass

    def make_autopct(self, values):
        def my_autopct(pct):
            total = sum(values)
            val = int(round(pct * total / 100.0))
            return '{p:.2f}%  ({v:d})'.format(p=pct, v=val)

        return my_autopct

