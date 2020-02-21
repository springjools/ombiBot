# ombiBot
A python-telegram-bot front-end to make ombi-requests

# Installation

install python 3

pip install -r requirements.txt

# Running

python3 bot.py

# List of things needed

you will need these things:

1) ombi api token: ombi->settings->ombi and look for apiKey

2) telegram bot token: see https://www.siteguarding.com/en/how-to-get-telegram-bot-api-token

# Config file

- Rename config.example.json to config.json

- Fill out: 
    * server: ip-address/url of your ombi server, for example http://192.168.1.1
    * port: default is 5000
    * baseUrl: default is /ombi
    * apiKey: insert apiKey from ombi
    * users:  you need at least one pair of user.id and ombi-user-name. The code assumes that any users not found in this list 
              go under the name 'guest'. So you need to set up one ombi user with the name 'guest'. Reason: otherwise any user
              interacting with this bot would have automatic admin access to your ombi server.
              
              To get your telegram id: see here: https://telegram.me/myidbot 
