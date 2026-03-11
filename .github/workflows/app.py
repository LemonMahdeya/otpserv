%%writefile app.py
import threading
import re
import tkinter as tk
import pyperclip
from flask import Flask, request
from waitress import serve
import logging
from urllib.parse import unquote
import time
# ملاحظة: winsound لن تعمل داخل كولاب (لينكس) ولكن ستعمل في الـ EXE على ويندوز
try:
    import winsound
except ImportError:
    winsound = None

app = Flask(__name__)

# متغيرات التحكم
alert_active = False
snooze_until = 0

def play_alert_sound():
    global alert_active
    while alert_active:
        if time.time() > snooze_until:
            if winsound:
                winsound.Beep(1000, 500)
                time.sleep(0.1)
                winsound.Beep(1200, 500)
            else:
                print("Sound Alert Triggered (No winsound on Linux)")
        time.sleep(1)

def show_order_popup():
    global alert_active, snooze_until
    def on_snooze():
        global snooze_until
        snooze_until = time.time() + 60
        
    def create_alert_ui():
        try:
            root = tk.Tk()
            root.attributes("-topmost", True)
            root.overrideredirect(True)
            w, h = 500, 250
            sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
            root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
            root.configure(bg='#1a1a1a')
            frame = tk.Frame(root, bg='#1a1a1a', highlightbackground="#ff0000", highlightthickness=3)
            frame.pack(fill='both', expand=True)
            tk.Label(frame, text="⚠️ تنبيه جديد ⚠️", fg='#ff4444', bg='#1a1a1a', font=('Segoe UI', 20, 'bold')).pack(pady=20)
            tk.Label(frame, text="يوجد طلب جديد على المنصة!", fg='#ffffff', bg='#1a1a1a', font=('Segoe UI', 14)).pack(pady=10)
            tk.Button(frame, text="إيقاف الصوت مؤقتاً (1 دقيقة)", command=on_snooze, bg='#cc0000', fg='white', font=('Segoe UI', 10, 'bold'), padx=20, pady=10).pack(pady=20)
            def check():
                if not alert_active: root.destroy()
                else: root.after(500, check)
            check()
            root.mainloop()
        except: pass
    threading.Thread(target=create_alert_ui, daemon=True).start()

def show_code_popup(code):
    def create_window():
        try:
            root = tk.Tk()
            root.overrideredirect(True)
            root.attributes("-topmost", True)
            width, height = 300, 90
            sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
            root.geometry(f"{width}x{height}+{sw - width - 20}+{sh - height - 50}")
            root.configure(bg='#121212')
            f = tk.Frame(root, bg='#121212', highlightbackground="#333333", highlightthickness=1)
            f.pack(fill='both', expand=True)
            tk.Label(f, text="NEW VERIFICATION CODE", fg='#888888', bg='#121212', font=('Segoe UI', 8, 'bold')).pack(pady=(10, 0))
            tk.Label(f, text=code, fg='#ffffff', bg='#121212', font=('Consolas', 24, 'bold')).pack(expand=True)
            pyperclip.copy(code)
            root.after(6000, root.destroy)
            root.mainloop()
        except: pass
    threading.Thread(target=create_window, daemon=True).start()

@app.route('/send')
def handle_code():
    match = re.search(r'\d{6}', unquote(request.full_path))
    if match:
        show_code_popup(match.group())
        return "OK", 200
    return "No code", 400

@app.route('/control')
def handle_control():
    global alert_active, snooze_until
    cmd = request.args.get('cmd', '').lower()
    if 'order' in cmd:
        if not alert_active:
            alert_active = True
            snooze_until = 0
            show_order_popup()
            threading.Thread(target=play_alert_sound, daemon=True).start()
        return "Activated", 200
    elif 'terminate' in cmd:
        alert_active = False
        return "Terminated", 200
    return "Invalid", 400

if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5000, threads=4)