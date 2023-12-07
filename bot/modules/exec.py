from asyncio import create_subprocess_shell, subprocess
from bot import bot
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from pyrogram.filters import command
from pyrogram.handlers import MessageHandler


async def execute(client, message):
    cmd = message.text.split(maxsplit=1)
    if len(cmd) == 1:
        await message.reply_text("No command to execute was given.")
        return
    cmd = cmd[1]
    process = await create_subprocess_shell(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    e = stderr.decode()
    if not e:
        e = "No Error"
    o = stdout.decode()
    if not o:
        o = "No Output"
    else:
        _o = o.split("\n")
        o = "`\n".join(_o)
    OUTPUT = f"**QUERY:**\n__Command:__\n`{cmd}` \n__PID:__\n`{process.pid}`\n\n**stderr:** \n`{e}`\n**Output:**\n{o}"
    if len(OUTPUT) > 3900:
        with open("exec.txt", "w") as out_file:
            out_file.write(str(OUTPUT))
        with open("exec.txt", "rb") as doc:
            await client.send_document(
                chat_id=message.chat.id,
                document=doc,
                file_name=doc.name,
                reply_to_message_id=message.id,
            )
    elif len(OUTPUT) != 0:
        await message.reply_text(OUTPUT)
    else:
        await message.reply_text("No Reply")


exec_handler = MessageHandler(
    execute, filters=command(BotCommands.ExecCommand) & (CustomFilters.owner_filter)
)
bot.add_handler(exec_handler)
