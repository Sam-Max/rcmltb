# -*- coding: utf-8 -*-

from bot.core.set_vars import set_val
from bot.uploaders.rclone_transfer import rclone_copy_transfer
from telethon.tl.types import KeyboardButtonCallback
from telethon import events
from bot import SessionVars
from bot.utils.list_selected_drive import list_selected_drive
from bot.utils.list_selected_drive_copy_menu import list_selected_drive_copy
from ..get_vars import get_val
from functools import partial
import time, os, configparser, logging, traceback

torlog = logging.getLogger(__name__)
# logging.getLogger("telethon").setLevel(logging.DEBUG)

TIMEOUT_SEC = 60

no = "❌"
yes = "✅"
drive_icon= "☁️"
header = ""


async def handle_settings_copy_menu(query, mmes="", drive_base="", edit=False, msg="", drive_name="", rclone_dir='', data_cb="", submenu=None, session_id=None, is_main_m= True, is_dest_drive= False):
    menu = []

    if submenu is None:
        rcval = await get_string_variable("RCLONE_CONFIG", menu, "load_rclone_config", session_id)

        if rcval != "None":
            # create a all drives menu
            if "Se cargo el archivo personalizado." in rcval:

                #path= get_val("RCLONE_CONFIG")
                path= os.path.join(os.getcwd(), "rclone.conf")
                conf = configparser.ConfigParser()
                conf.read(path)

                def_drive = get_val("DEF_RCLONE_DRIVE")

                for j in conf.sections():
                    prev = ""
                    if j == def_drive:
                        prev = yes

                    if "team_drive" in list(conf[j]):
                        set_val("DEF_RCLONE_DRIVE", j)
                        menu.append(
                            [KeyboardButtonCallback(f"{prev}{j} - TD", f"setting^list_drive_main_menu^{j}")]   
                        )
                    else:
                        menu.append(
                            [KeyboardButtonCallback(f"{prev}{j} - ND", f"setting^list_drive_main_menu^{j}")]
                        )
        await get_sub_menu("Ir Atras ⬅️", "mainmenu", session_id, menu)

        menu.append(
            [KeyboardButtonCallback("Cerrar Menu", f"settings^selfdest")]
        )
        base_dir= get_val("BASE_DIR")
        rclone_drive = get_val("DEF_RCLONE_DRIVE")
        msg= f"Seleccione la unidad en la que quiere guardar los archivos\n\nRuta:`{rclone_drive}:{base_dir}`"

        await query.reply(header + msg, parse_mode="md", buttons=menu, link_preview=False)


    elif submenu == "rclone_menu_copy":
        #path = get_val("RCLONE_CONFIG")
        path= os.path.join(os.getcwd(), "rclone.conf")
        conf = configparser.ConfigParser()
        conf.read(path)

        for j in conf.sections():
            if "team_drive" in list(conf[j]):
                menu.append(
                    [KeyboardButtonCallback(f"{j} - TD", f"settings^{data_cb}^{j}")]
                )
            else:
                menu.append(
                    [KeyboardButtonCallback(f"{j} - ND", f"settings^{data_cb}^{j}")]
                )

        menu.append(
            [KeyboardButtonCallback("Cerrar Menu", f"settings^selfdest")]
        )

        if edit:
            rmess = await mmes.edit(header + msg,
                                 parse_mode="html", buttons=menu, link_preview=False)
        else:
            rmess = await query.reply(msg,
                                  parse_mode="html", buttons=menu, link_preview=False)

    elif submenu == "list_drive":
        conf_path = await get_config()

        if is_main_m:
            logging.info("bbbbbbbbbbbbbbbbbbbbbb")
            await list_selected_drive(query, drive_base, drive_name, conf_path, rclone_dir, data_cb, menu, is_main_m= is_main_m)
        else:
            logging.info("ssssssssssssssssssssss")
            await list_selected_drive_copy(query, drive_base, drive_name, conf_path, rclone_dir, data_cb, menu, is_main_m= is_main_m, is_dest_drive= is_dest_drive)    

        menu.append(
            [KeyboardButtonCallback("Cerrar Menu", f"settings^selfdest")]

        )
        if edit:
            rmess = await mmes.edit(msg,
                                 parse_mode="md", buttons=menu, link_preview=False)
        else:
            rmess = await query.reply(header,
                                  parse_mode="md", buttons=menu, link_preview=False)

# an attempt to manager all the input
async def general_input_manager(callback_query, mmes, var_name, datatype, value, sub_menu):
    if value is not None and not "ignore" in value:
        await confirm_buttons(mmes, value)
        conf = await get_confirm(callback_query)
        if conf is not None:
            if conf:
                try:
                    if datatype == "int":
                        value = int(value)
                    if datatype == "str":
                        value = str(value)
                    if datatype == "bool":
                        if value.lower() == "true":
                            value = True
                        elif value.lower() == "false":
                            value = False
                        else:
                            raise ValueError("Invalid value from bool")

                    if var_name == "RCLONE_CONFIG":
                        # adjust the special case
                        try:
                            conf = configparser.ConfigParser()
                            conf.read(value)

                            for i in conf.sections():
                                SessionVars.update_var("DEF_RCLONE_DRIVE", str(i))
                                break

                            SessionVars.update_var("RCLONE_CONFIG", os.path.join(os.getcwd(), value))

                        except Exception:
                            torlog.error(traceback.format_exc())
                            await handle_settings(mmes, True, f"<b><u>The conf file is invalid check logs.</b></u>",
                                                  sub_menu)
                            return

                    else:
                        SessionVars.update_var(var_name, value)

                    await handle_settings(mmes, True,
                                          f"<b><u>Recibido {var_name} valor '{value}'.</b></u>", sub_menu)
                except ValueError:
                    await handle_settings(mmes, True,
                                          f"<b><u>Value [{value}] not valid try again and enter {datatype}.</b></u>",
                                          sub_menu)
            else:
                await handle_settings(mmes, True, f"<b><u>Confirm differed by user.</b></u>", sub_menu)
        else:
            await handle_settings(mmes, True, f"<b><u>Confirm timed out [waited 60s for input].</b></u>", sub_menu)
    else:
        await handle_settings(mmes, True, f"<b><u>Entry Timed out [waited 60s for input]. OR else ignored.</b></u>",
                              sub_menu)


async def get_value(callback_query, file=False):
    # todo replace with conver. - or maybe not Fix Dont switch to conversion
    # this function gets the new value to be set from the user in current context
    lis = [False, None]

    # func tools works as expected ;);)
    cbak = partial(val_input_callback, o_sender=callback_query.sender_id, lis=lis, file=file)

    callback_query.client.add_event_handler(
        # lambda callback_query: test_callback(callback_query,lis),
        cbak,
        events.NewMessage()
    )

    start = time.time()

    while not lis[0]:
        if (time.time() - start) >= TIMEOUT_SEC:
            break

        await aio.sleep(1)

    val = lis[1]

    callback_query.client.remove_event_handler(cbak)

    return val


async def get_confirm(callback_query):
    # abstract for getting the confirm in a context

    lis = [False, None]
    cbak = partial(get_confirm_callback, o_sender=callback_query.sender_id, lis=lis)

    callback_query.client.add_event_handler(
        # lambda callback_query: test_callback(callback_query,lis),
        cbak,
        events.CallbackQuery(pattern="confirmsetting")
    )

    start = time.time()

    while not lis[0]:
        if (time.time() - start) >= TIMEOUT_SEC:
            break
        await aio.sleep(1)

    val = lis[1]

    callback_query.client.remove_event_handler(cbak)

    return val


async def val_input_callback(callback_query, o_sender, lis, file):
    # get the input value
    if o_sender != callback_query.sender_id:
        return
    if not file:
        lis[0] = True
        lis[1] = callback_query.text
        await callback_query.delete()
    else:
        if callback_query.document is not None:
            path = await callback_query.download_media()
            lis[0] = True
            lis[1] = path
            await callback_query.delete()
        else:
            if "ignore" in callback_query.text:
                lis[0] = True
                lis[1] = "ignore"
                await callback_query.delete()
            else:
                await callback_query.delete()

    raise events.StopPropagation


async def get_confirm_callback(callback_query, o_sender, lis):
    # handle the confirm callback

    if o_sender != callback_query.sender_id:
        return
    lis[0] = True

    data = callback_query.data.decode().split(" ")
    if data[1] == "true":
        lis[1] = True
    else:
        lis[1] = False


async def confirm_buttons(callback_query, val):
    # add the confirm buttons at the bottom of the message
    await callback_query.edit(f"Confirmar lo enviado :- <u>{val}</u>", buttons=[KeyboardButtonCallback("Yes", "confirmsetting true"),
                                                                KeyboardButtonCallback("No", "confirmsetting false")],
                 parse_mode="html")


async def get_bool_variable(var_name, msg, menu, callback_name, session_id):
    # handle the vars having bool values

    val = get_val(var_name)

    if val:
        # setting the value in callback so calls will be reduced ;)
        menu.append(
            [KeyboardButtonCallback(yes + msg, f"settings {callback_name} false {session_id}".encode("UTF-8"))]
        )
    else:
        menu.append(
            [KeyboardButtonCallback(no + msg, f"settings {callback_name} true {session_id}".encode("UTF-8"))]
        )


async def get_sub_menu(msg, sub_name, session_id, menu):
    menu.append(
        [KeyboardButtonCallback(msg, f"settings {sub_name} {session_id}".encode("UTF-8"))]
    )


async def get_string_variable(var_name, menu, callback_name, session_id):
    # handle the vars having string value
    # condition for rclone config

    # val = SessionVars.get_var(var_name)

    # if var_name == "RCLONE_CONFIG":
    #     if val is not None:
    #         val = "Se cargo el archivo personalizado. (Click para cargar otro)"
    #     else:
    #         val = "Haga clic aquí para cargar la configuración de RCLONE."


    if var_name == "RCLONE_CONFIG":

        rfile= os.path.join(os.getcwd(), "rclone.conf")

        if os.path.exists(rfile):
           val = "Se cargo el archivo personalizado. (Click para cargar otro)"
        else:
           val = "Haga clic aquí para cargar la configuración de RCLONE."

    msg = str(val)
    menu.append(
        [KeyboardButtonCallback(msg, f"settings {callback_name}".encode("UTF-8"))]
    )

    # Just in case
    return val


async def get_int_variable(var_name, menu, callback_name, session_id):
    # handle the vars having string value

    val = get_val(var_name)
    msg = var_name + " " + str(val)
    menu.append(
        [KeyboardButtonCallback(msg, f"settings {callback_name} {session_id}".encode("UTF-8"))]
    )

    # todo handle the list value


async def get_config():
    config = os.path.join(os.getcwd(), "rclone.conf")
    if isinstance(config, str):
        if os.path.exists(config):
            return config

    return None
