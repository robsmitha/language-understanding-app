import datetime
import taxjar
import requests
import random

Language_Understanding_Service_Endpoint = 'https://westus.api.cognitive.microsoft.com/luis/v2.0/apps/'
App_Key = 'YOUR_APP_KEY'
LUIS_Api_Key = 'YOUR_API_KEY'
INTENT_NONE = 'None'
INTENT_GREETING = 'Greeting'
INTENT_CHECK_WEATHER = 'CheckWeather'
INTENT_CHECK_TAX_RATE = 'CheckTaxRate'

Google_Api_Endpoint = 'https://maps.googleapis.com/maps/api/geocode/json?address='
Google_Api_Key = 'YOUR_API_KEY'

DarkSky_Api_Endpoint = 'https://api.darksky.net/forecast/'
DarkSky_Secret_Key = 'YOUR_API_KEY'

TaxJar_Api_Key = 'YOUR_API_KEY'
client = taxjar.Client(api_key=TaxJar_Api_Key)


def location_api_call(address):
    return Google_Api_Endpoint + address + '&key=' + Google_Api_Key


def weather_api_call(lat, lng):
    return DarkSky_Api_Endpoint + DarkSky_Secret_Key + '/' + str(lat) + ',' + str(
        lng)  # + ',' + time  # "2018-11-02T00:00:00"


def language_understanding_api_call(q):
    return Language_Understanding_Service_Endpoint + App_Key + '?timezoneOffset=-360&subscription-key=' + LUIS_Api_Key + '&q=' + q


def greeting():
    n = random.randint(1, 3)
    if n == 1:
        print("Hey there!")
    elif n == 2:
        print("Howdy.")
    elif n == 3:
        print("Sup")


def get_tax_rates(country, city, zipcode):
    rates = client.rates_for_location(zipcode, {
        'city': city,
        'country': country
    })
    return rates


def process_speech(data):
    entities = data['entities']
    city = ''
    country_region = ''
    state = ''
    street = ''
    q = ''
    for e in entities:
        if e['type'] == 'builtin.geographyV2.city':
            city = e['entity']
        elif e['type'] == 'builtin.geographyV2.countryRegion':
            country_region = e['entity']
        elif e['type'] == 'builtin.geographyV2.state':
            state = e['entity']
        elif e['type'] == 'builtin.geographyV2.poi':
            street = e['entity']
        else:
            q = e['entity']

    q = q.replace(' ', '+')
    city = city.replace(' ', '+')
    country_region = country_region.replace(' ', '+')
    state = state.replace(' ', '+')
    street = street.replace(' ', '+')
    response = {
        "q": q,
        "state": state,
        "street": street,
        "country_region": country_region,
        "city": city,
    }
    return response


def get_location(data):
    d = process_speech(data)
    query = d['q'] + " " + d['street'] + " " + d['city'] + " " + d['state'] + " " + d['country_region']
    address_response = requests.get(location_api_call(query))
    return address_response.json()


def check_tax_rate(data):
    print("Checking tax rate...")
    resp_json_payload = get_location(data)
    if resp_json_payload['status'] == 'OK':
        formatted_address = resp_json_payload['results'][0]['formatted_address']
        address_components = resp_json_payload['results'][0]['address_components']
        city = ""
        country = ""
        zipcode = ""
        for component in address_components:
            types = component['types']
            for t in types:
                if t == 'locality':
                    city = component['long_name']
                    break
                if t == 'country':
                    country = component['short_name']
                    break
                if t == 'postal_code':
                    zipcode = component['long_name']
                    break
        print('Google API response: \n' + formatted_address)
        if zipcode == '':
            zipcode = input("Please enter the zip code: ")

        rates = get_tax_rates(country, city, zipcode)
        # TODO: Check for valid rates response
        print('TaxJar API response:')
        print('County: ' + rates.county + ' - Tax Rate: ' + str(rates.county_rate))
        print('State: ' + rates.state + ' - Tax Rate: ' + str(rates.state_rate))


def check_weather(data):
    print("Checking weather...")
    resp_json_payload = get_location(data)
    if resp_json_payload['status'] == 'OK':
        formatted_address = resp_json_payload['results'][0]['formatted_address']
        lat_lng = resp_json_payload['results'][0]['geometry']['location']
        print('Weather in ' + formatted_address)
        lat = lat_lng['lat']
        lng = lat_lng['lng']
        weather_response = requests.get(weather_api_call(lat, lng))
        weather_response_json_payload = weather_response.json()
        if 'code' in weather_response_json_payload:
            if weather_response_json_payload['code'] == 400:
                print("date time format error")
        else:
            weekly_summary = weather_response_json_payload['currently']['summary']
            icon = weather_response_json_payload['currently']['icon']
            temperature = weather_response_json_payload['currently']['temperature']
            daily = weather_response_json_payload['daily']
            daily_data = daily['data']
            hourly_data = weather_response_json_payload['hourly']['data']
            print(weekly_summary, '\n', temperature)

            for d in daily_data:
                print(datetime.datetime.utcfromtimestamp(int(d['time'])).strftime('%m/%d/%Y'), ' : ', d['summary'])


def none():
    print("I'm sorry, I did not understand that. Please try again.")


def run_program():
    print('Language Understanding v1.0.0.0')
    print('-------------------------------------------')
    q = input('Welcome!\nPlease type a greeting or ask about the weather / tax rate in a specific city.\n')
    while q != 'exit':
        response = requests.get(language_understanding_api_call(q))
        data = response.json()
        top_scoring_intent = data['topScoringIntent']
        top_intent = top_scoring_intent['intent']
        top_intent_score = top_scoring_intent['score']
        if top_intent == INTENT_GREETING:
            if top_intent_score > .98:
                greeting()
            else:
                none()
        elif top_intent == INTENT_CHECK_WEATHER:
            check_weather(data)
        elif top_intent == INTENT_CHECK_TAX_RATE:
            check_tax_rate(data)
        else:
            none()

        q = input('->')
        q = q.replace(' ', '+')


run_program()
