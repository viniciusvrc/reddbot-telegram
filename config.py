#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on 01.07.2019
@author: owebb
'''

# Telegram tipbot variables
bot_name = ""
bot_token = ""
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
admin_list = ["admin1", "admin2", "admin3", "admin4"]