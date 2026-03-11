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

# Disable logging for a silent background process
log = logging.getLogger('waitress')
log.setLevel(logging.ERROR)

app = Flask(__name__)

# Control variables
alert_active = False
snooze_until = 0
popup_visible = False

def alert_manager():
    """Manages sound and reappearing of the popup after snooze"""
    global alert_active, snooze_until, popup_visible
    while alert_active:
        current_time = time.time()
        if current_time > snooze_until:
            # Trigger Sound
            if winsound:
                winsound.Beep(1000, 500)
            
            # Show Popup if not already visible
            if not popup_visible:
                show_order_popup()
        time.sleep(1)

def show_order_popup():
    """Big alert popup in the center of the screen"""
    global alert_active, snooze_until, popup_visible
    
    def on_snooze():
        global snooze_until, popup_visible
        snooze_until = time.time() + 60  # Set snooze for 60 seconds
        popup_visible = False
        root.destroy()

    def create_alert_ui():
        global popup_visible
        try:
            popup_visible = True
            root = tk.Tk()
            root.title("System Alert")
            root.attributes("-topmost", True)
            root.overrideredirect(True)
            
            # Center the window
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

            tk.Button(frame, text="SNOOZE FOR 1 MINUTE", command=on_snooze,
                            bg='#cc0000', fg='white', font=('Segoe UI', 10, 'bold'),
                            padx=20, pady=10, border=0, cursor="hand2").pack(pady=20)

            # Monitor if alert is terminated from outside
            def monitor_status():
                global alert_active, popup_visible
                if not alert_active:
                    popup_visible = False
                    root.destroy()
                else:
                    root.after(500, monitor_status)

            monitor_status()
            root.mainloop()
        except:
            popup_visible = False

    threading.Thread(target=create_alert_ui, daemon=True).start()

def show_code_popup(code):
    """Small notification for 6-digit codes"""
    def create_window():
        try:
            root = tk.Tk()
            root.overrideredirect(True)
            root.attributes("-topmost", True)
            width, height = 300, 90
            sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
            root.geometry(f"{width}x{height}+{sw - width - 20}+{sh - height - 50}")
            root.configure(bg='#121212')
            
            main_frame = tk.Frame(root, bg='#121212', highlightbackground="#333333", highlightthickness=1)
            main_frame.pack(fill='both', expand=True)
            
            tk.Label(main_frame, text="NEW VERIFICATION CODE",
                     fg='#888888', bg='#121212', font=('Segoe UI', 8, 'bold')).pack(pady=(10, 0))
            tk.Label(main_frame, text=code,
                     fg='#ffffff', bg='#121212', font=('Consolas', 24, 'bold')).pack(expand=True)
            
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
        return "Code Received", 200
    return "No Code Found", 400

@app.route('/control')
def handle_control():
    global alert_active, snooze_until
    cmd = request.args.get('cmd', '').lower()
    
    if 'order' in cmd:
        if not alert_active:
            alert_active = True
            snooze_until = 0
            threading.Thread(target=alert_manager, daemon=True).start()
        return "Alert System Activated", 200
    
    elif 'terminate' in cmd:
        alert_active = False
        return "Alert System Terminated", 200
    
    return "Invalid Command", 400

if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5000, threads=4)
