import requests 
api_address =  'http://api.openweathermap.org/data/2.5/weather?appid=105ccbc068343b1fa41d3b69d9b97b17&lat='
import geocoder
g = geocoder.ip('me')

my_lat = g.latlng[0]
my_lon = g.latlng[0]
url = api_address +str(my_lat) + '&lon=' +str(my_lon)
json_data = requests.get(url).json()
#print(json_data)
formatted = json_data['weather'][0]['main'] 
temp = json_data['main']
print(formatted )
print(temp)
