#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on 07.05.2019
@author: owebb
'''

from config import *
import logging
import time
from apscheduler.schedulers.background import BackgroundScheduler
from string import Formatter
import requests
import pyqrcode
from PIL import Image
import subprocess
import json
from emoji import emojize
from telegram import ParseMode
from telegram.ext import (Updater, CommandHandler)
from builtins import str

## Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

## Called by scheduler for checking incoming receive transactions from accounts wallet and stake transactions from stake wallet 
def check_incoming_transactions():
    check_deposit_transactions()
    check_stake_transactions()

## Incoming transactions from users need to be tracked by moving transferred Reddcoins from users account to main account for staking support + adding to balance in json users file
def check_deposit_transactions():
    account_list = subprocess.run([accounts_wallet,"listaccounts"],stdout=subprocess.PIPE).stdout.strip().decode(encoding)
    accounts_json = json.loads(account_list)
    users_json = read_users_list()
    for user, user_balance in accounts_json.items():
        if len(user) > 0 and user_balance > 0.0:
            user_balance -= 0.001
            print("User: " + user)
            print("Balance: " + str(user_balance))
            if walletpassphrase == "":
                tx_id = subprocess.run([accounts_wallet,"sendfrom",user,staking_wallet_address,str(user_balance)],stdout=subprocess.PIPE).stdout.strip().decode(encoding)
            else:
                subprocess.run([accounts_wallet,"walletpassphrase", walletpassphrase,"1","false"],stdout=subprocess.PIPE)
                tx_id = subprocess.run([accounts_wallet,"sendfrom",user,staking_wallet_address,str(user_balance),"1"],stdout=subprocess.PIPE).stdout.strip().decode(encoding)
            print("tx_id: " + tx_id)
            if len(tx_id) == 64:
                if user in users_json:
                    users_json[user] += user_balance
                else:
                    users_json[user] = user_balance
                msg = "User id: {0} - User balance: {1} - Tx msg: {2}".format(user, user_balance, tx_id)
                print(msg)
                user_account_balance = subprocess.run([accounts_wallet,"getbalance",user],stdout=subprocess.PIPE).stdout.strip().decode(encoding)
                if float(user_account_balance) > 0.0:
                    subprocess.run([accounts_wallet,"move",user,"",user_account_balance],stdout=subprocess.PIPE)
            else:
                msg = "Something went wrong! User id: {0} - User balance: {1} - Tx msg: {2}".format(user, user_balance, tx_id)
                print(msg)
    write_users_list(users_json)

## For a successful stake from main account Reddcoins are distributed to all other accounts according to their balance
def check_stake_transactions():
    tx_ids_from_staking_wallet = rpc_connect("listtransactions", ["*", 99999])
    staking_tx_json = read_staking_tx_list()
    users_json = read_users_list()
    for tx in tx_ids_from_staking_wallet['result']:
        if tx['category'] == 'stake' and tx['txid'] not in staking_tx_json:
            staking_tx_json[tx['txid']] = tx['amount']
            users_balance = 0.0
            for user, user_balance in users_json.items():
                users_balance += user_balance
            print("users total balance: " + str(users_balance))
            for user, user_balance in users_json.items():
                if user_balance > 0.0:
                    print("current balance user: " + str(user_balance))
                    user_balance += (user_balance / users_balance) * tx['amount']
                    users_json[user] = user_balance
                    print("new balance user: " + str(user_balance))
    write_staking_tx_list(staking_tx_json)
    write_users_list(users_json)

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
    help_msg = "The following commands are at your disposal: /hi /commands /deposit /tip /donate /withdraw /balance /price /marketcap /statistics /moon /about /hallOfFame \n \nExamples: \n<code>/tip @TechAdept 100</code>\n<code>/tip @CryptoGnasher 100</code>\n-> send a tip of 100 Ɍeddcoins to our project lead Jay 'TechAdept' Laurence or to our lead dev John Nash\n<code>/donate 100</code>\n-> support Ɍeddcoin team by donating them 100 Ɍeddcoins\n<code>/withdraw {0} 100</code>\n-> send 100 Ɍeddcoins to a specific address (in this example: dev fund raising address which is also used for /donate)".format(dev_fund_address)
    send_text_msg(update, context, help_msg)

def about(update, context):
    about_msg = "{0} was originally coded by @xGozzy (Ex-Developer) and was further developed by @cryptoBUZE. The source code can be viewed at https://github.com/cryptoBUZE/reddbot-telegram. If you have any enquiries please contact @TechAdept or @cryptoBUZE".format(bot_name)
    send_text_msg(update, context, about_msg)

def deposit(update, context):
    user_username = update.message.from_user.username
    user_first_name = update.message.from_user.first_name
    users_json = read_users_list()
    if user_username is None:
        no_user_msg = "Hey {0}, please set a Telegram username in your profile settings first.\nWith your unique username you can access your <b>Telegram Reddcoin wallet</b>. If you change your username you might loose access to your Ɍeddcoins! This wallet is separated from any other wallets and cannot be connected to other ones!".format(user_first_name)
        send_text_msg(update, context, no_user_msg)
    else:
        if user_username not in users_json:
            create_new_wallet(update, context, user_first_name, user_username, users_json)
            fetch_deposit_address(update, context, user_username)
        else:
            fetch_deposit_address(update, context, user_username)

def tip(update, context):
    user = update.message.from_user.username
    user_first_name = update.message.from_user.first_name
    user_input = update.message.text[5:].strip()
    users_json = read_users_list()
    if user_input == "":
        no_parameters = "There is something missing! See /help for an example."
        send_text_msg(update, context, no_parameters)
    elif user is None:
        no_user_msg = "Hey {0}, please set a Telegram username in your profile settings first.\nWith your unique username you can access your <b>Telegram Reddcoin wallet</b>. If you change your username you might loose access to your Ɍeddcoins! This wallet is separated from any other wallets and cannot be connected to other ones!".format(user_first_name)
        send_text_msg(update, context, no_user_msg)
    else:
        target = user_input.split(" ")[0]
        amount = float(user_input.split(" ")[1])
        if target == bot_name:
            hodl_msg = "HODL."
            send_text_msg(update, context, hodl_msg)
        elif "@" in target and user in users_json:
            target = target[1:]
            balance = users_json[user]
            if balance < amount:
                insufficient_funds_msg = "@{0} you have insufficient funds.".format(user)
                send_text_msg(update, context, insufficient_funds_msg)
            elif target == user:
                self_tip_msg = "You can't tip yourself silly."
                send_text_msg(update, context, self_tip_msg)
            elif amount > 0.0:
                users_json[user] -= amount
                users_json[target] += amount 
                tip_msg = "@{0} tipped @{1} of {2} ɌDD".format(user, target, amount)
                send_text_msg(update, context, tip_msg)
            else:
                tip_msg = "I see what you did there!"
                send_text_msg(update, context, tip_msg)
        else:
            wrong_format_msg = "Error that user is not applicable. Need help? -> /help"
            send_text_msg(update, context, wrong_format_msg)
    write_users_list(users_json)

def balance(update, context):
    user_username = update.message.from_user.username
    user_first_name = update.message.from_user.first_name
    price_info = get_market_data_info_from_coingecko()
    price_usd = float(price_info[1])
    # Get JSON data
    json_obj = read_users_list()
    if user_username is None:
        no_user_msg = "Hey {0}, please set a Telegram username in your profile settings first.\nWith your unique username you can access your <b>Telegram Reddcoin wallet</b>. If you change your username you might loose access to your Ɍeddcoins! This wallet is separated from any other wallets and cannot be connected to other ones!".format(user_first_name)
        send_text_msg(update, context, no_user_msg)
    elif user_username in json_obj:
        user_balance = decimal_round_down(json_obj[user_username])
        fiat_balance = user_balance * price_usd
        fiat_balance = "{0:,.3f}".format(fiat_balance)
        balance_msg = "@{0} your current balance is: Ɍ<code>{1}</code> ≈ $<code>{2}</code>".format(user_username, user_balance, fiat_balance)
        send_text_msg(update, context, balance_msg)
    else:
        create_new_wallet(update, context, user_first_name, user_username, json_obj)

def create_new_wallet(update, context, user_first_name, user_username, json_obj):
    json_obj[user_username] = 0.0
    write_users_list(json_obj)
    balance_msg = "Hi {0}! I have just created a wallet which is associated with your unique Telegram user username @{1}\n-> If you need help just hit /help or /commands to get started!".format(user_first_name, user_username)
    send_text_msg(update, context, balance_msg)

def fetch_deposit_address(update, context, user_username):
    user_accountaddress = subprocess.run([accounts_wallet,"getaccountaddress",user_username],stdout=subprocess.PIPE).stdout.strip().decode(encoding)
    qrcode_png = create_qr_code(user_accountaddress)
    deposit_msq = "@{0} your depositing address is: {1}".format(user_username, user_accountaddress)
    send_photo_msg(update, context, qrcode_png, deposit_msq) 

def price(update, context):
    price_info = get_market_data_info_from_coingecko()
    price_btc = price_info[0]
    price_usd = price_info[1]
    price_change_percentage_24h = price_info[2]
    if price_change_percentage_24h < 0:
        change_symbol = "-"
        price_change_percentage_24h = -price_change_percentage_24h
    elif price_change_percentage_24h > 0:
        change_symbol = "+"
    else:
        change_symbol = ""
    price_change_percentage_24h = "{:.2f}".format(price_change_percentage_24h) + "%"
    if change_symbol != "":
        price_msg = "1 Ɍeddcoin is valued at $<code>{0}</code> Δ {1}<code>{2}</code> ≈ ₿<code>{3}</code>".format(price_usd,change_symbol,price_change_percentage_24h,price_btc)
    else:
        price_msg = "1 Ɍeddcoin is valued at $<code>{0}</code> ≈ ₿<code>{1}</code>".format(price_usd,price_btc)
    send_text_msg(update, context, price_msg)

def newDonation(update, context, allowed=False):
    user_id = update.message.from_user.username
    if allowed:
        user_input_user_id = "@" + user_id
        user_input_user_first_name = update.message.from_user.first_name
        user_input_user_last_name = update.message.from_user.last_name
        if user_input_user_last_name == None:
            user_input_user_display_name = user_input_user_first_name
        else:
            user_input_user_display_name = user_input_user_first_name + " " + user_input_user_last_name
        user_input_user_amount = update.message.text[8:].strip().split(" ")[0]
        addDonation(update, context, user_input_user_id, user_input_user_display_name, user_input_user_amount)
    elif user_id in admin_list:
        user_input = update.message.text.partition(' ')[2]
        user_input_user_id = ''.join(user_input.partition(" ")).split(" ")[0]
        user_input_user_display_name_and_amount = ''.join(user_input.partition(" ")).split(user_input_user_id)[1]
        user_input_user_display_name = user_input_user_display_name_and_amount[:user_input_user_display_name_and_amount.rfind(' ')].strip()
        user_input_user_amount = user_input_user_display_name_and_amount[user_input_user_display_name_and_amount.rfind(' '):].strip()
        addDonation(update, context, user_input_user_id, user_input_user_display_name, user_input_user_amount)
    else:
        send_user_not_allowed_text_msg(update, context)

def addDonation(update, context, user_input_user_id, user_input_user_display_name, user_input_user_amount):
    # Get JSON data to store donation
    json_obj = read_donors_list()
    user_key = user_input_user_id + " " + user_input_user_display_name
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
    write_donors_list(json_obj)
    send_text_msg(update, context, donation_msg)

def removeDonor(update, context):
    # Remove donor from hall of fame list
    user_id = update.message.from_user.username
    if user_id in admin_list:
        json_obj = read_donors_list()
        user_input = update.message.text.partition(' ')[2]
        user_input_user_id = ''.join(user_input.partition(" ")).split(" ")[0]
        user_input_user_display_name = ''.join(user_input.partition(" ")).split(user_input_user_id)[1]
        user_key = user_input_user_id + " " + user_input_user_display_name.strip()
        if user_key in json_obj:
            del json_obj[user_key]
            remove_msg = "Donor '{0}' was removed from hall of fame list.".format(user_key)
        else:
            neutral_face_emoji = get_emoji(":neutral_face:")
            remove_msg = "Sorry but donor '{0}' was not found on hall of fame list {1}".format(user_key, neutral_face_emoji)
        write_donors_list(json_obj)
        send_text_msg(update, context, remove_msg)
    else:
        send_user_not_allowed_text_msg(update, context)

def hallOfFame(update, context):
    user_id = update.message.from_user.username
    user_input = update.message.text[12:].strip().lower()
    json_obj = read_donors_list()
    counter = 0
    json_obj_size = str(len(json_obj))
    if user_id is not None and user_input == "position":
        for key, value in sorted(json_obj.items(), key=lambda item: item[1], reverse=True):
            counter += 1
            if user_id in key:
                hall_of_fame_msg = "Hey @{0}, your current position in hall of fame donation list is: {1} out of {2}".format(user_id, counter, json_obj_size)
                break;
    else:
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
    withdraw_successful = False
    if user_input == "":
        qrcode_png = create_qr_code(dev_fund_address)
        donate_qr_msg = "{0}".format(dev_fund_address)
        donate_text_msg = "Any donations are highly appreciated 👍\n-> Hit /hallOfFame to get a list of top 10 contributers.".format(dev_fund_address)
        send_photo_msg(update, context, qrcode_png, donate_qr_msg)
        send_text_msg(update, context, donate_text_msg)
    else:
        withdraw_successful = withdraw(update, context)
        if withdraw_successful:
            newDonation(update, context, True)

def withdraw(update, context):
    user = update.message.from_user.username
    user_first_name = update.message.from_user.first_name
    user_input = update.message.text.replace(bot_name, "")
    withdraw_successful = False
    users_json = read_users_list()
    if user_input.startswith("/donate"):
        user_input = user_input[8:].strip()
    else:
        user_input = user_input[10:].strip()
    if user_input == "":
        no_parameters_msg = "There is something missing! See /help for an example."
        send_text_msg(update, context, no_parameters_msg)
    elif user is None:
        no_user_msg = "Hey {0}, please set a Telegram username in your profile settings first.\nWith your unique username you can access your <b>Telegram Reddcoin wallet</b>. If you change your username you might loose access to your Ɍeddcoins! This wallet is separated from any other wallets and cannot be connected to other ones!".format(user_first_name)
        send_text_msg(update, context, no_user_msg)
    else:
        if update.message.text.startswith("/donate"):
            address = dev_fund_address
            amount = float(user_input)
        else:
            address = user_input.split(" ")[0]
            amount = float(user_input.split(" ")[1])
        balance = users_json[user]
        if amount < 0.0:
            negative_amount_msg = "I see what you did there!"
            send_text_msg(update, context, negative_amount_msg)
        elif balance < amount:
            neutral_face_emoji = get_emoji(":neutral_face:")
            empty_balance_msg = "Sorry @{0}, but you have insufficient funds {1}".format(user, neutral_face_emoji)
            send_text_msg(update, context, empty_balance_msg)
        elif amount > 0.002:
            tx_id = rpc_connect("sendtoaddress", [address, amount])['result']
            if len(tx_id) == 64:
                withdraw_successful = True
                withdraw_msg = "@{0} has successfully withdrawn Ɍ<code>{1}</code> to address <code>{2}</code> (transaction: https://live.reddcoin.com/tx/{3})".format(user, amount, address, tx_id)
                users_json[user] -= amount
                write_users_list(users_json)
                send_text_msg(update, context, withdraw_msg)
        else:
            withdraw_msg = "Sorry @{0} but the amount for withdrawals has to be more than Ɍ<code>0.002</code>".format(user)
            send_text_msg(update, context, withdraw_msg)
    return withdraw_successful

def hi(update, context):
    user = update.message.from_user.username
    hi_msg = "Hello @{0}, how are you doing today?".format(user)
    send_text_msg(update, context, hi_msg)

def moon(update, context):
    moon_msg = "Moon mission inbound!"
    send_animation_msg(update, context, reddcoin_rocket_ani, moon_msg)

def marketcap(update, context):
    price_info = get_market_data_info_from_coingecko()
    marketcap_btc = price_info[3]
    marketcap_usd = "{0:,.0f}".format(price_info[4])
    marketcap_msg = "The current market cap of Ɍeddcoin is valued at $<code>{0}</code> ≈ ₿<code>{1}</code>".format(marketcap_usd, marketcap_btc)
    send_text_msg(update, context, marketcap_msg)

def statistics(update, context):
    # sum of staking from staking tx json file
    stakings_json = read_staking_tx_list()
    number_of_stakes = 0
    total_stake_amount = 0.0
    for tx, stake_amount in stakings_json.items():
        number_of_stakes += 1
        total_stake_amount += stake_amount
    dev_fund_balance = str(requests.get(dev_fund_balance_api_url).content)
    dev_fund_balance = dev_fund_balance.replace("'","").replace("b","")
    dev_fund_balance = dev_fund_balance[:-8] + "." + dev_fund_balance[-8:]
    dev_fund_balance = "{0:,.8f}".format(float(dev_fund_balance)).rstrip("0").rstrip(".")
    getinfo = subprocess.run([accounts_wallet,"getinfo"],stdout=subprocess.PIPE).stdout.strip().decode(encoding)
    getstakinginfo = subprocess.run([accounts_wallet,"getstakinginfo"],stdout=subprocess.PIPE).stdout.strip().decode(encoding)
    getbalance = rpc_connect("getbalance", [])['result']
    listaccounts = subprocess.run([accounts_wallet,"listaccounts"],stdout=subprocess.PIPE).stdout.strip().decode(encoding)
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
    total_balance = "{0:,.8f}".format(getbalance).rstrip("0").rstrip(".")
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
    stake_msg = "{0} Wallet of Telegram tipping bot has staked {1} time(s) with a total of <code>{2}</code> Ɍeddcoins".format(check_mark_emoji, number_of_stakes, total_stake_amount)
    dev_fund_balance_msg = "{0} Balance of development funding address: Ɍ<code>{1}</code>".format(check_mark_emoji, dev_fund_balance)
    send_text_msg(update, context, block_height_msg + "\n" + netstake_weight_msg + "\n" + accounts_msg + "\n" + stake_msg + "\n" + dev_fund_balance_msg)

def get_market_data_info_from_coingecko():
    response = requests.get(market_data_origin)
    raw_data = response.json()
    price_btc = '{:.8f}'.format(raw_data['market_data']['current_price']['btc'])
    price_usd = '{:.6f}'.format(raw_data['market_data']['current_price']['usd'])
    price_change_percentage_24h = raw_data['market_data']['price_change_percentage_24h']
    market_cap_btc = raw_data['market_data']['market_cap']['btc']
    market_cap_usd = raw_data['market_data']['market_cap']['usd']
    return[price_btc, price_usd, price_change_percentage_24h, market_cap_btc, market_cap_usd]

def rpc_connect(method, params):
    url = "http://" + staking_wallet_rpc_ip +":" + staking_wallet_rpc_port + "/"
    payload = json.dumps({"method": method, "params": params})
    headers = {'content-type': "application/json", 'cache-control': "no-cache"}
    try:
        response = requests.request("POST", url, data=payload, headers=headers, auth=(staking_wallet_rpc_user, staking_wallet_rpc_pw))
        if response.text.startswith("{"):
            return json.loads(response.text)
        else:
            return response.text
    except:
        print("No response from server. Check if Reddcoin core wallet is running on " + staking_wallet_rpc_ip)

def send_user_not_allowed_text_msg(update, context):
    telegram_admin_user_list = ""
    for admin_user in admin_list: 
        telegram_admin_user_list += " @" + admin_user
    admin_msg = "This function is restricted to following admins:{0}".format(telegram_admin_user_list) 
    send_text_msg(update, context, admin_msg)

def resolve_reply_to_id(update):
    if update.message.chat_id < 0:
        # We are in a group message, reply to the original message
        return update.message.message_id
    # We are in a private chat, don't reply
    return None

def send_text_msg(update, context, msg):
    context.bot.send_message(chat_id=update.message.chat_id, text=msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True, reply_to_message_id=resolve_reply_to_id(update))
    print("chat-id: " + str(update.message.chat_id))

def send_photo_msg(update, context, photo, caption):
    context.bot.send_photo(chat_id=update.message.chat_id, photo=open(photo, "rb"), caption=caption, parse_mode=ParseMode.MARKDOWN, reply_to_message_id=resolve_reply_to_id(update))

def send_animation_msg(update, context, animation, caption):
    context.bot.sendAnimation(chat_id=update.message.chat_id, animation=open(animation, "rb"), caption=caption, parse_mode=ParseMode.MARKDOWN, reply_to_message_id=resolve_reply_to_id(update))

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

def read_staking_tx_list():
    return read_json_file(staking_json_file)

def write_staking_tx_list(json_obj):
    return write_json_file(staking_json_file, json_obj)

def read_tippings_list():
    return read_json_file(tippings_json_file)

def write_tippings_list(json_obj):
    return write_json_file(tippings_json_file, json_obj)

def read_users_list():
    return read_json_file(users_json_file)

def write_users_list(json_obj):
    return write_json_file(users_json_file, json_obj)

def read_donors_list():
    return read_json_file(donors_json_file)

def write_donors_list(json_obj):
    return write_json_file(donors_json_file, json_obj)

def read_json_file(filename):
    json_file = open(filename, 'r')
    try:
        json_obj = json.load(json_file)
    finally:
        json_file.close()
    return json_obj

def write_json_file(filename, json_obj):
    json_file = open(filename, 'w')
    try:
        json.dump(json_obj, json_file, indent=4)
    finally:
        json_file.close()
        
def decimal_round_down(input):
    if type(input) == float:
        str_input = str(input)
    decimal_places = str_input[::-1].find('.')
    if int(decimal_places) > 8:
        result = round(float(str_input) - 0.00000001, 8)
    else:
        result = float(str_input)
    return result

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)

def main():
    ## Main Scheduler setup for running tasks
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_incoming_transactions, 'interval', seconds=30)
    scheduler.start()

    ## Telegram bot dispatcher and handlers
    # Create the Updater and pass it your bot's token.
    updater = Updater(token=bot_token, use_context=True)
    
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

    check_deposit_transactions_handler = CommandHandler("check_deposit_transactions", check_deposit_transactions)
    dispatcher.add_handler(check_deposit_transactions_handler)

    check_stake_transactions_handler = CommandHandler("check_stake_transactions", check_stake_transactions)
    dispatcher.add_handler(check_stake_transactions_handler)

    # Add error handler.
    dispatcher.add_error_handler(error)

    # Start the Bot.
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

    # This is here to simulate application activity (which keeps the main thread alive).
    try:
        while scheduler_active:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        # Not strictly necessary if daemonic mode is enabled but should be done if possible
        scheduler.shutdown()

if __name__ == '__main__':
    main()
