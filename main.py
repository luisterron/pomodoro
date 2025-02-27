import tkinter as tk
from tkinter import ttk, messagebox
import time
import threading
import os
import sys
from pygame import mixer
import webbrowser
from datetime import datetime
import urllib.request
import io
import base64

class ModernTooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
    
    def show_tooltip(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        self.tooltip.attributes('-topmost', True)
        
        frame = tk.Frame(self.tooltip, background="#282a36", borderwidth=1, relief="solid")
        frame.pack(fill="both", expand=True)
        
        label = tk.Label(frame, text=self.text, justify="left", background="#282a36", 
                        foreground="#f8f8f2", wraplength=250, padx=10, pady=5,
                        font=("Segoe UI", 9))
        label.pack()
    
    def hide_tooltip(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

class PomodoroApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pomodoro Elegante")
        self.root.geometry("400x600")
        self.root.resizable(False, False)
        self.root.configure(bg="#191A21")
        
        # Intentar cargar icono desde URL o usar respaldo
        self.load_icon()
        
        # Configurar ventana para que siempre esté por encima
        self.root.attributes("-topmost", True)
        
        # Variables de tiempo en segundos
        self.pomodoro_time = 25 * 60      # 25 minutos
        self.short_break_time = 5 * 60    # 5 minutos
        self.long_break_time = 15 * 60    # 15 minutos
        self.current_time = self.pomodoro_time
        self.timer_running = False
        self.timer_paused = False
        self.timer_thread = None
        self.pomodoro_count = 0
        self.current_mode = "Pomodoro"
        self.tasks = []
        self.show_info_panel = True
        self.compact_mode = False
        self.last_position = (0, 0)
        
        # Inicializar mixer para los sonidos
        mixer.init()
        
        # Definir colores (Esquema Dracula)
        self.colors = {
            "background": "#191A21",
            "surface": "#282A36",
            "primary": "#FF79C6",
            "secondary": "#8BE9FD",
            "accent": "#50FA7B",
            "text": "#F8F8F2",
            "text_secondary": "#6272A4",
            "error": "#FF5555",
            "warning": "#FFB86C",
            "success": "#50FA7B",
            "info": "#BD93F9"
        }
        
        # Configurar estilo
        self.setup_styles()
        
        # Crear la interfaz
        self.setup_ui()
        
        # Iniciar con panel de información visible
        self.update_info_panel_visibility()
        
        # Manejar el cierre de la ventana
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Permitir mover la ventana en modo compacto
        self.root.bind("<Button-1>", self.start_move)
        self.root.bind("<ButtonRelease-1>", self.stop_move)
        self.root.bind("<B1-Motion>", self.do_move)
    
    def load_icon(self):
        try:
            # URL de un ícono de tomate como respaldo
            icon_url = "https://cdn-icons-png.flaticon.com/512/6195/6195699.png"
            image_bytes = urllib.request.urlopen(icon_url).read()
            icon_data = io.BytesIO(image_bytes)
            
            if sys.platform == 'win32':
                import tempfile
                from PIL import Image, ImageTk
                
                temp_icon = tempfile.NamedTemporaryFile(suffix='.ico', delete=False)
                temp_icon.close()
                
                img = Image.open(icon_data)
                img.save(temp_icon.name)
                
                self.root.iconbitmap(temp_icon.name)
                
                def cleanup_icon():
                    try:
                        os.unlink(temp_icon.name)
                    except:
                        pass
                
                self.root.after(1000, cleanup_icon)
            else:
                from PIL import Image, ImageTk
                img = Image.open(icon_data)
                photo = ImageTk.PhotoImage(img)
                self.root.iconphoto(True, photo)
        except Exception as e:
            print(f"Error al cargar ícono: {e}")
    
    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        self.style.configure("Title.TLabel", 
                             font=("Segoe UI", 24, "bold"),
                             background=self.colors["background"], 
                             foreground=self.colors["accent"])
        
        self.style.configure("Subtitle.TLabel", 
                             font=("Segoe UI", 18, "bold"),
                             background=self.colors["background"], 
                             foreground=self.colors["primary"])
        
        self.style.configure("Timer.TLabel", 
                             font=("Segoe UI", 64, "bold"),
                             background=self.colors["background"], 
                             foreground=self.colors["primary"])
        
        self.style.configure("CompactTimer.TLabel", 
                             font=("Segoe UI", 28, "bold"),
                             background=self.colors["background"], 
                             foreground=self.colors["primary"])
        
        self.style.configure("Text.TLabel", 
                             font=("Segoe UI", 10),
                             background=self.colors["background"], 
                             foreground=self.colors["text"])
        
        self.style.configure("Info.TLabel", 
                             font=("Segoe UI", 10),
                             background=self.colors["surface"], 
                             foreground=self.colors["text"])
        
        self.style.configure("InfoTitle.TLabel", 
                             font=("Segoe UI", 12, "bold"),
                             background=self.colors["surface"], 
                             foreground=self.colors["info"])
        
        self.style.configure("Primary.TButton", 
                             font=("Segoe UI", 10, "bold"),
                             background=self.colors["primary"])
        self.style.map("Primary.TButton",
                       background=[("active", self.colors["secondary"])],
                       foreground=[("active", self.colors["background"])])
        
        self.style.configure("Mode.TButton", 
                             font=("Segoe UI", 10),
                             background=self.colors["surface"])
        self.style.map("Mode.TButton",
                       background=[("active", self.colors["primary"])],
                       foreground=[("active", self.colors["background"])])
        
        self.style.configure("Action.TButton", 
                             font=("Segoe UI", 10),
                             background=self.colors["surface"])
        self.style.map("Action.TButton",
                       background=[("active", self.colors["accent"])],
                       foreground=[("active", self.colors["background"])])
        
        self.style.configure("Horizontal.TProgressbar", 
                             background=self.colors["primary"],
                             troughcolor=self.colors["surface"],
                             borderwidth=0,
                             thickness=10)
    
    def setup_ui(self):
        self.main_container = tk.Frame(self.root, bg=self.colors["background"], padx=20, pady=20)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Panel superior: Título y botones de configuración
        self.top_panel = tk.Frame(self.main_container, bg=self.colors["background"])
        self.top_panel.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(self.top_panel, text="POMODORO TIMER", style="Title.TLabel").pack(side=tk.LEFT)
        
        self.info_button = ttk.Button(self.top_panel, text="ℹ️", style="Primary.TButton",
                                      command=self.toggle_info_panel, width=3)
        self.info_button.pack(side=tk.RIGHT)
        ModernTooltip(self.info_button, "Mostrar/ocultar información sobre la técnica Pomodoro")
        
        self.compact_button = ttk.Button(self.top_panel, text="🗕", style="Primary.TButton",
                                         command=self.toggle_compact_mode, width=3)
        self.compact_button.pack(side=tk.RIGHT, padx=(0, 5))
        ModernTooltip(self.compact_button, "Cambiar a modo compacto/normal")
        
        # Panel de información
        self.info_panel = tk.Frame(self.main_container, bg=self.colors["surface"], 
                                   padx=15, pady=15, borderwidth=1, relief="solid")
        ttk.Label(self.info_panel, text="¿Qué es la técnica Pomodoro?", 
                  style="InfoTitle.TLabel").pack(anchor=tk.W, pady=(0, 5))
        
        info_text = """La técnica Pomodoro es un método de gestión del tiempo desarrollado por Francesco Cirillo que usa intervalos de tiempo para mejorar la productividad y reducir el agotamiento mental.

Cómo funciona:
1. Elige una tarea para trabajar
2. Configura el temporizador (25 minutos por defecto)
3. Trabaja en la tarea hasta que suene la alarma
4. Toma un descanso corto (5 minutos)
5. Después de completar 4 pomodoros, toma un descanso largo (15 minutos)

Beneficios:
• Mejora la concentración y atención
• Reduce la fatiga mental
• Aumenta la consciencia sobre el tiempo
• Ayuda a evitar distracciones
• Mejora la planificación de tareas"""
        
        info_label = ttk.Label(self.info_panel, text=info_text, style="Info.TLabel", 
                               wraplength=360, justify="left")
        info_label.pack(fill=tk.X, pady=5)
        
        # Panel del temporizador
        self.timer_panel = tk.Frame(self.main_container, bg=self.colors["background"])
        self.timer_panel.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.mode_label = ttk.Label(self.timer_panel, text=self.current_mode, style="Subtitle.TLabel")
        self.mode_label.pack(pady=(10, 5))
        
        self.timer_label = ttk.Label(self.timer_panel, text=self.format_time(self.current_time), 
                                     style="Timer.TLabel")
        self.timer_label.pack(pady=(0, 20))
        
        self.stats_frame = tk.Frame(self.timer_panel, bg=self.colors["background"])
        self.stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.count_label = ttk.Label(self.stats_frame, 
                                     text=f"Pomodoros completados: {self.pomodoro_count}", 
                                     style="Text.TLabel")
        self.count_label.pack(anchor=tk.W)
        
        self.circles_frame = tk.Frame(self.stats_frame, bg=self.colors["background"])
        self.circles_frame.pack(anchor=tk.W, pady=(5, 0))
        self.update_pomodoro_circles()
        
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(self.timer_panel, orient="horizontal", 
                                            length=360, mode="determinate", 
                                            variable=self.progress_var,
                                            style="Horizontal.TProgressbar")
        self.progress_bar.pack(fill=tk.X, pady=(0, 20))
        
        self.modes_frame = tk.Frame(self.timer_panel, bg=self.colors["background"])
        self.modes_frame.pack(fill=tk.X, pady=(0, 20))
        
        button_width = 12
        self.pomodoro_button = ttk.Button(self.modes_frame, text="Pomodoro", 
                                          command=lambda: self.change_mode("Pomodoro"),
                                          style="Mode.TButton", width=button_width)
        self.pomodoro_button.grid(row=0, column=0, padx=5)
        ModernTooltip(self.pomodoro_button, "Período de trabajo concentrado (25 min)")
        
        self.short_break_button = ttk.Button(self.modes_frame, text="Descanso Corto", 
                                             command=lambda: self.change_mode("Descanso Corto"),
                                             style="Mode.TButton", width=button_width)
        self.short_break_button.grid(row=0, column=1, padx=5)
        ModernTooltip(self.short_break_button, "Breve descanso entre pomodoros (5 min)")
        
        self.long_break_button = ttk.Button(self.modes_frame, text="Descanso Largo", 
                                            command=lambda: self.change_mode("Descanso Largo"),
                                            style="Mode.TButton", width=button_width)
        self.long_break_button.grid(row=0, column=2, padx=5)
        ModernTooltip(self.long_break_button, "Descanso más largo después de 4 pomodoros (15 min)")
        
        self.modes_frame.grid_columnconfigure(0, weight=1)
        self.modes_frame.grid_columnconfigure(1, weight=1)
        self.modes_frame.grid_columnconfigure(2, weight=1)
        
        self.controls_frame = tk.Frame(self.timer_panel, bg=self.colors["background"])
        self.controls_frame.pack(fill=tk.X)
        
        control_width = 10
        self.start_button = ttk.Button(self.controls_frame, text="▶ Iniciar", 
                                       command=self.start_timer, 
                                       style="Action.TButton", width=control_width)
        self.start_button.grid(row=0, column=0, padx=5)
        ModernTooltip(self.start_button, "Iniciar el temporizador")
        
        self.pause_button = ttk.Button(self.controls_frame, text="⏸ Pausar", 
                                       command=self.pause_timer, 
                                       style="Action.TButton", width=control_width,
                                       state=tk.DISABLED)
        self.pause_button.grid(row=0, column=1, padx=5)
        ModernTooltip(self.pause_button, "Pausar/reanudar el temporizador")
        
        self.reset_button = ttk.Button(self.controls_frame, text="↺ Reiniciar", 
                                       command=self.reset_timer, 
                                       style="Action.TButton", width=control_width)
        self.reset_button.grid(row=0, column=2, padx=5)
        ModernTooltip(self.reset_button, "Reiniciar el temporizador actual")
        
        self.controls_frame.grid_columnconfigure(0, weight=1)
        self.controls_frame.grid_columnconfigure(1, weight=1)
        self.controls_frame.grid_columnconfigure(2, weight=1)
        
        self.bottom_panel = tk.Frame(self.main_container, bg=self.colors["background"], pady=10)
        self.bottom_panel.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = ttk.Label(self.bottom_panel, 
                                      text="Listo para empezar. ¡Configura tu primer pomodoro!", 
                                      style="Text.TLabel")
        self.status_label.pack(fill=tk.X)
        
        self.datetime_label = ttk.Label(self.bottom_panel, text="", style="Text.TLabel")
        self.datetime_label.pack(fill=tk.X, pady=(5, 0))
        self.update_datetime()
        
        self.setup_compact_ui()
    
    def setup_compact_ui(self):
        self.compact_frame = tk.Frame(self.root, bg=self.colors["background"], padx=5, pady=5)
        
        self.compact_top = tk.Frame(self.compact_frame, bg=self.colors["background"])
        self.compact_top.pack(fill=tk.X, expand=True)
        
        self.expand_button = ttk.Button(self.compact_top, text="🗖", style="Primary.TButton",
                                        command=self.toggle_compact_mode, width=2)
        self.expand_button.pack(side=tk.RIGHT, padx=(5, 0))
        ModernTooltip(self.expand_button, "Expandir a modo normal")
        
        self.compact_mode_label = ttk.Label(self.compact_top, text=self.current_mode[:3], 
                                            style="Text.TLabel")
        self.compact_mode_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.compact_timer = ttk.Label(self.compact_frame, text=self.format_time(self.current_time), 
                                       style="CompactTimer.TLabel")
        self.compact_timer.pack(pady=(0, 5))
        
        self.compact_buttons = tk.Frame(self.compact_frame, bg=self.colors["background"])
        self.compact_buttons.pack(fill=tk.X)
        
        self.compact_play = ttk.Button(self.compact_buttons, text="▶", style="Action.TButton",
                                       command=self.toggle_play_pause, width=3)
        self.compact_play.pack(side=tk.LEFT, padx=(0, 5))
        
        self.compact_reset = ttk.Button(self.compact_buttons, text="↺", style="Action.TButton",
                                        command=self.reset_timer, width=3)
        self.compact_reset.pack(side=tk.LEFT)
        
        self.compact_circles = tk.Frame(self.compact_buttons, bg=self.colors["background"])
        self.compact_circles.pack(side=tk.RIGHT)
        # Inicialmente el modo compacto está oculto.
        # self.compact_frame.pack_forget()
    
    def toggle_play_pause(self):
        if not self.timer_running:
            self.start_timer()
        else:
            self.pause_timer()
    
    def update_compact_ui(self):
        self.compact_timer.config(text=self.format_time(self.current_time))
        self.compact_mode_label.config(text=self.current_mode[:3])
        
        if not self.timer_running or self.timer_paused:
            self.compact_play.config(text="▶")
        else:
            self.compact_play.config(text="⏸")
        
        for widget in self.compact_circles.winfo_children():
            widget.destroy()
        
        for i in range(4):
            canvas_size = 10
            circle = tk.Canvas(self.compact_circles, width=canvas_size, height=canvas_size, 
                                 bg=self.colors["background"], highlightthickness=0)
            if i < (self.pomodoro_count % 4):
                circle.create_oval(1, 1, canvas_size-1, canvas_size-1, 
                                   fill=self.colors["primary"], outline="")
            else:
                circle.create_oval(1, 1, canvas_size-1, canvas_size-1, 
                                   fill="", outline=self.colors["text_secondary"])
            circle.pack(side=tk.LEFT, padx=2)
    
    def toggle_compact_mode(self):
        self.compact_mode = not self.compact_mode
        
        if self.compact_mode:
            self.last_position = (self.root.winfo_x(), self.root.winfo_y())
            self.main_container.pack_forget()
            self.update_compact_ui()
            self.compact_frame.pack(fill=tk.BOTH, expand=True)
            
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            compact_width = 150
            compact_height = 120
            x_position = screen_width - compact_width - 20
            y_position = screen_height - compact_height - 60
            self.root.geometry(f"{compact_width}x{compact_height}+{x_position}+{y_position}")
        else:
            self.compact_frame.pack_forget()
            self.main_container.pack(fill=tk.BOTH, expand=True)
            self.root.geometry("400x600+{}+{}".format(*self.last_position))
    
    def start_move(self, event):
        if self.compact_mode:
            self.x = event.x
            self.y = event.y
    
    def stop_move(self, event):
        if self.compact_mode:
            self.x = None
            self.y = None
    
    def do_move(self, event):
        if self.compact_mode and (self.x is not None and self.y is not None):
            new_x = self.root.winfo_x() + (event.x - self.x)
            new_y = self.root.winfo_y() + (event.y - self.y)
            self.root.geometry(f"+{new_x}+{new_y}")
    
    def update_datetime(self):
        now = datetime.now()
        date_text = now.strftime("%d/%m/%Y %H:%M:%S")
        self.datetime_label.config(text=f"Última actualización: {date_text}")
        self.root.after(1000, self.update_datetime)
    
    def toggle_info_panel(self):
        self.show_info_panel = not self.show_info_panel
        self.update_info_panel_visibility()
    
    def update_info_panel_visibility(self):
        if self.show_info_panel:
            self.info_panel.pack(fill=tk.X, pady=(0, 15), before=self.timer_panel)
            self.info_button.config(text="✕")
        else:
            self.info_panel.pack_forget()
            self.info_button.config(text="ℹ️")
    
    def update_pomodoro_circles(self):
        for widget in self.circles_frame.winfo_children():
            widget.destroy()
        
        for i in range(4):
            circle = tk.Canvas(self.circles_frame, width=20, height=20, 
                               bg=self.colors["background"], highlightthickness=0)
            if i < (self.pomodoro_count % 4):
                circle.create_oval(2, 2, 18, 18, fill=self.colors["primary"], outline="")
            else:
                circle.create_oval(2, 2, 18, 18, fill="", outline=self.colors["text_secondary"])
            circle.pack(side=tk.LEFT, padx=3)
        
        if self.compact_mode:
            self.update_compact_ui()
    
    def format_time(self, seconds):
        minutes, seconds = divmod(seconds, 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def start_timer(self):
        if self.timer_running and self.timer_paused:
            self.timer_paused = False
            self.start_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.NORMAL, text="⏸ Pausar")
            self.status_label.config(text=f"Reanudando {self.current_mode.lower()}...")
            if self.compact_mode:
                self.compact_play.config(text="⏸")
            return
        
        if not self.timer_running:
            self.timer_running = True
            self.start_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.NORMAL)
            if self.compact_mode:
                self.compact_play.config(text="⏸")
            
            if self.current_mode == "Pomodoro":
                self.status_label.config(text="¡Concentración! Trabajando en el pomodoro actual...")
            else:
                self.status_label.config(text=f"Tomando un {self.current_mode.lower()}. ¡Relájate!")
            
            self.timer_thread = threading.Thread(target=self.run_timer)
            self.timer_thread.daemon = True
            self.timer_thread.start()
    
    def pause_timer(self):
        if self.timer_running and not self.timer_paused:
            self.timer_paused = True
            self.pause_button.config(text="▶ Reanudar")
            self.start_button.config(state=tk.NORMAL)
            self.status_label.config(text=f"{self.current_mode} en pausa. Continúa cuando estés listo.")
            if self.compact_mode:
                self.compact_play.config(text="▶")
        else:
            self.timer_paused = False
            self.pause_button.config(text="⏸ Pausar")
            self.start_button.config(state=tk.DISABLED)
            self.status_label.config(text=f"Reanudando {self.current_mode.lower()}...")
            if self.compact_mode:
                self.compact_play.config(text="⏸")
    
    def run_timer(self):
        total_duration = self.get_mode_duration()
        while self.current_time > 0 and self.timer_running:
            if not self.timer_paused:
                time.sleep(1)
                self.current_time -= 1
                self.root.after(0, self.update_timer_ui)
            else:
                time.sleep(0.1)
        if self.current_time <= 0 and self.timer_running:
            self.root.after(0, self.timer_finished)
    
    def update_timer_ui(self):
        self.timer_label.config(text=self.format_time(self.current_time))
        progress = (1 - self.current_time / self.get_mode_duration()) * 100
        self.progress_var.set(progress)
        if self.compact_mode:
            self.update_compact_ui()
    
    def timer_finished(self):
        self.timer_running = False
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED, text="⏸ Pausar")
        self.status_label.config(text=f"{self.current_mode} completado.")
        try:
            mixer.music.load("alarm_sound.mp3")
            mixer.music.play()
        except Exception as e:
            print("Error al reproducir sonido:", e)
        if self.current_mode == "Pomodoro":
            self.pomodoro_count += 1
            self.count_label.config(text=f"Pomodoros completados: {self.pomodoro_count}")
            self.update_pomodoro_circles()
        messagebox.showinfo("Tiempo completado", f"¡El {self.current_mode.lower()} ha finalizado!")
    
    def reset_timer(self):
        self.timer_running = False
        self.timer_paused = False
        self.current_time = self.get_mode_duration()
        self.timer_label.config(text=self.format_time(self.current_time))
        self.progress_var.set(0)
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED, text="⏸ Pausar")
        self.status_label.config(text="Temporizador reiniciado.")
        if self.compact_mode:
            self.update_compact_ui()
    
    def get_mode_duration(self):
        if self.current_mode == "Pomodoro":
            return self.pomodoro_time
        elif self.current_mode == "Descanso Corto":
            return self.short_break_time
        elif self.current_mode == "Descanso Largo":
            return self.long_break_time
        return self.pomodoro_time
    
    def change_mode(self, mode):
        if self.timer_running:
            if not messagebox.askyesno("Confirmar", "El temporizador está corriendo. ¿Deseas cambiar de modo y reiniciar el temporizador?"):
                return
            self.reset_timer()
        self.current_mode = mode
        self.mode_label.config(text=mode)
        if self.compact_mode:
            self.compact_mode_label.config(text=mode[:3])
        self.current_time = self.get_mode_duration()
        self.timer_label.config(text=self.format_time(self.current_time))
        self.progress_var.set(0)
        self.status_label.config(text=f"Modo cambiado a {mode}. Listo para iniciar.")
    
    def on_close(self):
        self.timer_running = False
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = PomodoroApp(root)
    root.mainloop()
