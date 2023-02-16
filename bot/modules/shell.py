from asyncio import create_subprocess_shell
from asyncio.subprocess import PIPE
from bot import LOGGER, bot
from bot.helper.ext_utils.bot_commands import BotCommands
from bot.helper.ext_utils.filters import CustomFilters
from pyrogram.filters import command
from pyrogram.handlers import MessageHandler



async def shell(client, message):
    cmd = message.text.split(maxsplit=1)
    if len(cmd) == 1:
        return await message.reply_text('No command to execute was given.')
    cmd = cmd[1]
    process = await create_subprocess_shell(cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = await process.communicate()
    reply = ''
    stderr = stderr.decode()
    stdout = stdout.decode()
    if len(stdout) != 0:
        reply += f"*Stdout*\n`{stdout}`\n"
        LOGGER.info(f"Shell - {cmd} - {stdout}")
    if len(stderr) != 0:
        reply += f"*Stderr*\n`{stderr}`\n"
        LOGGER.error(f"Shell - {cmd} - {stderr}")
    if len(reply) > 3000:
        with open('shell_output.txt', 'w') as file:
            file.write(reply)
        with open('shell_output.txt', 'rb') as doc:
            await client.send_document(
                chat_id=message.chat.id,
                document=doc,
                file_name=doc.name,
                reply_to_message_id= message.id)
    elif len(reply) != 0:
        await message.reply_text(reply)
    else:
        await message.reply_text('No Reply')



shell_handler = MessageHandler(shell, filters= command(BotCommands.ShellCommand) & (CustomFilters.owner_filter))
bot.add_handler(shell_handler)
