from pyrogram import Client

print('Required pyrogram V2 or greater')

API_ID = int(input("Enter API_ID: "))
API_HASH = input("Enter API_HASH: ")

with Client(name='USS', api_id=API_ID, api_hash=API_HASH) as app:
    print(app.export_session_string())
