#!/usr/bin/python
# coding: utf-8

# 2015 © Guillermo Gómez Fonfría <guillermo.gf@openmailbox.org>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import urllib2
import sys
import os
import json
import requests


# Load Token
try:
    token_file = open("token")
except:
    print("Token file missing")
    sys.exit(1)

token = token_file.read().rstrip("\n")
token_file.close()

# Telegram API urls
api_url = "https://api.telegram.org/bot"
token_url = api_url + token
getupdates_url = token_url + "/getUpdates"
sendmessage_url = token_url + "/sendMessage"
sendimage_url = token_url + "/sendPhoto"
senddocument_url = token_url + "/sendDocument"

# Messages content
start_text = "Hi!\nThis bot downloads a random picture from imgur.com and \
sends it to you.\n"

help_text = "List of available commands:\n/help Shows this list of available \
commands\n/random Sends random picture"

error_unknown = "Unknown command\n"


def download_image():
    name = urllib2.urlopen("http://www.imgur.com/random").\
           geturl().split("/")[-1]
    typeheader = urllib2.urlopen("http://i.imgur.com/{0}.gif".
                                 format(name)).headers.typeheader

    if typeheader == "image/gif":
        name = name + ".gif"
    elif typeheader == "image/png":
        name = name + ".png"
    elif typeheader == "image/jpeg":
        name = name + ".jpeg"

    path = "/tmp/" + name

    image = open(path, "w")
    image.write(urllib2.urlopen("http://i.imgur.com/{0}".format(name)).read())
    image.close()

    return path

while True:
    # Load last update
    try:
        last_update_file = open("lastupdate")
        last_update = last_update_file.read().rstrip("\n")
        last_update_file.close()
    except:
        last_update = "0"  # If lastupdate file not present, read all updates

    getupdates_offset_url = getupdates_url + "?offset=" + str(int(last_update)
                                                              + 1)

    get_updates = requests.get(getupdates_offset_url)
    if get_updates.status_code != 200:
        print(get_updates.status_code)  # For debugging
        continue
    else:
        updates = json.loads(get_updates.content)["result"]

    for item in updates:
        if int(last_update) >= item["update_id"]:
            continue
        # Store last update
        last_update_file = open("lastupdate", "w")
        last_update_file.write(str(item["update_id"]))
        last_update_file.close()

        if "/start" == item["message"]["text"]:
            message = requests.get(sendmessage_url + "?chat_id=" +
                                   str(item["message"]["chat"]["id"]) +
                                   "&text=" + start_text + help_text)
        elif "/help" in item["message"]["text"]:
            message = requests.get(sendmessage_url + "?chat_id=" +
                                   str(item["message"]["chat"]["id"]) +
                                   "&text=" + help_text)
        elif "/random" in item["message"]["text"]:
            path = download_image()
            data = {"chat_id": str(item["message"]["chat"]["id"])}
            if path.endswith(".gif"):
                files = {"document": (path, open(path, "rb"))}
                requests.post(senddocument_url, data=data, files=files)
            else:
                files = {"photo": (path, open(path, "rb"))}
                requests.post(sendimage_url, data=data, files=files)
            os.remove(path)
        elif item["message"]["chat"]["id"] < 0:
            # If it is none of the above and it's a group, let's guess it was for
            # another bot rather than sending the unknown command message
            continue
        else:
            message = requests.get(sendmessage_url + "?chat_id=" +
                                   str(item["message"]["chat"]["id"]) +
                                   "&text=" + error_unknown + help_text)
