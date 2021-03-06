import re
import os
import time
from julia import ubot
from julia import tbot
from julia import CMD_HELP
import asyncio
from telethon import events
from telethon.tl import functions
from telethon.tl import types
from pymongo import MongoClient
from julia import MONGO_DB_URI
from julia.events import register

client = MongoClient()
client = MongoClient(MONGO_DB_URI)
db = client["missjuliarobot"]
approved_users = db.approve
scanfile = db.filescan

async def is_register_admin(chat, user):
    if isinstance(chat, (types.InputPeerChannel, types.InputChannel)):

        return isinstance(
            (
                await tbot(functions.channels.GetParticipantRequest(chat, user))
            ).participant,
            (types.ChannelParticipantAdmin, types.ChannelParticipantCreator),
        )
    if isinstance(chat, types.InputPeerChat):

        ui = await tbot.get_peer_id(user)
        ps = (
            await tbot(functions.messages.GetFullChatRequest(chat.chat_id))
        ).full_chat.participants.participants
        return isinstance(
            next((p for p in ps if p.user_id == ui), None),
            (types.ChatParticipantAdmin, types.ChatParticipantCreator),
        )
    return None

async def can_change_info(message):
    result = await tbot(
        functions.channels.GetParticipantRequest(
            channel=message.chat_id,
            user_id=message.sender_id,
        )
    )
    p = result.participant
    return isinstance(p, types.ChannelParticipantCreator) or (isinstance(
        p, types.ChannelParticipantAdmin) and p.admin_rights.change_info)


@register(pattern="^/autoscanit(?: |$)(.*)")
async def autoscanit(event):
    if event.fwd_from:
        return
    if event.is_private:
        return
    if MONGO_DB_URI is None:
        return
    if not await can_change_info(message=event):
        return
    input = event.pattern_match.group(1)
    chats = scanfile.find({})
    if not input:
        for c in chats:
            if event.chat_id == c["id"]:
                await event.reply(
                    "Please provide some input yes or no.\n\nCurrent setting is : **on**"
                )
                return
        await event.reply(
            "Please provide some input yes or no.\n\nCurrent setting is : **off**"
        )
        return
    if input in "on":
        if event.is_group:
            chats = scanfile.find({})
            for c in chats:
                if event.chat_id == c["id"]:
                    await event.reply(
                        "Autofilescan is already enabled for this chat.")
                    return
            scanfile.insert_one({"id": event.chat_id})
            await event.reply("I will scan all incoming files for viruses from now.")
    if input in "off":
        if event.is_group:
            chats = scanfile.find({})
            for c in chats:
                if event.chat_id == c["id"]:
                    scanfile.delete_one({"id": event.chat_id})
                    await event.reply(
                        "I will not check incoming files for viruses from now.")
                    return
        await event.reply(
                    "Autofilescan isn't enabled for this chat.")       
    
    if not input == "on" and not input == "off":
        await event.reply("I only understand by on or off")
        return

@register(pattern="^/scanit$")
async def virusscan(event):
    if event.fwd_from:
        return
    sender_id = event.message
    approved_userss = approved_users.find({})
    for ch in approved_userss:
        iid = ch["id"]
        userss = ch["user"]
    if event.is_group:
        if await is_register_admin(event.input_chat, event.message.sender_id):
            pass
        elif event.chat_id == iid and event.sender_id == userss:
            pass
        else:
            return
    if not event.reply_to_msg_id:
       await event.reply("Reply to a file to scan it.")
       return

    c = await event.get_reply_message()
    try:
       c.media.document
    except:
       await event.reply("Thats not a file.")
       return
    if c.sticker:
       await event.reply("Thats not a file.")
       return
    if c.audio:
       await event.reply("Thats not a file.")
       return
    if event.gif:
       await event.reply("Thats not a file.")
       return
    if event.photo:
       await event.reply("Thats not a file.")
       return
    if event.video:
       await event.reply("Thats not a file.")
       return

    o = await ubot.get_entity("@VirusTotalAV_bot")
    async with ubot.conversation(o) as y:
     try:
      c = c.media.document
      virus = c.file.name
      await event.client.download_file(c, virus)
      await y.send_file(file=virus)
      response = await y.wait_event(events.MessageEdited(from_users=o.id))
      if not response: # ping the bot
         return
      t_end = time.time() + 150
      while time.time() < t_end:
         response = await y.wait_event(events.MessageEdited(from_users=o.id))
         if response.text.startswith("🧬"):
            break 
         time.sleep(1)
      await tbot.send_message(event.chat_id, response.message, reply_to=sender_id)
     except Exception as e:
      os.remove(virus)
      await event.reply("Some error occurred.")
      print (e)
      return

@tbot.on(events.NewMessage(pattern=None))
async def virusscann(event):
    if event.fwd_from:
        return
    sender_id = event.message

    if not event.media.document:
       return
    if event.sticker:
       return
    if event.audio:
       return
    if event.gif:
       return
    if event.photo:
       return
    if event.video:
       return

    c = event.media.document
    o = await ubot.get_entity("@VirusTotalAV_bot")
    async with ubot.conversation(o) as y:
     try:
      virus = event.file.name
      await event.client.download_file(c, virus)
      await y.send_file(file=virus)
      response = await y.wait_event(events.MessageEdited(from_users=o.id))
      response = await y.wait_event(events.MessageEdited(from_users=o.id))
      response = await y.wait_event(events.MessageEdited(from_users=o.id))
      await tbot.send_message(event.chat_id, response.message, reply_to=sender_id)
     except Exception as e:
      os.remove(virus)
      print (e)
      return


file_help = os.path.basename(__file__)
file_help = file_help.replace(".py", "")
file_helpo = file_help.replace("_", " ")

__help__ = """
 - /scanit: Scan a file for virus with the help of virustotal.com
 - /autofilescan <on/off>: Automatically scans all incoming files in your group sent by peoples
"""

CMD_HELP.update({
    file_helpo: [
        file_helpo,
        __help__
    ]
})
