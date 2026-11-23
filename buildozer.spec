[app]
title = TG Forwarder
package.name = tgforwarder
package.domain = org.amir
source.dir = .
source.include_exts = py,png,jpg
version = 1.1
requirements = python3,kivy==2.3.0,telethon,openssl,libffi
orientation = portrait

android.permissions = INTERNET,FOREGROUND_SERVICE,RECEIVE_BOOT_COMPLETED,WAKE_LOCK
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.accept_sdk_license = True
android.archs = arm64-v8a
android.wakelock = True
fullscreen = 0
p4a.branch = v2024.01.21

[buildozer]
log_level = 2
warn_on_root = 1
