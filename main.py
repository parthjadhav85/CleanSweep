import os
import shutil
import threading
import time
import webbrowser
import datetime
import platform
import subprocess
import customtkinter as ctk
from tkinter import filedialog

# --- THEME: "MIDNIGHT OBSIDIAN" ---
# High contrast, deep blacks, and electric purple accents
THEME = {
    "window_bg": "#09090b",       
    "sidebar_bg": "#121215",      
    "card_bg": "#1c1c21",         
    "card_border": "#2c2c35",     
    "primary": "#6366f1",         
    "primary_hover": "#4f46e5",   
    "text_main": "#ffffff",       
    "text_sub": "#a1a1aa",        
    "success": "#10b981",         
    "warning": "#f59e0b",         
    "error": "#ef4444",           
    "input_bg": "#23232a"         
}

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# --- HELPER: CROSS-PLATFORM OPEN ---
def open_file_explorer(path):
    try:
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception as e:
        print(f"Error opening folder: {e}")

# --- CUSTOM WIDGETS ---
class StatCard(ctk.CTkFrame):
    def __init__(self, parent, icon, title, **kwargs):
        super().__init__(parent, fg_color=THEME["card_bg"], corner_radius=12, 
                         border_width=1, border_color=THEME["card_border"], **kwargs)
        self.grid_columnconfigure(1, weight=1)
        
        self.icon_frame = ctk.CTkFrame(self, width=45, height=45, corner_radius=22, fg_color=THEME["input_bg"])
        self.icon_frame.grid(row=0, column=0, rowspan=2, padx=15, pady=15)
        
        self.icon_lbl = ctk.CTkLabel(self.icon_frame, text=icon, font=("Segoe UI Emoji", 20))
        self.icon_lbl.place(relx=0.5, rely=0.5, anchor="center")

        self.title_lbl = ctk.CTkLabel(self, text=title.upper(), font=("Segoe UI", 10, "bold"), text_color=THEME["text_sub"])
        self.title_lbl.grid(row=0, column=1, sticky="sw", pady=(15, 0), padx=5)

        self.count_lbl = ctk.CTkLabel(self, text="0", font=("Inter", 22, "bold"), text_color=THEME["text_main"])
        self.count_lbl.grid(row=1, column=1, sticky="nw", pady=(0, 15), padx=5)

    def update_count(self, value):
        self.count_lbl.configure(text=str(value))

class SidebarLink(ctk.CTkButton):
    def __init__(self, parent, text, command):
        super().__init__(
            parent, text=text, command=command, height=32, corner_radius=6,
            fg_color="transparent", text_color=THEME["text_sub"],
            hover_color=THEME["card_border"], anchor="w", font=("Segoe UI", 12)
        )

# --- MAIN APPLICATION ---
class FileOrganizerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- WINDOW SETUP ---
        self.title("CleanSweep Ultimate")
        self.geometry("1000x720")
        self.minsize(900, 650)
        self.configure(fg_color=THEME["window_bg"])
        
        # --- STATE ---
        self.selected_path = ""
        self.sidebar_width = 280
        self.current_pos = -self.sidebar_width 
        self.target_pos = -self.sidebar_width
        self.is_sidebar_open = False
        
        # Extended File Categories
        self.categories = {
            "Images":    ["🖼️", [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".tiff", ".ico", ".heic"]],
            "Documents": ["📄", [".pdf", ".docx", ".doc", ".txt", ".xlsx", ".xls", ".csv", ".pptx", ".odt", ".rtf"]],
            "Media":     ["🎬", [".mp4", ".mkv", ".mov", ".avi", ".mp3", ".wav", ".flac", ".aac", ".m4a"]],
            "Archives":  ["📦", [".zip", ".rar", ".7z", ".tar", ".gz", ".iso", ".bz2"]],
            "Software":  ["💾", [".exe", ".msi", ".bat", ".sh", ".apk", ".dmg", ".pkg", ".appimage"]],
            "Code":      ["💻", [".py", ".js", ".html", ".css", ".java", ".cpp", ".json", ".xml", ".php", ".ts", ".sql"]]
        }

        self.init_ui()

    def init_ui(self):
        # ==========================================================
        # 1. MAIN CONTENT LAYER
        # ==========================================================
        self.main_view = ctk.CTkFrame(self, fg_color="transparent")
        self.main_view.pack(fill="both", expand=True, padx=30, pady=30)
        self.main_view.grid_columnconfigure(0, weight=1)
        self.main_view.grid_rowconfigure(3, weight=1)

        # --- HEADER ---
        self.header_frame = ctk.CTkFrame(self.main_view, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(10, 20))
        self.header_frame.grid_columnconfigure(1, weight=1)

        self.menu_btn = ctk.CTkButton(
            self.header_frame, text="☰", width=45, height=45,
            fg_color="transparent", text_color=THEME["text_main"],
            font=("Segoe UI", 26), hover_color=THEME["card_border"],
            corner_radius=8, command=self.toggle_sidebar
        )
        self.menu_btn.grid(row=0, column=0, rowspan=2, padx=(0, 15))

        hour = datetime.datetime.now().hour
        greeting = "Good Morning" if 5 <= hour < 12 else "Good Afternoon" if 12 <= hour < 18 else "Good Evening"
        
        self.hello_lbl = ctk.CTkLabel(self.header_frame, text=f"{greeting}, User", font=("Inter", 32, "bold"), text_color=THEME["text_main"])
        self.hello_lbl.grid(row=0, column=1, sticky="w")
        
        self.status_lbl = ctk.CTkLabel(self.header_frame, text="System Ready", font=("Segoe UI", 13, "bold"), text_color=THEME["success"])
        self.status_lbl.grid(row=1, column=1, sticky="w")

        # --- INPUT BAR ---
        self.input_container = ctk.CTkFrame(self.main_view, fg_color=THEME["card_bg"], corner_radius=12, border_width=1, border_color=THEME["card_border"])
        self.input_container.grid(row=1, column=0, sticky="ew", pady=(0, 25))
        
        self.path_entry = ctk.CTkEntry(
            self.input_container, placeholder_text="Select a target directory...",
            border_width=0, fg_color="transparent", height=55,
            font=("Consolas", 14), text_color=THEME["text_main"]
        )
        self.path_entry.pack(side="left", fill="x", expand=True, padx=20)
        
        self.browse_btn = ctk.CTkButton(
            self.input_container, text="📂 Browse", width=110, height=38,
            fg_color=THEME["input_bg"], hover_color=THEME["card_border"],
            font=("Segoe UI", 13, "bold"), command=self.select_folder
        )
        self.browse_btn.pack(side="right", padx=15)

        # --- STATS GRID ---
        self.stats_frame = ctk.CTkFrame(self.main_view, fg_color="transparent")
        self.stats_frame.grid(row=2, column=0, sticky="ew", pady=(0, 20))
        self.stats_frame.grid_columnconfigure((0,1,2), weight=1) 
        
        self.cards = {}
        r, c = 0, 0
        for name, data in self.categories.items():
            card = StatCard(self.stats_frame, data[0], name)
            card.grid(row=r, column=c, sticky="ew", padx=5, pady=5)
            self.cards[name] = card
            c += 1
            if c > 2:
                c = 0
                r += 1

        # --- LOGS & ACTIONS ---
        self.bottom_section = ctk.CTkFrame(self.main_view, fg_color="transparent")
        self.bottom_section.grid(row=3, column=0, sticky="nsew")
        self.bottom_section.grid_rowconfigure(1, weight=1) 
        self.bottom_section.grid_columnconfigure(0, weight=1)

        self.progress = ctk.CTkProgressBar(self.bottom_section, height=6, corner_radius=3, progress_color=THEME["primary"], fg_color=THEME["input_bg"])
        self.progress.set(0)
        self.progress.grid(row=0, column=0, sticky="ew", pady=(10, 15))

        self.log_box = ctk.CTkTextbox(
            self.bottom_section, corner_radius=12,
            fg_color=THEME["input_bg"], text_color=THEME["text_sub"],
            font=("Consolas", 11), border_width=1, border_color=THEME["card_border"]
        )
        self.log_box.grid(row=1, column=0, sticky="nsew", pady=(0, 20))
        self.log_box.insert("0.0", "> CleanSweep Kernel Initialized...\n")
        self.log_box.configure(state="disabled")

        self.btn_container = ctk.CTkFrame(self.bottom_section, fg_color="transparent")
        self.btn_container.grid(row=2, column=0, sticky="ew")

        self.reset_btn = ctk.CTkButton(
            self.btn_container, text="Reset", width=100, height=50,
            fg_color=THEME["card_bg"], hover_color=THEME["card_border"],
            font=("Segoe UI", 13, "bold"), text_color=THEME["text_sub"],
            command=self.reset_app
        )
        self.reset_btn.pack(side="left", padx=(0, 10))

        self.action_btn = ctk.CTkButton(
            self.btn_container, text="START ORGANIZATION", height=50,
            fg_color=THEME["primary"], hover_color=THEME["primary_hover"],
            font=("Segoe UI", 14, "bold"), command=self.start_processing_thread
        )
        self.action_btn.pack(side="left", fill="x", expand=True)

        # ==========================================================
        # 2. SIDEBAR LAYER (OVERLAY)
        # ==========================================================
        self.sidebar = ctk.CTkFrame(self, fg_color=THEME["sidebar_bg"], corner_radius=0, width=self.sidebar_width)
        self.sidebar.place(x=self.current_pos, y=0, relheight=1)
        
        self.sb_header = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=60)
        self.sb_header.pack(fill="x", padx=20, pady=(20, 0))
        
        self.close_btn = ctk.CTkButton(
            self.sb_header, text="×", width=40, height=40,
            fg_color="transparent", hover_color=THEME["card_border"],
            text_color=THEME["text_sub"], font=("Arial", 32),
            command=self.toggle_sidebar
        )
        self.close_btn.pack(side="right")

        self.logo_lbl = ctk.CTkLabel(self.sidebar, text="CleanSweep", font=("Inter", 24, "bold"), text_color=THEME["text_main"])
        self.logo_lbl.pack(pady=(10, 5), padx=25, anchor="w")
        
        self.ver_lbl = ctk.CTkLabel(self.sidebar, text="SYSTEM v1.0", font=("Consolas", 11), text_color=THEME["primary"])
        self.ver_lbl.pack(pady=(0, 30), padx=25, anchor="w")

        # Sidebar Divider
        ctk.CTkFrame(self.sidebar, height=1, fg_color=THEME["card_border"]).pack(fill="x", padx=25, pady=10)

        # --- DEFINING THE DESCRIPTION TEXT (Fixed Missing Variable) ---
        description_text = (
        "CleanSweep is your\n"
            "go-to solution for\n"
            "decluttering\n"
            "and organizing\n"
            "your files\n"
            "effortlessly.\n"
        )

        self.info_lbl = ctk.CTkLabel(
            self.sidebar, 
            text=description_text,
            font=("Consolas", 12),  # Monospace for that "Hacker" look
            text_color=THEME["text_sub"], 
            justify="left"
        )
        self.info_lbl.pack(padx=25, pady=20, anchor="w")

        self.social_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.social_frame.pack(side="bottom", fill="x", padx=20, pady=30)
        
        ctk.CTkLabel(self.social_frame, text="DEVELOPER", font=("Segoe UI", 10, "bold"), text_color=THEME["text_sub"]).pack(anchor="w", pady=(0, 5))
        SidebarLink(self.social_frame, "↗  GitHub Profile", lambda: webbrowser.open("https://github.com/parthjadhav85")).pack(fill="x", pady=2)
        SidebarLink(self.social_frame, "↗  Portfolio Website", lambda: webbrowser.open("https://parthjadhav.com")).pack(fill="x", pady=2)

    # --- ANIMATION LOGIC ---
    def toggle_sidebar(self):
        self.is_sidebar_open = not self.is_sidebar_open
        self.target_pos = 0 if self.is_sidebar_open else -self.sidebar_width
        if self.is_sidebar_open: self.sidebar.lift()
        self.animate()

    def animate(self):
        if self.current_pos < self.target_pos:
            self.current_pos += 40
            if self.current_pos > self.target_pos: self.current_pos = self.target_pos
        elif self.current_pos > self.target_pos:
            self.current_pos -= 40
            if self.current_pos < self.target_pos: self.current_pos = self.target_pos
            
        self.sidebar.place(x=self.current_pos, y=0, relheight=1)
        if self.current_pos != self.target_pos:
            self.after(10, self.animate)

    # --- CORE LOGIC (THREAD SAFE) ---
    def log(self, msg, type="info"):
        self.after(0, lambda: self._log_internal(msg, type))

    def _log_internal(self, msg, type):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        prefix = "✔" if type=="success" else "✖" if type=="error" else ">"
        formatted = f"[{timestamp}] {prefix} {msg}\n"
        self.log_box.configure(state="normal")
        self.log_box.insert("end", formatted)
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def set_status(self, text, color):
        self.after(0, lambda: self.status_lbl.configure(text=text, text_color=color))

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.selected_path = folder
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, folder)
            self.log(f"Selected target: {folder}")
            self.set_status("Scanning Directory...", THEME["warning"])
            threading.Thread(target=self.scan_folder, daemon=True).start()

    def scan_folder(self):
        try:
            total = 0
            for _, _, files in os.walk(self.selected_path):
                total += len(files)
                break 
            if total == 0: self.set_status("Folder Empty", THEME["text_sub"])
            else: self.set_status(f"{total} Files Found - Ready", THEME["success"])
        except Exception: self.set_status("Error Reading Folder", THEME["error"])

    def start_processing_thread(self):
        if not self.selected_path:
            self.log("No directory selected.", "error")
            return
        self.action_btn.configure(state="disabled", text="PROCESSING...")
        self.reset_btn.configure(state="disabled")
        self.browse_btn.configure(state="disabled")
        self.set_status("Organizing Files...", THEME["primary"])
        self.progress.set(0)
        threading.Thread(target=self.organize_logic, daemon=True).start()

    def get_unique_name(self, folder, filename):
        name, ext = os.path.splitext(filename)
        counter = 1
        new_name = filename
        while os.path.exists(os.path.join(folder, new_name)):
            new_name = f"{name} ({counter}){ext}"
            counter += 1
        return new_name

    def organize_logic(self):
        try:
            files = [f for f in os.listdir(self.selected_path) if os.path.isfile(os.path.join(self.selected_path, f))]
            total = len(files)
            if total == 0:
                self.log("No files to organize.")
                self.after(0, lambda: self.finish_process(0))
                return

            moved_count = 0
            cat_counts = {k:0 for k in self.categories}

            for i, filename in enumerate(files):
                file_path = os.path.join(self.selected_path, filename)
                _, ext = os.path.splitext(filename)
                ext = ext.lower()
                matched = False
                
                for cat, data in self.categories.items():
                    if ext in data[1]:
                        target_dir = os.path.join(self.selected_path, cat)
                        if not os.path.exists(target_dir): os.makedirs(target_dir)
                        safe_name = self.get_unique_name(target_dir, filename)
                        shutil.move(file_path, os.path.join(target_dir, safe_name))
                        
                        cat_counts[cat] += 1
                        self.after(0, lambda c=cat, v=cat_counts[cat]: self.cards[c].update_count(v))
                        self.log(f"Moved {filename} -> {cat}")
                        matched = True
                        break
                
                if not matched:
                    target_dir = os.path.join(self.selected_path, "Others")
                    if not os.path.exists(target_dir): os.makedirs(target_dir)
                    safe_name = self.get_unique_name(target_dir, filename)
                    shutil.move(file_path, os.path.join(target_dir, safe_name))
                    self.log(f"Moved {filename} -> Others")

                moved_count += 1
                self.after(0, lambda p=(i + 1) / total: self.progress.set(p))
                time.sleep(0.01)

            self.after(0, lambda: self.finish_process(moved_count))
            
        except Exception as e:
            self.log(f"Critical Error: {e}", "error")
            self.set_status("Error Occurred", THEME["error"])
            self.after(0, lambda: self.action_btn.configure(state="normal", text="TRY AGAIN"))

    def finish_process(self, count):
        self.set_status("Organization Complete", THEME["success"])
        self.log(f"Successfully organized {count} files.", "success")
        self.progress.set(1)
        self.action_btn.configure(state="normal", text="OPEN FOLDER", fg_color=THEME["success"], command=lambda: open_file_explorer(self.selected_path))
        self.reset_btn.configure(state="normal")
        self.browse_btn.configure(state="normal")

    def reset_app(self):
        self.selected_path = ""
        self.path_entry.delete(0, "end")
        self.progress.set(0)
        self.log_box.configure(state="normal")
        self.log_box.delete("0.0", "end")
        self.log_box.insert("0.0", "> System Reset. Ready.\n")
        self.log_box.configure(state="disabled")
        for card in self.cards.values(): card.update_count(0)
        self.action_btn.configure(text="START ORGANIZATION", fg_color=THEME["primary"], command=self.start_processing_thread)
        self.set_status("System Ready", THEME["text_sub"])

if __name__ == "__main__":
    app = FileOrganizerApp()
    app.mainloop()