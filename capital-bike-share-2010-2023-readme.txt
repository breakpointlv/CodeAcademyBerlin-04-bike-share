Combined dataset from Capital Bike Share trip history data and weather data from 2010 to 2023.
Bike trip datasets used: https://www.capitalbikeshare.com/system-data
Weather dataset used: https://open-meteo.com/en/docs/historical-weather-api#latitude=52.54&longitude=13.44&start_date=2011-02-16&end_date=2023-03-18&hourly=temperature_2m

TRIP DATA

start_time - %Y-%m-%d %H:%M:%S, time when the trip started
end_time - %Y-%m-%d %H:%M:%S, time when the trip started and ended
duration - seconds, duration of the trip
start_station - str, name of the start station
start_station_nr - int, station number
end_station - str, name of the end station
bike_number - str, bike number used for the trip (not available for all trips)
member_type - casual, member
end_station_nr - int, station number
rideable_type - electric bike, classic bike, docked bike
start_lat - float, latitude start station
start_lng - float, longitude start station
end_lat - float, latitude end station
end_lng - float, longitude end station
distance - km, distance between start and end station

ADDITIONAL FIELDS

date - %Y-%m-%d, date when the trip started
hour - 0-23, hour when the trip started
weekday - monday, tuesday, wednesday, thursday, friday, saturday, sunday
month - 1-12, month when the trip started
season - winter, spring, summer, autumn
year - 2010-2023, year when the trip started
is_weekend - yes/no

WEATHER DATA

temp - °C, temperature
atemp - °C, apparent temperature
humidity - %, relative humidity
pressure - hPa, air pressure
precipitation - mm, precipitation
rain - mm, rain
snowfall - mm, snowfall
wmo_code - https://www.nodc.noaa.gov/archive/arc0021/0002199/1.1/data/0-data/HTML/WMO-CODE/WMO4677.HTM
wind_speed - m/s, wind speed
cloud_cover - %, cloud cover
wo_description - description of wmo_code above
is_warm - yes/no, is temperature above 15°C