from bot import bot
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.telegram_helper.message_utils import deleteMessage, editMessage
from pyrogram.filters import regex
from pyrogram.handlers import CallbackQueryHandler


YT_HELP_DICT = {}
MIRROR_HELP_DICT = {}
LEECH_HELP_DICT = {}

ytdl = """ 
***YT-DL MENU COMMANDS***

1. <b>Send link along with command line:</b>
<code>/cmd</code> link -s -opt x:y|x1:y1

2. <b>By replying to link</b>

<b>NOTES:</b>
Check all yt-dlp api options from this <a href='https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py#L184'>FILE</a> or use this <a href='https://t.me/mltb_official_channel/177'>script</a> to convert cli arguments to api options.
"""

quality = """
4. <b>Quality Buttons:</b>

<code>/cmd</code> link -s

Incase default quality added from yt-dlp options using format option and you need to select quality for specific link or links with multi links feature.
"""

options = """ <b>Options</b>: -opt

<code>/cmd</code> link -opt playliststart:^10|fragment_retries:^inf|matchtitle:S13|writesubtitles:true|live_from_start:true|postprocessor_args:{"ffmpeg": ["-threads", "4"]}|wait_for_video:(5, 100)

<b>Note:</b> Add `^` before integer or float, some values must be numeric and some string.
Like playlist_items:10 works with string, so no need to add `^` before the number but playlistend works only with integer so you must add `^` before the number like example above.
You can add tuple and dict also. Use double quotes inside dict.
"""

mirror = """

***MIRROR COMMANDS MENU***

<b>NOTE:</b>
1. Commands that start with <b>qb</b> are ONLY for torrents.
"""

new_name = """ 
<b>New Name: </b>

1. <code>/cmd</code> link -n newname

2. <b>By replying to link/file</b>  

Note: It does not work with torrents.
"""

extract = """ 
<b>Extract: </b>

1. <code>/cmd</code> link -e 

2. <code>/cmd</code> link -e password (extract password protected)
"""

zip = """
<b>Zip: </b>

1.<code>/cmd</code> link -z

2.<code>/cmd</code> link -z password (zip password protected)
"""

multi = """
<b>Multi by replying to first link/file:</b>

<code>/cmd</code> link -i 5 (number of links/files)
"""

same_multi = """
<b>Multi (with same directory) by replying to first link/file:</b>

<code>/cmd</code> link -i 5(number of links/files) -m foldername
"""

direct_link = """

1.<code>/cmd</code> link 

2.<b>Direct link authorization:</b>

<code>/cmd</code> link -au username -ap password

3. <b>By replying to link</b> 
"""

torr_select = """
<b>Bittorrent selection:</b>  

1. <code>/cmd</code> link -s

2. <b>By replying to file/link</b> 
"""

torr_seed = """
<b>Bittorrent seed:</b>

1. <code>/cmd</code> link -d ratio:seed_time 

2. <b>By replying to file/link</b> 

To specify ratio and seed time add -d ratio:time. Ex: -d 0.7:10 (ratio and time) or -d 0.7 (only ratio) or -d :10 (only time) where time in minutes.
"""

screenshots = """
<b>Screenshots:</b>

<code>/cmd</code> -ss (default values which is 10 photos).

You can control this value. Example: /cmd -ss 6.
"""

leech = """
***LEECH MENU COMMANDS***

<b>Send link to leech, /ignore to cancel</b>
"""

RSS_HELP_MESSAGE = """
Use this format to add feed url:
Title1 link (required)
Title2 link c: cmd inf: xx exf: xx opt: options like(up, rcf, pswd) (optional)
Title3 link c: cmd d:ratio:time opt: up: gd

c: command + any mirror option before link like seed option.
opt: any option after link like up, rcf and pswd(zip).
inf: For included words filter.
exf: For excluded words filter.

Example: Title https://www.rss-url.com inf: 1080 or 720 or 144p|mkv or mp4|hevc exf: flv or web|xxx opt: up: mrcc:remote:path/subdir rcf: --buffer-size:8M|key|key:value
This filter will parse links that it's titles contains `(1080 or 720 or 144p) and (mkv or mp4) and hevc` and doesn't conyain (flv or web) and xxx` words. You can add whatever you want.

Another example: inf:  1080  or 720p|.web. or .webrip.|hvec or x264. This will parse titles that contains ( 1080  or 720p) and (.web. or .webrip.) and (hvec or x264). I have added space before and after 1080 to avoid wrong matching. If this `10805695` number in title it will match 1080 if added 1080 without spaces after it.

Filter Notes:
1. | means and.
2. Add `or` between similar keys, you can add it between qualities or between extensions, so don't add filter like this f: 1080|mp4 or 720|web because this will parse 1080 and (mp4 or 720) and web ... not (1080 and mp4) or (720 and web)."
3. You can add `or` and `|` as much as you want."
4. Take look on title if it has static special character after or before the qualities or extensions or whatever and use them in filter to avoid wrong match.
Timeout: 60 sec.
"""

CLONE_HELP_MESSAGE = """
Send Gdrive|Gdot|Filepress|Filebee|Appdrive|Gdflix link along with command or by replying to the link 

1. <b>Multi links only by replying to first gdlink link:</b>
<code>/clone</code> -i 5(number of links)

2. <b>Gdrive:</b>
<code>/clone</code> gdlink/gdrive_id 

If you want to clone from your token.pickle (uploaded from /user_setting) add mtp: before the path/gdrive_id without space.
Incase you want to specify whether using token or service accounts you can add tp:link or tp:gdrive_id or sa:link or sa:gdrive_id.
"""

PASSWORD_ERROR_MESSAGE = """
<b>This link requires a password!</b>
- Insert <b>::</b> after the link and write the password after the sign.

<b>Example:</b> link::my password
"""

batch = """
Send me one of the followings:      

/ignore to cancel
"""

tg_link = """
<b>Telegram Link</b> 

Public: https://t.me/channel_name/message_id
Private: https://t.me/c/channel_id/message_id
"""

url_link = """
<b>URL links</b> 

Each link separated by new line 

<b>Direct link authorization:</b>  
link username password
"""

txt_file = """
<b>Txt File</b> 

Each link inside .txt file separated by new line        
"""


MIRROR_HELP_DICT = {
    "Cmd": mirror,
    "Menu": None,
    "Rename": new_name,
    "Zip": zip,
    "Extract": extract,
    "Multi": multi,
    "Link": direct_link,
    "Seed": torr_seed,
    "Select": torr_select,
    "Screenshot": screenshots,
}

LEECH_HELP_DICT = {
    "Cmd": leech,
    "Menu": None,
    "Rename": new_name.replace("<code>/cmd</code>", ""),
    "Zip": zip.replace("<code>/cmd</code>", ""),
    "Extract": extract.replace("<code>/cmd</code>", ""),
    "Multi": multi.replace("<code>/cmd</code>", ""),
    "Link": direct_link.replace("<code>/cmd</code>", ""),
    "Seed": torr_seed.replace("<code>/cmd</code>", ""),
    "Select": torr_select.replace("<code>/cmd</code>", ""),
    "Screenshot": screenshots.replace("<code>/cmd</code>", ""),
}

YT_HELP_DICT = {
    "Cmd": ytdl,
    "Menu": None,
    "Rename": f"{new_name}\nNote: Don't add file extension",
    "Zip": zip,
    "Quality": quality,
    "Options": options,
    "Multi": multi,
}

BATCH_HELP_DICT = {
    "Cmd": batch,
    "Menu": None,
    "TG-Link": tg_link,
    "Txt-File": txt_file,
    "Url-Link": url_link,
}


async def create_mirror_help_buttons():
    buttons = ButtonMaker()
    for name in list(MIRROR_HELP_DICT.keys())[2:]:
        buttons.cb_buildbutton(name, f"help m {name}")
    buttons.cb_buildbutton("✘ Close Menu", f"help close", "footer")
    MIRROR_HELP_DICT["Menu"] = buttons.build_menu(3)


async def create_ytdl_help_buttons():
    buttons = ButtonMaker()
    for name in list(YT_HELP_DICT.keys())[2:]:
        buttons.cb_buildbutton(name, f"help y {name}")
    buttons.cb_buildbutton("✘ Close Menu", f"help close", "footer")
    YT_HELP_DICT["Menu"] = buttons.build_menu(3)


async def create_leech_help_buttons():
    buttons = ButtonMaker()
    for name in list(LEECH_HELP_DICT.keys())[2:]:
        buttons.cb_buildbutton(name, f"help l {name}")
    buttons.cb_buildbutton("✘ Close Menu", f"help close", "footer")
    LEECH_HELP_DICT["Menu"] = buttons.build_menu(3)


async def create_batch_help_buttons():
    buttons = ButtonMaker()
    for name in list(BATCH_HELP_DICT.keys())[2:]:
        buttons.cb_buildbutton(name, f"help b {name}")
    buttons.cb_buildbutton("✘ Close Menu", f"help close", "footer")
    BATCH_HELP_DICT["Menu"] = buttons.build_menu(3)


async def help_callback(_, query):
    data = query.data.split()
    message = query.message
    if data[1] == "close":
        await deleteMessage(message)
    elif data[1] == "back":
        if data[2] == "m":
            await editMessage(
                MIRROR_HELP_DICT["Cmd"], message, MIRROR_HELP_DICT["Menu"]
            )
        elif data[2] == "l":
            await editMessage(LEECH_HELP_DICT["Cmd"], message, LEECH_HELP_DICT["Menu"])
        elif data[2] == "b":
            await editMessage(BATCH_HELP_DICT["Cmd"], message, BATCH_HELP_DICT["Menu"])
        else:
            await editMessage(YT_HELP_DICT["Cmd"], message, YT_HELP_DICT["Menu"])
    elif data[1] == "m":
        buttons = ButtonMaker()
        buttons.cb_buildbutton("⬅️ Back", f"help back m")
        await editMessage(MIRROR_HELP_DICT[data[2]], message, buttons.build_menu())
    elif data[1] == "y":
        buttons = ButtonMaker()
        buttons.cb_buildbutton("⬅️ Back", f"help back y")
        await editMessage(YT_HELP_DICT[data[2]], message, buttons.build_menu())
    elif data[1] == "l":
        buttons = ButtonMaker()
        buttons.cb_buildbutton("⬅️ Back", f"help back l")
        await editMessage(LEECH_HELP_DICT[data[2]], message, buttons.build_menu())
    elif data[1] == "b":
        buttons = ButtonMaker()
        buttons.cb_buildbutton("⬅️ Back", f"help back b")
        await editMessage(BATCH_HELP_DICT[data[2]], message, buttons.build_menu())


bot.add_handler(CallbackQueryHandler(help_callback, filters=regex("^help")))
