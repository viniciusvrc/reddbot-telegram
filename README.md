# Reddbot - Telegram Reddcoin Tipbot v3

#### Reddcoin crypto currency tipbot for [Telegram](https://telegram.org)


## Dependencies 

*  `apt-get install python3`
*  `apt-get install python3-pip`
*  `pip3 install requests`
*  `pip3 install beautifulsoup4`
*  `pip3 install pyqrcode`
*  `pip3 install Image`
*  `pip3 install pypng`
*  `pip3 install emoji`
*  `pip3 install apscheduler`
*  `pip3 install python-telegram-bot==12.0.0b1 --upgrade`

* In order to run the tip-bot effectively, a Bitcoin-core based client is needed. For this git Reddcoin Core Wallet is used, but any major alternate crypto-currency client could easily be incorperated.

## Setup

* Download the git: 
`git clone https://github.com/cryptoBUZE/reddbot-telegram`

* Setup a bot with the user @BotFather through PM on Telegram, after going through a setup you will be given a bot token. Edit the command.py file and replace the parameter 'bot_token' and 'bot_name' with the one you just recieved/defined. Also change following parameters in config.py file to match corresponding values of your server:

`bot_name = ""`
`bot_token = ""`
`accounts_wallet = "/home/rdd/reddcoind"`
`staking_wallet_address = ""`
`staking_wallet_rpc_ip = ""`
`staking_wallet_rpc_port = ""`
`staking_wallet_rpc_user = ""`
`staking_wallet_rpc_pw = ""`
`market_data_origin = "https://api.coingecko.com/api/v3/coins/reddcoin?localization=false&tickers=false&community_data=false&developer_data=false"`
`reddbot_home = "/home/rdd/reddbot/"`
`dev_fund_address = ""`
`dev_fund_balance_api_url = "https://live.reddcoin.com/api/addr/" + dev_fund_address + "/balance"`
`dev_fund_tx = "http://live.reddcoin.com/api/txs/?address=" + dev_fund_address`
`walletpassphrase = ""`
`admin_list = ["admin1", "admin2", "admin3", "admin4"]`

*  Run the script: 
`nohup python3 reddbot.py > bot.log 2>&1`

*  Initiate the bot by inviting it to a chat or via PM, some commands are `/balance` , `/price` , `/help` and to find out the format related to tip others and withdrawal of funds use `/commands`.

## Update from V1 version to V2 or V3

* Stop running bot: `pkill -f reddbot.py` (killing process which contains 'reddbot.py')
* Install new dependencies: `pip3 install pyqrcode && pip3 install Image && pip3 install pypng && pip3 install emoji && pip3 install apscheduler && pip3 install python-telegram-bot==12.0.0b1 --upgrade`
* Download new script into reddbot-telegram-v3 folder: `git clone https://github.com/cryptoBUZE/reddbot-telegram reddbot-telegram-v3`
* Change into reddbot-telegram-v3 directory: `cd reddbot-telegram-v3`
* Set bot token: `sed -i 's/(token="")/(token="bot_token")/g' reddbot.py` (Replace bot_token with token from Telegram BotFather)
* Set path to Reddcoin core wallet: `sed -i 's|"/home/rdd/reddcoind"|"accounts_wallet"|g' reddbot.py` (Replace accounts_wallet with path to reddcoind)
* Set path to script directory: `sed -i 's|"/home/rdd/reddbot/"|"reddbot_home"|g' reddbot.py` (Replace reddbot_home with path to home of script file, e.g. /home/rdd/reddbot-telegram-v3/
* Start script with python: `nohup python3 command.py > bot.log 2>&1` (nohup for running script as background process)

## Some further notes:
*  Stop current running bot python instance with 'pkill -f reddbot.py' -> If script was renamed you have to adjust this value. Default filename from repo is reddbot.py (step can be also done later)
*  Install new dependencies with pip3 command -> If Maven 3.x and pip is installed pip3 command should work
*  Git clone repo -> Should be self explanatory but don't delete folder with current Telegram tip bot (backup). Repo will be cloned into reddbot-telegram-v3 directory
*  Set bot token -> Have a look into reddbot.py script file of current running version and copy bot token value to replace bot_token with help of sed command
*  Set path to Reddcoin core wallet -> Replace accounts_wallet with path to reddcoin core daemon file
*  Set path to script directory -> Replace reddbot_home with path of reddbot-telegram-v3 directory with help of sed command (don't forget / at the end)
* If bot python instance is still running now it's time to kill this process
* Start new script with python -> There should be no legacy warning message with latest version of python-telegram-bot (v12)

### Setting up the bot as so still leaves the wallet unencrypted, so please go to extra measures to provide extra security. Make sure to have SSH encryption on whatever device/droplet you run it on. 

*  Please fork the code, happy tipping!
