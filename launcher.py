#!/usr/bin/env python3
import os
import sys
import subprocess
import platform
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk


# Cores do design original
BG = "#FEF8F4"
FG = "#1D1B19"
FG_MUTED = "#5B4039"
ACCENT = "#B02F00"
ACCENT_HOVER = "#FF5722"
BORDER = "#1D1B19"
CARD = "#FFFFFF"
OK = "#00A66C"
WARN = "#FCBC16"
ERR = "#BA1A1A"


class Launcher:
    def __init__(self, root):
        self.root = root
        self.root.title("Azumanga Donjara Daioh Launcher")
        self.root.geometry("1020x500")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)
        try:
            self.root.attributes('-toolwindow', True)
        except:
            pass
        
        # Center window on screen
        self.root.update_idletasks()
        w = 1020
        h = 500
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        
        # Game path = folder where exe/script lives
        if getattr(sys, 'frozen', False):
            self.game_dir = Path(sys.executable).parent
        else:
            self.game_dir = Path(__file__).parent
        
        # Images folder
        self.img_dir = self.game_dir / "imgs"
        
        # State
        self.status = {"rom": False, "textures": False, "emulator": False}
        self.images = {}
        
        self.load_images()
        self.build_ui()
        self.check_status_loop()
    
    def load_images(self):
        """Load all images from imgs folder - keep original aspect ratio"""
        for name in ["Jogar", "Creditos", "logo"]:
            path = self.img_dir / f"{name}.png"
            if path.exists():
                try:
                    img = Image.open(path)
                    self.images[name] = img
                except Exception as e:
                    print(f"Failed to load {name}: {e}")
    
    def build_ui(self):
        # Main container - top-aligned
        main_frame = tk.Frame(self.root, bg=BG)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Center container - anchored to top, centered horizontally
        center_frame = tk.Frame(main_frame, bg=BG)
        center_frame.pack(anchor="n", pady=20)
        
        # Two columns side by side with grid
        left_frame = tk.Frame(center_frame, bg=BG)
        left_frame.grid(row=0, column=0, padx=(0, 20), pady=0, sticky="n")
        
        right_frame = tk.Frame(center_frame, bg=BG)
        right_frame.grid(row=0, column=1, padx=(0, 0), pady=0, sticky="n")
        
        # === LEFT COLUMN === (aligned left)
        # Panel width constant: 420px outer = changelog width
        PANEL_W = 420
        GAP = 8
        BTN_OUTER_W = 206  # each button outer: 206px (200 inner + 6 border/padding)
        BTN_INNER_W = BTN_OUTER_W - 6  # 200px
        BTN_H = 78
        
        # Row container for JOGAR + CRÉDITOS side by side (matches PANEL_W)
        btn_row = tk.Frame(left_frame, bg=BG, width=PANEL_W, height=BTN_H)
        btn_row.pack_propagate(False)
        btn_row.pack(anchor="w", pady=(0, GAP))
        
        # JOGAR - left half
        jogar_outer = tk.Frame(btn_row, bg=BORDER, width=BTN_OUTER_W, height=BTN_H)
        jogar_outer.pack_propagate(False)
        jogar_outer.place(x=0, y=0)
        jogar_inner = tk.Frame(jogar_outer, bg=BG, width=BTN_INNER_W, height=BTN_H - 6)
        jogar_inner.pack_propagate(False)
        jogar_inner.place(x=3, y=3)
        self.btn_jogar = self.make_button(jogar_inner, "Jogar", self.launch_game, 
                                           max_width=BTN_INNER_W, height=BTN_H - 6, disabled=True)
        
        # CRÉDITOS - right half
        creditos_outer = tk.Frame(btn_row, bg=BORDER, width=BTN_OUTER_W, height=BTN_H)
        creditos_outer.pack_propagate(False)
        creditos_outer.place(x=BTN_OUTER_W + GAP, y=0)
        creditos_inner = tk.Frame(creditos_outer, bg=BG, width=BTN_INNER_W, height=BTN_H - 6)
        creditos_inner.pack_propagate(False)
        creditos_inner.place(x=3, y=3)
        self.btn_creditos = self.make_button(creditos_inner, "Creditos", self.show_credits, 
                                              max_width=BTN_INNER_W, height=BTN_H - 6)
        
        # Status text
        self.status_label = tk.Label(left_frame, text="Verificando arquivos...", 
                                     font=("Segoe UI", 9), fg=FG_MUTED, bg=BG)
        self.status_label.pack(anchor="w", pady=(0, GAP))
        
        # === CHANGELOG / PROGRESS PANEL ===
        self.build_changelog_panel(left_frame)
        
        # Version + update button below changelog
        ver_frame = tk.Frame(left_frame, bg=BG)
        ver_frame.pack(anchor="w", pady=(12, 0))
        
        self.version_label = tk.Label(ver_frame, text="v.0.1", 
                                      font=("Segoe UI", 10), fg=FG_MUTED, bg=BG)
        self.version_label.pack(side=tk.LEFT, padx=(0, 12))
        
        self.btn_update = tk.Button(ver_frame, text="VERIFICAR ATUALIZAÇÕES",
                                    font=("Segoe UI", 9, "bold"), fg=FG, bg=CARD,
                                    activebackground=ACCENT, activeforeground=CARD,
                                    bd=2, relief="solid", cursor="hand2",
                                    padx=12, pady=4, command=self.check_updates)
        self.btn_update.pack(side=tk.LEFT)
        
        # === RIGHT COLUMN ===
        # Logo only
        if "logo" in self.images:
            self.setup_logo(right_frame)
    
    def setup_logo(self, parent):
        """Setup logo at fixed size - no zoom/resize"""
        self.logo_original = self.images["logo"]
        
        # Logo label - fills available space
        self.logo_label = tk.Label(parent, bg=BG)
        self.logo_label.pack(fill=tk.BOTH, expand=True)
        
        # Render logo once at fixed size
        self.root.after(50, self.render_logo)
    
    def check_updates(self):
        """Check GitHub for updates"""
        import threading
        threading.Thread(target=self._check_updates_thread, daemon=True).start()
    
    def _check_updates_thread(self):
        try:
            self.root.after(0, lambda: self.status_label.config(text="Verificando atualizações...", fg=FG_MUTED))
            self.root.after(0, lambda: self.btn_update.config(state=tk.DISABLED))
            
            import requests
            r = requests.get("https://api.github.com/repos/Kanb4/AzumangaDonjaraBR/releases/latest", timeout=10)
            data = r.json()
            latest_tag = data["tag_name"]  # "v0.1", "v0.2", etc.
            
            # Simple version comparison
            current = "v0.1"
            if self._version_gt(latest_tag, current):
                # Find zip asset
                zip_asset = next((a for a in data["assets"] if a["name"].endswith(".zip")), None)
                if zip_asset:
                    self.root.after(0, lambda: self._prompt_update(latest_tag, zip_asset["browser_download_url"], data.get("body", "")))
                else:
                    self.root.after(0, lambda: messagebox.showerror("Erro", "Zip não encontrado no release."))
            else:
                self.root.after(0, lambda: messagebox.showinfo("Atualizações", f"Você já está na versão mais recente ({current})."))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Erro", f"Falha ao verificar atualizações:\n{e}"))
        finally:
            self.root.after(0, lambda: self.status_label.config(text="", fg=OK))
            self.root.after(0, lambda: self.btn_update.config(state=tk.NORMAL))
    
    def _version_gt(self, a, b):
        """Compare version tags like v0.1 < v0.2"""
        try:
            a_num = tuple(map(int, a.lstrip('v').split('.')))
            b_num = tuple(map(int, b.lstrip('v').split('.')))
            return a_num > b_num
        except:
            return a > b
    
    def _prompt_update(self, version, zip_url, changelog):
        msg = f"Nova versão {version} disponível!\n\n"
        if changelog:
            msg += f"Changelog:\n{changelog[:500]}"
            if len(changelog) > 500:
                msg += "..."
            msg += "\n\n"
        msg += "Baixar e instalar agora? (pode demorar, ~220MB)"
        
        if messagebox.askyesno("Atualização disponível", msg):
            self._do_full_update(zip_url)
    
    def _do_full_update(self, zip_url):
        import threading
        threading.Thread(target=self._download_and_install, args=(zip_url,), daemon=True).start()
    
    def _download_and_install(self, zip_url):
        try:
            import requests, zipfile, tempfile, shutil, subprocess, sys, os
            
            self.root.after(0, lambda: self.status_label.config(text="Baixando atualização...", fg=FG_MUTED))
            self.root.after(0, lambda: self.btn_jogar.config(state=tk.DISABLED))
            self.root.after(0, lambda: self.btn_update.config(state=tk.DISABLED))
            
            tmp_zip = os.path.join(tempfile.gettempdir(), "Azumanga_update.zip")
            
            # Download with progress
            with requests.get(zip_url, stream=True, timeout=30) as r:
                total = int(r.headers.get('content-length', 0))
                downloaded = 0
                with open(tmp_zip, "wb") as f:
                    for chunk in r.iter_content(8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total:
                                pct = downloaded * 100 // total
                                self.root.after(0, lambda p=pct: self.status_label.config(text=f"Baixando... {p}%"))
            
            self.root.after(0, lambda: self.status_label.config(text="Instalando...", fg=FG_MUTED))
            
            tmp_extract = os.path.join(tempfile.gettempdir(), "Azumanga_update")
            if os.path.exists(tmp_extract):
                shutil.rmtree(tmp_extract)
            
            with zipfile.ZipFile(tmp_zip, 'r') as z:
                z.extractall(tmp_extract)
            
            # Copy extracted files to game dir
            for item in os.listdir(tmp_extract):
                src = os.path.join(tmp_extract, item)
                dst = os.path.join(self.game_dir, item)
                if os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)
            
            self.root.after(0, lambda: self.status_label.config(text="Atualizado! Reiniciando...", fg=OK))
            
            # Restart new exe
            new_exe = os.path.join(self.game_dir, "Azumanga Launcher.exe")
            subprocess.Popen([new_exe])
            self.root.after(0, self.root.quit)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Erro", f"Falha na atualização:\n{e}"))
            self.root.after(0, lambda: self.btn_jogar.config(state=tk.NORMAL if all(self.status.values()) else tk.DISABLED))
            self.root.after(0, lambda: self.btn_update.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.status_label.config(text="", fg=OK))
    
    def build_changelog_panel(self, parent):
        """Build compact changelog/progress panel below credits button"""
        panel_w = 414  # match button max_width (PANEL_W - 6)
        
        # ===== PROGRESS PANEL =====
        prog_outer = tk.Frame(parent, bg=BORDER)
        prog_outer.pack(anchor="w", pady=(0, 8), fill=tk.X)
        
        prog_inner = tk.Frame(prog_outer, bg=CARD)  # #FFFFFF
        prog_inner.pack(padx=3, pady=3, fill=tk.X)
        
        prog_content = tk.Frame(prog_inner, bg=CARD)
        prog_content.pack(padx=14, pady=10, fill=tk.X)
        
        # Header
        prog_header = tk.Frame(prog_content, bg=CARD)
        prog_header.pack(fill=tk.X, pady=(0, 6))
        
        icon_frame = tk.Frame(prog_header, bg=OK, width=12, height=12)
        icon_frame.pack(side=tk.LEFT)
        icon_frame.pack_propagate(False)
        
        tk.Label(prog_header, text="TRADUÇÃO", font=("Segoe UI", 12, "bold"), 
                 fg=FG, bg=CARD).pack(side=tk.LEFT, padx=6)
        
        # Progress bar - simple canvas
        bar_canvas = tk.Canvas(prog_content, height=24, bg=CARD, 
                               highlightthickness=0, bd=0)
        bar_canvas.pack(fill=tk.X, pady=(0, 4))
        
        def draw_progress_bar(event=None):
            bar_canvas.delete("all")
            w = bar_canvas.winfo_width()
            h = 24
            # Background track
            bar_canvas.create_rectangle(0, 0, w, h, fill="#FFFFFF", outline=BORDER, width=2)
            # Fill (18.8%)
            fill_w = int(w * 0.188)
            bar_canvas.create_rectangle(0, 0, fill_w, h, fill=OK, outline="")
            # Percentage text
            bar_canvas.create_text(w // 2, h // 2, text="18,8%", font=("Segoe UI", 10, "bold"), fill=FG)
        
        bar_canvas.bind("<Configure>", draw_progress_bar)
        
        # Percent labels
        perc_row = tk.Frame(prog_content, bg=CARD)
        perc_row.pack(fill=tk.X)
        tk.Label(perc_row, text="MENUS E INTERFACES: 50%", font=("Segoe UI", 10, "bold"), 
                 fg=FG_MUTED, bg=CARD).pack(side=tk.LEFT)
        tk.Label(perc_row, text="CAMPANHA: 8,8%", font=("Segoe UI", 10, "bold"), 
                 fg=FG_MUTED, bg=CARD).pack(side=tk.RIGHT)
        
        # ===== CHANGELOG PANEL (scrollable) =====
        log_outer = tk.Frame(parent, bg=BORDER)
        log_outer.pack(anchor="w", pady=(0, 0), fill=tk.X)
        
        log_inner = tk.Frame(log_outer, bg=CARD)  # #FFFFFF
        log_inner.pack(padx=3, pady=3, fill=tk.X)
        
        # Canvas + scrollbar for scrolling
        log_canvas = tk.Canvas(log_inner, bg=CARD, highlightthickness=0, bd=0, height=100)
        log_scrollbar = tk.Scrollbar(log_inner, orient="vertical", command=log_canvas.yview)
        log_canvas.configure(yscrollcommand=log_scrollbar.set)
        
        log_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=8)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=8)
        
        # Content frame inside canvas
        log_content = tk.Frame(log_canvas, bg=CARD)
        log_canvas_window = log_canvas.create_window(0, 0, window=log_content, anchor="nw")
        
        # Header
        lang_header = tk.Frame(log_content, bg=CARD)
        lang_header.pack(fill=tk.X, padx=10, pady=(8, 4))
        
        lang_icon = tk.Frame(lang_header, bg=ACCENT, width=11, height=11)
        lang_icon.pack(side=tk.LEFT)
        lang_icon.pack_propagate(False)
        
        tk.Label(lang_header, text="CHANGELOG", font=("Segoe UI", 12, "bold"), 
                 fg=FG, bg=CARD).pack(side=tk.LEFT, padx=6)
        
        # Changelog items
        items = [
            "• Campanha da Chiyo traduzida",
            "• Menus e interfaces parcialmente traduzidas",
        ]
        
        for item in items:
            tk.Label(log_content, text=item, font=("Segoe UI", 10), 
                     fg=FG_MUTED, bg=CARD, anchor="w", justify="left", 
                     wraplength=panel_w - 40).pack(fill=tk.X, padx=14, pady=2)
        
        # Scroll handling
        def on_content_configure(event):
            log_canvas.configure(scrollregion=log_canvas.bbox("all"))
            log_canvas.itemconfig(log_canvas_window, width=log_canvas.winfo_width())
        
        def on_canvas_configure(event):
            log_canvas.itemconfig(log_canvas_window, width=event.width)
        
        def on_mousewheel(event):
            log_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        def on_mousewheel_linux(event):
            log_canvas.yview_scroll(-1 if event.num == 4 else 1, "units")
        
        log_content.bind("<Configure>", on_content_configure)
        log_canvas.bind("<Configure>", on_canvas_configure)
        log_canvas.bind_all("<MouseWheel>", on_mousewheel)
        log_canvas.bind_all("<Button-4>", on_mousewheel_linux)
        log_canvas.bind_all("<Button-5>", on_mousewheel_linux)
        
        def unbind(event):
            log_canvas.unbind_all("<MouseWheel>")
            log_canvas.unbind_all("<Button-4>")
            log_canvas.unbind_all("<Button-5>")
        log_canvas.bind("<Destroy>", unbind)
        
        # Store reference
        self.changelog_canvas = log_canvas

    def render_logo(self):
        """Render logo at fixed width, auto height (maintain aspect ratio)"""
        if not hasattr(self, 'logo_original'):
            return
        
        img = self.logo_original
        # Fixed width - much larger
        new_w = 522
        ratio = img.height / img.width
        new_h = int(new_w * ratio)
        
        # Don't upscale beyond original
        if new_w > img.width:
            new_w = img.width
            new_h = img.height
        
        img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        self.logo_photo = ImageTk.PhotoImage(img_resized)
        self.logo_label.configure(image=self.logo_photo)

    def make_button(self, parent, key, command, max_width=342, disabled=False, height=78):
        """
        Create brutalist button.
        - If image exists in self.images[key], use it + text (compound)
        - Otherwise use Unicode icon + text
        Parent must have fixed size (pack_propagate(False) + place).
        """
        # Button styling - JOGAR gets WARN (#FCBC16) background
        is_jogar = (key == "Jogar")
        btn_bg = WARN if (is_jogar and not disabled) else (CARD if not disabled else "#E8E0DA")
        btn_fg = FG if not disabled else FG_MUTED
        # JOGAR active = #EFB316, others = ACCENT
        btn_active_bg = "#EFB316" if (is_jogar and not disabled) else (ACCENT if not disabled else btn_bg)
        btn_active_fg = CARD if not disabled else btn_fg
        
        # Icon fallback mapping
        icons = {"Jogar": "▶", "Creditos": "✦"}
        icon = icons.get(key, "◆")
        label = key.upper()
        
        if key in self.images:
            # Use custom image + text (compound left)
            img = self.images[key]
            # Scale to 32px height, keep aspect ratio
            target_h = 32
            if img.height > target_h:
                ratio = target_h / img.height
                new_size = (int(img.width * ratio), target_h)
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            
            if not hasattr(self, '_btn_images'):
                self._btn_images = {}
            self._btn_images[key] = photo
            
            btn = tk.Button(parent, text=f"  {label}", image=photo, compound="left",
                           font=("Segoe UI", 15, "bold"), bd=0, command=command,
                           state=tk.NORMAL if not disabled else tk.DISABLED,
                           bg=btn_bg, fg=btn_fg,
                           activebackground=btn_active_bg, activeforeground=btn_active_fg,
                           cursor="hand2" if not disabled else "arrow",
                           padx=16, pady=0)
            btn.image = photo
        else:
            # Unicode icon + text fallback
            btn = tk.Button(parent, text=f"{icon}  {label}", font=("Segoe UI", 15, "bold"),
                           bd=0, command=command,
                           state=tk.NORMAL if not disabled else tk.DISABLED,
                           bg=btn_bg, fg=btn_fg,
                           activebackground=btn_active_bg, activeforeground=btn_active_fg,
                           cursor="hand2" if not disabled else "arrow",
                           padx=16, pady=0)
        
        btn.place(x=0, y=0, width=max_width, height=height)
        return btn

    def check_files(self):
        """Check if ROM, textures, emulator exist"""
        rom_ok = (self.game_dir / "Azumanga_Final.cue").exists() and \
                 (self.game_dir / "Azumanga_Final.bin").exists()
        
        textures_ok = (self.game_dir / "duckstation" / "textures" / "SLPS-03424" / "replacements").is_dir()
        
        system = platform.system().lower()
        if system == "windows":
            emu_path = self.game_dir / "duckstation" / "duckstation-qt-x64-ReleaseLTCG.exe"
        elif system == "darwin":
            emu_path = self.game_dir / "duckstation" / "duckstation-qt.app" / "Contents" / "MacOS" / "duckstation-qt"
        else:
            emu_path = self.game_dir / "duckstation" / "duckstation-qt"
        
        emu_ok = emu_path.exists()
        
        self.status = {"rom": rom_ok, "textures": textures_ok, "emulator": emu_ok}
        return self.status
    
    def update_status_ui(self):
        """Update status text"""
        missing = []
        if not self.status["rom"]:
            missing.append("ROM (cue/bin)")
        if not self.status["textures"]:
            missing.append("Texturas")
        if not self.status["emulator"]:
            missing.append("Emulador")
        
        all_ready = len(missing) == 0
        
        if all_ready:
            self.status_label.config(text="", fg=OK)
        else:
            self.status_label.config(text="Faltando: " + ", ".join(missing), fg=WARN)
        
        # Update button state directly
        self.btn_jogar.configure(state=tk.NORMAL if all_ready else tk.DISABLED)
        self.btn_jogar.configure(cursor="hand2" if all_ready else "arrow")
        # Update background color for JOGAR (FCBC16 when enabled)
        if all_ready:
            self.btn_jogar.configure(bg=WARN, activebackground=ACCENT)
        else:
            self.btn_jogar.configure(bg="#E8E0DA", activebackground="#E8E0DA")
    
    def check_status_loop(self):
        self.check_files()
        self.update_status_ui()
        self.root.after(3000, self.check_status_loop)
    
    def launch_game(self):
        if not all(self.status.values()):
            return
        
        system = platform.system().lower()
        if system == "windows":
            emu = self.game_dir / "duckstation" / "duckstation-qt-x64-ReleaseLTCG.exe"
        elif system == "darwin":
            emu = self.game_dir / "duckstation" / "duckstation-qt.app" / "Contents" / "MacOS" / "duckstation-qt"
        else:
            emu = self.game_dir / "duckstation" / "duckstation-qt"
        
        cue = self.game_dir / "Azumanga_Final.cue"
        cwd = self.game_dir / "duckstation"
        
        try:
            subprocess.Popen([str(emu), "-batch", str(cue)], cwd=str(cwd))
            self.root.quit()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao iniciar:\n{e}")
    
    def show_credits(self):
        messagebox.showinfo("Créditos", 
            "Azumanga Donjara Daioh - Tradução PT-BR\n\n"
            "Equipe YABAI SCAN\n\n"
            "Tradução: Ronald Debona\n"
            "Texturas: Kanba\n"
            "Testes: Nois\n\n"
            "Obrigado por jogar!\nVersão 2025.4")


class RoundedFrame(tk.Frame):
    """Frame with rounded corners using Canvas"""
    def __init__(self, parent, width, height, radius=4, bg_color=CARD, border_color=BORDER, border_width=3, **kwargs):
        # Extract custom kwargs before passing to parent
        self.width = width
        self.height = height
        self.radius = radius
        self.bg_color = bg_color
        self.border_color = border_color
        self.border_width = border_width
        
        super().__init__(parent, bg=parent.cget("bg"), **kwargs)
        
        # Canvas for rounded background
        self.canvas = tk.Canvas(self, width=width, height=height, 
                                highlightthickness=0, bg=parent.cget("bg"), bd=0)
        self.canvas.pack()
        
        # Inner frame for content (placed on canvas)
        self.inner = tk.Frame(self.canvas, bg=bg_color)
        self.inner_id = self.canvas.create_window(
            border_width, border_width, 
            window=self.inner, 
            width=width - 2 * border_width, 
            height=height - 2 * border_width,
            anchor="nw"
        )
        
        self.draw()
        self.canvas.bind("<Configure>", self.on_resize)
    
    def draw(self):
        self.canvas.delete("bg")
        w = self.canvas.winfo_width() or self.width
        h = self.canvas.winfo_height() or self.height
        r = self.radius
        bw = self.border_width
        
        # Draw border (outer rounded rect)
        self.canvas.create_rounded_rect(0, 0, w, h, r, 
                                         fill=self.border_color, outline="", tags="bg")
        # Draw inner background
        self.canvas.create_rounded_rect(bw, bw, w - bw, h - bw, max(0, r - bw), 
                                         fill=self.bg_color, outline="", tags="bg")
        
        # Update inner frame size
        self.canvas.coords(self.inner_id, bw, bw)
        self.canvas.itemconfig(self.inner_id, width=w - 2*bw, height=h - 2*bw)
    
    def on_resize(self, event):
        self.draw()


class ScrollableFrame(tk.Frame):
    """Scrollable frame with mousewheel support"""
    def __init__(self, parent, bg=CARD, height=140, **kwargs):
        super().__init__(parent, bg=bg, **kwargs)
        self.height = height
        
        # Canvas
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0, height=height)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Content frame
        self.content = tk.Frame(self.canvas, bg=bg)
        self.content_id = self.canvas.create_window(0, 0, window=self.content, anchor="nw")
        
        self.content.bind("<Configure>", self.on_content_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        
        # Mousewheel
        self.bind_mousewheel()
    
    def on_content_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        # Set content width to canvas width
        self.canvas.itemconfig(self.content_id, width=self.canvas.winfo_width())
    
    def on_canvas_configure(self, event):
        self.canvas.itemconfig(self.content_id, width=event.width)
    
    def bind_mousewheel(self):
        def on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        def on_mousewheel_linux(event):
            self.canvas.yview_scroll(-1 if event.num == 4 else 1, "units")
        
        self.canvas.bind_all("<MouseWheel>", on_mousewheel)
        self.canvas.bind_all("<Button-4>", on_mousewheel_linux)
        self.canvas.bind_all("<Button-5>", on_mousewheel_linux)
        
        # Unbind when destroyed
        def unbind(event):
            self.canvas.unbind_all("<MouseWheel>")
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")
        self.bind("<Destroy>", unbind)


# Add rounded rect method to Canvas
def _create_rounded_rect(self, x1, y1, x2, y2, radius=25, **kwargs):
    points = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1
    ]
    return self.create_polygon(points, smooth=True, **kwargs)

tk.Canvas.create_rounded_rect = _create_rounded_rect


def main():
    root = tk.Tk()
    # Disable maximize button on Windows
    try:
        root.attributes('-toolwindow', True)  # Removes maximize button
    except:
        pass
    
    try:
        ico = Path(__file__).parent / "imgs" / "logo.png"
        if ico.exists():
            img = Image.open(ico)
            photo = ImageTk.PhotoImage(img)
            root.iconphoto(True, photo)
    except:
        pass
    
    app = Launcher(root)
    root.mainloop()


if __name__ == "__main__":
    main()