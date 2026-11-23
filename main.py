"""
TG Forwarder - Android Native App
Fonda barqaror ishlaydi, jonli loglar va holatni ko'rsatadi.
"""
import os
import sys
import threading
import asyncio
from datetime import datetime, timezone, timedelta
from collections import OrderedDict

# Kivy komponentlari
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import platform

# Telethon
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import (
    User, MessageActionPhoneCall,
    PhoneCallDiscardReasonMissed, PhoneCallDiscardReasonBusy,
    MessageMediaContact, MessageMediaGeo, MessageMediaGeoLive,
    MessageMediaPoll, MessageMediaVenue
)

# Qora/to'q zamonaviy fon
Window.clearcolor = (0.1, 0.12, 0.15, 1)

# ================= SOZLAMALAR =================
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


class TGForwarderApp(App):
    def build(self):
        self.title = "TG Forwarder"
        self.running = False
        self.loop = None
        self.wake_lock = None

        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)

        # Sarlavha
        title = Label(
            text="⚡ TG Forwarder",
            font_size='22sp',
            bold=True,
            size_hint_y=None,
            height=45,
            color=(0.3, 0.75, 1, 1)
        )
        layout.add_widget(title)

        # Holat indikatori
        self.status_label = Label(
            text="● Boshlanmoqda...",
            font_size='16sp',
            bold=True,
            size_hint_y=None,
            height=35,
            color=(1, 0.8, 0.2, 1)
        )
        layout.add_widget(self.status_label)

        # Tugmalar paneli
        btn_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        
        self.btn_toggle = Button(
            text="⏹ To'xtatish",
            font_size='15sp',
            background_color=(0.8, 0.2, 0.2, 1)
        )
        self.btn_toggle.bind(on_press=self.toggle_service)
        btn_layout.add_widget(self.btn_toggle)

        btn_minimize = Button(
            text="📱 Orqa fonga olish",
            font_size='15sp',
            background_color=(0.2, 0.5, 0.8, 1)
        )
        btn_minimize.bind(on_press=self.minimize_app)
        btn_layout.add_widget(btn_minimize)

        layout.add_widget(btn_layout)

        # Jonli loglar oynasi
        log_title = Label(
            text="Jonli hisobot (Loglar):",
            font_size='13sp',
            size_hint_y=None,
            height=25,
            color=(0.7, 0.7, 0.7, 1)
        )
        layout.add_widget(log_title)

        scroll = ScrollView(size_hint=(1, 1))
        self.log_text = Label(
            text="[Dastur ochildi]\n",
            font_size='12sp',
            size_hint_y=None,
            halign='left',
            valign='top',
            color=(0.4, 1, 0.5, 1)
        )
        self.log_text.bind(width=lambda *x: setattr(self.log_text, 'text_size', (self.log_text.width, None)))
        self.log_text.bind(texture_size=lambda *x: setattr(self.log_text, 'height', self.log_text.texture_size[1]))
        scroll.add_widget(self.log_text)
        layout.add_widget(scroll)

        # Android Wakelock faollashtirish
        self.acquire_wakelock()

        # Avtomatik ishga tushirish
        Clock.schedule_once(lambda dt: self.start_forwarder(), 1)

        return layout

    def log(self, msg):
        now = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{now}] {msg}"
        print(formatted)
        Clock.schedule_once(lambda dt: self._append_log(formatted))

    def _append_log(self, text):
        lines = self.log_text.text.split('\n')
        if len(lines) > 100:
            lines = lines[-80:]
        lines.append(text)
        self.log_text.text = '\n'.join(lines)

    def set_status(self, text, color):
        Clock.schedule_once(lambda dt: self._set_status(text, color))

    def _set_status(self, text, color):
        self.status_label.text = text
        self.status_label.color = color

    def acquire_wakelock(self):
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                activity = PythonActivity.mActivity
                Context = autoclass('android.content.Context')
                pm = activity.getSystemService(Context.POWER_SERVICE)
                # 1 = PARTIAL_WAKE_LOCK (ekran o'chsa ham CPU va tarmoq uxlamaydi)
                self.wake_lock = pm.newWakeLock(1, 'tgforwarder:wakelock')
                self.wake_lock.acquire()
                self.log("✅ Android WakeLock faollashtirildi (fondan o'chmaydi)")
            except Exception as e:
                self.log(f"⚠️ WakeLock ogohlantirish: {e}")

    def minimize_app(self, instance):
        self.log("📱 Ilova orqa fonga o'tkazildi (ishlashda davom etadi)")
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                PythonActivity.mActivity.moveTaskToBack(True)
            except Exception as e:
                self.log(f"Minimize xato: {e}")

    def toggle_service(self, instance):
        if self.running:
            self.stop_forwarder()
        else:
            self.start_forwarder()

    def start_forwarder(self):
        if self.running:
            return
        self.running = True
        self.btn_toggle.text = "⏹ To'xtatish"
        self.btn_toggle.background_color = (0.8, 0.2, 0.2, 1)
        self.set_status("● Ulanmoqda...", (1, 0.8, 0.2, 1))
        self.thread = threading.Thread(target=self._run_thread, daemon=True)
        self.thread.start()

    def stop_forwarder(self):
        self.running = False
        self.btn_toggle.text = "▶ Ishga tushirish"
        self.btn_toggle.background_color = (0.2, 0.8, 0.3, 1)
        self.set_status("● To'xtatilgan", (0.8, 0.3, 0.3, 1))
        self.log("[!] Dastur to'xtatildi.")

    def _run_thread(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._async_main())
        except Exception as e:
            self.log(f"❌ Xatolik: {e}")
            self.set_status(f"● Xatolik: {e}", (1, 0.3, 0.3, 1))
            self.running = False

    async def _async_main(self):
        self.log("🔄 Telegram mijozlari yaratilmoqda...")
        client = TelegramClient(
            StringSession(SESSION_STRING), API_ID, API_HASH,
            device_model='Honor HONOR X8c',
            system_version='Android 13',
            app_version='1.8.4',
            lang_code='en',
            system_lang_code='en'
        )
        bot = TelegramClient(StringSession(), API_ID, API_HASH)

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
                    self.log(f"[+] Qo'ng'iroq yetkazildi: {st}")
                    return

                # Kontent
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
                        self.log(f"[+] Media yetkazildi: {'Chiquvchi' if event.out else 'Kiruvchi'}")
                    finally:
                        if path and os.path.exists(path):
                            os.remove(path)
                else:
                    sent = await bot.send_message(TARGET_CHAT, full_text, reply_to=reply_id)
                    MESSAGE_MAP[(c_id, event.id)] = sent.id
                    MESSAGE_MAP[event.id] = sent.id
                    self.log(f"[+] Xabar yetkazildi: {'Chiquvchi' if event.out else 'Kiruvchi'}")

            except Exception as e:
                self.log(f"⚠️ Xabar yuborishda xato: {e}")

        @client.on(events.NewMessage())
        async def on_new(event):
            await process_and_send(event, False)

        @client.on(events.MessageEdited())
        async def on_edit(event):
            await process_and_send(event, True)

        await bot.start(bot_token=BOT_TOKEN)
        bot_me = await bot.get_me()
        self.log(f"✅ Bot tayyor: @{bot_me.username}")

        await client.start(phone=lambda: (_ for _ in ()).throw(RuntimeError("Session expired!")))
        me = await client.get_me()
        self.log(f"✅ 1-akkaunt faol: {me.first_name}")

        self.set_status("● Faol ishlamoqda (24/7)", (0.2, 1, 0.3, 1))
        self.log("🚀 [MONITORING BOSHLANDI] Xabarlar kutilyapti...")

        while self.running:
            try:
                await client.run_until_disconnected()
                if self.running:
                    self.log("⚠️ Aloqa uzildi, 5 soniyada qayta ulanmoqda...")
                    await asyncio.sleep(5)
                    await client.connect()
            except Exception as e:
                self.log(f"⚠️ Aloqa xatosi: {e}")
                await asyncio.sleep(10)

        await client.disconnect()
        await bot.disconnect()
        self.log("⏹ Barcha ulanishlar yopildi.")

if __name__ == '__main__':
    TGForwarderApp().run()
