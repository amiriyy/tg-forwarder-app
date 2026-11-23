"""
TG Forwarder - Fon xizmat (Android Service)
Barcha Telegram xabarlarini kuzatadi va @azatov_571 ga yetkazadi.
"""
import os, asyncio
from collections import OrderedDict
from datetime import datetime, timezone, timedelta
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import (
    User, MessageActionPhoneCall,
    PhoneCallDiscardReasonMissed, PhoneCallDiscardReasonBusy,
    MessageMediaContact, MessageMediaGeo, MessageMediaGeoLive,
    MessageMediaPoll, MessageMediaVenue
)

# Android notification yangilash
try:
    from android.service import AndroidService
    service = AndroidService()
    service.setAutoRestoreEnabled(True)
except:
    pass

# ================= CONFIGURATION =================
API_ID = 38785091
API_HASH = '25bbecd9da53fb70e2b4490971203fac'
BOT_TOKEN = '9299937878:AAHoa7RX-BC-65m0ZHIhHaLUwZOYY6R9-g0'
TARGET_CHAT = '@azatov_571'
SESSION_STRING = '1ApWapzMBuyo8AzBc_5GurH5Wp4J23nO5yGwYWgR-H4vUwC6l_Pf9lDRBVcfBRpBNEOUgYCp94dMKReM56B3oq3oxlVidfvg1oWhHAtLuYwWapAd8EfqmfBDHfe7xSs_WZBQ3iyTxlE3geAjtuZioLs_ZdQbZv9lfp_swV7PY7_q0wHsPYisuMp4APcNKIlGgeb8KL_JykvbhResP6-ynoZKhxWYs-PnMs0d9Bxj3AuNN2g24o2q7I1_NEFl1tkcrIjw3JK1IoOio-kFa5cZ23kT8RMd_BE_Hq2Ie1zNMyH0MPzRhB9dEbDwD2nyvugJKzmuv1Zmd7XxPwf-LOP7Pqoy9DfshGL8='

TASHKENT_TZ = timezone(timedelta(hours=5))

class BoundedDict(OrderedDict):
    def __init__(self, maxsize=15000, *args, **kwargs):
        self.maxsize = maxsize
        super().__init__(*args, **kwargs)
    def __setitem__(self, key, value):
        if len(self) >= self.maxsize:
            self.popitem(last=False)
        super().__setitem__(key, value)

MESSAGE_MAP = BoundedDict(15000)

client = TelegramClient(
    StringSession(SESSION_STRING), API_ID, API_HASH,
    device_model='Honor HONOR X8c',
    system_version='Android 13',
    app_version='1.8.4',
    lang_code='en',
    system_lang_code='en'
)
bot = TelegramClient(StringSession(), API_ID, API_HASH)

def format_user_info(entity):
    if not entity or not isinstance(entity, User):
        return "👤 **Ismi:** Noma'lum\n🆔 **ID:** Noma'lum\n🔗 **Username:** Yo'q\n📞 **Telefon:** Yashiringan\n⭐ **Premium:** Yo'q\n🏷 **Turi:** Inson 👤"
    fn = entity.first_name or ""
    ln = entity.last_name or ""
    full = f"{fn} {ln}".strip() or "Nomsiz"
    uname = f"@{entity.username}" if entity.username else "Yo'q"
    phone = f"+{entity.phone}" if entity.phone else "Yashiringan"
    premium = "Ha ⭐️" if getattr(entity, 'premium', False) else "Yo'q"
    kind = "Bot 🤖" if getattr(entity, 'bot', False) else "Inson 👤"
    return f"👤 **Ismi:** {full}\n🆔 **ID:** `{entity.id}`\n🔗 **Username:** {uname}\n📞 **Telefon:** {phone}\n⭐ **Premium:** {premium}\n🏷 **Turi:** {kind}"

async def process_and_send(event, is_edited=False):
    try:
        if not event.is_private:
            return
        chat = await event.get_chat()
        if getattr(chat, 'username', None) in ['xabarchi571_bot']:
            return

        c_id = event.chat_id
        t = event.date.astimezone(TASHKENT_TZ).strftime("%d-%m-%Y %H:%M:%S")
        user_details = format_user_info(chat)

        # Qo'ng'iroq
        if getattr(event, 'action', None) and isinstance(event.action, MessageActionPhoneCall):
            a = event.action
            dur = getattr(a, 'duration', 0)
            reason = getattr(a, 'reason', None)
            if isinstance(reason, PhoneCallDiscardReasonMissed):
                st = "❌ O'tkazib yuborilgan"
            elif isinstance(reason, PhoneCallDiscardReasonBusy):
                st = "📵 Band (rad etildi)"
            elif dur and dur > 0:
                m, s = divmod(dur, 60)
                st = f"✅ Yakunlandi ({m}:{s:02d})"
            else:
                st = "📞 Amalga oshirildi"
            d = "Chiquvchi ↗️" if event.out else "Kiruvchi ↙️"
            await bot.send_message(TARGET_CHAT, f"📞 ══ [QO'NG'IROQ] ══\n\n{d}\nHolat: {st}\n───────────────────\n__{t}__\n\n{user_details}")
            return

        # Content
        extra = ""
        if isinstance(event.media, MessageMediaContact):
            c = event.media
            extra = f"\n📇 Kontakt: {c.first_name} {c.last_name} (+{c.phone_number})"
        elif isinstance(event.media, (MessageMediaGeo, MessageMediaGeoLive, MessageMediaVenue)):
            geo = getattr(event.media, 'geo', None)
            if geo:
                extra = f"\n📍 Lokatsiya: https://www.google.com/maps?q={geo.lat},{geo.long}"
        elif isinstance(event.media, MessageMediaPoll):
            extra = f"\n📊 So'rovnoma: {event.media.poll.question.text}"

        content = (event.text or "").strip() + extra

        if getattr(event, 'sticker', None):
            emoji = getattr(event.file, 'emoji', '') if getattr(event, 'file', None) else ''
            content = f"[🎭 Stiker {emoji}]".strip()
        elif getattr(event, 'video_note', None):
            content = "[🔵 Krujok]"
        elif getattr(event, 'voice', None):
            content = "[🎙 Ovozli xabar]"
        elif not content:
            content = "[📎 Media/Fayl]"

        if is_edited:
            header = "✏️ ══ [TAHRIRLANDI] ══"
        else:
            header = "📤 ══ [CHIQUVCHI] ══" if event.out else "💬 ══ [KIRUVCHI] ══"

        rf = getattr(chat, 'first_name', '') or ''
        rl = getattr(chat, 'last_name', '') or ''
        rname = f"{rf} {rl}".strip() or "Nomsiz"
        runame = f"@{chat.username}" if getattr(chat, 'username', None) else "Yo'q"
        rid = str(chat.id) if getattr(chat, 'id', None) else "?"

        if event.out:
            full_text = f"{header}\n\n{content}\n───────────────────\n__{t}__\n\n🎯 **Kimga:** {rname}\n🆔 **ID:** `{rid}`\n🔗 **Username:** {runame}"
        else:
            full_text = f"{header}\n\n{content}\n───────────────────\n__{t}__\n\n{user_details}"

        # Reply
        reply_id = None
        if is_edited:
            reply_id = MESSAGE_MAP.get((c_id, event.id)) or MESSAGE_MAP.get(event.id)
        else:
            orig = getattr(event, 'reply_to_msg_id', None)
            if not orig and getattr(event, 'reply_to', None):
                orig = getattr(event.reply_to, 'reply_to_msg_id', None)
            if orig:
                reply_id = MESSAGE_MAP.get((c_id, orig)) or MESSAGE_MAP.get(orig)

        if event.media and not isinstance(event.media, (MessageMediaContact, MessageMediaGeo, MessageMediaGeoLive, MessageMediaPoll)):
            path = await event.download_media()
            is_no_cap = bool(getattr(event, 'sticker', None) or getattr(event, 'video_note', None))
            try:
                if is_no_cap or len(full_text) > 1024:
                    sent = await bot.send_message(TARGET_CHAT, full_text, reply_to=reply_id)
                    await bot.send_message(TARGET_CHAT, file=path, reply_to=sent.id)
                else:
                    sent = await bot.send_message(TARGET_CHAT, full_text, file=path, reply_to=reply_id)
                MESSAGE_MAP[(c_id, event.id)] = sent.id
                MESSAGE_MAP[event.id] = sent.id
            finally:
                if path and os.path.exists(path):
                    os.remove(path)
        else:
            sent = await bot.send_message(TARGET_CHAT, full_text, reply_to=reply_id)
            MESSAGE_MAP[(c_id, event.id)] = sent.id
            MESSAGE_MAP[event.id] = sent.id

    except Exception as e:
        print(f"[ERR] {e}")

@client.on(events.NewMessage())
async def on_new(event):
    await process_and_send(event, False)

@client.on(events.MessageEdited())
async def on_edit(event):
    await process_and_send(event, True)

async def main():
    await bot.start(bot_token=BOT_TOKEN)
    await client.start(phone=lambda: (_ for _ in ()).throw(RuntimeError("Session expired!")))
    while True:
        try:
            await client.run_until_disconnected()
            await asyncio.sleep(5)
            await client.connect()
        except Exception as e:
            print(f"[ERR] {e}")
            await asyncio.sleep(10)

asyncio.run(main())
