from dotenv import load_dotenv
import requests
import os

load_dotenv()
API_KEY = os.getenv('CURRENCY_API_KEY')

def get_convert_currency(from_currency='USD', to_currency='RUB', amount=5.0):
    url = f'https://v6.exchangerate-api.com/v6/{API_KEY}/pair/{from_currency}/{to_currency}/{amount}'
    response = requests.get(url)
    data = response.json()

    if data.get('result') != 'success':
        return "Произошла ошибка. Попробуйте ввести заново, или попробуйте позже. Пример: /convert usd rub 1"
    return data

def get_all_currency(base_currency='RUB'):
    url = f'https://v6.exchangerate-api.com/v6/{API_KEY}/latest/{base_currency}'
    response = requests.get(url)
    data = response.json()

    if data.get('result') != 'success':
        return "Произошла ошибка. Попробуйте ввести заново, или попробуйте позже. Пример: /every_currency rub"
    return data

def get_test_convert_currency(from_currency='USD', to_currency='RUB', amount=5.0):
    url = f'https://v6.exchangerate-api.com/v6/{API_KEY}/pair/{from_currency}/{to_currency}/{amount}'
    response = requests.get(url)
    data = response.json()
    return data