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
import queue

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

app = Flask(__name__)

# ---------------- GLOBAL STATE ---------------- #

alert_active = False
snooze_until = 0

popup_queue = queue.Queue()
popup_running = False

# ---------------- ALERT MANAGER ---------------- #

def alert_manager():

    global alert_active, snooze_until, popup_running

    while True:

        try:

            if not alert_active:
                time.sleep(1)
                continue

            now = time.time()

            if now >= snooze_until:

                if not popup_running:
                    popup_queue.put(("order", None))

                    if winsound:
                        try:
                            winsound.Beep(1000, 300)
                        except:
                            pass

            time.sleep(1)

        except Exception:
            logging.error(traceback.format_exc())
            time.sleep(2)


# ---------------- POPUP WORKER ---------------- #

def popup_worker():

    global popup_running

    while True:

        try:

            task, data = popup_queue.get()

            if task == "order":
                show_order_popup()

            elif task == "code":
                show_code_popup(data)

        except Exception:
            logging.error(traceback.format_exc())


# ---------------- ORDER POPUP ---------------- #

def show_order_popup():

    global snooze_until, popup_running

    if popup_running:
        return

    popup_running = True

    def snooze():
    global snooze_until, popup_running

    snooze_until = time.time() + 60
    popup_running = False
    root.destroy()

    try:

        root = tk.Tk()
        root.attributes("-topmost", True)
        root.overrideredirect(True)

        w, h = 600, 60
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()

        root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2 - 100}")
        root.configure(bg='#1a1a1a')

        frame = tk.Frame(
            root,
            bg='#1a1a1a',
            highlightbackground="#ff0000",
            highlightthickness=2
        )
        frame.pack(fill='both', expand=True)

        content = tk.Frame(frame, bg='#1a1a1a')
        content.pack(expand=True)

        tk.Label(
            content,
            text="⚠️",
            fg='#ff4444',
            bg='#1a1a1a',
            font=('Segoe UI', 16)
        ).pack(side='left', padx=(10, 5))

        tk.Label(
            content,
            text="NEW ORDER ALERT!",
            fg='#ff4444',
            bg='#1a1a1a',
            font=('Segoe UI', 12, 'bold')
        ).pack(side='left')

        tk.Label(
            content,
            text="| Check platform",
            fg='#ffffff',
            bg='#1a1a1a',
            font=('Segoe UI', 10)
        ).pack(side='left', padx=10)

        tk.Button(
            content,
            text="SNOOZE",
            command=snooze,
            bg='#cc0000',
            fg='white',
            font=('Segoe UI', 9, 'bold'),
            padx=15,
            pady=2,
            border=0
        ).pack(side='left', padx=20)

        root.mainloop()

    except Exception:
        logging.error(traceback.format_exc())

    finally:
        popup_running = False


# ---------------- CODE POPUP ---------------- #

def show_code_popup(code):

    try:

        root = tk.Tk()
        root.overrideredirect(True)
        root.attributes("-topmost", True)

        w, h = 280, 70
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()

        root.geometry(f"{w}x{h}+{sw-w-20}+{sh-h-50}")
        root.configure(bg='#121212')

        f = tk.Frame(
            root,
            bg='#121212',
            highlightbackground="#333",
            highlightthickness=1
        )
        f.pack(fill='both', expand=True)

        tk.Label(
            f,
            text="VERIFICATION CODE",
            fg='#888',
            bg='#121212',
            font=('Segoe UI', 7, 'bold')
        ).pack(pady=(5, 0))

        tk.Label(
            f,
            text=code,
            fg='#fff',
            bg='#121212',
            font=('Consolas', 22, 'bold')
        ).pack(expand=True)

        pyperclip.copy(code)

        root.after(6000, root.destroy)

        root.mainloop()

    except Exception:
        logging.error(traceback.format_exc())


# ---------------- ROUTES ---------------- #

@app.route('/send')
def handle_code():

    try:

        match = re.search(r'\d{6}', unquote(request.full_path))

        if match:
            popup_queue.put(("code", match.group()))
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

    threading.Thread(target=alert_manager, daemon=True).start()
    threading.Thread(target=popup_worker, daemon=True).start()

    serve(
        app,
        host='0.0.0.0',
        port=5000,
        threads=2
    )

