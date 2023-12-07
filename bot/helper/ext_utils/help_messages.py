YT_HELP_MESSAGE = """
1. <b>Send link along with command line:</b>
<code>/cmd</code> link -s -opt x:y|x1:y1

2. <b>By replying to link:</b>

3. <b>New Name</b>: 
<code>/cmd</code> link -n newname
Note: Don't add file extension

4. <b>Quality Buttons:</b>
Incase default quality added from yt-dlp options using format option and you need to select quality for specific link or links with multi links feature.
<code>/cmd</code> link -s

5. <b>Zip</b>: -z password
<code>/cmd</code> link -z (zip)
<code>/cmd</code> link -z password (zip password protected)

6. <b>Options</b>: -opt
<code>/cmd</code> link -opt playliststart:^10|fragment_retries:^inf|matchtitle:S13|writesubtitles:true|live_from_start:true|postprocessor_args:{"ffmpeg": ["-threads", "4"]}|wait_for_video:(5, 100)
Note: Add `^` before integer or float, some values must be numeric and some string.
Like playlist_items:10 works with string, so no need to add `^` before the number but playlistend works only with integer so you must add `^` before the number like example above.
You can add tuple and dict also. Use double quotes inside dict.

7. <b>Multi links only by replying to first link:</b>
<code>/cmd</code> -i 5(number of links)

<b>NOTES:</b>
Check all yt-dlp api options from this <a href='https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py#L184'>FILE</a> or use this <a href='https://t.me/mltb_official_channel/177'>script</a> to convert cli arguments to api options.
"""


MIRROR_HELP_MESSAGE = """         
1. <code>/cmd</code> link 

2. <b>Replying to link/file</b>    

3. <b>New Name</b>: 
<code>/cmd</code> link -n newname
Note: No work with torrents.

4. <b>Extract & Zip</b>: 
<code>/cmd</code> link -e password (extract password protected)
<code>/cmd</code> link -z password (zip password protected)

5. <b>Multi by replying to first link/file:</b>
<code>/cmd</code> -i 5(number of links/files)

6. <b>Multi with same directory by replying to first link/file:</b>
<code>/cmd</code> -i 5(number of links/files) -m foldername

7. <b>Direct link authorization:</b>
<code>/cmd</code> link -au username -ap password

8. <b>Bittorrent selection</b>    
<code>/cmd</code> link -s or by replying to file/link

9. <b>Bittorrent seed</b>:
<code>/cmd</code> <b>d</b> link -d ratio:seed_time or by replying to file/link
To specify ratio and seed time add -d ratio:time. Ex: -d 0.7:10 (ratio and time) or -d 0.7 (only ratio) or -d :10 (only time) where time in minutes.

"""

LEECH_HELP_MESSAGE = """  

<b>Send link to leech, /ignore to cancel</b>

Options:
1. <b>New Name</b>: 
link -n newname
Note: No work with torrents.

2. <b>Extract & Zip</b>: 
link -e password (extract password protected)
link -z password (zip password protected)

3. <b>Direct link authorization:</b>
link -au username -ap password

4. <b>Bittorrent selection</b>    
link -s

5. <b>Bittorrent seed</b>:
link -d ratio:seed_time
To specify ratio and seed time add -d ratio:time. Ex: -d 0.7:10 (ratio and time) or -d 0.7 (only ratio) or -d :10 (only time) where time in minutes.

Note: You can also reply to link to leech it with options.
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
<code>/clone</code> gdlink
"""

PASSWORD_ERROR_MESSAGE = """
<b>This link requires a password!</b>
- Insert <b>::</b> after the link and write the password after the sign.

<b>Example:</b> link::my password
"""