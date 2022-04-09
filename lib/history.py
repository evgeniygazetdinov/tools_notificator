import json
import os
from lib.const import URL
import aiohttp
import asyncio
import requests
import time

# here save user and bot message id into file and methods for bring this


def get_path(user=False):
    if user:
        path = os.getcwd() + "/session/{}/user_action.json".format(user)
    else:
        path = os.getcwd() + "/session/bot_action.json"
    return path


def path_for_user_or_bot(user, is_user):
    return get_path(user) if is_user else get_path()


def get_data_by_path(user, is_user=False):
    path = path_for_user_or_bot(user, is_user)
    if os.path.exists(path):
        with open(path, "r") as json_file:
            data = json.load(json_file)
            return data if data is not None else store_action(path, {user: []})
            {user: []}
    else:
        data = {user: []}
        store_action(path, data)
        return data


def store_action(path, result):
    if not os.path.exists(path):
        not_exist_dir = os.path.split(path)
        if not os.path.exists(not_exist_dir[0]):
            # create_not_exists_folder
            os.makedirs(str(not_exist_dir[0]))
        # creating not exists file
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)


def delete_from_storige(user, data):
    if user in data:
        del data[user]


def get_data_and_paths(user):
    path_user = get_path(user)
    bot_path = get_path()
    user_data = get_data_by_path(user, True)
    bot_data = get_data_by_path(user)
    return path_user, bot_path, user_data, bot_data


def cover_user_tracks(user):
    path_user, bot_path, user_data, bot_data = get_data_and_paths(user)
    delete_from_storige(user, user_data)
    delete_from_storige(user, bot_data)
    store_action(bot_path, bot_data)


def save_action(content):
    content = content.json()
    if "result" in content:
        if len(content["result"]) != 0:
            cur_result = content["result"]
            # it's bot action
            if "message_id" in cur_result:
                if cur_result["from"]["is_bot"]:
                    path = get_path()
                    if "id" in cur_result["chat"]:
                        user = str(cur_result["chat"]["id"])
                    message = content["result"]["message_id"]
                    data = get_data_by_path(user)
                    if user in data:
                        data[user].append(message)
                        store_action(path, data)
                        print("store bot action")
                    else:
                        data[user] = []
                        store_action(path, data)
            elif isinstance(content["result"], list):
                # it's user
                res = content["result"][0]
                if "message" in res:
                    if res["message"]["from"]["is_bot"] == False:
                        message = res["message"]["message_id"]
                        from_ = res["message"]["from"]
                        if "id" in from_:
                            user = str(from_["id"])
                        path = get_path(user)
                        data = get_data_by_path(user, is_user=True)
                        if user in data:
                            data[user].append(message)
                        else:
                            data[user] = []
                        store_action(path, data)
                        print("store user action")
    else:
        pass


def extract_ids(username):
    message_ids = []
    user_path, bot_path, user_data, bot_data = get_data_and_paths(username)
    if str(username) in bot_data:
        if str(username) in user_data:
            for message_id in bot_data[str(username)]:
                message_ids.append(message_id)
            for message_id in user_data[str(username)]:
                message_ids.append(message_id)
    return message_ids


def create_links_for_delete(session, username):
    links = []
    chat_id = session.get_user_info_value("cur_chat")
    message_ids = extract_ids(str(username))
    for message_id in message_ids:
        links.append(
            URL + "deletemessage?message_id={}&chat_id={}".format(message_id, chat_id)
        )
    return links


async def do_request(session, url):
    async with session.get(url) as response:
        print("Read {0} from {1}".format(response.status_code, url))


async def remove_messages(sites):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in sites:
            try:
                task = asyncio.ensure_future(do_request(session, url))
                asyncio.sleep(0.1)
                tasks.append(task)
            except RuntimeWarning:
                pass
        await asyncio.gather(*tasks, return_exceptions=True)


def clean_history(session, username):
    links = create_links_for_delete(session, username)
    start_time = time.time()
    asyncio.get_event_loop().run_until_complete(remove_messages(links))
    duration = time.time() - start_time
    print(f"REMOVE {len(links)} messages in {duration} seconds")


def take_all_bot_actions(path):
    with open(path, "r") as json_file:
        data = json.load(json_file)
        return data if data is not None else store_action(path, {user: []})
        {user: []}


# remove_from_bot action file
def delete_user_ids_from_bot_actions(user):
    path = get_path()
    bot_data = take_all_bot_actions(path)
    if user in bot_data:
        bot_data.pop(user, None)
        store_action(path, bot_data)
