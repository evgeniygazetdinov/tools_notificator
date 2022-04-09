import os
import json
import shutil
from datetime import datetime
import time


class Session(object):
    def __init__(self, username, chat, message_id, password=False):
        self.username = username
        self.password = password
        self.cur_chat = chat
        self.message_id = message_id
        # check_folder
        # exists load
        # else create
        self.user_file_path = (
            os.getcwd()
            + "/session/"
            + str(self.username)
            + "/"
            + str(self.username)
            + ".json"
        )
        if os.path.exists(self.user_file_path):
            self.user_folder = os.getcwd() + "/session/" + str(self.username)
            self.user_info = self.get_session_details()
            self.save_user_info()
        else:
            self.user_info = {
                "username": username,
                "password": password,
                "state": {
                    "login": False,
                    "created": False,
                    "upload": False,
                    "change_password": False,
                    "change_time_check_updates": False,
                },
                "changer": {"old_password": False, "new_password": False},
                "photo_position": {
                    "filename": False,
                    "latitude": False,
                    "longitude": False,
                },
                "last_action": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "pushed_button": False,
                "cur_chat": self.cur_chat,
                "message_id": self.message_id,
                "profile": {"username": False, "password1": False, "password2": False},
                "login_credentials": {"username": False, "password": False},
                "time_for_check_updates": 60,
                "on_check_photos": False,
                "uploaded_photos": [],
                "photos_from_requests": [],
            }
            self.user_folder = self.create_user_folder()
            self.save_user_info()

    def update_user_info(self, value, condition):
        self.user_info[value] = condition
        self.save_user_info()

    def update_last_action(self):
        self.user_info["last_action"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    def push_photos_from_request(self, photos):
        self.user_info["photos_from_requests"] = photos
        self.save_user_info()

    def update_state_user(self, state, value, password=False):
        self.update_last_action()
        self.user_info["state"][state] = value
        if password:
            self.user_info["password"] = password
        self.save_user_info()

    def update_user_creditails(self, place, check_place, value_for_place):
        self.update_last_action()
        self.user_info[place][check_place] = value_for_place
        # if 'password2' != 'in_process' and 'password2' != False:
        # flag for success user create
        # self.username = self.user_info['profile']['username']
        # self.password = self.user_info['profile']['password2']
        self.save_user_info()

    def reset_login_session(self):
        # reset all and back to login menu
        self.user_info["on_check_photos"] = False
        self.user_info["changer"]["old_password"] = False
        self.user_info["changer"]["new_password"] = False
        self.user_info["photo_position"]["latitude"] = False
        self.user_info["photo_position"]["longitude"] = False
        self.update_state_user("upload", False)
        self.update_state_user("change_password", False)
        self.update_state_user("change_time_check_updates", False)
        self.update_state_user("login", True)
        self.save_user_info()

    def put_user_photos_to_session(self, photos):
        self.user_info["uploaded_photos"] = photos
        self.save_user_info()

    def get_user_info_value(self, value):
        self.update_last_action()
        return self.user_info[value]

    def save_to_user_history(self):
        with open(self.user_folder + "/history.json", "w+", encoding="utf-8") as f:
            json.dump(self.user_info, f, ensure_ascii=False, indent=4)

    def save_user_info(self):
        self.update_last_action()
        # self.save_to_user_history()
        with open(
            self.user_folder + "/{}.json".format(self.username), "w", encoding="utf-8"
        ) as f:
            json.dump(self.user_info, f, ensure_ascii=False, indent=4)

    def get_session_details(self):
        user_session_path = self.user_folder + "/{}.json".format(self.username)
        with open(user_session_path) as json_file:
            data = json.load(json_file)
            return data

    def create_user_folder(self):
        os.makedirs(os.getcwd() + "/session/" + str(self.username), exist_ok=True)
        return str(os.getcwd() + "/session/" + str(self.username))

    def clean_session(self):
        shutil.rmtree(self.user_folder, ignore_errors=True)
