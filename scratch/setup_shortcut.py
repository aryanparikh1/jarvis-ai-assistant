import glob
import os
import shutil
from PIL import Image
from win32com.client import Dispatch

project_root = r"c:\study\cpp2\antigrav\Personal Assistant"
assets_icons_dir = os.path.join(project_root, "assets", "icons")
os.makedirs(assets_icons_dir, exist_ok=True)

app_data_dir = r"C:\Users\aryan\.gemini\antigravity\brain\45c9f7c3-7fae-46a5-b311-001f75e506c4"
png_files = glob.glob(os.path.join(app_data_dir, "jarvis_icon_*.png"))
ico_path = None

if png_files:
    latest_png = max(png_files, key=os.path.getctime)
    dest_png = os.path.join(assets_icons_dir, "jarvis.png")
    shutil.copy2(latest_png, dest_png)
    print("Copied icon png to:", dest_png)
    
    try:
        img = Image.open(dest_png)
        ico_path = os.path.join(assets_icons_dir, "jarvis.ico")
        img.save(ico_path, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
        print("Saved .ico file to:", ico_path)
    except Exception as e:
        print("Failed to convert icon to ICO:", e)
else:
    print("No generated icon png found.")

desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
shortcut_path = os.path.join(desktop, 'Jarvis.lnk')
shell = Dispatch('WScript.Shell')
shortcut = shell.CreateShortCut(shortcut_path)

shortcut.Targetpath = os.path.join(project_root, 'venv', 'Scripts', 'pythonw.exe')
shortcut.Arguments = os.path.join(project_root, 'main.py')
shortcut.WorkingDirectory = project_root
shortcut.Description = 'Jarvis AI Desktop Assistant'

if ico_path and os.path.exists(ico_path):
    shortcut.IconLocation = ico_path
shortcut.save()
print("Shortcut created at:", shortcut_path)
