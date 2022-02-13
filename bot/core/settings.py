# -*- coding: utf-8 -*-

from bot.uploaders.rclone_copy_transfer import rclone_copy_transfer
from telethon.tl.types import KeyboardButtonCallback
from telethon import events
from bot import SessionVars
from bot.utils.get_rclone import get_rclone
from bot.utils.list_selected_drive import list_selected_drive
import asyncio as aio
from .getVars import get_val
from functools import partial
import time, os, configparser, logging, traceback

torlog = logging.getLogger(__name__)
# logging.getLogger("telethon").setLevel(logging.DEBUG)

TIMEOUT_SEC = 60

no = "❌"
yes = "✅"
drive_icon= "☁️"
header = ""


async def handle_setting_callback(e):
    session_id = None
    conf_path = await get_config()
    data = e.data.decode()
    cmd = data.split(" ")
    val = ""

    if cmd[1] == "rclonemenu":
        # this is menu
        mmes = await e.get_message()
        await handle_settings(mmes, True, "\nBienvenido al Menu de Configuracion de Rclone. TD= Team Drive, ND= Normal Drive",
                              submenu="rclonemenu", session_id=session_id)
    elif cmd[1] == "mainmenu":
        # this is menu
        mmes = await e.get_message()
        await handle_settings(mmes, True, session_id=session_id)

    elif cmd[1] == "rcloneconfig":
        await e.answer("Envíe el archivo de configuración rclone.conf", alert=True)
        mmes = await e.get_message()
        await mmes.edit(f"{mmes.raw_text}\n/ignore para ir atras", buttons=None)
        val = await get_value(e, True)

        await general_input_manager(e, mmes, "RCLONE_CONFIG", "str", val, "rclonemenu")

    elif cmd[1] == "rclonemenucopy":
        SessionVars.update_var("ORIGIN_DIR", cmd[2])
        await handle_settings(await e.get_message(), edit=True, msg="Seleccione unidad destino", submenu="rclonemenucopy", data_cb="list_drive_dest")                         

    elif cmd[1] == "start_copy":
        torlog.info("DIR: {}".format(cmd[2]))
        SessionVars.update_var("DEST_DIR", cmd[2])
        await rclone_copy_transfer(e, conf_path)

    elif cmd[1] == "list_drive":
        SessionVars.update_var("ORIGIN_DRIVE", cmd[2])
        await handle_settings(await e.get_message(), edit=True, msg='Seleccione directorio origen', drive_name= cmd[2],submenu="list_drive", data_cb="rclonemenucopy")

    elif cmd[1] == "list_drive_dest":
        torlog.info("DIR: {}".format(cmd[2]))
        SessionVars.update_var("DEST_DRIVE", cmd[2])
        await handle_settings(await e.get_message(), edit=True, msg='Seleccione directorio destino', drive_name= cmd[2],
                              submenu="list_drive", data_cb="start_copy")

    elif cmd[1] == "list_drive_main_menu":
        base_dir = get_val("BASE_DIR")
        SessionVars.update_var("DEF_RCLONE_DRIVE", cmd[2])
        await handle_settings(await e.get_message(), edit=True, msg='Seleccione carpeta para subir', drive_name= cmd[2], rclone_dir= base_dir, submenu="list_drive", data_cb="reload_list_drive_main_menu")

    elif cmd[1] == "reload_list_drive_main_menu":
        rclone_drive = get_val("DEF_RCLONE_DRIVE")
        if cmd[2] != "/":
            rclone_route= rclone_drive + '/' + cmd[2]
        else:
            rclone_route= rclone_drive
        SessionVars.update_var("BASE_DIR", cmd[2])
        await handle_settings(await e.get_message(), edit=True, msg=f'Cambio al ruta predeterminada a {rclone_route}', drive_name= rclone_drive, rclone_dir= cmd[2], submenu="list_drive", data_cb="reload_list_drive_main_menu")     
    
    elif cmd[1] == "selfdest":
        await e.answer("Closed")
        await e.delete()


async def handle_settings(e, edit=False, msg="", drive_name="", rclone_dir='', data_cb="", submenu=None, session_id=None):
    # this function creates the menu
    # and now submenus too

    menu = []

    if submenu is None:
        await get_sub_menu("☁️ Abrir Menu Rclone ☁️", "rclonemenu", session_id, menu)
        menu.append(
            [KeyboardButtonCallback("Cerrar Menu", f"settings selfdest {session_id}".encode("UTF-8"))]
        )

        header_m = '<u>MENU CONFIGURACION</u>'

        if edit:
            rmess = await e.edit(header_m + msg,
                                 parse_mode="html", buttons=menu, link_preview=False)
        else:
            rmess = await e.reply(header_m,
                                  parse_mode="html", buttons=menu, link_preview=False)

    elif submenu == "rclonemenu":

        rcval = await get_string_variable("RCLONE_CONFIG", menu, "rcloneconfig", session_id)

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
                        menu.append(
                            [KeyboardButtonCallback(f"{prev}{j} - TD", f"settings list_drive_main_menu {j} {session_id}")]   
                        )
                    else:
                        menu.append(
                            [KeyboardButtonCallback(f"{prev}{j} - ND", f"settings list_drive_main_menu {j} {session_id}")]
                        )
        await get_sub_menu("Ir Atras ⬅️", "mainmenu", session_id, menu)

        menu.append(
            [KeyboardButtonCallback("Cerrar Menu", f"settings selfdest {session_id}".encode("UTF-8"))]
        )

        if edit:
            rmess = await e.edit(header + msg,
                                 parse_mode="html", buttons=menu, link_preview=False)


    elif submenu == "rclonemenucopy":

        #path = get_val("RCLONE_CONFIG")
        path= os.path.join(os.getcwd(), "rclone.conf")
        conf = configparser.ConfigParser()
        conf.read(path)

        for j in conf.sections():
            if "team_drive" in list(conf[j]):
                menu.append(
                    [KeyboardButtonCallback(f"{drive_icon} {j}", f"settings {data_cb} {j} {session_id} ")]
                )
            else:
                menu.append(
                    [KeyboardButtonCallback(f"{drive_icon} {j}", f"settings {data_cb} {j} {session_id}")]
                )

        menu.append(
            [KeyboardButtonCallback("Cerrar Menu", f"settings selfdest {session_id}".encode("UTF-8"))]
        )

        if edit:
            rmess = await e.edit(header + msg,
                                 parse_mode="html", buttons=menu, link_preview=False)
        else:
            rmess = await e.reply(msg,
                                  parse_mode="html", buttons=menu, link_preview=False)

    elif submenu == "list_drive":
        conf_path = await get_config()
        await list_selected_drive("/", drive_name, conf_path, rclone_dir, data_cb, menu)

        menu.append(
            [KeyboardButtonCallback("Cerrar Menu", f"settings selfdest {session_id}".encode("UTF-8"))]

        )
        if edit:
            rmess = await e.edit(msg,
                                 parse_mode="html", buttons=menu, link_preview=False)
        else:
            rmess = await e.reply(header,
                                  parse_mode="html", buttons=menu, link_preview=False)                             

# an attempt to manager all the input
async def general_input_manager(e, mmes, var_name, datatype, value, sub_menu):
    if value is not None and not "ignore" in value:
        await confirm_buttons(mmes, value)
        conf = await get_confirm(e)
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


async def get_value(e, file=False):
    # todo replace with conver. - or maybe not Fix Dont switch to conversion
    # this function gets the new value to be set from the user in current context
    lis = [False, None]

    # func tools works as expected ;);)
    cbak = partial(val_input_callback, o_sender=e.sender_id, lis=lis, file=file)

    e.client.add_event_handler(
        # lambda e: test_callback(e,lis),
        cbak,
        events.NewMessage()
    )

    start = time.time()

    while not lis[0]:
        if (time.time() - start) >= TIMEOUT_SEC:
            break

        await aio.sleep(1)

    val = lis[1]

    e.client.remove_event_handler(cbak)

    return val


async def get_confirm(e):
    # abstract for getting the confirm in a context

    lis = [False, None]
    cbak = partial(get_confirm_callback, o_sender=e.sender_id, lis=lis)

    e.client.add_event_handler(
        # lambda e: test_callback(e,lis),
        cbak,
        events.CallbackQuery(pattern="confirmsetting")
    )

    start = time.time()

    while not lis[0]:
        if (time.time() - start) >= TIMEOUT_SEC:
            break
        await aio.sleep(1)

    val = lis[1]

    e.client.remove_event_handler(cbak)

    return val


async def val_input_callback(e, o_sender, lis, file):
    # get the input value
    if o_sender != e.sender_id:
        return
    if not file:
        lis[0] = True
        lis[1] = e.text
        await e.delete()
    else:
        if e.document is not None:
            path = await e.download_media()
            lis[0] = True
            lis[1] = path
            await e.delete()
        else:
            if "ignore" in e.text:
                lis[0] = True
                lis[1] = "ignore"
                await e.delete()
            else:
                await e.delete()

    raise events.StopPropagation


async def get_confirm_callback(e, o_sender, lis):
    # handle the confirm callback

    if o_sender != e.sender_id:
        return
    lis[0] = True

    data = e.data.decode().split(" ")
    if data[1] == "true":
        lis[1] = True
    else:
        lis[1] = False


async def confirm_buttons(e, val):
    # add the confirm buttons at the bottom of the message
    await e.edit(f"Confirmar lo enviado :- <u>{val}</u>", buttons=[KeyboardButtonCallback("Yes", "confirmsetting true"),
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

        rfile= await get_rclone()

        if os.path.exists(rfile):
           val = "Se cargo el archivo personalizado. (Click para cargar otro)"
        else:
           val = "Haga clic aquí para cargar la configuración de RCLONE."

    msg = str(val)
    menu.append(
        [KeyboardButtonCallback(msg, f"settings {callback_name} {session_id}".encode("UTF-8"))]
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
