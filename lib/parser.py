from telethon import TelegramClient, events, sync
from const import APP_ID, API_HASH, PHONE, username
import datetime




# collect channels group
# do job with multiply group



def up_client():
    # @client.on(events.NewMessage(chats='-1001439011975'))
    # @client.on(events.NewMessage(chats='-1001696221413'))
    # @client.on(events.NewMessage(chats='-1001414968083'))
    # @client.on(events.NewMessage(chats='-1001363478011'))
#    @client.on(events.NewMessage(chats='-1001674506295'))

    # some functions to parse json date
    import json
    class DateTimeEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, datetime):
                return o.isoformat()

            if isinstance(o, bytes):
                return list(o)

            return json.JSONEncoder.default(self, o)
    import configparser
    import json
    import asyncio

    from telethon import TelegramClient
    from telethon.errors import SessionPasswordNeededError
    from telethon.tl.functions.messages import (GetHistoryRequest)
    from telethon.tl.types import (
        PeerChannel
    )

    # Reading Configs

    # Setting configuration values
    api_id = APP_ID
    api_hash = API_HASH

    phone = PHONE

    # Create the client and connect
    client = TelegramClient(username, api_id, api_hash)

    async def main(phone):
        await client.start()
        print("Client Created")
        # Ensure you're authorized
        if await client.is_user_authorized() == False:
            await client.send_code_request(phone)
            try:
                await client.sign_in(phone, input('Enter the code: '))
            except SessionPasswordNeededError:
                await client.sign_in(password=input('Password: '))

        me = await client.get_me()

        user_input_channel = 'https://t.me/relocate_it'#input("enter entity(telegram URL or entity id):")

        if user_input_channel.isdigit():
            entity = PeerChannel(int(user_input_channel))
        else:
            entity = user_input_channel

        my_channel = await client.get_entity(entity)

        offset_id = 0
        limit = 100
        all_messages = []
        total_messages = 0
        total_count_limit = 0

        while True:
            print("Current Offset ID is:", offset_id, "; Total Messages:", total_messages)
            history = await client(GetHistoryRequest(
                peer=my_channel,
                offset_id=offset_id,
                offset_date=None,
                add_offset=0,
                limit=limit,
                max_id=0,
                min_id=0,
                hash=0
            ))
            if not history.messages:
                break
            messages = history.messages
            for message in messages:
                all_messages.append(message.to_dict())
            offset_id = messages[len(messages) - 1].id
            total_messages = len(all_messages)
            if total_count_limit != 0 and total_messages >= total_count_limit:
                break

        with open('channel_messages.json', 'w') as outfile:
            json.dump(all_messages, outfile, cls=DateTimeEncoder)

    with client:
        client.loop.run_until_complete(main(phone))
up_client()