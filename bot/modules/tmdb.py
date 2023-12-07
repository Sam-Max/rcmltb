from bot import config_dict, tmdb_titles, bot
from os import remove as osremove
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram import filters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.telegram_helper.message_utils import editMessage, sendMessage, sendPhoto
from bot.helper.ext_utils.misc_utils import get_image_from_url
from bot.modules.search import tmdbSearch
from tmdbv3api import TMDb, Discover, Movie, TV, Trending


tmdb = TMDb()
tmdb.debug = False
tmdb_image_base = "http://image.tmdb.org/t/p/w500"
tmdb_dict = {}


async def tdmb_categories(_, message):
    tmdb.api_key = config_dict["TMDB_API_KEY"]
    tmdb.language = config_dict["TMDB_LANGUAGE"]
    if config_dict["TMDB_API_KEY"] and config_dict["SEARCH_PLUGINS"]:
        button = ButtonMaker()
        button.cb_buildbutton("📺 Movies", "tmdbsubcat^movie")
        button.cb_buildbutton("🎬 TV Shows", "tmdbsubcat^tv")
        button.cb_buildbutton("🔍 Search", "tmdbsearchapi")
        button.cb_buildbutton("✘ Close Menu", "tdmbcatinfo^close", position="footer")
        await sendMessage("Choose one category", message, button.build_menu(2))
    else:
        await sendMessage("No Tmdb API key or search plugins provided", message)


async def tmdb_sub_categories(_, query):
    data = query.data.split("^")
    message = query.message
    button = ButtonMaker()
    if data[1] == "movie":
        button.cb_buildbutton("Trending", "tdmbcatinfo^trending_movie")
        button.cb_buildbutton("Discover", "tdmbcatinfo^discover_movie")
    elif data[1] == "tv":
        button.cb_buildbutton("Trending", "tdmbcatinfo^trending_tv")
        button.cb_buildbutton("Discover", "tdmbcatinfo^discover_tv")
    button.cb_buildbutton("✘ Close Menu", "tdmbcatinfo^close", position="footer")
    await query.answer()
    await editMessage("Choose one category", message, button.build_menu(2))


async def tmdb_get_category_info(_, query):
    data = query.data.split("^")
    message = query.message
    discover = Discover()
    trending = Trending()
    button = ButtonMaker()
    user_id = message.reply_to_message.from_user.id

    if data[1] == "discover_movie":
        await query.answer()
        movies = discover.discover_movies({"sort_by": "popularity.desc"})
        await pagination(button, movies, data[1], user_id)
        await editMessage("Popular Movies", message, button.build_menu(2))
    elif data[1] == "trending_movie":
        await query.answer()
        movies = trending.movie_week()
        await pagination(button, movies, data[1], user_id)
        await editMessage("Trending Movies", message, button.build_menu(2))
    elif data[1] == "discover_tv":
        await query.answer()
        shows = discover.discover_tv_shows({"sort_by": "popularity.desc"})
        await pagination(button, shows, data[1], user_id)
        await editMessage("Popular TV Shows", message, button.build_menu(2))
    elif data[1] == "trending_tv":
        await query.answer()
        shows = trending.tv_day()
        await pagination(button, shows, data[1], user_id)
        await editMessage("Trending TV Shows", message, button.build_menu(2))
    else:
        await query.answer()
        await message.delete()


async def tmdb_get_details(_, query):
    data = query.data.split("^")
    message = query.message
    button = ButtonMaker()

    if data[1] == "movie":
        await query.answer()
        movie = Movie()
        m = movie.details(data[2])
        title = m.title
        msg = f"<b>Title:</b> {title}\n\n"
        msg += f"<b>Plot:</b> {m.overview}\n\n"
        tmdb_titles[m.id] = title
        if m.poster_path is None:
            button.cb_buildbutton("🔍 Torrent Search", f"tdmbsearch^{m.id}")
            await sendMessage(msg, message, button.build_menu(2))
        else:
            image_url = tmdb_image_base + m.poster_path
            path = await get_image_from_url(image_url, title)
            if path:
                button.cb_buildbutton("🔍 Torrent Search", f"tdmbsearch^{m.id}")
                await sendPhoto(msg, message, path, button.build_menu(2))
                osremove(path)
            else:
                await sendMessage("Failed to retrieve image.", message)
    elif data[1] == "tv":
        await query.answer()
        tv = TV()
        m = tv.details(data[2])
        title = m.name
        msg = f"<b>Title:</b> {title}\n\n"
        msg += f"<b>Plot:</b> {m.overview}\n\n"
        tmdb_titles[m.id] = title
        if m.poster_path is None:
            button.cb_buildbutton("🔍 Torrent Search", f"tdmbsearch^{m.id}")
            await sendMessage(msg, message, button.build_menu(2))
        else:
            image_url = tmdb_image_base + m.poster_path
            path = await get_image_from_url(image_url, title)
            if path:
                button.cb_buildbutton("🔍 Torrent Search", f"tdmbsearch^{m.id}")
                await sendPhoto(msg, message, path, button.build_menu(2))
                osremove(path)
            else:
                await sendMessage("Failed to retrieve image.", message)
    elif data[1] == "pages":
        await query.answer()
    else:
        await query.answer()
        await message.delete()


async def tmdb_next(_, query):
    message = query.message
    user_id = message.reply_to_message.from_user.id

    _, offset, type = query.data.split()
    button = ButtonMaker()
    info = tmdb_dict.get(user_id, {})

    total = len(info)
    offset = int(offset)
    next_offset = int(offset) + 10
    prev_offset = int(offset) - 10

    page = tmdbPage(info, offset)
    await tmdb_menu_maker(type, page, button)

    await tmdb_next_buttons_maker(
        offset, next_offset, prev_offset, total, button, type, user_id
    )

    await editMessage(f"{type}", message, reply_markup=button.build_menu(2))


async def tmdb_menu_maker(type, info, button):
    if type == "discover_movie":
        for movie in info:
            title = movie["original_title"]
            id = movie["id"]
            button.cb_buildbutton(f"{title}", f"tmdbdetails^movie^{id}")
    elif type == "trending_movie":
        for movie in info:
            title = movie.title
            id = movie["id"]
            button.cb_buildbutton(f"{title}", f"tmdbdetails^movie^{id}")
    elif type == "discover_tv":
        for show in info:
            title = show["name"]
            id = show["id"]
            button.cb_buildbutton(f"{title}", f"tmdbdetails^tv^{id}")
    elif type == "trending_tv":
        for show in info:
            title = show.name
            id = show["id"]
            button.cb_buildbutton(f"{title}", f"tmdbdetails^tv^{id}")


async def pagination(button, info, type, user_id, offset=0):
    if len(info) == 0:
        button.cb_buildbutton("❌Nothing to show❌", f"next_tmdb next^pages^{user_id}")
    else:
        total = len(info)
        tmdb_dict[user_id] = info
        page = tmdbPage(info, offset)
        await tmdb_menu_maker(type, page, button)
        next_offset = int(offset) + 10

        if total <= 10:
            button.cb_buildbutton(
                f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}", 
                f"detail^pages^{user_id}",
                "footer"
            ) 
        else:
            button.cb_buildbutton(
                f"🗓 {round(int(offset) / 10) + 1} / {round(total / 10)}",
                f"detail^pages^{user_id}"
                "footer"
            )
            button.cb_buildbutton("NEXT ⏩", f"tmdbnext {next_offset} {type}", "footer")
        button.cb_buildbutton("✘ Close Menu", "tmdbdetails^close^", "footer_third")
    return button


def tmdbPage(info, offset=0, max_results=10):
    start = offset
    end = max_results + start
    total = len(info)

    if end > total:
        page = info[start:]
    elif start >= total:
        page = []
    else:
        page = info[start:end]

    return page


async def tmdb_next_buttons_maker(
    offset, next_offset, prev_offset, total, buttons, type, user_id
):
    if offset <= 0:
        buttons.cb_buildbutton(
            f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}", 
            "tmdbdetails^pages",
            "footer"
        )
        buttons.cb_buildbutton("NEXT ⏩", f"tmdbnext {next_offset} {type}", "footer")
    elif offset >= total:
        buttons.cb_buildbutton("⏪ BACK", f"tmdbnext {prev_offset} {type}", "footer")
        buttons.cb_buildbutton(
            f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}",
            "tmdbdetails^pages"
            "footer"
        )
    else:
        buttons.cb_buildbutton(
            "⏪ BACK", f"tmdbnext {prev_offset} {type}", "footer_second"
        )
        buttons.cb_buildbutton(
            f"🗓 {round(int(next_offset) / 10) + 1} / {round(total / 10)}",
            "tmdbdetails^pages",
            "footer",
        )
        buttons.cb_buildbutton(
            "NEXT ⏩", f"tmdbnext {next_offset} {type}", "footer_second"
        )
    buttons.cb_buildbutton(
        "✘ Close Menu", f"tmdbdetails^close^{user_id}", "footer_third"
    )


async def tmdb_search(_, query):
    message = query.message
    id = query.data.split("^")[1]
    await tmdbSearch(message, id)
    if id in tmdb_titles.keys():
        del tmdb_titles[id]


async def tmdb_search_api(client, query):
    message = query.message
    user_id = query.from_user.id
    button = ButtonMaker()

    question = await sendMessage(
        "Send a movie or tv name to search, /ignore to cancel", message
    )
    try:
        if response := await client.listen.Message(
            filters.text, id=filters.user(user_id), timeout=60
        ):
            if "/ignore" in response.text:
                pass
            else:
                title = response.text

                mv = Movie()
                movies = mv.search(title)
                for movie in movies:
                    button.cb_buildbutton(
                        f"[Movie] {movie.title}", f"tmdbdetails^movie^{movie.id}"
                    )

                tv = TV()
                shows = tv.search(title)
                for show in shows:
                    button.cb_buildbutton(
                        f"[TV] {show.name}", f"tmdbdetails^tv^{show.id}"
                    )

                button.cb_buildbutton(
                    "✘ Close Menu", f"tmdbdetails^close^{user_id}", "footer_third"
                )
                await sendMessage("Results found: ", message, button.build_menu(2))
    except TimeoutError:
        await sendMessage("Too late 60s gone, try again!", message)
    finally:
        await question.delete()


bot.add_handler(
    MessageHandler(
        tdmb_categories,
        filters=filters.command(BotCommands.TMDB) & (CustomFilters.owner_filter),
    )
)
bot.add_handler(
    CallbackQueryHandler(tmdb_sub_categories, filters=filters.regex("tmdbsubcat"))
)
bot.add_handler(
    CallbackQueryHandler(tmdb_get_category_info, filters=filters.regex("tdmbcatinfo"))
)
bot.add_handler(
    CallbackQueryHandler(tmdb_get_details, filters=filters.regex("tmdbdetails"))
)
bot.add_handler(CallbackQueryHandler(tmdb_next, filters=filters.regex("tmdbnext")))
bot.add_handler(CallbackQueryHandler(tmdb_search, filters=filters.regex("tdmbsearch")))
bot.add_handler(
    CallbackQueryHandler(tmdb_search_api, filters=filters.regex("tmdbsearchapi"))
)
