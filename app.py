import threading
import tkinter as tk
from flask import Flask, request
from waitress import serve
import logging
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

# ---------------- FLASK ---------------- #
app = Flask(__name__)

# ---------------- GLOBAL STATE ---------------- #
alert_active = False
popup_visible = False
snooze_until = 0


# ---------------- SAFE THREAD ---------------- #
def safe_thread(target):
    def wrapper():
        while True:
            try:
                target()
            except Exception:
                logging.error(traceback.format_exc())
                time.sleep(2)

    t = threading.Thread(target=wrapper)
    t.daemon = True
    t.start()
    return t


# ---------------- ALERT LOOP ---------------- #
def alert_loop():
    global alert_active, popup_visible, snooze_until

    while True:
        try:

            if not alert_active:
                time.sleep(1)
                continue

            if time.time() >= snooze_until and not popup_visible:
                show_popup()

            time.sleep(1)

        except Exception:
            logging.error(traceback.format_exc())
            time.sleep(2)


# ---------------- POPUP ---------------- #
def show_popup():
    global popup_visible, snooze_until, alert_active

    def ui():

        global popup_visible, snooze_until, alert_active

        try:
            popup_visible = True

            root = tk.Tk()
            root.attributes("-topmost", True)
            root.overrideredirect(True)

            w, h = 600, 70
            sw = root.winfo_screenwidth()
            sh = root.winfo_screenheight()

            root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
            root.configure(bg="#1a1a1a")

            frame = tk.Frame(root, bg="#1a1a1a", highlightbackground="#ff0000", highlightthickness=2)
            frame.pack(fill="both", expand=True)

            content = tk.Frame(frame, bg="#1a1a1a")
            content.pack(expand=True)

            tk.Label(
                content,
                text="⚠ NEW ORDER ALERT",
                fg="#ff4444",
                bg="#1a1a1a",
                font=("Segoe UI", 14, "bold")
            ).pack(side="left", padx=20)

            tk.Label(
                content,
                text="Check the platform now",
                fg="white",
                bg="#1a1a1a",
                font=("Segoe UI", 10)
            ).pack(side="left")

            # ---------------- SNOOZE ---------------- #
            def snooze():
                global snooze_until, popup_visible
                snooze_until = time.time() + 60
                popup_visible = False
                root.destroy()

            tk.Button(
                content,
                text="SNOOZE (1m)",
                command=snooze,
                bg="#cc0000",
                fg="white",
                font=("Segoe UI", 9, "bold"),
                border=0,
                padx=15,
                pady=4
            ).pack(side="right", padx=20)

            # ---------------- SOUND LOOP ---------------- #
            def sound_loop():
                while popup_visible and alert_active:
                    try:
                        if winsound:
                            winsound.Beep(1200, 300)
                    except:
                        pass
                    time.sleep(1)

            safe_thread(sound_loop)

            # ---------------- TERMINATE MONITOR ---------------- #
            def monitor():
                global popup_visible

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

    safe_thread(ui)


# ---------------- ROUTE ---------------- #
@app.route("/control")
def control():

    global alert_active, snooze_until

    try:

        cmd = request.args.get("cmd", "").lower()

        if cmd == "order":

            alert_active = True
            snooze_until = 0

            return "ORDER ALERT ACTIVATED", 200

        elif cmd == "terminate":

            alert_active = False

            return "ALERT TERMINATED", 200

        return "INVALID COMMAND", 400

    except Exception:
        logging.error(traceback.format_exc())
        return "ERROR", 500


# ---------------- MAIN ---------------- #
if __name__ == "__main__":

    safe_thread(alert_loop)

    serve(app, host="0.0.0.0", port=5000, threads=2)
