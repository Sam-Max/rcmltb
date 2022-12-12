from asyncio import get_event_loop
from pyrogram import Client

async def generate_string_sesion():
    print('Required pyrogram V2 or greater.')

    API_ID= int(input("Enter API_ID: "))
    API_HASH = input("Enter API_HASH: ")

    async with Client(name='USS', api_id=API_ID, api_hash=API_HASH, in_memory=True) as app:
        print(await app.export_session_string())

get_event_loop().run_until_complete(generate_string_sesion())
