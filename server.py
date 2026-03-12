import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import tkinter as tk
import winsound

PORT = 17321

alert_active = False
root = None
alert_window = None
last_trigger = 0


# =========================
# SOUND LOOP
# =========================

def beep_loop():
    global alert_active

    while alert_active:
        try:
            winsound.Beep(1200, 400)
        except:
            pass
        time.sleep(2)


# =========================
# SHOW ALERT WINDOW
# =========================

def show_alert():

    global alert_active, alert_window, last_trigger

    now = time.time()

    # Anti spam (لو وصل نفس الطلب بسرعة)
    if now - last_trigger < 2:
        return

    last_trigger = now

    if alert_active:
        return

    alert_active = True

    alert_window = tk.Toplevel(root)
    alert_window.title("Order Alert")
    alert_window.attributes("-topmost", True)

    w = 360
    h = 160

    ws = alert_window.winfo_screenwidth()
    hs = alert_window.winfo_screenheight()

    x = int((ws / 2) - (w / 2))
    y = int((hs / 2) - (h / 2))

    alert_window.geometry(f"{w}x{h}+{x}+{y}")

    label = tk.Label(
        alert_window,
        text="🚨 New Order Detected\nCheck Lemon Platform",
        font=("Arial", 12),
        justify="center"
    )
    label.pack(pady=25)

    def close():

        global alert_active

        alert_active = False

        try:
            alert_window.destroy()
        except:
            pass

    btn = tk.Button(
        alert_window,
        text="OK",
        command=close,
        width=12,
        height=1
    )

    btn.pack()

    threading.Thread(target=beep_loop, daemon=True).start()


# =========================
# TERMINATE ALERT
# =========================

def terminate_alert():

    global alert_active, alert_window

    if not alert_active:
        return

    alert_active = False

    try:
        alert_window.destroy()
    except:
        pass


# =========================
# HTTP HANDLER
# =========================

class Handler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        return

    def do_GET(self):

        try:

            print("Request:", self.path)

            if self.path == "/order":

                root.after(0, show_alert)

            elif self.path == "/terminate":

                root.after(0, terminate_alert)

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")

        except Exception as e:

            print("Handler error:", e)


# =========================
# SERVER LOOP
# =========================

def server_loop():

    while True:

        try:

            server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)

            print("Server started on port", PORT)

            server.serve_forever()

        except Exception as e:

            print("Server crash:", e)

            time.sleep(3)


def start_server():

    threading.Thread(
        target=server_loop,
        daemon=True
    ).start()


# =========================
# GUI
# =========================

root = tk.Tk()

root.withdraw()

start_server()

root.mainloop()
