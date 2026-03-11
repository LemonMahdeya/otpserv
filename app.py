import threading
import re
import tkinter as tk
import pyperclip
from flask import Flask, request
from waitress import serve
import logging
from urllib.parse import unquote
import time
import sys

# Attempt to import winsound for Windows alerts
try:
    import winsound
except ImportError:
    winsound = None

# Global Control Variables
alert_active = False
snooze_until = 0
popup_visible = False

def alert_manager():
    global alert_active, snooze_until, popup_visible
    while alert_active:
        try:
            current_time = time.time()
            if current_time > snooze_until:
                if winsound:
                    winsound.Beep(1000, 400)
                
                if not popup_visible:
                    show_order_popup()
            time.sleep(1)
        except Exception as e:
            time.sleep(1) # prevent CPU hogging on error

def show_order_popup():
    global alert_active, snooze_until, popup_visible
    
    def on_snooze():
        global snooze_until, popup_visible
        snooze_until = time.time() + 60
        popup_visible = False
        root.destroy()

    def create_alert_ui():
        global popup_visible
        try:
            popup_visible = True
            root = tk.Tk()
            root.attributes("-topmost", True)
            root.overrideredirect(True)
            
            w, h = 500, 250
            sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
            root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
            root.configure(bg='#1a1a1a')
            
            frame = tk.Frame(root, bg='#1a1a1a', highlightbackground="#ff0000", highlightthickness=3)
            frame.pack(fill='both', expand=True)

            tk.Label(frame, text="⚠️ NEW ORDER ALERT ⚠️", fg='#ff4444', bg='#1a1a1a', 
                     font=('Segoe UI', 20, 'bold')).pack(pady=20)
            
            tk.Label(frame, text="A new request is available! Check the platform.", fg='#ffffff', bg='#1a1a1a', 
                     font=('Segoe UI', 12)).pack(pady=10)

            tk.Button(frame, text="SNOOZE & HIDE NOW", command=on_snooze,
                            bg='#cc0000', fg='white', font=('Segoe UI', 11, 'bold'),
                            padx=40, pady=15, border=0, cursor="hand2").pack(pady=20)

            def monitor():
                global alert_active
                if not alert_active:
                    root.destroy()
                else:
                    root.after(500, monitor)

            monitor()
            root.mainloop()
        except Exception:
            pass
        finally:
            popup_visible = False

    threading.Thread(target=create_alert_ui, daemon=True).start()

def show_code_popup(code):
    def create_window():
        try:
            root = tk.Tk()
            root.overrideredirect(True)
            root.attributes("-topmost", True)
            w, h = 300, 90
            sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
            root.geometry(f"{w}x{h}+{sw-w-20}+{sh-h-50}")
            root.configure(bg='#121212')
            f = tk.Frame(root, bg='#121212', highlightbackground="#333333", highlightthickness=1)
            f.pack(fill='both', expand=True)
            tk.Label(f, text="VERIFICATION CODE", fg='#888888', bg='#121212', font=('Segoe UI', 8, 'bold')).pack(pady=(10, 0))
            tk.Label(f, text=code, fg='#ffffff', bg='#121212', font=('Consolas', 24, 'bold')).pack(expand=True)
            pyperclip.copy(code)
            root.after(6000, root.destroy)
            root.mainloop()
        except Exception: pass
    threading.Thread(target=create_window, daemon=True).start()

# Flask Setup
app = Flask(__name__)
log = logging.getLogger('waitress')
log.setLevel(logging.ERROR)

@app.route('/send')
def handle_code():
    match = re.search(r'\d{6}', unquote(request.full_path))
    if match:
        show_code_popup(match.group())
        return "OK", 200
    return "Fail", 400

@app.route('/control')
def handle_control():
    global alert_active, snooze_until
    cmd = request.args.get('cmd', '').lower()
    if 'order' in cmd:
        if not alert_active:
            alert_active = True
            snooze_until = 0
            threading.Thread(target=alert_manager, daemon=True).start()
        return "Activated", 200
    elif 'terminate' in cmd:
        alert_active = False
        return "Terminated", 200
    return "Invalid", 400

# Main Self-Healing Wrapper
if __name__ == '__main__':
    while True: # Infinite loop to restart on failure
        try:
            serve(app, host='0.0.0.0', port=5000, threads=4)
        except Exception as e:
            # If server crashes, wait 5 seconds and restart
            time.sleep(5)
            continue
