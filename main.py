from telebot import telebot
from telebot import types
from dotenv import load_dotenv
import os
import currency_api

popular_currencies = ['RUB', 'USD', 'EUR', 'GBP', 'JPY', 'CNY', 'BYN', 'AMD', 'GEL', 'KZT', 'UZS', 'TRY', 'THB', 'QAR',
                      'VND', 'MVR']
currencies = {}
load_dotenv()
bot = telebot.TeleBot(token=os.getenv('CURRENCY_BOT_TOKEN'))


def validate_currency(from_currency, to_currency, amount):
    if len(from_currency) != 3 or len(to_currency) != 3:
        return from_currency, to_currency, amount, 'Некорректное значение валюты. Попробуйте ещё раз. Пример: /convert usd rub 1'
    try:
        amount = float(amount)
    except ValueError:
        return from_currency, to_currency, amount, 'Некорректное количество. Попробуйте ещё раз. Пример: /convert usd rub 1'
    return from_currency, to_currency, amount, None


def validate_currency_structure(from_currency):
    if currency_api.get_test_convert_currency(from_currency).get('result') == 'error':
        return from_currency, 'Неверный ввод валюты. Такой валюты не существует.'
    return from_currency, None


@bot.message_handler(commands=['start', 'help'])
def welcome(message):
    welcome_message = (
        f'Привет, {message.from_user.first_name}!\n'
        'Я - бот, который может помочь с курсом разных валют!\n\n'
    ) if message.text == '/start' else ''

    welcome_message += (
        'Список моих команды:\n'
        '/help - список команд.\n'
        '/convert <валюта> <валюта> <количество> - курс определенной валюты.\n'
        '/convert_to_every_currency <валюта> - перевод из <валюты> во все доступные валюты.\n'
        '/convert_to_popular_currency <валюта> - перевод из <валюты> во все популярные валюты.'
    )

    bot.send_message(message.chat.id, welcome_message)


@bot.message_handler(func=lambda message: message.text.split()[0] == '/convert')
def convert_currency_pair(message):
    global popular_currencies
    split_message = message.text.split()
    try:
        from_currency = split_message[1].upper()
        try:
            to_currency = split_message[2].upper()
            amount = split_message[3]
        except IndexError:
            bot_message = f'Некорректный ввод. {IndexError}. Попробуйте ещё раз. Пример: /convert usd rub 1'
            return bot.send_message(message.chat.id, bot_message)

        from_currency, to_currency, amount, error = validate_currency(from_currency, to_currency, amount)
        if error:
            return bot.send_message(message.chat.id, error)

        data = currency_api.get_convert_currency(from_currency, to_currency, amount)
        bot_message = f'{amount} {data.get("base_code")} -> {data.get("target_code")} = {data.get("conversion_result")} {data.get("target_code")}'
        bot.send_message(message.chat.id, bot_message)
    except IndexError:
        markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
        for currency in popular_currencies:
            button = types.KeyboardButton(currency)
            markup.add(button)
        bot_message = 'Выбери 1 валюту. (из какой переводить)'
        bot.send_message(message.chat.id, bot_message, reply_markup=markup)
        bot.register_next_step_handler(message, get_to_currency_receive_from_currency)


def get_to_currency_receive_from_currency(message):
    global popular_currencies
    from_currency = message.text
    markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
    for currency in popular_currencies:
        if currency != from_currency:
            button = types.KeyboardButton(currency)
            markup.add(button)
    bot_message = 'Выбери 2 валюту. (в какую переводить)'
    bot.send_message(message.chat.id, bot_message, reply_markup=markup)
    bot.register_next_step_handler(message, get_amount_receive_to_currency, from_currency)


def get_amount_receive_to_currency(message, from_currency):
    to_currency = message.text
    markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
    buttons = [types.KeyboardButton('1'),
               types.KeyboardButton('5'),
               types.KeyboardButton('10'),
               types.KeyboardButton('25'),
               types.KeyboardButton('100'),
               types.KeyboardButton('250'),
               types.KeyboardButton('500'),
               types.KeyboardButton('1000'),
               types.KeyboardButton('2500'),
               types.KeyboardButton('5000')]
    for button in buttons:
        markup.add(button)
    bot_message = 'Выбери количество. (сколько переводить)'
    bot.send_message(message.chat.id, bot_message, reply_markup=markup)
    bot.register_next_step_handler(message, get_final_rate, from_currency, to_currency)


def get_final_rate(message, from_currency, to_currency):
    amount = message.text
    data = currency_api.get_convert_currency(from_currency, to_currency, amount)
    bot_message = f'{amount} {data.get("base_code")} -> {data.get("target_code")} = {data.get("conversion_result")} {data.get("target_code")}'
    bot.send_message(message.chat.id, bot_message)


@bot.message_handler(func=lambda message: message.text.startswith('/convert_to_every_currency'))
def get_every_currency(message):
    global currencies
    user_command = message.text.lower()
    try:
        base_currency = message.text.split()[1].upper()
        base_currency, error = validate_currency_structure(base_currency)
        if error is not None:
            return bot.send_message(message.chat.id, error)
    except IndexError:
        markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
        for currency in popular_currencies:
            button = types.KeyboardButton(currency)
            markup.add(button)
        bot_message = 'Выбери валюту.'
        bot.send_message(message.chat.id, bot_message, reply_markup=markup)
        return bot.register_next_step_handler(message, get_receive_from_currency_for_every_currency, user_command)

    to_currencies = currencies.get(user_command)

    if to_currencies is None:
        to_currencies = currency_api.get_all_currency(base_currency)
        currencies[user_command] = to_currencies

    bot_message = f'Курс всех валют в {base_currency}'
    for currency in to_currencies.get('conversion_rates'):
        bot_message += f'\n{base_currency} -> {currency} = {to_currencies.get("conversion_rates").get(currency)}'
    bot.send_message(message.chat.id, bot_message)


@bot.message_handler(func=lambda message: message.text.startswith('/convert_to_popular_currency'))
def get_popular_currency(message):
    global popular_currencies
    split_message = message.text.split()
    try:
        base_currency = split_message[1].upper()
        base_currency, error = validate_currency_structure(base_currency)
        if error is not None:
            return bot.send_message(message.chat.id, error)
    except IndexError:
        markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
        for currency in popular_currencies:
            button = types.KeyboardButton(currency)
            markup.add(button)
        bot_message = 'Выбери валюту.'
        bot.send_message(message.chat.id, bot_message, reply_markup=markup)
        return bot.register_next_step_handler(message, get_receive_base_currency_for_popular_currency)

    bot_message = f'Курс всех популярных валют в {base_currency}'
    for currency in popular_currencies:
        currencies = currency_api.get_all_currency(currency)
        value = currencies.get('conversion_rates').get(base_currency)
        bot_message += f'\n {currency} -> {base_currency} = {value}'
    bot_message += f'\n\nКурс {base_currency} во все популярные валюты.'

    for currency in popular_currencies:
        currencies = currency_api.get_all_currency(base_currency)
        value = currencies.get('conversion_rates').get(currency)
        bot_message += f'\n {base_currency} -> {currency} = {value}'
    bot.send_message(message.chat.id, bot_message)


def get_receive_from_currency_for_every_currency(message, user_command):
    global popular_currencies
    base_currency = message.text
    to_currencies = currencies.get(user_command)
    base_currency, error = validate_currency_structure(base_currency)
    if error is not None:
        return bot.send_message(message.chat.id, error)

    if to_currencies is None:
        to_currencies = currency_api.get_all_currency(base_currency)
        currencies[user_command] = to_currencies

    bot_message = f'Курс всех валют в {base_currency}'
    for currency in to_currencies.get('conversion_rates'):
        bot_message += f'\n{base_currency} -> {currency} = {to_currencies.get("conversion_rates").get(currency)}'
    bot.send_message(message.chat.id, bot_message)


def get_receive_base_currency_for_popular_currency(message):
    global popular_currencies
    base_currency = message.text
    base_currency, error = validate_currency_structure(base_currency)
    if error is not None:
        return bot.send_message(message.chat.id, error)
    bot_message = f'Курс всех популярных валют в {base_currency}'
    for currency in popular_currencies:
        currencies = currency_api.get_all_currency(currency)
        value = currencies.get('conversion_rates').get(base_currency)
        bot_message += f'\n {currency} -> {base_currency} = {value}'
    bot_message += f'\n\nКурс {base_currency} во все популярные валюты.'
    for currency in popular_currencies:
        currencies = currency_api.get_all_currency(base_currency)
        value = currencies.get('conversion_rates').get(currency)
        bot_message += f'\n {base_currency} -> {currency} = {value}'
    bot.send_message(message.chat.id, bot_message)


bot.infinity_polling()
