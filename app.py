import threading
import re
import tkinter as tk
import pyperclip
from flask import Flask, request
from waitress import serve
import logging
from urllib.parse import unquote
import time

# Attempt to import winsound for Windows alerts
try:
    import winsound
except ImportError:
    winsound = None

# Disable logging
log = logging.getLogger('waitress')
log.setLevel(logging.ERROR)

app = Flask(__name__)

# Control variables
alert_active = False
snooze_until = 0
popup_visible = False

def alert_manager():
    """Manages sound and triggers popup only if NOT in snooze mode"""
    global alert_active, snooze_until, popup_visible
    while alert_active:
        current_time = time.time()
        if current_time > snooze_until:
            # Trigger Sound
            if winsound:
                winsound.Beep(1000, 400)
            
            # Show Popup if it was closed or not yet visible
            if not popup_visible:
                show_order_popup()
        time.sleep(1)

def show_order_popup():
    """Shows the popup and handles immediate closing on snooze"""
    global alert_active, snooze_until, popup_visible
    
    def on_snooze():
        global snooze_until, popup_visible
        snooze_until = time.time() + 60  # Sleep for 60 seconds
        popup_visible = False
        root.quit()  # Stop mainloop
        root.destroy() # Close window immediately

    def create_alert_ui():
        global popup_visible
        try:
            popup_visible = True
            root = tk.Tk()
            root.title("Order Alert")
            root.attributes("-topmost", True)
            root.overrideredirect(True) # No title bar
            
            # Window size and position (Center)
            w, h = 500, 250
            sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
            root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
            root.configure(bg='#1a1a1a')
            
            frame = tk.Frame(root, bg='#1a1a1a', highlightbackground="#ff0000", highlightthickness=3)
            frame.pack(fill='both', expand=True)

            tk.Label(frame, text="⚠️ NEW ORDER ALERT ⚠️", fg='#ff4444', bg='#1a1a1a', 
                     font=('Segoe UI', 20, 'bold')).pack(pady=20)
            
            tk.Label(frame, text="A new request is available on the platform!", fg='#ffffff', bg='#1a1a1a', 
                     font=('Segoe UI', 12)).pack(pady=10)

            # Snooze button will destroy the window immediately
            tk.Button(frame, text="SNOOZE & HIDE (1 MIN)", command=on_snooze,
                            bg='#cc0000', fg='white', font=('Segoe UI', 10, 'bold'),
                            padx=30, pady=15, border=0, cursor="hand2").pack(pady=20)

            # Check if alert is killed from outside (terminate)
            def monitor():
                if not alert_active:
                    root.destroy()
                else:
                    root.after(500, monitor)

            monitor()
            root.mainloop()
        except:
            popup_visible = False

    # Start UI in a separate thread
    threading.Thread(target=create_alert_ui, daemon=True).start()

def show_code_popup(code):
    """Small code notification remains the same"""
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
            tk.Label(f, text="VERIFICATION CODE", fg='#888888', bg='#121212', font=('Segoe UI', 8, 'bold')).pack(pady=(10, 0))
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

if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5000, threads=4)
