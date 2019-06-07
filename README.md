# Reddbot - Telegram Reddcoin Tipbot v2.0
 
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
*  `pip3 install python-telegram-bot --upgrade`

* In order to run the tip-bot effectively, a Bitcoin-core based client is needed. For this git Reddcoin-Core is used , but any major alternate crypto-currency client could easily be incorperated. 

## Setup

* Download the git: 
`git clone https://github.com/cryptoBUZE/reddbot-telegram`

* Setup a bot with the user @BotFather through PM on Telegram, after going through a setup you will be given a bot token. Edit the command.py file and replace the parameter 'BOT_TOKEN' and 'bot_name' with the one you just recieved/defined. Also change following parameters to match corresponding values of your server:

`core = "/home/rdd/reddcoind"`
`reddbot_home = "/home/rdd/reddbot/"`

*  Run the script: 
`nohup python3 command.py > bot.log 2>&1`

*  Initiate the bot by inviting it to a chat or via PM, some commands are `/balance` , `/price` , `/help` and to find out the format related to tip others and withdrawal of funds use `/commands`.

## Update from previous version to V2

* Stop running bot: `pkill -f command.py` (killing process which contains 'command.py')
* Install new dependencies: `pip3 install pyqrcode && pip3 install Image && pip3 install pypng && pip3 install emoji`
* Download new script into reddbot-telegram-v2 folder: `git clone https://github.com/cryptoBUZE/reddbot-telegram reddbot-telegram-v2`
* Change into reddbot-telegram-v2 directory: `cd reddbot-telegram-v2`
* Set bot token: `sed -i 's/(token="")/(token="BOT_TOKEN")/g' command.py` (Replace BOT_TOKEN with token from Telegram BotFather)
* Set path to Reddcoin core wallet: `sed -i 's|"/home/rdd/reddcoind"|"REDDCOIN_CORE"|g' command.py` (Replace REDDCOIN_CORE with path to reddcoind)
* Set path to script directory: `sed -i 's|"/home/rdd/reddbot/"|"REDDBOT_HOME"|g' command.py` (Replace REDDBOT_HOME with path to home of script file, e.g. /home/rdd/reddbot-telegram-v2
* Start script with python: `nohup python3 command.py > bot.log 2>&1` (nohup for running script as background process)

### Setting up the bot as so still leaves the wallet unencrypted, so please go to extra measures to provide extra security. Make sure to have SSH encryption on whatever device/droplet you run it on. 

*  Please fork the code, happy tipping! 



