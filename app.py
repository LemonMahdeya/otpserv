import threading
import re
import tkinter as tk
import pyperclip
from flask import Flask, request
from waitress import serve
import logging
from urllib.parse import unquote
import time
import traceback

try:
    import winsound
except:
    winsound = None

# ---------------- LOGGING ---------------- #
logging.basicConfig(
    filename="server.log",
    level=logging.ERROR,
    format="%(asctime)s %(levelname)s %(message)s"
)

# ---------------- FLASK APP ---------------- #
app = Flask(__name__)

# ---------------- GLOBAL STATE ---------------- #
alert_active = False
snooze_until = 0
popup_visible = False

# ---------------- SAFE THREAD ---------------- #
def safe_thread(target, *args):
    """
    يشغل أي دالة في thread مستقل، يعيد تشغيلها إذا حدث خطأ.
    """
    def wrapper():
        while True:
            try:
                target(*args)
            except Exception:
                logging.error(traceback.format_exc())
                time.sleep(2)
    t = threading.Thread(target=wrapper)
    t.start()
    return t

# ---------------- SOUND LOOP ---------------- #
def sound_loop():
    global alert_active, popup_visible
    while popup_visible and alert_active:
        try:
            if winsound:
                winsound.Beep(1200, 300)
        except:
            pass
        time.sleep(1)

# ---------------- ALERT MANAGER ---------------- #
def alert_manager():
    global alert_active, snooze_until, popup_visible
    while True:
        try:
            if not alert_active:
                time.sleep(1)
                continue
            now = time.time()
            if now >= snooze_until and not popup_visible:
                show_order_popup()
            time.sleep(1)
        except Exception:
            logging.error(traceback.format_exc())
            time.sleep(2)

# ---------------- ORDER POPUP ---------------- #
def show_order_popup():
    global popup_visible, snooze_until, alert_active

    def create_ui():
        global popup_visible, snooze_until, alert_active
        try:
            popup_visible = True
            root = tk.Tk()
            root.attributes("-topmost", True)
            root.overrideredirect(True)

            w, h = 600, 60
            sw = root.winfo_screenwidth()
            sh = root.winfo_screenheight()
            root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2 - 100}")
            root.configure(bg='#1a1a1a')

            frame = tk.Frame(root, bg='#1a1a1a', highlightbackground="#ff0000", highlightthickness=2)
            frame.pack(fill='both', expand=True)

            content = tk.Frame(frame, bg='#1a1a1a')
            content.pack(expand=True)

            tk.Label(content, text="⚠️", fg='#ff4444', bg='#1a1a1a', font=('Segoe UI', 16)).pack(side='left', padx=(10, 5))
            tk.Label(content, text="NEW ORDER ALERT!", fg='#ff4444', bg='#1a1a1a', font=('Segoe UI', 12, 'bold')).pack(side='left')
            tk.Label(content, text="| Check the platform now", fg='#ffffff', bg='#1a1a1a', font=('Segoe UI', 10)).pack(side='left', padx=10)

            def snooze():
                global snooze_until, popup_visible
                snooze_until = time.time() + 60
                popup_visible = False
                root.destroy()

            tk.Button(content, text="SNOOZE (1m)", command=snooze,
                      bg='#cc0000', fg='white', font=('Segoe UI', 9, 'bold'),
                      padx=15, pady=2, border=0).pack(side='left', padx=20)

            # تشغيل الصوت المتكرر في thread آمن
            safe_thread(sound_loop)

            # مراقبة terminate
            def monitor():
                if not alert_active:
                    popup_visible = False
                    root.destroy()
                    return
                root.after(500, monitor)

            monitor()
            root.mainloop()
        except Exception:
            logging.error(traceback.format_exc())
        finally:
            popup_visible = False

    safe_thread(create_ui)

# ---------------- CODE POPUP ---------------- #
def show_code_popup(code):
    def create_window():
        try:
            root = tk.Tk()
            root.overrideredirect(True)
            root.attributes("-topmost", True)
            w, h = 280, 70
            sw = root.winfo_screenwidth()
            sh = root.winfo_screenheight()
            root.geometry(f"{w}x{h}+{sw-w-20}+{sh-h-50}")
            root.configure(bg='#121212')
            f = tk.Frame(root, bg='#121212', highlightbackground="#333333", highlightthickness=1)
            f.pack(fill='both', expand=True)
            tk.Label(f, text="VERIFICATION CODE", fg='#888888', bg='#121212', font=('Segoe UI', 7, 'bold')).pack(pady=(5, 0))
            tk.Label(f, text=code, fg='#ffffff', bg='#121212', font=('Consolas', 22, 'bold')).pack(expand=True)
            pyperclip.copy(code)
            root.after(6000, root.destroy)
            root.mainloop()
        except Exception:
            logging.error(traceback.format_exc())

    safe_thread(create_window)

# ---------------- ROUTES ---------------- #
@app.route('/send')
def handle_code():
    try:
        match = re.search(r'\d{6}', unquote(request.full_path))
        if match:
            show_code_popup(match.group())
            return "OK", 200
        return "Fail", 400
    except Exception:
        logging.error(traceback.format_exc())
        return "Error", 500

@app.route('/control')
def handle_control():
    global alert_active, snooze_until
    try:
        cmd = request.args.get('cmd', '').lower()
        if 'order' in cmd:
            alert_active = True
            snooze_until = 0
            return "Activated", 200
        elif 'terminate' in cmd:
            alert_active = False
            return "Terminated", 200
        return "Invalid", 400
    except Exception:
        logging.error(traceback.format_exc())
        return "Error", 500

# ---------------- MAIN ---------------- #
if __name__ == '__main__':
    # تشغيل alert manager thread آمن
    safe_thread(alert_manager)
    serve(app, host='0.0.0.0', port=5000, threads=2)
