#!/bin/bash
echo "Instalandor iniciado......"
apt update && apt upgrade -y
git clone https://github.com/viniciusvrc/reddbot-telegram
sudo apt-get install python-dev python3-dev libxml2-dev libxslt1-dev zlib1g-dev libsasl2-dev libldap2-dev build-essential libssl-dev libffi-dev libmysqlclient-dev libjpeg-dev libpq-dev libjpeg8-dev liblcms2-dev libblas-dev libatlas-base-dev
apt-get install python3
apt-get install python3-pip
pip3 install -r requirements.txt
pip3 install python-telegram-bot==12.0.0b1 --upgrade
echo "Instalado com sucesso!."


