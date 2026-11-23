"""
TG Forwarder - Android App
Ochilganda xizmatni ishga tushiradi va o'zi yopiladi.
"""
from kivy.app import App
from kivy.uix.label import Label
from kivy.clock import Clock
from android import AndroidService
import os

class TGForwarderApp(App):
    def build(self):
        # Fon xizmatini ishga tushirish
        self.start_service()
        # 2 soniyada app o'zini yopadi
        Clock.schedule_once(self.stop_app, 2)
        return Label(text='TG Forwarder ishga tushmoqda...')

    def start_service(self):
        from android import AndroidService
        service = AndroidService('TG Forwarder', 'Xabarlar kuzatilmoqda')
        service.start('start')
        self.service = service

    def stop_app(self, dt):
        # App o'zini yopadi, xizmat fonda qoladi
        from android.runnable import run_on_ui_thread
        import android
        android.mActivity.moveTaskToBack(True)

if __name__ == '__main__':
    TGForwarderApp().run()
