'''
Created on 07.05.2019
-*- coding: utf-8 -*-
@author: owebb
'''

from string import Formatter
from datetime import timedelta
import requests
from bs4 import BeautifulSoup, SoupStrainer
import pyqrcode
from PIL import Image
import png
import subprocess
import json
from telegram.ext.dispatcher import run_async
from telegram.ext import Updater

updater = Updater(token='BOT_TOKEN')
dispatcher = updater.dispatcher

import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

bot_name = "@Reddcoin_bot"
encoding = "utf-8"
core = "/home/rdd/reddcoind"
data_origin = "https://coinmarketcap.com/currencies/reddcoin"
reddbot_home = "/home/rdd/reddbot/"
qrcode_logo_img = "rdd_qrcode_logo.png"
 
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
        address = (result.stdout.strip()).decode(encoding)
        qrcode_png = createQRcode(address)
        bot.send_photo(chat_id=update.message.chat_id, photo=open(qrcode_png, 'rb'), caption="@{0} your depositing address is: {1}".format(user,address))

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
    if price != None:
        price = soup.find("span", {"class": "h2 text-semi-bold details-panel-item--price__value"}).get_text(strip=True)
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
    strainer = SoupStrainer('div', {'class': 'details-panel-item--price bottom-margin-1x'})
    soup = BeautifulSoup(quote_page.content, 'html.parser', parse_only=strainer)
    price = soup.find("span", {"class": "h2 text-semi-bold details-panel-item--price__value"})
    if price != None:
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
            bot.send_message(chat_id=update.message.chat_id, text="@{0} has successfully withdrew to address: {1} of {2} RDD (transaction: https://live.reddcoin.com/tx/{3})".format(user,address,amount,tx))

def hi(bot,update):
    user = update.message.from_user.username
    bot.send_message(chat_id=update.message.chat_id, text="Hello @{0}, how are you doing today?".format(user))

def moon(bot,update):
    bot.send_message(chat_id=update.message.chat_id, text="Moon mission inbound!")

def when(bot,update):
    user_text = update.message.text[6:]
    if user_text == 'moon':
        bot.send_message(chat_id=update.message.chat_id, text="Very soon my friend!")
    elif user_text == 'mars':
        bot.send_message(chat_id=update.message.chat_id, text="Very soon my friend!")
    elif user_text == 'jupiter':
        bot.send_message(chat_id=update.message.chat_id, text="Very soon my friend!")
    elif user_text == 'saturn':
        bot.send_message(chat_id=update.message.chat_id, text="Very soon my friend!")
    elif user_text == 'uranus':
        bot.send_message(chat_id=update.message.chat_id, text="Very soon my friend!")
    elif user_text == 'neptun':
        bot.send_message(chat_id=update.message.chat_id, text="Very soon my friend!")
    elif user_text == 'binance':
        bot.sendAnimation(chat_id=update.message.chat_id, animation=open(reddbot_home + 'when_binance.mp4', 'rb'))

def marketcap(bot,update):
    quote_page = requests.get(data_origin)
    strainer = SoupStrainer('div', {'class': 'coin-summary-item-detail'})
    soup = BeautifulSoup(quote_page.content, 'html.parser', parse_only=strainer)
    marketcap_raw = soup.get_text().replace("\n",'')
    marketcap_usd = marketcap_raw[:marketcap_raw.find('USD')]
    marketcap_btc = marketcap_raw[marketcap_raw.find('USD')+3:marketcap_raw.find('BTC')]
    bot.send_message(chat_id=update.message.chat_id, text="The current market cap of Reddcoin is valued at ${0} USD ({1} ฿)".format(marketcap_usd,marketcap_btc))

def statistics(bot,update):
    getinfo = subprocess.run([core,'getinfo'],stdout=subprocess.PIPE).stdout.strip().decode(encoding)
    getstakinginfo = subprocess.run([core,'getstakinginfo'],stdout=subprocess.PIPE).stdout.strip().decode(encoding)
    getinfo_json = json.loads(getinfo)
    getstakinginfo_json = json.loads(getstakinginfo)
    block_height = getinfo_json['blocks']
    money_supply = getinfo_json['moneysupply']
    net_stake_weight = getstakinginfo_json['netstakeweight']
    staking_quota = '{0:,.2f}'.format(float(net_stake_weight) / float(moneysupply) * 100)
    block_height = '{0:,.0f}'.format(block_height)
    money_supply = '{0:,.0f}'.format(money_supply)
    net_stake_weight = '{0:,.0f}'.format(net_stake_weight)
    next_party_block = str(int(block_height[:block_height.find(',')]) + 1)
    next_party_block = next_party_block.ljust(len(str(getinfo_json['blocks'])), '0')
    diff = int(next_party_block) - getinfo_json['blocks']
    time_to_party = strfdelta(diff, inputtype='m')
    diff = '{0:,.0f}'.format(diff)
    next_party_block = '{0:,.0f}'.format(int(next_party_block))
    block_height_msg = 'With current block height of ${0} there are ${1} left to block ${2}! Countdown: ${3} :tada:\n'.format(block_height,diff,next_party_block,time_to_party)
    netstake_weight_msg = 'There are currently ${0} (${1}%) Reddcoins beeing staked from a total of ${2}'.format(net_stake_weight,staking_quota,money_supply)
    bot.send_message(chat_id=update.message.chat_id, text=block_height_msg)

def createQRcode(value):
    # Generate the qr code and save as png
    qrcode_png = value + '.png'
    qrobj = pyqrcode.QRCode(value,error = 'H')
    qrobj.png(qrcode_png, scale=10)
     
    # Now open that png image to put the logo
    img = Image.open(qrcode_png)
    img = img.convert("RGBA")
    width, height = img.size
     
    # Open the logo image and  define how big the logo we want to put in the qr code png
    logo = Image.open(reddbot_home + qrcode_logo_img)
    logo_size = 80
     
    # Calculate logo size and position
    xmin = ymin = int((width / 2) - (logo_size / 2))
    xmax = ymax = int((width / 2) + (logo_size / 2))
    logo = logo.resize((xmax - xmin, ymax - ymin))
     
    # put the logo in the qr code and save image
    img.paste(logo, (xmin, ymin, xmax, ymax))
    img.save(reddbot_home + qrcode_png)
     
    return qrcode_png

def strfdelta(tdelta, fmt='{D:02}d {H:02}h {M:02}m {S:02}s', inputtype='timedelta'):
    """Convert a datetime.timedelta object or a regular number to a custom-
    formatted string, just like the stftime() method does for datetime.datetime
    objects.

    The fmt argument allows custom formatting to be specified.  Fields can 
    include seconds, minutes, hours, days, and weeks.  Each field is optional.

    Some examples:
        '{D:02}d {H:02}h {M:02}m {S:02}s' --> '05d 08h 04m 02s' (default)
        '{W}w {D}d {H}:{M:02}:{S:02}'     --> '4w 5d 8:04:02'
        '{D:2}d {H:2}:{M:02}:{S:02}'      --> ' 5d  8:04:02'
        '{H}h {S}s'                       --> '72h 800s'

    The inputtype argument allows tdelta to be a regular number instead of the  
    default, which is a datetime.timedelta object.  Valid inputtype strings: 
        's', 'seconds', 
        'm', 'minutes', 
        'h', 'hours', 
        'd', 'days', 
        'w', 'weeks'
    """

    # Convert tdelta to integer seconds.
    if inputtype == 'timedelta':
        remainder = int(tdelta.total_seconds())
    elif inputtype in ['s', 'seconds']:
        remainder = int(tdelta)
    elif inputtype in ['m', 'minutes']:
        remainder = int(tdelta)*60
    elif inputtype in ['h', 'hours']:
        remainder = int(tdelta)*3600
    elif inputtype in ['d', 'days']:
        remainder = int(tdelta)*86400
    elif inputtype in ['w', 'weeks']:
        remainder = int(tdelta)*604800

    f = Formatter()
    desired_fields = [field_tuple[1] for field_tuple in f.parse(fmt)]
    possible_fields = ('W', 'D', 'H', 'M', 'S')
    constants = {'W': 604800, 'D': 86400, 'H': 3600, 'M': 60, 'S': 1}
    values = {}
    for field in possible_fields:
        if field in desired_fields and field in constants:
            values[field], remainder = divmod(remainder, constants[field])
    return f.format(fmt, **values)
 
from telegram.ext import CommandHandler
 
start_handler = CommandHandler('start', commands)
dispatcher.add_handler(start_handler)

commands_handler = CommandHandler('commands', commands)
dispatcher.add_handler(commands_handler)

moon_handler = CommandHandler('moon', moon)
dispatcher.add_handler(moon_handler)

when_handler = CommandHandler('when', when)
dispatcher.add_handler(when_handler)

statistics_handler = CommandHandler('statistics', statistics)
dispatcher.add_handler(statistics_handler)

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
