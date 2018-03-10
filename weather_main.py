import json, threading, time
import sys, shutil
from config.key import api_key
import pyowm
from pyowm.exceptions import OWMError
from pyowm.exceptions.unauthorized_error import UnauthorizedError
from db import saveHourlyForecast, saveDailyForecasts, saveWeatherMaps
from requests import get
from PIL import Image

# Wrapper object for openWeatherMap's API calls
owm = pyowm.OWM(api_key)

class hourly_forecasts_thread(threading.Thread):
    def __init__(self, thread_name):
        threading.Thread.__init__(self)
        self.thread_name = thread_name
    
    
    def run(self):
        # daemon to run continuously 
        while True:
            # read locations dynamically
            locations = read_locations()
            for location in locations:
                try:
                    three_hour_forecast = owm.three_hours_forecast(location)
                    for weather_details in three_hour_forecast.get_forecast():
                        print (self.thread_name, location, weather_details.get_reference_time('iso'), weather_details.get_status())
                        # saves in mongo
                        object_to_be_saved = json.loads(weather_details.to_JSON())
                        object_to_be_saved['location'] = location
                        saveHourlyForecast(object_to_be_saved)
                except OWMError:
                    print ("{0}: OpenWeatherMap seems to be down or the location entered is invalid: {1}".format(self.thread_name, location))
                except:
                    print ("{0}: Unexpected error: {1}".format(self.thread_name, sys.exc_info()[0]))
                    raise 
            # once the save is complete just sleep for 60 seconds before starting again 
            print ("{0}: run complete, sleeping for a minute".format(self.thread_name))
            time.sleep(60)


class daily_forecasts_thread(threading.Thread):
    def __init__(self, thread_name):
        threading.Thread.__init__(self)
        self.thread_name = thread_name
    
    def run(self):
        # daemon to run continuously 
        while True:
            # read locations dynamically
            locations = read_locations()
            for location in locations:
                try:
                    daily_forecast = owm.daily_forecast(location)
                    for weather_details in daily_forecast.get_forecast():
                        print ("{0}: ".format(self.thread_name), location, weather_details.get_reference_time('iso'), weather_details.get_status())
                        # saves in mongo
                        object_to_be_saved = json.loads(weather_details.to_JSON())
                        object_to_be_saved['location'] = location
                        saveDailyForecast(object_to_be_saved)
                except UnauthorizedError as e:
                    print ("{0}: Unauthorized error: {1}".format(self.thread_name, str(e)))
                except OWMError:
                    print ("{0}: OpenWeatherMap seems to be down or the location entered is invalid: {1}".format(self.thread_name, location))
                except:
                    print ("{0}: Unexpected error: {1}".format(self.thread_name, sys.exc_info()[0]))
                    raise 
            # once the save is complete just sleep for 60 seconds before starting again 
            print ("{0}: run complete, sleeping for a minute".format(self.thread_name))
            time.sleep(60)

class weather_maps_thread(threading.Thread):
    def __init__(self, thread_name):
        threading.Thread.__init__(self)
        self.thread_name = thread_name

    def run(self):
        print ("{0}: downloading precipitation maps".format(self.thread_name))
        base_url = 'http://tile.openweathermap.org/map/precipitation_new/0/0/0.png?appid={0}'.format(api_key)

        while True:
            try:
                # download image
                image_response = get(base_url, stream=True)
                object_to_be_saved = {}
                object_to_be_saved['imageHeaders'] = image_response.headers
                object_to_be_saved['timestamp'] = int(time.time()) # epoch time
                
                # save image to show it on the screen
                with open("img.png", 'wb') as out_file:
                    shutil.copyfileobj(image_response.raw, out_file)

                with open("img.png", "rb") as image_file:
                    object_to_be_saved['image'] = image_file.read()

                # save image to mongo
                saveWeatherMaps(object_to_be_saved)

            except:
                print ("{0}: Unexpected error: {1}".format(self.thread_name, sys.exc_info()[0]))
                raise
            
            # show the downloaded image
            image = Image.open("img.png")
            image.show()

            print ("{0}: run complete, sleeping for a minute".format(self.thread_name))
            time.sleep(60)

            # stop showing the image
            image.close()


def read_locations():
    f = open("config/locations", "r").read()
    locations = []
    for line in f.split("\n"):
        if line != "":
            locations.append(line)
    
    return locations

if __name__ == '__main__':
    # start threads for forecasts and maps
    daily_forecasts_thread1 = daily_forecasts_thread("daily forecasts thread")
    hourly_forecasts_thread1 = hourly_forecasts_thread("hourly forecasts thread")
    weather_maps_thread1 = weather_maps_thread("weather maps thread")

    daily_forecasts_thread1.start()
    hourly_forecasts_thread1.start()
    weather_maps_thread1.start()
