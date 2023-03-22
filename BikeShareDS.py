import pandas as pd


class BikeShareDS:

    hour_ds = None
    day_ds = None
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
        self.hour_ds = pd.read_csv('data/hour.csv')
        # day_ds = pd.read_csv('data/day.csv')

        self.transform_fields(self.hour_ds)
        self.update_data_format(self.hour_ds)


    def transform_fields(self, ds):
        ds['dteday'] = pd.to_datetime(ds['dteday'])
        ds['season'] = ds['season'].map({1: 'winter', 2: 'sprint', 3: 'summer', 4: 'fall'})
        ds['yr'] = ds['yr'].map({0: 2011, 1: 2012})
        ds['mnth'] = ds['mnth'].map({1: 'jan', 2: 'feb', 3: 'mar', 4: 'apr', 5: 'may', 6: 'jun',
                                      7: 'jul', 8: 'aug', 9: 'sep', 10: 'oct', 11: 'nov', 12: 'dec'})
        ds['weathersit'] = ds['weathersit'].map({1: 'clear', 2: 'mist', 3: 'light_rain', 4: 'heavy_rain'})
        ds['weekday'] = ds['weekday'].map({0: 'sun', 1: 'mon', 2: 'tue', 3: 'wed', 4: 'thu', 5: 'fri', 6: 'sat'})

        # reverse normalized fields
        # min and max values from https://archive.ics.uci.edu/ml/datasets/bike+sharing+dataset
        self.denormalize_data(ds, 'temp', -8, 39)
        self.denormalize_data(ds, 'atemp', -16, 50)
        ds['hum'] = ds['hum'] * 100
        ds['windspeed'] = ds['windspeed'] * 67


    def denormalize_data(self, ds, ds_field, t_min, t_max):
        """ Denormalize data from 0-1 to t_min-t_max """
        ds[ds_field] = ds[ds_field] * (t_max - t_min) + t_min

    def update_data_format(self, ds):
        ds.astype({
            'instant':        'int64',
            'dteday':         'datetime64[ns]',
            'season':         'category',
            'yr' :            'category',
            'mnth':           'category',
            'hr':             'int64',
            'holiday':        'bool',
            'weekday':        'category',
            'workingday':     'bool',
            'weathersit':     'category',
            'temp':           'float64',
            'atemp':          'float64',
            'hum':            'float64',
            'windspeed':      'float64',
            'casual':         'int64',
            'registered':     'int64',
            'cnt':            'int64'
        }, inplace=True)

    def make_autopct(self, values):
        def my_autopct(pct):
            total = sum(values)
            val = int(round(pct * total / 100.0))
            return '{p:.2f}%  ({v:d})'.format(p=pct, v=val)

        return my_autopct

