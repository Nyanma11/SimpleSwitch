import winreg
import ctypes
import sys
import threading
import time
import json
import os
import schedule
import customtkinter as ctk 
from tkinter import messagebox
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item

# バージョン情報
VERSION_LABEL = "v1.1.0"
VERSION_FULL = "version 1.1.0"

# 設定ファイルの保存先
CONFIG_FILE = os.path.join(os.environ["APPDATA"], "SimpleSwitch_config.json")

# --- モダンGUIの基本設定 ---
ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")

def load_config():
    default_config = {"light_time": "08:00", "dark_time": "20:00", "enabled": True}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                if "enabled" not in config: config["enabled"] = True
                return config
        except: return default_config
    return default_config

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

def get_is_dark_mode():
    path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_READ) as key:
            current, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        return current == 0
    except: return False

def set_mode(to_dark):
    path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
    new_value = 0 if to_dark else 1
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "AppsUseLightTheme", 0, winreg.REG_DWORD, new_value)
            winreg.SetValueEx(key, "SystemUsesLightTheme", 0, winreg.REG_DWORD, new_value)
        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x001A
        ctypes.windll.user32.SendMessageW(HWND_BROADCAST, WM_SETTINGCHANGE, 0, "ImmersiveColorSet")
    except Exception: pass

def create_icon_image(size=64):
    image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    dc = ImageDraw.Draw(image)
    dc.pieslice((4, 4, size-4, size-4), 90, 270, fill=(200, 200, 200)) 
    dc.pieslice((4, 4, size-4, size-4), 270, 90, fill=(50, 50, 50))    
    return image

# --- 設定画面 ---
def open_settings():
    config = load_config()
    
    root = ctk.CTk()
    # ウィンドウ上部のタイトルを修正
    root.title(f"Simple Switch {VERSION_LABEL}")
    root.geometry("460x450")
    root.attributes("-topmost", True)

    header_frame = ctk.CTkFrame(root, fg_color="transparent")
    header_frame.pack(pady=(30, 20))

    icon_pil = create_icon_image(120)
    ctk_icon = ctk.CTkImage(light_image=icon_pil, dark_image=icon_pil, size=(40, 40))

    # アイコンクリックでの切り替え
    icon_btn = ctk.CTkButton(header_frame, image=ctk_icon, text="", width=40, height=40,
                             fg_color="transparent", hover_color=("#ebebeb", "#323232"),
                             command=lambda: set_mode(not get_is_dark_mode()))
    icon_btn.grid(row=0, column=0, padx=10)

    label_title = ctk.CTkLabel(header_frame, text="Simple Switch", font=("Arial", 32, "bold"))
    label_title.grid(row=0, column=1, padx=10)

    enabled_var = ctk.BooleanVar(value=config["enabled"])
    switch = ctk.CTkSwitch(root, text="スケジュール自動実行", variable=enabled_var, font=("MS Gothic", 17))
    switch.pack(pady=15)

    input_frame = ctk.CTkFrame(root, fg_color="transparent")
    input_frame.pack(pady=15)

    ctk.CTkLabel(input_frame, text="☀️ ライト", font=("MS Gothic", 15)).grid(row=0, column=0, padx=20, pady=5)
    light_entry = ctk.CTkEntry(input_frame, placeholder_text="08:00", width=110, height=40, justify="center", font=("Arial", 18))
    light_entry.insert(0, config["light_time"])
    light_entry.grid(row=1, column=0, padx=20, pady=5)

    ctk.CTkLabel(input_frame, text="🌙 ダーク", font=("MS Gothic", 15)).grid(row=0, column=1, padx=20, pady=5)
    dark_entry = ctk.CTkEntry(input_frame, placeholder_text="20:00", width=110, height=40, justify="center", font=("Arial", 18))
    dark_entry.insert(0, config["dark_time"])
    dark_entry.grid(row=1, column=1, padx=20, pady=5)

    def on_save():
        new_config = {"light_time": light_entry.get(), "dark_time": dark_entry.get(), "enabled": enabled_var.get()}
        save_config(new_config)
        messagebox.showinfo("Success", "設定を保存しました！")
        root.destroy()

    save_button = ctk.CTkButton(root, text="設定を保存して閉じる", 
                                command=on_save, corner_radius=10, font=("MS Gothic", 17, "bold"),
                                height=55, width=220)
    save_button.pack(pady=(30, 10))
    
    # 画面右下の表示は「version 1.1.0」を維持
    version_label = ctk.CTkLabel(root, text=VERSION_FULL, font=("Arial", 11), text_color="gray50")
    version_label.pack(side="bottom", anchor="e", padx=15, pady=10)
    
    root.mainloop()

# --- システム処理 ---
def run_schedule():
    while True:
        config = load_config()
        if config["enabled"]:
            schedule.clear()
            schedule.every().day.at(config["light_time"]).do(set_mode, to_dark=False)
            schedule.every().day.at(config["dark_time"]).do(set_mode, to_dark=True)
            schedule.run_pending()
        time.sleep(30)

def on_clicked(icon, item_name):
    if str(item_name) == "Switch!":
        set_mode(not get_is_dark_mode())
    elif str(item_name) == "設定":
        threading.Thread(target=open_settings, daemon=True).start()
    elif str(item_name) == "終了":
        icon.stop()

if __name__ == "__main__":
    instance_name = f"Global\\SimpleSwitch_{VERSION_LABEL.replace('.', '_')}"
    kernel32 = ctypes.windll.kernel32
    mutex = kernel32.CreateMutexW(None, False, instance_name)
    if kernel32.GetLastError() == 183: sys.exit()

    threading.Thread(target=run_schedule, daemon=True).start()

    icon = pystray.Icon("SimpleSwitch")
    icon.icon = create_icon_image()
    # ツールチップはシンプルに「Simple Switch」
    icon.title = "Simple Switch"
    
    icon.menu = pystray.Menu(
        item('Switch!', on_clicked, default=True),
        item('設定', on_clicked),
        item('終了', on_clicked)
    )
    icon.run()