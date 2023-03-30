import csv
import os
from datetime import datetime
from os import listdir
from os.path import isfile, join
import time

from ipywidgets import IntProgress
from geopy.distance import geodesic as GD
import pandas as pd

from IPython.display import HTML, display
def progress(value, max=100):
    return HTML("""
        <progress
            value='{value}'
            max='{max}',
            style='width: 100%'
        >
            {value}
        </progress>
    """.format(value=value, max=max))


class GiantBikeDS:

    dir = None
    fields = [
        # ride data
        'start_time',
        'end_time',
        'duration',
        'start_station',
        'start_station_nr',
        'end_station_nr',
        'end_station',
        'bike_number',
        'is_member',
        'rideable_type',
        'start_lat',
        'start_lng',
        'end_lat',
        'end_lng',
        # 'distance',

        # additional fields
        'date',
        'hour',
        'weekday',
        'month',
        'season',
        'year',
        'is_weekend',

        # weather data
        'temp',
        'atemp',
        'humidity',
        'pressure',
        'precipitation',
        'rain',
        'snowfall',
        'wmo_code',  # https://www.nodc.noaa.gov/archive/arc0021/0002199/1.1/data/0-data/HTML/WMO-CODE/WMO4677.HTM
        'wind_speed',
        'cloud_cover',
        'wo_description',
        'is_warm'
    ]
    fis = {}
    output_file_path = None
    output_csv = None
    output_csv_writer = None
    weather_ds = None
    do_profile = False

    ex_times = {
        'process_line': 0,
        'print_line': 0,
        'process_ride': 0,
        'process_additional': 0,
        'process_weather': 0,
    }
    prof_start = {}

    bike_number_ds = None
    bike_number_dict = {}

    def __init__(self, ds_dir, weather_ds_path, output_file_path, do_profile=False):
        self.ds_dir = ds_dir
        self.weather_ds_path = weather_ds_path
        self.output_file_path = output_file_path
        self.do_profile = do_profile

        # get all files in the directory
        self.files = [f for f in listdir(self.ds_dir) if isfile(join(self.ds_dir, f)) and f.endswith('.csv')]
        self.files.sort()

        for field in self.fields:
          self.fis[field] = self.fields.index(field)

        self.load_weather_data()


    def init_output_csv(self):
        # remove output file if it exists
        if os.path.isfile(self.output_file_path):
            os.remove(self.output_file_path)

        self.output_csv = open(self.output_file_path, "w", newline='')
        self.output_csv_writer = csv.writer(self.output_csv, delimiter=',')

        self.print_header()

    def add_bike_share_ds(self, f, limit=None, show_progress=True, only_every=None):
        from ipywidgets import IntProgress

        file_path = join(self.ds_dir, f)
        file_fields = []

        # calculate number of entries, so we can display a progress bar
        if limit is None:
            with open(file_path, "r") as f:
                reader = csv.reader(f, delimiter=",")
                entry_count = sum(1 for row in reader)
                f.close()
        else:
            entry_count = limit

        # display progress bar
        if show_progress:
            out = display(progress(0, entry_count), display_id=True)

        with open(file_path, "r") as f:
            reader = csv.reader(f, delimiter=",")

            for i, line in enumerate(reader):
                if i == 0:
                    file_field_indexes, file_fields = self.standardize_file_fields(line)
                    continue

                if only_every is not None and i % only_every != 0:
                    continue

                ds_line = self.process_line(file_fields, file_field_indexes, line)
                # self.print_line(ds_line)

                if show_progress:
                    out.update(progress(i, entry_count))

                if limit is not None and i > limit:
                    break
            f.close()

    def standardize_file_fields(self, file_fields):
        """ standardize file fields to match the fields of the final dataset """
        file_fields = [f.lower() for f in file_fields]
        file_fields = [f.replace(' ', '_') for f in file_fields]

        try:
            file_fields[file_fields.index('start_date')] = 'started_at'
        except ValueError:
            pass

        try:
            file_fields[file_fields.index('end_date')] = 'ended_at'
        except ValueError:
            pass

        try:
            file_fields[file_fields.index('start_station')] = 'start_station_name'
        except ValueError:
            pass

        try:
            file_fields[file_fields.index('start_station_number')] = 'start_station_id'
        except ValueError:
            pass

        try:
            file_fields[file_fields.index('end_station')] = 'end_station_name'
        except ValueError:
            pass

        try:
            file_fields[file_fields.index('end_station_number')] = 'end_station_id'
        except ValueError:
            pass

        try:
            file_fields[file_fields.index('member_type')] = 'member_casual'
        except ValueError:
            pass

        file_field_indexes = {}
        for field in file_fields:
            file_field_indexes[field] = file_fields.index(field)

        return file_field_indexes, file_fields

    def print_header(self):
        self.print_line(self.fields)

    def field_index(self, field):
        return self.fis[field]

    def process_line(self, file_fields, file_field_indexes, line):
        """ process initial data set line and return a new line with correct format and additional fields """
        # initialize new line
        ds_line = [''] * len(self.fields)

        # start time
        ds_line[self.field_index('start_time')] = line[file_field_indexes['started_at']]

        # end time
        ds_line[self.field_index('end_time')] = line[file_field_indexes['ended_at']]

        # duration
        try:
            duration = int(line[file_field_indexes['duration']])
            if int(duration) > 0:
                ds_line[self.field_index('duration')] = str(duration)
            else:
                print('NEGATIVE DURATION!', line)
        except KeyError:
            # convert start and end time to datetime objects
            start_time = datetime.strptime(line[file_field_indexes['started_at']], '%Y-%m-%d %H:%M:%S')
            end_time = datetime.strptime(line[file_field_indexes['ended_at']], '%Y-%m-%d %H:%M:%S')
            ds_line[self.field_index('duration')] = str((end_time - start_time).total_seconds())

        # # start station
        # # ds_line[self.field_index('start_station')] = line[file_field_indexes['start_station_name']]
        #
        # # start station nr
        # ds_line[self.field_index('start_station_nr')] = line[file_field_indexes['start_station_id']]
        #
        # # end station
        # # ds_line[self.field_index('end_station')] = line[file_field_indexes['end_station_name']]
        #
        # # end station nr
        # ds_line[self.field_index('end_station_nr')] = line[file_field_indexes['end_station_id']]

        # member type
        ds_line[self.field_index('is_member')] = '1' if line[file_field_indexes[
            'member_casual']].lower() == 'member' else '0'

        # rideable type
        ds_line_i = self.field_index('rideable_type')
        try:
            ds_line[ds_line_i] = line[file_field_indexes['rideable_type']]
        except KeyError:
            ds_line[ds_line_i] = ''

        # bike number
        ds_line_i = self.field_index('bike_number')
        try:
            bike_number = line[file_field_indexes['bike_number']]
            ds_line[ds_line_i] = bike_number
            if bike_number in self.bike_number_dict:
                self.bike_number_dict[bike_number]['total_trip_count'] += 1
                self.bike_number_dict[bike_number]['casual_trip_count'] += 1 if ds_line[self.field_index('is_member')] == '0' else 0
                self.bike_number_dict[bike_number]['member_trip_count'] += 1 if ds_line[self.field_index('is_member')] == '1' else 0
                self.bike_number_dict[bike_number]['total_duration'] += int(float(ds_line[self.field_index('duration')]))
                self.bike_number_dict[bike_number]['last_trip_date'] = ds_line[self.field_index('start_time')]
            else:
                self.bike_number_dict[bike_number] = {
                    'number': bike_number,
                    'type': ds_line[self.field_index('rideable_type')],
                    'total_trip_count': 1,
                    'casual_trip_count': 1 if ds_line[self.field_index('is_member')] == '0' else 0,
                    'member_trip_count': 1 if ds_line[self.field_index('is_member')] == '1' else 0,
                    'total_duration': int(float(ds_line[self.field_index('duration')])),
                    'first_trip_date': ds_line[self.field_index('start_time')],
                    'last_trip_date': ds_line[self.field_index('start_time')]
                }
        except KeyError:
            ds_line[ds_line_i] = ''


        #
        #
        # # start lat
        # try:
        #     ds_line_i = self.field_index('start_lat')
        #     start_lat = float(line[file_field_indexes['start_lat']])
        #     ds_line[ds_line_i] = str(start_lat)
        # except KeyError:
        #     ds_line[ds_line_i] = ''
        # except ValueError:
        #     ds_line[ds_line_i] = ''
        #
        # # end lat
        #
        # try:
        #     ds_line_i = self.field_index('end_lat')
        #     end_lat = float(line[file_field_indexes['end_lat']])
        #     ds_line[ds_line_i] = str(end_lat)
        # except KeyError:
        #     ds_line[ds_line_i] = ''
        # except ValueError:
        #     ds_line[ds_line_i] = ''
        #
        # # start lng
        # try:
        #     ds_line_i = self.field_index('start_lng')
        #     start_lng = float(line[file_field_indexes['start_lng']])
        #     ds_line[ds_line_i] = str(start_lng)
        # except KeyError:
        #     ds_line[ds_line_i] = ''
        # except ValueError:
        #     ds_line[ds_line_i] = ''
        #
        # # end lng
        #
        # try:
        #     ds_line_i = self.field_index('end_lng')
        #     end_lng = float(line[file_field_indexes['end_lng']])
        #     ds_line[ds_line_i] = str(end_lng)
        # except KeyError:
        #     ds_line[ds_line_i] = ''
        # except ValueError:
        #     ds_line[ds_line_i] = ''

        # duration
        # if start_lat and start_lng and end_lat and end_lng:
        #     ds_line[self.field_index('distance')] = str(self.calculate_distance(start_lat, start_lng, end_lat, end_lng))

        # converts start date to datetime object
        dt = datetime.strptime(ds_line[self.field_index('start_time')], '%Y-%m-%d %H:%M:%S')
        #
        # date
        ds_line[self.field_index('date')] = dt.strftime('%Y-%m-%d')

        # hour
        ds_line[self.field_index('hour')] = str(dt.strftime('%H'))
        #
        # # weekday name
        # ds_line[self.field_index('weekday')] = dt.strftime('%A').lower()
        #
        # # month
        # ds_line[self.field_index('month')] = str(dt.month)
        #
        # # season
        # if dt.month in [12, 1, 2]:
        #     ds_line[self.field_index('season')] = 'winter'
        # elif dt.month in [3, 4, 5]:
        #     ds_line[self.field_index('season')] = 'spring'
        # elif dt.month in [6, 7, 8]:
        #     ds_line[self.field_index('season')] = 'summer'
        # elif dt.month in [9, 10, 11]:
        #     ds_line[self.field_index('season')] = 'fall'
        #
        # # year
        # ds_line[self.field_index('year')] = str(dt.year)
        #
        # # is weekend
        # if dt.weekday() in [5,6]:
        #     ds_line[self.field_index('is_weekend')] = '1'
        # else:
        #     ds_line[self.field_index('is_weekend')] = '0'
        #
        # # weather
        # self.profile_start('weather_find_series')
        timestamp = ds_line[self.field_index('date')] + ' ' + ds_line[self.field_index('hour')]
        #
        # weather = self.weather_dict[timestamp]
        # self.profile_end('weather_find_series')
        #
        # self.profile_start('weather_assign_field')
        #
        # self.profile_start('weather_common_fields')
        # weather_fields = [
        #     'temp',
        #     'atemp',
        #     'humidity',
        #     'pressure',
        #     'precipitation',
        #     'rain',
        #     'snowfall',
        #     'wmo_code',
        #     'wind_speed',
        #     'cloud_cover',
        # ]
        # for wf in weather_fields:
        #     ds_line[self.field_index(wf)] = weather[wf]
        #
        # self.profile_end('weather_common_fields')
        #
        # self.profile_start('weather_is_warm')
        # # is warm
        # if weather['temp'] > 15:
        #     ds_line[self.field_index('is_warm')] = '1'
        # else:
        #     ds_line[self.field_index('is_warm')] = '0'
        # self.profile_end('weather_is_warm')
        #
        # # wo_description
        # # https://www.nodc.noaa.gov/archive/arc0021/0002199/1.1/data/0-data/HTML/WMO-CODE/WMO4677.HTM
        # self.profile_start('weather_wmo_code')
        # ds_line[self.field_index('wmo_description')] = self.get_wo_description(weather['wmo_code'])

        try:
            self.weather_dict[timestamp]['total_trips'] += 1
            self.weather_dict[timestamp]['total_trip_duration'] += int(float(ds_line[self.field_index('duration')]))

            if ds_line[self.field_index('is_member')] == '1':
                self.weather_dict[timestamp]['member_trips'] += 1
                self.weather_dict[timestamp]['total_member_trip_duration'] += int(float(ds_line[self.field_index('duration')]))
            if ds_line[self.field_index('is_member')] == '0':
                self.weather_dict[timestamp]['casual_trips'] += 1
                self.weather_dict[timestamp]['total_casual_trip_duration'] += int(float(ds_line[self.field_index('duration')]))
        except ValueError:
            print('VALUE ERROR', ds_line[self.field_index('duration')])

        self.profile_end('weather_assign_field')
        # self.profile_end('weather_wmo_code')

        return ds_line

    def get_wo_description(self, wmo_code):
        if wmo_code <= 19:
            desc = 'dry'
        elif wmo_code <= 29:
            desc = 'cloudy'
        elif wmo_code <= 39:
            desc = 'storm'
        elif wmo_code <= 49:
            desc = 'fog'
        elif wmo_code <= 59:
            desc = 'rain'
        elif wmo_code <= 69:
            desc = 'rain'
        elif wmo_code <= 79:
            desc = 'snow'
        else:
            desc = 'rain'
        return desc

    def profile_start(self, metric):
        if self.do_profile:
            self.prof_start[metric] = time.time()

    def profile_end(self, metric):
        if self.do_profile:
            if metric not in self.ex_times:
                self.ex_times[metric] = 0
            self.ex_times[metric] += time.time() - self.prof_start[metric]

    def calculate_distance(self, start_lat, start_lng, end_lat, end_lng):
        """ calculate distance in km between two points """
        return GD((start_lat, start_lng), (end_lat, end_lng)).km

    def print_line(self, line):
        self.output_csv_writer.writerow(line)

    def close_output_csv(self):
        self.output_csv.close()

    weather_dict = {}
    def load_weather_data(self):
        """ loads weather data from csv file """
        self.weather_ds = pd.read_csv(self.weather_ds_path, sep=',')

        self.weather_ds['time'] = pd.to_datetime(self.weather_ds['time'])

        self.weather_ds['hour'] = self.weather_ds['time'].dt.hour
        self.weather_ds['date'] = self.weather_ds['time'].dt.strftime('%Y-%m-%d')
        self.weather_ds['weekday'] = self.weather_ds['time'].dt.strftime('%A')
        self.weather_ds['month'] = self.weather_ds['time'].dt.month
        self.weather_ds['year'] = self.weather_ds['time'].dt.year
        self.weather_ds['season'] = self.weather_ds['time'].dt.month%12 // 3 + 1

        self.weather_ds['tms'] = self.weather_ds['time'].dt.strftime('%Y-%m-%d %H')
        self.weather_ds = self.weather_ds.set_index('tms')

        for index, row in self.weather_ds.iterrows():
            self.weather_dict[index] = {}
            for indx, values in row.items():
                self.weather_dict[index][indx] = values
                if indx == 'wmo_code':
                    self.weather_dict[index]['wmo_description'] = self.get_wo_description(values)
            self.weather_dict[index]['total_trips'] = 0
            self.weather_dict[index]['casual_trips'] = 0
            self.weather_dict[index]['member_trips'] = 0
            self.weather_dict[index]['total_trip_duration'] = 0
            self.weather_dict[index]['total_member_trip_duration'] = 0
            self.weather_dict[index]['total_casual_trip_duration'] = 0


    def save_weather_csv(self, file_path):
        """ saves weather data to csv file """
        w_ds = pd.DataFrame.from_dict(self.weather_dict, orient='index')
        display(w_ds.head(10))
        w_ds.to_csv(file_path, index=False)

    def save_bike_number_csv(self, file_path):
        """ saves weather data to csv file """
        ds = pd.DataFrame.from_dict(self.bike_number_dict, orient='index')
        display(ds.head(10))
        ds.to_csv(file_path, index=False)




