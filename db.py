from pymongo import MongoClient
client = MongoClient()

# weather is the name of the database
db = client.weather

hourly_forecasts = db.hourly_forecasts
daily_forecasts = db.daily_forecasts
weather_maps = db.maps

def saveHourlyForecast(forecast):
    save_result = hourly_forecasts.insert_one(forecast)
    # print ('Inserted id: {0}'.format(save_result.inserted_id))

def saveDailyForecasts(forecast):
    save_result = daily_forecasts.insert_one(forecast)

def saveWeatherMaps(map_details):
    save_result = weather_maps.insert_one(map_details)