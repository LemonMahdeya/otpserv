import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
import tkinter as tk
import winsound

PORT = 17321

alert_active = False
root = None
alert_window = None


def beep_loop():
    global alert_active
    while alert_active:
        try:
            winsound.Beep(1000, 300)
        except:
            pass
        time.sleep(2)


def show_alert():
    global alert_active, alert_window

    if alert_active:
        return

    alert_active = True

    def create_window():
        global alert_window, alert_active

        alert_window = tk.Toplevel(root)
        alert_window.title("Order Alert")
        alert_window.attributes("-topmost", True)

        w = 360
        h = 140

        ws = alert_window.winfo_screenwidth()
        hs = alert_window.winfo_screenheight()

        x = int((ws/2) - (w/2))
        y = int((hs/2) - (h/2))

        alert_window.geometry(f"{w}x{h}+{x}+{y}")

        label = tk.Label(
            alert_window,
            text="You have new order!\nCheck platform now",
            font=("Arial", 12),
            justify="center"
        )
        label.pack(pady=20)

        def close():
            global alert_active
            alert_active = False
            alert_window.destroy()

        btn = tk.Button(alert_window, text="OK", command=close, width=10)
        btn.pack(pady=5)

        threading.Thread(target=beep_loop, daemon=True).start()

        repeat_check()

    def repeat_check():
        if alert_active:
            root.after(60000, recreate)

    def recreate():
        global alert_window
        if alert_active:
            try:
                alert_window.destroy()
            except:
                pass
            create_window()

    root.after(0, create_window)


def terminate_alert():
    global alert_active, alert_window

    if not alert_active:
        return

    alert_active = False

    try:
        alert_window.destroy()
    except:
        pass


class Handler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        return

    def do_GET(self):

        try:

            if self.path == "/order":
                show_alert()

            elif self.path == "/terminate":
                terminate_alert()

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")

        except Exception as e:
            print("error:", e)


def server_loop():

    while True:
        try:
            server = HTTPServer(("127.0.0.1", PORT), Handler)
            server.serve_forever()

        except Exception as e:
            print("server error:", e)
            time.sleep(3)


def start_server():
    threading.Thread(target=server_loop, daemon=True).start()


# GUI loop
root = tk.Tk()
root.withdraw()

start_server()

root.mainloop()
