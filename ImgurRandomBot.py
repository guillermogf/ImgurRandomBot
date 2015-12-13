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
import time


# Load Token
try:
    with open("token") as token_file:
        token = token_file.read().rstrip("\n")
except:
    print("Token file missing")
    sys.exit(1)


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
commands\n/random Sends random picture\n/about Shows info about this bot\n\
/feedback <message> Send your feedback to the ImgurRandomBot developers"

about_text = "Source code at: https://github.com/guillermogf/ImgurRandomBot"

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

    with open(path, "w") as image:
        image.write(urllib2.urlopen("http://i.imgur.com/{0}".format(name)).read())

    return path


def get_argument(message):
    message = message.split(" ")
    if "/feedback" in message:
        message.remove("/feedback")
    elif "/feedback@ImgurRandomBot" in message:
        message.remove("/feedback@ImgurRangomBot")

    argument = " ".join(message)
    return argument


def feedback(message):
    with open("feedback", "a") as feedback_file:
        feedback = " ".join(message) + "\n"
        feedback_file.write(feedback.encode("utf-8"))


while True:
    # Load last update
    try:
        with open("lastupdate") as last_update_file:
            last_update = last_update_file.read().rstrip("\n")
    except:
        last_update = "0"  # If lastupdate file not present, read all updates

    getupdates_offset_url = getupdates_url + "?offset=" + \
        str(int(last_update) + 1)

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
        with open("lastupdate", "w") as last_update_file:
            last_update_file.write(str(item["update_id"]))

        # Store time to log
        with open("log", "a") as log:
            log.write(str(time.time()) + "\n")

        # Group's status messages don't include "text" key
        try:
            text = item["message"]["text"]
        except KeyError:
            continue

        if "/start" == text:
            message = requests.get(sendmessage_url + "?chat_id=" +
                                   str(item["message"]["chat"]["id"]) +
                                   "&text=" + start_text + help_text)

        elif "/help" in text:
            message = requests.get(sendmessage_url + "?chat_id=" +
                                   str(item["message"]["chat"]["id"]) +
                                   "&text=" + help_text)

        elif "/random" in text:
            path = download_image()
            data = {"chat_id": str(item["message"]["chat"]["id"])}
            if path.endswith(".gif"):
                files = {"document": (path, open(path, "rb"))}
                requests.post(senddocument_url, data=data, files=files)
            else:
                files = {"photo": (path, open(path, "rb"))}
                requests.post(sendimage_url, data=data, files=files)
            os.remove(path)

        elif "/feedback" in text:
            if get_argument(text) != "":
                feedback([time.ctime(item["message"]["date"]),
                          "id:" + str(item["message"]["chat"]["id"]),
                          item["message"]["from"]["first_name"], text])
                answer = "Thanks for your feedback!"
            else:
                answer = "Write your message after /feedback"
            message = requests.get(sendmessage_url + "?chat_id=" +
                                   str(item["message"]["chat"]["id"]) +
                                   "&text=" + answer)

        elif "/about" in text:
            message = requests.get(sendmessage_url + "?chat_id=" +
                                   str(item["message"]["chat"]["id"]) +
                                   "&text=" + about_text)

        elif item["message"]["chat"]["id"] < 0:
            # If it is none of the above and it's a group, let's guess it was
            # for another bot rather than sending the unknown command message
            continue

        else:
            message = requests.get(sendmessage_url + "?chat_id=" +
                                   str(item["message"]["chat"]["id"]) +
                                   "&text=" + error_unknown + help_text)
