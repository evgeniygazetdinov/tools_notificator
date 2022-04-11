# -*- coding: utf-8 -*-
import sys

print(sys.getdefaultencoding())
import json
import unicodedata
import os
import requests
import time
import urllib
import re
import sys
import datetime
import threading
from multiprocessing import Process, current_process, cpu_count, active_children


from lib.sessions import Session
from lib.session_methods import check_user_actions, send_raw_message, hide_tracks
from lib.const import URL
from lib.buttons import (
    menu_items,
    login_items,
    kick_out,
    yes_no_items,
    under_upload_menu,
)
from lib.protect import do_some_protection
from lib.active_users import (
    get_active_users,
    save_users_state,
    push_active_users,
    remove_active_users,
)
from lib.base import (
    build_keyboard,
    clean_patern,
    send_message,
    send_location,
    get_url,
    find_user_message_chat,
    div_password,
    build_keyboard,
    get_json_from_url,
    get_last_update_id,
    get_updates,
    get_updates,
    get_last_chat_id_and_text,
    telegram_clean_history,
    make_filestring_for_request,
)


def check_telegram_updates():
    last_update_id = None
    args = []
    while True:
        try:
            updates = get_updates(last_update_id)
        except KeyboardInterrupt:
            print("Interrupted")
            sys.exit(0)
        if len(updates["result"]) != 0:
            # init section
            last_update_id = get_last_update_id(updates) + 1
            cur_user, cur_chat, cur_message, message_id = find_user_message_chat(
                updates["result"]
            )
            if cur_message == "/start":
                send_message("Привет это бот фотохостинга", cur_chat)
            if cur_message:
                send_message("йш=о", cur_chat)
            time.sleep(0.5)


def main_flow():
    check_telegram_updates()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--debug":
            do_some_protection()
            main_flow()
    else:
        main_flow()
