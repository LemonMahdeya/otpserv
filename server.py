import threading
import time
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
import tkinter as tk
import winsound

PORT = 17321

alert_active = False
window = None

def beep_loop():
    global alert_active
    while alert_active:
        try:
            winsound.Beep(1000, 300)
        except:
            pass
        time.sleep(2)

def show_alert():
    global alert_active, window

    if alert_active:
        return

    alert_active = True

    def ui():
        global alert_active, window

        window = tk.Tk()
        window.title("Order Alert")

        window.attributes("-topmost", True)

        w = 360
        h = 140

        ws = window.winfo_screenwidth()
        hs = window.winfo_screenheight()

        x = int((ws/2) - (w/2))
        y = int((hs/2) - (h/2))

        window.geometry(f"{w}x{h}+{x}+{y}")

        label = tk.Label(
            window,
            text="You have new order!\nCheck platform now",
            font=("Arial", 12),
            justify="center"
        )

        label.pack(pady=20)

        def close():
            global alert_active
            alert_active = False
            window.destroy()

        btn = tk.Button(window, text="OK", command=close, width=10)
        btn.pack(pady=5)

        threading.Thread(target=beep_loop, daemon=True).start()

        window.mainloop()

    threading.Thread(target=ui, daemon=True).start()

def terminate_alert():
    global alert_active, window

    if not alert_active:
        return

    alert_active = False

    try:
        if window:
            window.destroy()
    except:
        pass

class Handler(BaseHTTPRequestHandler):

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
            print(e)

def run_server():
    while True:
        try:
            server = HTTPServer(("127.0.0.1", PORT), Handler)
            print("Server running...")
            server.serve_forever()

        except Exception as e:
            print("Server crashed:", e)
            time.sleep(5)

if __name__ == "__main__":
    run_server()
