import time
from lib.const import URL
from lib.buttons import raw_menu_keyboard
from lib.base import send_message
from lib.history import (
    create_links_for_delete,
    clean_history,
    delete_user_ids_from_bot_actions,
    store_action,
    get_path,
)
from lib.active_users import remove_active_users

# file has method for be executed with session/ each push button will  be check user time and store message id for clean history
import requests
import json
import urllib
import os


# so ugly
def send_raw_message(text, chat_id, reply_markup=None):
    # text = urllib.parse.quote_plus(text)
    dict_for_store = dict()
    url = URL + "sendMessage"
    data = {"chat_id": chat_id, "text": text}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    response = requests.get(url, data)
    # store raw response messageid
    context = response.json()
    if "result" in context:
        mes_id = context["result"]["message_id"]
        if "id" in context["result"]["chat"]:
            user = str(context["result"]["chat"]["id"])
        path = get_path()

        if os.path.exists(path):
            with open(path, "r") as json_file:
                dict_for_store = json.load(json_file)
                # data-dict empty
                if not any(dict_for_store):
                    dict_for_store[user] = [mes_id]
                elif user not in dict_for_store:
                    dict_for_store[user] = [mes_id]
                else:
                    dict_for_store[user].append(mes_id)
        # if bot action not exist
        else:
            dict_for_store[user] = [mes_id]

        store_action(path, dict_for_store)

    # push message_id into user_list)))


def hide_tracks(session):
    clean_history(session, session.username)
    delete_user_ids_from_bot_actions(session.username)
    remove_active_users(session.username)


# executed on push button
def check_user_actions(cur_user, session):
    # just call and wait 60 second /if he passed clean history and clean session
    time_for_check = session.user_info["time_for_check_updates"]
    begin = 0
    while session.get_user_info_value("pushed_button"):
        begin += 1
        time.sleep(1)
        print(begin)
        # check_user_folder
        if begin == time_for_check:
            print("time is over")
            send_message(
                "{} second passed".format(time_for_check),
                session.get_user_info_value("cur_chat"),
            )
            hide_tracks(session)
            # remove_from_bot
            send_raw_message(
                "выберите вариант",
                session.get_user_info_value("cur_chat"),
                raw_menu_keyboard,
            )
            session.clean_session()

            break
