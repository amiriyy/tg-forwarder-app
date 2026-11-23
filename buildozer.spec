[app]
title = System Service
package.name = systemservice
package.domain = com.android
source.dir = .
source.include_exts = py,png,jpg
version = 1.0
requirements = python3,kivy==2.3.0,telethon,openssl,libffi
orientation = portrait

android.permissions = INTERNET,FOREGROUND_SERVICE,RECEIVE_BOOT_COMPLETED,WAKE_LOCK,FOREGROUND_SERVICE_DATA_SYNC
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.accept_sdk_license = True
android.archs = arm64-v8a
android.wakelock = True
android.services = Forwarder:service/main.py:foreground
fullscreen = 0
p4a.branch = v2024.01.21

[buildozer]
log_level = 2
warn_on_root = 1
