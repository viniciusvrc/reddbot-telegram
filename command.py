#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on 07.05.2019
@author: owebb
'''

import os
import logging
from string import Formatter
import requests
from bs4 import BeautifulSoup, SoupStrainer
import pyqrcode
from PIL import Image
import png
import subprocess
import json
from emoji import emojize
from telegram import ParseMode
from telegram.ext import (Updater, CommandHandler)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
bot_name = "@Reddcoin_bot"
encoding = "utf-8"
core = "/home/rdd/reddcoind"
data_origin = "https://coinmarketcap.com/currencies/reddcoin"
reddbot_home = "/home/rdd/reddbot/"
dev_fund_address = "Ru6sDVdn4MhxXJauQ2GAJP4ozpPpmcDKdc"
dev_fund_balance_api_url = "https://live.reddcoin.com/api/addr/" + dev_fund_address + "/balance"
dev_fund_tx = "http://live.reddcoin.com/api/txs/?address=" + dev_fund_address
walletpassphrase = ""
animation_home = reddbot_home + "animation/"
image_home = reddbot_home + "image/"
reddcoin_rocket_ani = animation_home + "reddcoin_rocket.mp4"
qrcode_logo_img = image_home + "rdd_qrcode_logo.png"
hall_of_fame_max_entries = 10
admin_list = ["TechAdept", "CryptoGnasher", "Chris_NL_1152", "cryptoBUZE"]

def commands(update, context):
    user = update.message.from_user.username
    if user is None:
        user = "!"
    else:
        user = " @" + user
    wave_emoji = get_emoji(":wave:")
    commands_msg = "Hello{0} {1} Initiating commands /tip & /withdraw have a specific format. Use them like so: \n \n Parameters: \n <code>username</code> = target user to tip (starting with @) \n <code>amount</code> = amount of Ɍeddcoin to utilize \n <code>address</code> = Ɍeddcoin address to withdraw to \n \n Tipping format: \n <code>/tip @username amount</code> \n \n Withdrawing format: \n <code>/withdraw address amount</code> \n \n Need more help? -> /help".format(user, wave_emoji)
    send_text_msg(update, context, commands_msg)

def help(update, context):
    help_msg = "The following commands are at your disposal: /hi /commands /deposit /tip /donate /withdraw /balance /price /marketcap /statistics /moon /about \n \nExamples: \n<code>/tip @TechAdept 100</code>\n<code>/tip @CryptoGnasher 100</code>\n-> send a tip of 100 Ɍeddcoins to our project lead Jay 'TechAdept' Laurence or to our lead dev John Nash\n<code>/donate 100</code>\n-> support Ɍeddcoin team by donating them 100 Ɍeddcoins\n<code>/withdraw {0} 100</code>\n-> send 100 Ɍeddcoins to a specific address (in this example: dev fund raising address which is also used for /donate)".format(dev_fund_address)
    send_text_msg(update, context, help_msg)

def about(update, context):
    about_msg = "{0} was originally coded by @xGozzy (Ex-Developer) and was further developed by @cryptoBUZE. The source code can be viewed at https://github.com/cryptoBUZE/reddbot-telegram. If you have any enquiries please contact @TechAdept or @cryptoBUZE".format(bot_name)
    send_text_msg(update, context, about_msg)

def deposit(update, context):
    user = update.message.from_user.username
    if user is None:
        no_user_msg = "Hey, please set a telegram username in your profile settings first.\nWith your unique username you can access your wallet. If you change your username you might loose access to your Ɍeddcoins! This wallet is separated from any other wallets and cannot be connected to other ones!"
        send_text_msg(update, context, no_user_msg)
    else:
        result = subprocess.run([core,"getaccountaddress",user],stdout=subprocess.PIPE)
        address = (result.stdout.strip()).decode(encoding)
        qrcode_png = create_qr_code(address)
        deposit_msq = "@{0} your depositing address is: {1}".format(user,address)
        send_photo_msg(update, context, qrcode_png, deposit_msq)

def tip(update, context):
    user = update.message.from_user.username
    user_input = update.message.text[5:].strip()
    if user_input == "":
        no_parameters = "There is something missing! See /help for an example."
        send_text_msg(update, context, no_parameters)
    elif user is None:
        no_user_msg = "Hey, please set a telegram username in your profile settings first.\nWith your unique username you can access your wallet. If you change your username you might loose access to your Ɍeddcoins! This wallet is separated from any other wallets and cannot be connected to other ones!"
        send_text_msg(update, context, no_user_msg)
    else:
        target = user_input.split(" ")[0]
        amount = user_input.split(" ")[1]
        if target == bot_name:
            hodl_msg = "HODL."
            send_text_msg(update, context, hodl_msg)
        elif "@" in target:
            target = target[1:]
            user = update.message.from_user.username
            result = subprocess.run([core,"getbalance",user],stdout=subprocess.PIPE)
            balance = float((result.stdout.strip()).decode(encoding))
            amount = float(amount)
            if balance < amount:
                insufficient_funds_msg = "@{0} you have insufficient funds.".format(user)
                send_text_msg(update, context, insufficient_funds_msg)
            elif target == user:
                self_tip_msg = "You can't tip yourself silly."
                send_text_msg(update, context, self_tip_msg)
            else:
                balance = str(balance)
                amount = str(amount)
                subprocess.run([core,"move",user,target,amount],stdout=subprocess.PIPE)
                tip_msg = "@{0} tipped @{1} of {2} ɌDD".format(user, target, amount)
                send_text_msg(update, context, tip_msg)
        else:
            wrong_format_msg = "Error that user is not applicable. Need help? -> /help"
            send_text_msg(update, context, wrong_format_msg)

def balance(update, context):
    quote_page = requests.get(data_origin)
    strainer = SoupStrainer("div", {"class": "details-panel-item--price bottom-margin-1x"})
    soup = BeautifulSoup(quote_page.content, "html.parser", parse_only=strainer)
    price = soup.find("span", {"class": "h2 text-semi-bold details-panel-item--price__value"})
    if price != None:
        price = soup.find("span", {"class": "h2 text-semi-bold details-panel-item--price__value"}).get_text(strip=True)
    price = float(price)
    user = update.message.from_user.username
    if user is None:
        no_user_msg = "Hey, please set a telegram username in your profile settings first.\nWith your unique username you can access your wallet. If you change your username you might loose access to your Ɍeddcoins! This wallet is separated from any other wallets and cannot be connected to other ones!"
        send_text_msg(update, context, no_user_msg)
    else:
        result = subprocess.run([core,"getbalance",user],stdout=subprocess.PIPE)
        clean = (result.stdout.strip()).decode(encoding)
        balance  = float(clean)
        fiat_balance = balance * price
        fiat_balance = "{0:,.3f}".format(fiat_balance)
        balance = "{0:,.8f}".format(balance).rstrip("0").rstrip(".")
        balance_msg = "@{0} your current balance is: Ɍ<code>{1}</code> ≈ $<code>{2}</code>".format(user,balance,fiat_balance)
        send_text_msg(update, context, balance_msg)

def price(update, context):
    quote_page = requests.get(data_origin)
    strainer = SoupStrainer("div", {"class": "details-panel-item--price bottom-margin-1x"})
    soup = BeautifulSoup(quote_page.content, "html.parser", parse_only=strainer)
    price = soup.find("span", {"class": "h2 text-semi-bold details-panel-item--price__value"})
    change_symbol = ""
    price_change = ""
    if price != None:
        price = soup.find("span", {"class": "h2 text-semi-bold details-panel-item--price__value"}).get_text(strip=True)
    else:
        price = "?"
    price_change_positive = soup.find("span", {"class": "h2 text-semi-bold positive_change"})
    percent_change_span_class_name = "h2 text-semi-bold positive_change"
    if price_change_positive == None:
        price_change_positive = soup.find("span", {"class": "h2 text-semi-bold positive_change "})
        percent_change_span_class_name = "h2 text-semi-bold positive_change "
    if price_change_positive != None:
        price_change_positive = soup.find("span", {"class": percent_change_span_class_name}).get_text(strip=True)
        change_symbol = "+"
        price_change = price_change_positive
    price_change_negative = soup.find("span", {"class": "h2 text-semi-bold negative_change"})
    percent_change_span_class_name = "h2 text-semi-bold negative_change"
    if price_change_negative == None:
        price_change_negative = soup.find("span", {"class": "h2 text-semi-bold negative_change "})
        percent_change_span_class_name = "h2 text-semi-bold negative_change "
    if price_change_negative != None:
        price_change_negative = soup.find("span", {"class": percent_change_span_class_name}).get_text(strip=True)
        change_symbol = ""
        price_change = price_change_negative
    sats = soup.find("span", {"class": "text-gray"})
    if sats != None:
        sats = soup.find("span", {"class": "text-gray"}).get_text(strip=True)
        sats = sats[:10]
    if change_symbol != "":
        price_change = price_change.replace("(","")
        price_change = price_change.replace(")","")
        price_msg = "1 Ɍeddcoin is valued at $<code>{0}</code> Δ {1}<code>{2}</code> ≈ ₿<code>{3}</code>".format(price,change_symbol,price_change,sats)
    else:
        price_msg = "1 Ɍeddcoin is valued at $<code>{0}</code> ≈ ₿<code>{1}</code>".format(price,sats)
    send_text_msg(update, context, price_msg)

def newDonation(update, context, allowed=False):
    user_id = update.message.from_user.username
    if allowed:
        user_input_user_id = "@" + user_id
        user_input_user_first_name = update.message.from_user.first_name
        user_input_user_amount = update.message.text[8:].strip().split(" ")[0]
        addDonation(update, context, user_input_user_id, user_input_user_first_name, user_input_user_amount)
    elif user_id in admin_list:
        user_input = update.message.text.partition(' ')[2]
        user_input_user_id = ''.join(user_input.partition(" ")).split(" ")[0]
        user_input_user_first_name_and_amount = ''.join(user_input.partition(" ")).split(user_input_user_id)[1]
        user_input_user_first_name = user_input_user_first_name_and_amount[:user_input_user_first_name_and_amount.rfind(' ')].strip()
        user_input_user_amount = user_input_user_first_name_and_amount[user_input_user_first_name_and_amount.rfind(' '):].strip()
        addDonation(update, context, user_input_user_id, user_input_user_first_name, user_input_user_amount)
    else:
        send_user_not_allowed_text_msg(update, context)

def addDonation(update, context, user_input_user_id, user_input_user_first_name, user_input_user_amount):
    # Get JSON data to store donation
    json_obj = readJSON()
    user_key = user_input_user_id + " " + user_input_user_first_name
    tada_emoji = get_emoji(":tada:")
    if user_key in json_obj:
        donation_amount = json_obj[user_key]
        new_donation = float(user_input_user_amount)
        new_balance = donation_amount + new_donation
        json_obj[user_key] = new_balance
        donation_msg = "Donation from user {0} increased from {1} to {2} ɌDD {3}".format(user_input_user_id, donation_amount, new_balance, tada_emoji)
    else:
        json_obj[user_key] = float(user_input_user_amount)
        donation_msg = "Added new donation of {0} ɌDD from user {1} to hall of fame list {2}".format(user_input_user_amount, user_input_user_id, tada_emoji)
    writeJSON(json_obj)
    send_text_msg(update, context, donation_msg)

def removeDonor(update, context):
    # Remove donor from hall of fame list
    user_id = update.message.from_user.username
    if user_id in admin_list:
        json_obj = readJSON()
        user_input = update.message.text.partition(' ')[2]
        user_input_user_id = ''.join(user_input.partition(" ")).split(" ")[0]
        user_input_user_first_name = ''.join(user_input.partition(" ")).split(user_input_user_id)[1]
        user_key = user_input_user_id + " " + user_input_user_first_name.strip()
        
        if user_key in json_obj:
            del json_obj[user_key]
            remove_msg = "Donor '{0}' was removed from hall of fame list.".format(user_key)
        else:
            neutral_face_emoji = get_emoji(":neutral_face:")
            remove_msg = "Sorry but donor '{0}' was not found on hall of fame list {1}".format(user_key, neutral_face_emoji)
        writeJSON(json_obj)
        send_text_msg(update, context, remove_msg)
    else:
        send_user_not_allowed_text_msg(update, context)

def hallOfFame(update, context):
    # Get list of donors
    json_obj = readJSON()
    counter = 0
    rank = {1 : "🥇", 2 : "🥈", 3 : "🥉", 4 : "🎖", 5 : "🎖", 6 : "🎖", 7 : "🎖", 8 : "🎖", 9 : "🎖", 10 : "🎖"}
    tada_emoji = get_emoji(":tada:")
    hall_of_fame_msg = "<b>Top {0} Ɍeddcoin donors</b> {1}\n".format(hall_of_fame_max_entries, tada_emoji)
    for key, value in sorted(json_obj.items(), key=lambda item: item[1], reverse=True):
        counter += 1
        if counter > hall_of_fame_max_entries:
            break
        else:
            username = key.split(" ")[0]
            display_name = key.replace(username, "")
            html_username_link = '<a href="#/im?p=%40' + username[1:] + '">' + username + '</a>' + display_name
            value = "{0:,.8f}".format(value).rstrip("0").rstrip(".")
            hall_of_fame_msg += rank[counter] + " " + html_username_link + "\n-> Ɍ<code>" + value + "</code>\n"
    hall_of_fame_msg += "_____________________________\n"
    hall_of_fame_msg += "<b>We also want to thank the following anonymous donors:</b>\n"
    hall_of_fame_msg += "🥇 Anonymous 1 -> Ɍ<code>1,500,000</code>\n"
    hall_of_fame_msg += "🥈 Anonymous 2 -> Ɍ<code>1,000,000</code>\n"
    hall_of_fame_msg += "🥉 Anonymous 3 -> Ɍ<code>500,000</code>\n"
    hall_of_fame_msg += "_____________________________\n"
    hall_of_fame_msg += "‼ Use /donate 'amount of RDD' to support Ɍeddcoin development team and you might be on this list!"
    send_text_msg(update, context, hall_of_fame_msg)

def donate(update, context):
    user_input = update.message.text.replace(bot_name,"")
    user_input = user_input[8:].strip()
    if user_input == "":
        qrcode_png = create_qr_code(dev_fund_address)
        donate_qr_msg = "{0}".format(dev_fund_address)
        donate_text_msg = "Any donations are highly appreciated 👍\n-> Hit /hallOfFame to get a list of top 10 contributers.".format(dev_fund_address)
        send_photo_msg(update, context, qrcode_png, donate_qr_msg)
        send_text_msg(update, context, donate_text_msg)
    else:
        withdraw(update, context)
        newDonation(update, context, True)

def withdraw(update, context):
    user = update.message.from_user.username
    user_input = update.message.text.replace(bot_name,"")
    if user_input.startswith("/donate"):
        user_input = user_input[8:].strip()
    else:
        user_input = user_input[10:].strip()
    if user_input == "":
        no_parameters_msg = "There is something missing! See /help for an example."
        send_text_msg(update, context, no_parameters_msg)
    elif user is None:
        no_user_msg = "Hey, please set a telegram username in your profile settings first.\nWith your unique username you can access your wallet. If you change your username you might loose access to your Ɍeddcoins! This wallet is separated from any other wallets and cannot be connected to other ones!"
        send_text_msg(update, context, no_user_msg)
    else:
        if update.message.text.startswith("/donate"):
            address = dev_fund_address
            amount = float(user_input)
        else:
            address = user_input.split(" ")[0]
            amount = float(user_input.split(" ")[1])
        result = subprocess.run([core,"getbalance",user],stdout=subprocess.PIPE)
        balance = (result.stdout.strip()).decode(encoding)
        balance = float(balance)
        if balance < amount:
            neutral_face_emoji = get_emoji(":neutral_face:")
            empty_balance_msg = "Sorry @{0}, but you have insufficient funds {1}".format(user, neutral_face_emoji)
            send_text_msg(update, context, empty_balance_msg)
        else:
            amount = str(amount)
            if walletpassphrase == "":
                tx = subprocess.run([core,"sendfrom",user,address,amount],stdout=subprocess.PIPE)
            else:
                subprocess.run([core,"walletpassphrase", walletpassphrase,"1","false"],stdout=subprocess.PIPE)
                tx = subprocess.run([core,"sendfrom",user,address,amount,"1"],stdout=subprocess.PIPE)
            tx = (tx.stdout.strip()).decode(encoding)
            withdraw_msg = "@{0} has successfully withdrawn Ɍ<code>{1}</code> to address <code>{2}</code> (transaction: https://live.reddcoin.com/tx/{3})".format(user, amount, address, tx)
            send_text_msg(update, context, withdraw_msg)

def hi(update, context):
    user = update.message.from_user.username
    hi_msg = "Hello @{0}, how are you doing today?".format(user)
    send_text_msg(update, context, hi_msg)

def moon(update, context):
    moon_msg = "Moon mission inbound!"
    send_animation_msg(update, context, reddcoin_rocket_ani, moon_msg)

def marketcap(update, context):
    quote_page = requests.get(data_origin)
    strainer = SoupStrainer("div", {"class": "coin-summary-item-detail"})
    soup = BeautifulSoup(quote_page.content, "html.parser", parse_only=strainer)
    marketcap_raw = soup.get_text().replace("\n","")
    marketcap_usd = marketcap_raw[:marketcap_raw.find("USD")]
    marketcap_btc = marketcap_raw[marketcap_raw.find("USD") + 3:marketcap_raw.find("BTC")]
    marketcap_msg = "The current market cap of Ɍeddcoin is valued at $<code>{0}</code> ≈ ₿<code>{1}</code>".format(marketcap_usd, marketcap_btc)
    send_text_msg(update, context, marketcap_msg)

def statistics(update, context):
    dev_fund_balance = str(requests.get(dev_fund_balance_api_url).content)
    dev_fund_balance = dev_fund_balance.replace("'","").replace("b","")
    dev_fund_balance = dev_fund_balance[:-8] + "." + dev_fund_balance[-8:]
    dev_fund_balance = "{0:,.8f}".format(float(dev_fund_balance)).rstrip("0").rstrip(".")
    getinfo = subprocess.run([core,"getinfo"],stdout=subprocess.PIPE).stdout.strip().decode(encoding)
    getstakinginfo = subprocess.run([core,"getstakinginfo"],stdout=subprocess.PIPE).stdout.strip().decode(encoding)
    getbalance = subprocess.run([core,"getbalance"],stdout=subprocess.PIPE).stdout.strip().decode(encoding)
    listaccounts = subprocess.run([core,"listaccounts"],stdout=subprocess.PIPE).stdout.strip().decode(encoding)
    getinfo_json = json.loads(getinfo)
    getstakinginfo_json = json.loads(getstakinginfo)
    listaccounts_json = json.loads(listaccounts)
    block_height = getinfo_json["blocks"]
    money_supply = getinfo_json["moneysupply"]
    net_stake_weight = getstakinginfo_json["netstakeweight"]
    staking_quota = "{0:,.2f}".format(float(net_stake_weight) / float(money_supply) * 100)
    block_height = "{0:,.0f}".format(block_height)
    money_supply = "{0:,.0f}".format(money_supply)
    net_stake_weight = "{0:,.0f}".format(net_stake_weight)
    total_balance = "{0:,.8f}".format(float(getbalance)).rstrip("0").rstrip(".")
    total_users = len(listaccounts_json) - 1
    next_party_block = str(int(block_height[:block_height.find(",")]) + 1)
    next_party_block = next_party_block.ljust(len(str(getinfo_json["blocks"])), "0")
    diff = int(next_party_block) - getinfo_json["blocks"]
    time_to_party = strfdelta(diff, "{D:02}d {H:02}h {M:02}m", inputtype="m")
    diff = "{0:,.0f}".format(diff)
    next_party_block = "{0:,.0f}".format(int(next_party_block))
    tada_emoji = get_emoji(":tada:")
    check_mark_emoji = emojize(":white_check_mark:", use_aliases=True)
    block_height_msg = "{0} With current block height of <code>{1}</code> there are <code>{2}</code> left to block <code>{3}</code> {4} -> Countdown: <code>{5}</code>".format(check_mark_emoji, block_height, diff, next_party_block, tada_emoji, time_to_party)
    netstake_weight_msg = "{0} There are currently <code>{1} ({2}%)</code> Ɍeddcoins being staked from a total of <code>{3}</code>".format(check_mark_emoji, net_stake_weight, staking_quota, money_supply)
    accounts_msg = "{0} Our famous Telegram tipping bot {1} is currently holding <code>{2}</code> Ɍeddcoins from <code>{3}</code> users".format(check_mark_emoji, bot_name, total_balance, total_users)
    dev_fund_balance_msg = "{0} Balance of development funding address: Ɍ<code>{1}</code>".format(check_mark_emoji, dev_fund_balance)
    send_text_msg(update, context, block_height_msg + "\n" + netstake_weight_msg + "\n" + accounts_msg + "\n" + dev_fund_balance_msg)

def send_user_not_allowed_text_msg(update, context):
    telegram_admin_user_list = ""
    for admin_user in admin_list: 
        telegram_admin_user_list += " @" + admin_user
    admin_msg = "This function is restricted to following admins:{0}".format(telegram_admin_user_list) 
    send_text_msg(update, context, admin_msg)

def send_text_msg(update, context, msg):
    context.bot.send_message(chat_id=update.message.chat_id, text=msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

def send_photo_msg(update, context, photo, caption):
    context.bot.send_photo(chat_id=update.message.chat_id, photo=open(photo, "rb"), caption=caption, parse_mode=ParseMode.MARKDOWN)

def send_animation_msg(update, context, animation, caption):
    context.bot.sendAnimation(chat_id=update.message.chat_id, animation=open(animation, "rb"), caption=caption, parse_mode=ParseMode.MARKDOWN)

def get_emoji(emoji_shortcode):
    emoji = emojize(emoji_shortcode, use_aliases=True)
    return emoji

def create_qr_code(value):
    # Generate the qr code and save as png
    qrcode_png = value + ".png"
    qrcode_prefix = "reddcoin:"
    qrobj = pyqrcode.QRCode(qrcode_prefix + value, error = "H")
    qrobj.png(qrcode_png, scale=10, quiet_zone=1)
    # Now open that png image to put the logo
    img = Image.open(qrcode_png)
    img = img.convert("RGBA")
    width, height = img.size
    # Open the logo image and  define how big the logo we want to put in the qr code png
    logo = Image.open(qrcode_logo_img)
    logo_size = 80
    # Calculate logo size and position
    xmin = ymin = int((width / 2) - (logo_size / 2))
    xmax = ymax = int((width / 2) + (logo_size / 2))
    logo = logo.resize((xmax - xmin, ymax - ymin))
    # put the logo in the qr code and save image
    img.paste(logo, (xmin, ymin, xmax, ymax))
    img.save(image_home + qrcode_png)
    return image_home + qrcode_png

def strfdelta(tdelta, fmt="{D:02}d {H:02}h {M:02}m {S:02}s", inputtype="timedelta"):
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
    if inputtype == "timedelta":
        remainder = int(tdelta.total_seconds())
    elif inputtype in ["s", "seconds"]:
        remainder = int(tdelta)
    elif inputtype in ["m", "minutes"]:
        remainder = int(tdelta)*60
    elif inputtype in ["h", "hours"]:
        remainder = int(tdelta)*3600
    elif inputtype in ["d", "days"]:
        remainder = int(tdelta)*86400
    elif inputtype in ["w", "weeks"]:
        remainder = int(tdelta)*604800

    f = Formatter()
    desired_fields = [field_tuple[1] for field_tuple in f.parse(fmt)]
    possible_fields = ("W", "D", "H", "M", "S")
    constants = {"W": 604800, "D": 86400, "H": 3600, "M": 60, "S": 1}
    values = {}
    for field in possible_fields:
        if field in desired_fields and field in constants:
            values[field], remainder = divmod(remainder, constants[field])
    return f.format(fmt, **values)

def readJSON():
    if os.path.isfile('key'):
        json_file = open("db.json", 'r')
    else:
        json_file = open("db.json", "a+")
        #json_file.write("{}")
        json_file.close()
        json_file = open("db.json", 'r')
    try:
        json_obj = json.load(json_file)
    finally:
        json_file.close()
    return json_obj

def writeJSON(json_obj):
    json_file = open("db.json", 'w')
    try:
        json.dump(json_obj, json_file, indent=4)
    finally:
        json_file.close()

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)

def main():
    # Create the Updater and pass it your bot's token.
    updater = Updater(token="872012702:AAEGfPfievApCyR8p28FFrG4AmWKoCz5FYM", use_context=True)
    
    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    
    # Add command handlers
    start_handler = CommandHandler("start", commands)
    dispatcher.add_handler(start_handler)
    
    commands_handler = CommandHandler("commands", commands)
    dispatcher.add_handler(commands_handler)
    
    moon_handler = CommandHandler("moon", moon)
    dispatcher.add_handler(moon_handler)

    statistics_handler = CommandHandler("statistics", statistics)
    dispatcher.add_handler(statistics_handler)
    
    hi_handler = CommandHandler("hi", hi)
    dispatcher.add_handler(hi_handler)
    
    donate_handler = CommandHandler("donate", donate)
    dispatcher.add_handler(donate_handler)
    
    withdraw_handler = CommandHandler("withdraw", withdraw)
    dispatcher.add_handler(withdraw_handler)
    
    marketcap_handler = CommandHandler("marketcap", marketcap)
    dispatcher.add_handler(marketcap_handler)
    
    deposit_handler = CommandHandler("deposit", deposit)
    dispatcher.add_handler(deposit_handler)

    price_handler = CommandHandler("price", price)
    dispatcher.add_handler(price_handler)
    
    tip_handler = CommandHandler("tip", tip)
    dispatcher.add_handler(tip_handler)
    
    balance_handler = CommandHandler("balance", balance)
    dispatcher.add_handler(balance_handler)
    
    help_handler = CommandHandler("help", help)
    dispatcher.add_handler(help_handler)
    
    about_handler = CommandHandler("about", about)
    dispatcher.add_handler(about_handler)
    
    newDonation_handler = CommandHandler("newDonation", newDonation)
    dispatcher.add_handler(newDonation_handler)
    
    removeDonor_handler = CommandHandler("removeDonor", removeDonor)
    dispatcher.add_handler(removeDonor_handler)
    
    hallOfFame_handler = CommandHandler("hallOfFame", hallOfFame)
    dispatcher.add_handler(hallOfFame_handler)
    
    # Add error handler.
    dispatcher.add_error_handler(error)
    
    # Start the Bot.
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()
