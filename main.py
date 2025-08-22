import os
import platform
import hashlib
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import re
import math
from tkinter import font

def create_hidden_folder(folder_name=".secret_folder"):
    """
    Create a hidden folder if it doesn't exist.
    On Windows: Set folder attribute to hidden.
    """
    try:
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
            if platform.system() == "Windows":
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(
                    os.path.abspath(folder_name), 2
                )
        return folder_name
    except Exception as e:
        messagebox.showerror("Error", f"Error creating folder: {e}")
        return None

def hash_password(password):
    """Return SHA-256 hash of the password."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_hash, input_password):
    """Check if input_password matches the stored hash."""
    return stored_hash == hash_password(input_password)

def open_folder(folder_path):
    """Open the folder in the system's file explorer."""
    try:
        abs_path = os.path.abspath(folder_path)
        system = platform.system()
        if system == "Windows":
            os.startfile(abs_path)
        elif system == "Darwin":  # macOS
            subprocess.run(["open", abs_path])
        else:  # Linux and others
            subprocess.run(["xdg-open", abs_path])
    except Exception as e:
        messagebox.showerror("Error", f"Error opening folder: {e}")

def draw_rounded_rect(canvas, x, y, width, height, radius, **kwargs):
    """Draw a rounded rectangle on a canvas."""
    points = [
        x + radius, y,
        x + width - radius, y,
        x + width, y + radius,
        x + width, y + height - radius,
        x + width - radius, y + height,
        x + radius, y + height,
        x, y + height - radius,
        x, y + radius,
        x + radius, y
    ]
    return canvas.create_polygon(points, **kwargs, smooth=True)

class PasswordWindow(tk.Toplevel):
    """Password prompt window for secret folder access."""

    def __init__(self, master, stored_hash, max_attempts, on_success_callback):
        super().__init__(master)
        self.title("Access Secret Folder")
        self.geometry("500x350")
        self.configure(bg="#0a101e")
        self.resizable(False, False)
        self.stored_hash = stored_hash
        self.max_attempts = max_attempts
        self.attempts = 0
        self.on_success_callback = on_success_callback

        # Center the window
        self.update_idletasks()
        parent_x = master.winfo_x()
        parent_y = master.winfo_y()
        parent_width = master.winfo_width()
        parent_height = master.winfo_height()
        x = parent_x + (parent_width - self.winfo_width()) // 2
        y = parent_y + (parent_height - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

        # Main canvas with premium gradient
        main_frame = tk.Canvas(self, width=500, height=350, bg="#0a101e", highlightthickness=0)
        main_frame.pack(fill="both", expand=True)
        
        # Draw premium gradient background
        for i in range(350):
            r = int(10 + (i/350)*15)
            g = int(16 + (i/350)*20)
            b = int(30 + (i/350)*25)
            color = f'#{r:02x}{g:02x}{b:02x}'
            main_frame.create_line(0, i, 500, i, fill=color)

        # Add subtle glow effect
        main_frame.create_oval(50, 50, 450, 300, fill="", outline="#00d4ff", width=1, stipple="gray25")

        # Title with premium font
        main_frame.create_text(250, 60, text="Secure Access", fill="#00d4ff", 
                              font=("Helvetica Neue", 24, "bold"))

        # Password entry frame with glow
        entry_frame = tk.Frame(main_frame, bg="#1e293b", bd=0, relief="flat", 
                              highlightbackground="#00d4ff", highlightthickness=2)
        main_frame.create_window(250, 140, window=entry_frame, width=350, height=60)
        
        self.entry = tk.Entry(entry_frame, show="•", font=("Helvetica Neue", 18), 
                             bg="#1e293b", fg="#00d4ff", bd=0, highlightthickness=0, 
                             insertbackground="#00d4ff")
        self.entry.pack(fill="both", expand=True, padx=15, pady=15)
        self.entry.focus_set()

        # Attempts label
        self.attempt_label = main_frame.create_text(250, 200, 
                                                   text=f"{self.max_attempts - self.attempts} attempts remaining", 
                                                   fill="#00d4ff", font=("Helvetica Neue", 12))

        # Button frame
        btn_frame = tk.Frame(main_frame, bg="#0a101e")
        main_frame.create_window(250, 280, window=btn_frame, width=350, height=60)

        # Submit button with animation
        submit_btn = tk.Canvas(btn_frame, width=160, height=50, bg="#0a101e", highlightthickness=0)
        submit_btn.pack(side="left", padx=(0, 15))
        draw_rounded_rect(submit_btn, 0, 0, 160, 50, 20, fill="#00d4ff", outline="")
        submit_btn.create_text(80, 25, text="Unlock", fill="#0a101e", font=("Helvetica Neue", 14, "bold"))
        submit_btn.bind("<Button-1>", lambda e: self.verify())
        submit_btn.bind("<Enter>", lambda e: [submit_btn.configure(cursor="hand2"), 
                                             submit_btn.itemconfig(1, fill="#33eaff")])
        submit_btn.bind("<Leave>", lambda e: [submit_btn.configure(cursor=""), 
                                             submit_btn.itemconfig(1, fill="#00d4ff")])

        # Cancel button with animation
        cancel_btn = tk.Canvas(btn_frame, width=160, height=50, bg="#0a101e", highlightthickness=0)
        cancel_btn.pack(side="right", padx=(15, 0))
        draw_rounded_rect(cancel_btn, 0, 0, 160, 50, 20, fill="#64748b", outline="")
        cancel_btn.create_text(80, 25, text="Cancel", fill="#0a101e", font=("Helvetica Neue", 14, "bold"))
        cancel_btn.bind("<Button-1>", lambda e: self.destroy())
        cancel_btn.bind("<Enter>", lambda e: [cancel_btn.configure(cursor="hand2"), 
                                             cancel_btn.itemconfig(1, fill="#94a3b8")])
        cancel_btn.bind("<Leave>", lambda e: [cancel_btn.configure(cursor=""), 
                                             cancel_btn.itemconfig(1, fill="#64748b")])

        self.bind("<Return>", lambda e: self.verify())
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.transient(master)
        self.grab_set()

    def verify(self):
        """Verify entered password, allow access or show warnings/errors."""
        password = self.entry.get()
        self.attempts += 1
        remaining = self.max_attempts - self.attempts
        if verify_password(self.stored_hash, password):
            self.on_success_callback()
            self.destroy()
        else:
            self.master.after(50, lambda: self.entry.configure(bg="#ff4d4d"))
            self.master.after(300, lambda: self.entry.configure(bg="#1e293b"))
            self.itemconfig(self.attempt_label, text=f"{remaining} attempts remaining")
            if remaining == 0:
                messagebox.showerror(
                    "Access Denied", "Too many failed attempts.", parent=self
                )
                self.destroy()
            else:
                messagebox.showwarning(
                    "Wrong Password",
                    f"Wrong password! {remaining} attempts remaining.",
                    parent=self
                )
                self.entry.delete(0, tk.END)

class AnimatedButton(tk.Canvas):
    """Custom animated button with hover, click, and glow effects."""
    
    def __init__(self, parent, width, height, text, color, command=None):
        super().__init__(parent, width=width, height=height, highlightthickness=0, bg=parent["bg"])
        self.width = width
        self.height = height
        self.text = text
        self.color = color
        self.command = command
        
        # Draw glow effect
        self.glow = draw_rounded_rect(self, 2, 2, width-4, height-4, 15, fill="", outline="#00d4ff", stipple="gray25")
        # Draw button
        self.rect = draw_rounded_rect(self, 0, 0, width, height, 15, fill=color, outline="")
        self.text_id = self.create_text(width/2, height/2, text=text, fill="#fff",
                                        font=("Helvetica Neue", 20, "bold"))
        
        # Bind events
        self.bind("<Button-1>", self.on_click)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        
    def on_enter(self, event):
        self.configure(cursor="hand2")
        self.itemconfig(self.rect, fill=self.lighten_color(self.color))
        self.itemconfig(self.glow, stipple="")
        
    def on_leave(self, event):
        self.configure(cursor="")
        self.itemconfig(self.rect, fill=self.color)
        self.itemconfig(self.glow, stipple="gray25")
        
    def on_click(self, event):
        self.itemconfig(self.rect, fill=self.darken_color(self.color))
        self.after(100, lambda: self.itemconfig(self.rect, fill=self.color))
        if self.command:
            self.after(150, self.command)
            
    def lighten_color(self, color):
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        r = min(255, r + 50)
        g = min(255, g + 50)
        b = min(255, b + 50)
        return f"#{r:02x}{g:02x}{b:02x}"
        
    def darken_color(self, color):
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        r = max(0, r - 50)
        g = max(0, g - 50)
        b = max(0, b - 50)
        return f"#{r:02x}{g:02x}{b:02x}"

class CalculatorApp:
    """Main calculator application with secret folder access."""

    def __init__(self, root):
        self.root = root
        self.root.title("DevNotFound Calculator")
        self.root.state("zoomed")  # Maximized window
        self.root.configure(bg="#0a101e")
        
        # Secret folder setup
        self.SECRET_FOLDER = ".secret_folder"
        self.PASSWORD_FILE = os.path.join(self.SECRET_FOLDER, ".password")
        self.DEFAULT_PASSWORD = "subscribe"

        # Ensure folder and password file exist
        folder = create_hidden_folder(self.SECRET_FOLDER)
        if folder and not os.path.exists(self.PASSWORD_FILE):
            try:
                with open(self.PASSWORD_FILE, "w") as f:
                    f.write(hash_password(self.DEFAULT_PASSWORD))
            except Exception as e:
                messagebox.showerror("Error", f"Error creating password file: {e}")

        # Create main canvas with premium gradient
        self.canvas = tk.Canvas(root, bg="#0a101e", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # Draw gradient and glow effect
        self.draw_gradient()
        
        # Title
        self.canvas.create_text(self.root.winfo_screenwidth()//2, 50, text="Premium Calculator", 
                               fill="#00d4ff", font=("Helvetica Neue", 28, "bold"))

        # Create display frame with shadow
        display_frame = tk.Frame(self.canvas, bg="#1e293b", bd=0, relief="flat", 
                                highlightbackground="#00d4ff", highlightthickness=2)
        self.canvas.create_window(self.root.winfo_screenwidth()//2, 150, window=display_frame, 
                                 width=min(800, self.root.winfo_screenwidth()-100), height=120)
        
        # Display entry with glow effect
        self.display_var = tk.StringVar()
        self.display_var.set("0")
        self.display = tk.Entry(display_frame, textvariable=self.display_var, 
                               font=("Helvetica Neue", 36, "bold"), bg="#1e293b", fg="#00d4ff", 
                               bd=0, justify="right", highlightthickness=0, 
                               insertbackground="#00d4ff")
        self.display.pack(fill="both", expand=True, padx=25, pady=25)
        self.display.configure(state="readonly")
        
        # Create buttons
        self.create_buttons()
        
        # Bind secret code check and window resize
        self.display_var.trace("w", self.check_secret_code)
        self.root.bind("<Configure>", self.on_resize)

    def draw_gradient(self):
        """Draw a premium gradient background with subtle glow."""
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        
        if width <= 1 or height <= 1:
            self.root.after(100, self.draw_gradient)
            return
            
        self.canvas.delete("gradient")
        
        for i in range(height):
            r = int(10 + (i/height)*15)
            g = int(16 + (i/height)*20)
            b = int(30 + (i/height)*25)
            color = f'#{r:02x}{g:02x}{b:02x}'
            self.canvas.create_line(0, i, width, i, tags="gradient", fill=color)
        
        # Add subtle glow effect
        self.canvas.create_oval(50, 50, width-50, height-50, fill="", outline="#00d4ff", 
                               width=1, stipple="gray12", tags="gradient")

    def on_resize(self, event):
        """Redraw gradient and reposition elements on window resize."""
        self.draw_gradient()
        self.canvas.coords(self.canvas.find_withtag("title")[0], 
                          self.root.winfo_screenwidth()//2, 50)
        self.canvas.coords(self.canvas.find_withtag("display")[0], 
                          self.root.winfo_screenwidth()//2, 150)
        self.canvas.coords(self.canvas.find_withtag("buttons")[0], 
                          self.root.winfo_screenwidth()//2, 450)

    def create_buttons(self):
        """Create calculator buttons with premium visual design."""
        buttons = [
            ["C", "(", ")", "÷"],
            ["7", "8", "9", "×"],
            ["4", "5", "6", "-"],
            ["1", "2", "3", "+"],
            [".", "0", "="]
        ]
        
        button_colors = {
            "C": "#ef4444",  # Red
            "=": "#00d4ff",  # Cyan
            "default": "#2d3748",  # Darker blue-gray
            "operator": "#4b5563"  # Lighter blue-gray
        }
        
        button_frame = tk.Frame(self.canvas, bg="#0a101e")
        self.canvas.create_window(self.root.winfo_screenwidth()//2, 450, window=button_frame, 
                                 width=min(800, self.root.winfo_screenwidth()-100), height=500, 
                                 tags="buttons")
        
        # Configure grid
        for i in range(5):
            button_frame.grid_rowconfigure(i, weight=1, minsize=90)
        for i in range(4):
            button_frame.grid_columnconfigure(i, weight=1, minsize=180)
        
        # Create buttons
        for row_idx, row in enumerate(buttons):
            for col_idx, text in enumerate(row):
                if text == "C":
                    color = button_colors["C"]
                    cmd = self.clear
                elif text == "=":
                    color = button_colors["="]
                    cmd = self.calculate
                elif text in ["÷", "×", "-", "+", "(", ")"]:
                    color = button_colors["operator"]
                    cmd = lambda t=text: self.append_to_display(t)
                else:
                    color = button_colors["default"]
                    cmd = lambda t=text: self.append_to_display(t)
                
                btn = AnimatedButton(button_frame, 170, 80, text, color, cmd)
                btn.grid(row=row_idx, column=col_idx, padx=8, pady=8, sticky="nsew")

    def append_to_display(self, text):
        """Append character to calculator display."""
        current = self.display_var.get()
        if current == "0" and text not in "+-×÷()":
            self.display_var.set("")
        self.display_var.set(self.display_var.get() + text)

    def clear(self):
        """Clear display and reset to zero."""
        self.display_var.set("0")

    def calculate(self):
        """Evaluate the expression."""
        expression = self.display_var.get()
        
        try:
            if not re.match(r'^[\d+\-×÷/().\s]+$', expression):
                messagebox.showerror("Error", "Invalid characters in expression", parent=self.root)
                self.clear()
                return
                
            expression = expression.replace('×', '*').replace('÷', '/')
            result = eval(expression)
            
            if isinstance(result, float):
                if result.is_integer():
                    result = int(result)
                else:
                    result = round(result, 10)
            
            self.display_var.set(str(result))
            
        except ZeroDivisionError:
            messagebox.showerror("Error", "Division by zero is not allowed", parent=self.root)
            self.clear()
        except Exception as e:
            messagebox.showerror("Error", f"Invalid calculation: {str(e)}", parent=self.root)
            self.clear()

    def check_secret_code(self, *args):
        """Check if the display contains the secret code."""
        if self.display_var.get().strip() == "69÷69":
            self.open_secret_folder()

    def open_secret_folder(self):
        """Prompt for password and open secret folder if authenticated."""
        if not os.path.exists(self.SECRET_FOLDER):
            messagebox.showerror(
                "Error", "Secret folder not found. Please restart the application.", parent=self.root
            )
            return
            
        if not os.path.exists(self.PASSWORD_FILE):
            try:
                with open(self.PASSWORD_FILE, "w") as f:
                    f.write(hash_password(self.DEFAULT_PASSWORD))
            except Exception as e:
                messagebox.showerror("Error", f"Error creating password file: {e}")
                return

        with open(self.PASSWORD_FILE, "r") as f:
            stored_hash = f.read().strip()

        self.clear()
        PasswordWindow(self.root, stored_hash, 3, lambda: open_folder(self.SECRET_FOLDER))

if __name__ == "__main__":
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()
