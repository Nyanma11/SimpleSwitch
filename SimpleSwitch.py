import winreg
import ctypes
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item

# --- ダークモード切り替えロジック ---
def toggle_dark_mode():
    path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_READ) as key:
            current_value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        
        # 1(ライト)なら0(ダーク)に、0なら1にする
        new_value = 0 if current_value == 1 else 1
        
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "AppsUseLightTheme", 0, winreg.REG_DWORD, new_value)
            winreg.SetValueEx(key, "SystemUsesLightTheme", 0, winreg.REG_DWORD, new_value)
        
        # Windows全体に「設定変更」を通知（エクスプローラーの白残りを防ぐ）
        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x001A
        ctypes.windll.user32.SendMessageW(HWND_BROADCAST, WM_SETTINGCHANGE, 0, "ImmersiveColorSet")
    except Exception:
        pass

# --- アイコン作成（Simple Switch 専用デザイン） ---
def create_image():
    # シンプルな白黒反転のアイコンを生成
    width, height = 64, 64
    image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    dc = ImageDraw.Draw(image)
    # 左半分を白、右半分を黒にしたスイッチ風のアイコン
    dc.pieslice((4, 4, 60, 60), 90, 270, fill=(200, 200, 200)) # 左半円
    dc.pieslice((4, 4, 60, 60), 270, 90, fill=(50, 50, 50))    # 右半円
    return image

def on_clicked(icon, item_name):
    if str(item_name) == "Switch!":
        toggle_dark_mode()
    elif str(item_name) == "Exit":
        icon.stop()

# --- アプリ起動設定 ---
icon = pystray.Icon("SimpleSwitch")
icon.icon = create_image()
icon.title = "Simple Switch (Click to toggle)"

# メニュー構成
icon.menu = pystray.Menu(
    item('Switch!', on_clicked, default=True), 
    item('Exit', on_clicked)
)

print("Simple Switch が起動しました。")
icon.run()