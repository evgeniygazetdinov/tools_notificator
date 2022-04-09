from lib.base import create_dir_for_not_exists_file
import os
from lib.const import active_users_path
import json

# list  with active_users: here methods discribe that


def get_active_users():
    create_dir_for_not_exists_file(active_users_path)
    with open(active_users_path, "r") as json_file:

        data = json.load(json_file)
        if "users" not in data:
            data = {"users": []}
            save_users_state(data)
            get_active_users()

        return data


def save_users_state(active_users):
    with open(active_users_path, "w", encoding="utf-8") as f:
        json.dump(active_users, f, ensure_ascii=False, indent=4)


def push_active_users(user):
    active_users = get_active_users()
    active_users["users"].append(user)
    save_users_state(active_users)


def remove_active_users(user):
    users = get_active_users()
    if user in users:
        users["users"].remove(user)
    save_users_state(users)
