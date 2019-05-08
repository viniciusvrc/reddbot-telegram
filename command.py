'''
Created on 07.05.2019
-*- coding: utf-8 -*-
@author: owebb
'''

import requests
from bs4 import BeautifulSoup, SoupStrainer
import subprocess
from telegram.ext.dispatcher import run_async
from telegram.ext import Updater

updater = Updater(token='872012702:AAEGfPfievApCyR8p28FFrG4AmWKoCz5FYM')
dispatcher = updater.dispatcher

import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

bot_name = "@Reddcoin_bot"
encoding = "utf-8"
core = "/usr/local/bin/reddcoind"
data_origin = "https://coinmarketcap.com/currencies/reddcoin"

def commands(bot, update):
    user = update.message.from_user.username 
    bot.send_message(chat_id=update.message.chat_id, text="Initiating commands /tip & /withdraw have a specific format,\n use them like so:" + "\n \n Parameters: \n <user> = target user to tip \n <amount> = amount of reddcoin to utilise \n <address> = reddcoin address to withdraw to \n \n Tipping format: \n /tip <user> <amount> \n \n Withdrawing format: \n /withdraw <address> <amount>")

def help(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="The following commands are at your disposal: /hi , /commands , /deposit , /tip , /withdraw , /price , /marketcap or /balance")

def deposit(bot, update):
    user = update.message.from_user.username
    if user is None:
        bot.send_message(chat_id=update.message.chat_id, text="Please set a telegram username in your profile settings!")
    else:
        result = subprocess.run([core,"getaccountaddress",user],stdout=subprocess.PIPE)
        clean = (result.stdout.strip()).decode(encoding)
        bot.send_message(chat_id=update.message.chat_id, text="@{0} your depositing address is: {1}".format(user,clean))

def tip(bot,update):
    user = update.message.from_user.username
    target = update.message.text[5:]
    amount = target.split(" ")[1]
    target = target.split(" ")[0]
    if user is None:
        bot.send_message(chat_id=update.message.chat_id, text="Please set a telegram username in your profile settings!")
    else:
        if target == bot_name:
            bot.send_message(chat_id=update.message.chat_id, text="HODL.")
        elif "@" in target:
            target = target[1:]
            user = update.message.from_user.username
            result = subprocess.run([core,"getbalance",user],stdout=subprocess.PIPE)
            balance = float((result.stdout.strip()).decode(encoding))
            amount = float(amount)
            if balance < amount:
                bot.send_message(chat_id=update.message.chat_id, text="@{0} you have insufficient funds.".format(user))
            elif target == user:
                bot.send_message(chat_id=update.message.chat_id, text="You can't tip yourself silly.")
            else:
                balance = str(balance)
                amount = str(amount) 
                tx = subprocess.run([core,"move",user,target,amount],stdout=subprocess.PIPE)
                bot.send_message(chat_id=update.message.chat_id, text="@{0} tipped @{1} of {2} RDD".format(user, target, amount))
        else: 
            bot.send_message(chat_id=update.message.chat_id, text="Error that user is not applicable.")

def balance(bot,update):
    quote_page = requests.get(data_origin)
    strainer = SoupStrainer('div', {'class': 'details-panel-item--price bottom-margin-1x'})
    soup = BeautifulSoup(quote_page.content, 'html.parser', parse_only=strainer)
    price = soup.find("span", {"class": "h2 text-semi-bold details-panel-item--price__value"})
    price = float(price)
    user = update.message.from_user.username
    if user is None:
        bot.send_message(chat_id=update.message.chat_id, text="Please set a telegram username in your profile settings!\n With your unique username you can access your wallet. If you change your username you might loose access to your Reddcoins! This wallet is separated from any other wallets and cannot be connected to other wallets!")
    else:
        result = subprocess.run([core,"getbalance",user],stdout=subprocess.PIPE)
        clean = (result.stdout.strip()).decode(encoding)
        balance  = float(clean)
        fiat_balance = balance * price
        fiat_balance = str(round(fiat_balance,3))
        balance = str(round(balance,3))
        bot.send_message(chat_id=update.message.chat_id, text="@{0} your current balance is: {1} RDD ≈ ${2}".format(user,balance,fiat_balance))

def price(bot,update):
    quote_page = requests.get(data_origin)
#   strainer = SoupStrainer('span', {'class': 'h2 text-semi-bold details-panel-item--price__value'})
    strainer = SoupStrainer('div', {'class': 'details-panel-item--price bottom-margin-1x'})
    soup = BeautifulSoup(quote_page.content, 'html.parser', parse_only=strainer)
    price = soup.find("span", {"class": "h2 text-semi-bold details-panel-item--price__value"})
    if price != "":
        price = soup.find("span", {"class": "h2 text-semi-bold details-panel-item--price__value"}).get_text(strip=True)
    else:
        price = "?"
    price_change_positive = soup.find("span", {"class": "h2 text-semi-bold positive_change"})
    if price_change_positive != None:
        price_change_positive = soup.find("span", {"class": "h2 text-semi-bold positive_change"}).get_text(strip=True)
        change_symbol = "+"
        price_change = price_change_positive
    price_change_negative = soup.find("span", {"class": "h2 text-semi-bold negative_change"})
    if price_change_negative != None:
        price_change_negative = soup.find("span", {"class": "h2 text-semi-bold negative_change"}).get_text(strip=True)
        change_symbol = ""
        price_change = price_change_negative
    sats = soup.find("span", {"class": "text-gray"})
    if sats != None:
        sats = soup.find("span", {"class": "text-gray"}).get_text(strip=True)
        sats = sats[:10]
    price_change = price_change.replace("(",'')
    price_change = price_change.replace(")",'')
    bot.send_message(chat_id=update.message.chat_id, text="Reddcoin is valued at ${0} Δ {1}{2} ≈ {3}".format(price,change_symbol,price_change,sats) + " ฿")

def withdraw(bot,update):
    user = update.message.from_user.username
    if user is None:
        bot.send_message(chat_id=update.message.chat_id, text="Please set a telegram username in your profile settings!")
    else:
        target = update.message.text[9:]
        address = target[:35]
        address = ''.join(str(e) for e in address)
        target = target.replace(target[:35], '')
        amount = float(target)
        result = subprocess.run([core,"getbalance",user],stdout=subprocess.PIPE)
        clean = (result.stdout.strip()).decode(encoding)
        balance = float(clean)
        if balance < amount:
            bot.send_message(chat_id=update.message.chat_id, text="@{0} you have insufficient funds.".format(user))
        else:
            amount = str(amount)
            tx = subprocess.run([core,"sendfrom",user,address,amount],stdout=subprocess.PIPE)
            bot.send_message(chat_id=update.message.chat_id, text="@{0} has successfully withdrew to address: {1} of {2} RDD".format(user,address,amount))

def hi(bot,update):
    user = update.message.from_user.username
    bot.send_message(chat_id=update.message.chat_id, text="Hello @{0}, how are you doing today?".format(user))

def moon(bot,update):
    bot.send_message(chat_id=update.message.chat_id, text="Moon mission inbound!")

def marketcap(bot,update):
    quote_page = requests.get(data_origin)
    strainer = SoupStrainer('div', {'class': 'coin-summary-item-detail'})
    soup = BeautifulSoup(quote_page.content, 'html.parser', parse_only=strainer)
    marketcap_raw = soup.get_text().replace("\n",'')
    marketcap_usd = marketcap_raw[:marketcap_raw.find('USD')]
    marketcap_btc = marketcap_raw[marketcap_raw.find('USD')+3:marketcap_raw.find('BTC')]
    bot.send_message(chat_id=update.message.chat_id, text="The current market cap of Reddcoin is valued at ${0} USD (${1} ฿)".format(marketcap_usd,marketcap_btc))

from telegram.ext import CommandHandler

commands_handler = CommandHandler('commands', commands)
dispatcher.add_handler(commands_handler)

moon_handler = CommandHandler('moon', moon)
dispatcher.add_handler(moon_handler)

hi_handler = CommandHandler('hi', hi)
dispatcher.add_handler(hi_handler)

withdraw_handler = CommandHandler('withdraw', withdraw)
dispatcher.add_handler(withdraw_handler)

marketcap_handler = CommandHandler('marketcap', marketcap)
dispatcher.add_handler(marketcap_handler)

deposit_handler = CommandHandler('deposit', deposit)
dispatcher.add_handler(deposit_handler)

price_handler = CommandHandler('price', price)
dispatcher.add_handler(price_handler)

tip_handler = CommandHandler('tip', tip)
dispatcher.add_handler(tip_handler)

balance_handler = CommandHandler('balance', balance)
dispatcher.add_handler(balance_handler)

help_handler = CommandHandler('help', help)
dispatcher.add_handler(help_handler)

updater.start_polling()
