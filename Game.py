import math
import random
import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox

# Try importing sound handlers cross-platform
try:
    import winsound  # Native on Windows
except ImportError:
    winsound = None

try:
    import pygame
    pygame.mixer.init()
except ImportError:
    pygame = None

# ==========================================
# ADVANCED ROCK-PAPER-SCISSORS & BEYOND
# Built with Tkinter & Canvas Animation
# ==========================================

CHOICES = {
    "Rock": {"beats": ["Scissors", "Fire"], "symbol": "✊", "color": "#E74C3C"},
    "Paper": {"beats": ["Rock", "Water"], "symbol": "✋", "color": "#3498DB"},
    "Scissors": {"beats": ["Paper", "Water"], "symbol": "✌️", "color": "#2ECC71"},
    "Fire": {"beats": ["Paper", "Scissors"], "symbol": "🔥", "color": "#E67E22"},
    "Water": {"beats": ["Rock", "Fire"], "symbol": "💧", "color": "#1ABC9C"},
}

MODES = ["Classic (RPS)", "Elemental (5-Way RPSFW)", "Ultimate Combo"]


class SoundManager:
    """Handles sound effects cross-platform or via system sound beeps."""
    @staticmethod
    def play(sound_type):
        if winsound:
            # Native Windows procedural sounds if no audio files present
            if sound_type == "start":
                winsound.Beep(600, 150)
                winsound.Beep(800, 200)
            elif sound_type == "win":
                winsound.Beep(523, 100) # C5
                winsound.Beep(659, 100) # E5
                winsound.Beep(784, 200) # G5
            elif sound_type == "lose":
                winsound.Beep(400, 150)
                winsound.Beep(300, 250)
            elif sound_type == "draw":
                winsound.Beep(440, 150)
                winsound.Beep(440, 150)
            elif sound_type == "ultimate":
                winsound.Beep(800, 80)
                winsound.Beep(1000, 80)
                winsound.Beep(1200, 200)
        else:
            # Cross-platform terminal fallback bell
            print("\a", end="", flush=True)


class Particle:
    """Particle system for background and visual action effects."""
    def __init__(self, canvas, x, y, color=None, is_bg=False):
        self.canvas = canvas
        self.is_bg = is_bg
        self.x = x
        self.y = y
        self.radius = random.randint(2, 6) if is_bg else random.randint(4, 10)
        self.color = color or random.choice(["#FFD700", "#FF5733", "#33FF57", "#3385FF", "#F033FF"])
        
        if is_bg:
            self.vx = random.uniform(-0.5, 0.5)
            self.vy = random.uniform(-0.8, -0.2)
            self.life = 1.0
            self.decay = random.uniform(0.002, 0.005)
        else:
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 8)
            self.vx = math.cos(angle) * speed
            self.vy = math.sin(angle) * speed
            self.life = 1.0
            self.decay = random.uniform(0.02, 0.05)

        self.id = self.canvas.create_oval(
            self.x - self.radius, self.y - self.radius,
            self.x + self.radius, self.y + self.radius,
            fill=self.color, outline=""
        )

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= self.decay
        
        if self.is_bg and self.y < 0:
            self.y = 600
            self.x = random.randint(0, 900)
            self.life = 1.0
            
        self.canvas.coords(
            self.id,
            self.x - self.radius, self.y - self.radius,
            self.x + self.radius, self.y + self.radius
        )
        return self.life > 0

    def destroy(self):
        self.canvas.delete(self.id)


class ModernRPSGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Ultra Rock-Paper-Scissors Master")
        self.root.geometry("900x680")
        self.root.resizable(False, False)
        
        # State variables
        self.player_name = "Player 1"
        self.player_score = 0
        self.cpu_score = 0
        self.streak = 0
        self.best_streak = 0
        self.special_charge = 0  # Ultimate charge meter (0 to 100)
        self.current_mode = "Elemental (5-Way RPSFW)"
        
        # CPU AI Tracking
        self.history = []
        
        # Animation & Particle management
        self.particles = []
        self.bg_particles = []
        self.animating_clash = False

        self.setup_ui()
        self.init_background_particles()
        self.animate_loop()
        
        # Play Start Sound when application initializes
        SoundManager.play("start")

    def setup_ui(self):
        # Canvas setup
        self.canvas = tk.Canvas(self.root, width=900, height=680, bg="#0F0F1A", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Header Frame (Name Input & Mode Selector)
        top_frame = tk.Frame(self.canvas, bg="#1A1A2E")
        top_frame.place(x=20, y=15, width=860, height=50)

        tk.Label(top_frame, text="PLAYER:", fg="#8E94F2", bg="#1A1A2E", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT, padx=10)
        
        self.name_entry = tk.Entry(top_frame, font=("Segoe UI", 11), bg="#252545", fg="white", insertbackground="white", bd=0)
        self.name_entry.insert(0, "CyberKnight")
        self.name_entry.pack(side=tk.LEFT, padx=5, ipady=3)
        
        btn_apply = tk.Button(top_frame, text="Set Name", bg="#4E54C8", fg="white", font=("Segoe UI", 9, "bold"), bd=0, command=self.update_name)
        btn_apply.pack(side=tk.LEFT, padx=5)

        tk.Label(top_frame, text="MODE:", fg="#8E94F2", bg="#1A1A2E", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT, padx=(30, 10))
        
        self.mode_var = tk.StringVar(value=self.current_mode)
        mode_dropdown = ttk.Combobox(top_frame, textvariable=self.mode_var, values=MODES, state="readonly", width=22)
        mode_dropdown.pack(side=tk.LEFT, padx=5)
        mode_dropdown.bind("<<ComboboxSelected>>", self.change_mode)

        # Scoreboard Canvas Items
        self.lbl_player_title = self.canvas.create_text(220, 100, text=self.player_name, fill="#00F0FF", font=("Segoe UI", 18, "bold"))
        self.lbl_cpu_title = self.canvas.create_text(680, 100, text="CPU (AI)", fill="#FF0055", font=("Segoe UI", 18, "bold"))

        self.lbl_player_score = self.canvas.create_text(220, 140, text="0", fill="white", font=("Segoe UI", 36, "bold"))
        self.lbl_cpu_score = self.canvas.create_text(680, 140, text="0", fill="white", font=("Segoe UI", 36, "bold"))

        self.lbl_streak = self.canvas.create_text(450, 100, text="STREAK: 0", fill="#FFD700", font=("Segoe UI", 14, "bold"))
        self.lbl_status = self.canvas.create_text(450, 140, text="Choose your Move!", fill="#FFFFFF", font=("Segoe UI", 16, "italic"))

        # Arena Display (Center stage)
        self.p_choice_draw = self.canvas.create_text(220, 260, text="❓", font=("Segoe UI Emoji", 72))
        self.c_choice_draw = self.canvas.create_text(680, 260, text="❓", font=("Segoe UI Emoji", 72))

        self.vs_draw = self.canvas.create_text(450, 260, text="VS", fill="#555577", font=("Impact", 32))

        # Special Ability / Combo Meter
        self.canvas.create_rectangle(300, 360, 600, 375, outline="#444466", width=2)
        self.special_bar = self.canvas.create_rectangle(300, 360, 300, 375, fill="#FFD700", width=0)
        self.lbl_special = self.canvas.create_text(450, 390, text="ULTIMATE CHARGE: 0%", fill="#FFD700", font=("Segoe UI", 10, "bold"))

        # Control Buttons Container
        self.buttons_frame = tk.Frame(self.canvas, bg="#0F0F1A")
        self.buttons_frame.place(x=50, y=430, width=800, height=180)
        
        self.create_move_buttons()

        # Reset Game Button
        btn_reset = tk.Button(self.root, text="🔄 Reset Game", bg="#22223B", fg="#AAAAAA", font=("Segoe UI", 10), bd=0, command=self.reset_game)
        btn_reset.place(x=400, y=635, width=100, height=30)

    def create_move_buttons(self):
        for widget in self.buttons_frame.winfo_children():
            widget.destroy()

        active_choices = ["Rock", "Paper", "Scissors"] if "Classic" in self.current_mode else list(CHOICES.keys())

        for move in active_choices:
            data = CHOICES[move]
            btn = tk.Button(
                self.buttons_frame,
                text=f"{data['symbol']}\n{move}",
                font=("Segoe UI", 12, "bold"),
                bg="#1A1A2E",
                fg=data['color'],
                activebackground=data['color'],
                activeforeground="white",
                bd=2,
                relief="groove",
                command=lambda m=move: self.play_round(m)
            )
            btn.pack(side=tk.LEFT, expand=True, fill="both", padx=8, pady=10)

        # Ultimate Move Button
        self.btn_ultimate = tk.Button(
            self.buttons_frame,
            text="⚡ ULTIMATE\nBEAM",
            font=("Segoe UI", 11, "bold"),
            bg="#333344",
            fg="#777777",
            state=tk.DISABLED,
            bd=2,
            command=self.use_ultimate
        )
        self.btn_ultimate.pack(side=tk.LEFT, expand=True, fill="both", padx=8, pady=10)

    def update_name(self):
        new_name = self.name_entry.get().strip()
        if new_name:
            self.player_name = new_name
            self.canvas.itemconfig(self.lbl_player_title, text=self.player_name)

    def change_mode(self, event=None):
        self.current_mode = self.mode_var.get()
        self.create_move_buttons()
        self.reset_game()

    def get_cpu_choice(self):
        if not self.history or random.random() < 0.3:
            return random.choice(list(CHOICES.keys()) if "Classic" not in self.current_mode else ["Rock", "Paper", "Scissors"])

        most_common_player_move = max(set(self.history), key=self.history.count)
        counters = [m for m, data in CHOICES.items() if most_common_player_move in data['beats']]
        
        if "Classic" in self.current_mode:
            counters = [c for c in counters if c in ["Rock", "Paper", "Scissors"]]
            
        return random.choice(counters)

    def play_round(self, player_move):
        if self.animating_clash:
            return

        self.history.append(player_move)
        cpu_move = self.get_cpu_choice()
        self.run_clash_animation(player_move, cpu_move)

    def use_ultimate(self):
        if self.special_charge < 100 or self.animating_clash:
            return

        SoundManager.play("ultimate")
        self.special_charge = 0
        self.update_special_bar()
        self.create_burst_particles(450, 260, color="#FFD700", amount=80)
        
        cpu_move = random.choice(list(CHOICES.keys()))
        self.canvas.itemconfig(self.p_choice_draw, text="⚡")
        self.canvas.itemconfig(self.c_choice_draw, text=CHOICES[cpu_move]['symbol'])
        
        self.handle_result("WIN", "ULTIMATE OVERLOAD!", "#FFD700")

    def run_clash_animation(self, p_move, c_move):
        self.animating_clash = True
        self.canvas.itemconfig(self.lbl_status, text="CLASHING...", fill="#FFD700")

        def animate_step(step=0):
            if step < 6:
                offset = 15 if step % 2 == 0 else -15
                self.canvas.itemconfig(self.p_choice_draw, text="✊")
                self.canvas.itemconfig(self.c_choice_draw, text="✊")
                self.canvas.coords(self.p_choice_draw, 220, 260 + offset)
                self.canvas.coords(self.c_choice_draw, 680, 260 - offset)
                self.root.after(80, lambda: animate_step(step + 1))
            else:
                self.canvas.coords(self.p_choice_draw, 220, 260)
                self.canvas.coords(self.c_choice_draw, 680, 260)
                self.canvas.itemconfig(self.p_choice_draw, text=CHOICES[p_move]['symbol'])
                self.canvas.itemconfig(self.c_choice_draw, text=CHOICES[c_move]['symbol'])
                self.evaluate_round(p_move, c_move)
                self.animating_clash = False

        animate_step()

    def evaluate_round(self, p_move, c_move):
        if p_move == c_move:
            self.handle_result("DRAW", "IT'S A TIE!", "#AAAAAA")
        elif c_move in CHOICES[p_move]['beats']:
            self.handle_result("WIN", f"{p_move} beats {c_move}!", "#00FF66")
        else:
            self.handle_result("LOSE", f"{c_move} beats {p_move}!", "#FF3366")

    def handle_result(self, result, msg, color):
        self.canvas.itemconfig(self.lbl_status, text=msg, fill=color)

        if result == "WIN":
            SoundManager.play("win")
            self.player_score += 1
            self.streak += 1
            self.best_streak = max(self.best_streak, self.streak)
            self.special_charge = min(100, self.special_charge + 25)
            self.create_burst_particles(220, 260, color="#00FF66")
        elif result == "LOSE":
            SoundManager.play("lose")
            self.cpu_score += 1
            self.streak = 0
            self.create_burst_particles(680, 260, color="#FF3366")
        else:
            SoundManager.play("draw")
            self.special_charge = min(100, self.special_charge + 10)

        # Update HUD Labels
        self.canvas.itemconfig(self.lbl_player_score, text=str(self.player_score))
        self.canvas.itemconfig(self.lbl_cpu_score, text=str(self.cpu_score))
        self.canvas.itemconfig(self.lbl_streak, text=f"STREAK: {self.streak}")
        self.update_special_bar()

    def update_special_bar(self):
        width = (self.special_charge / 100) * 300
        self.canvas.coords(self.special_bar, 300, 360, 300 + width, 375)
        self.canvas.itemconfig(self.lbl_special, text=f"ULTIMATE CHARGE: {self.special_charge}%")

        if self.special_charge == 100:
            self.btn_ultimate.config(state=tk.NORMAL, bg="#FFD700", fg="#000000")
        else:
            self.btn_ultimate.config(state=tk.DISABLED, bg="#333344", fg="#777777")

    def init_background_particles(self):
        for _ in range(40):
            p = Particle(self.canvas, random.randint(0, 900), random.randint(0, 680), is_bg=True)
            self.bg_particles.append(p)

    def create_burst_particles(self, x, y, color=None, amount=30):
        for _ in range(amount):
            self.particles.append(Particle(self.canvas, x, y, color=color))

    def animate_loop(self):
        for p in self.bg_particles:
            p.update()

        self.particles = [p for p in self.particles if p.update()]
        self.root.after(20, self.animate_loop)

    def reset_game(self):
        SoundManager.play("start")
        self.player_score = 0
        self.cpu_score = 0
        self.streak = 0
        self.special_charge = 0
        self.history.clear()

        self.canvas.itemconfig(self.lbl_player_score, text="0")
        self.canvas.itemconfig(self.lbl_cpu_score, text="0")
        self.canvas.itemconfig(self.lbl_streak, text="STREAK: 0")
        self.canvas.itemconfig(self.lbl_status, text="Game Reset! Select a move.", fill="#FFFFFF")
        self.canvas.itemconfig(self.p_choice_draw, text="❓")
        self.canvas.itemconfig(self.c_choice_draw, text="❓")
        self.update_special_bar()


if __name__ == "__main__":
    root = tk.Tk()
    app = ModernRPSGame(root)
    root.mainloop()