"""Lightweight transparent hologram intro for TD2 Loot Advisor."""
from __future__ import annotations

import math
import time
import tkinter as tk


class IntroSplash:
    """Raise animated watch rings from a ground plane, then reveal the app mark."""

    WIDTH = 912
    HEIGHT = 720
    DURATION_MS = 4600
    KEY = "#010203"
    ORANGE = "#ff6d10"
    WHITE = "#edf0f5"
    MUTED = "#8d95a5"

    def __init__(self, root: tk.Tk, version: str, on_done):
        self.root = root
        self.version = version
        self.on_done = on_done
        self.started = None
        self.closed = False
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.configure(bg=self.KEY)
        try:
            # Windows removes this exact color, leaving the desktop visible around the effect.
            self.win.attributes("-transparentcolor", self.KEY)
        except tk.TclError:
            self.win.attributes("-alpha", .96)
        self.win.attributes("-topmost", True)
        sw, sh = self.win.winfo_screenwidth(), self.win.winfo_screenheight()
        x, y = max(0, (sw - self.WIDTH) // 2), max(0, (sh - self.HEIGHT) // 2)
        self.win.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")
        self.canvas = tk.Canvas(self.win, width=self.WIDTH, height=self.HEIGHT,
                                bg=self.KEY, bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self._draw_frame(0.0)
        self.win.bind("<Escape>", self.finish)
        self.win.bind("<Button-1>", self.finish)
        # Paint the transparent overlay before the app performs synchronous setup.
        self.win.update_idletasks()
        self.win.update()
        self.win.after(16, self._tick)

    @staticmethod
    def _color(level: float) -> str:
        level = min(1.0, max(0.0, level))
        start = (68, 36, 25)
        end = (255, 109, 16)
        return "#" + "".join(f"{round(a + (b - a) * level):02x}" for a, b in zip(start, end))

    @staticmethod
    def _hex_points(cx: float, cy: float, radius: float, angle: float):
        points = []
        for i in range(6):
            a = angle - math.pi / 2 + i * math.tau / 6
            points.extend((cx + math.cos(a) * radius, cy + math.sin(a) * radius))
        return points

    def _draw_frame(self, progress: float):
        c = self.canvas
        scale = 1.0
        c.delete("all")
        # Cubic easing keeps the hologram calm at the beginning and end.
        ease = progress * progress * (3 - 2 * progress)
        cx, watch_y, floor_y = self.WIDTH / 2, 260 * scale, 505 * scale
        pulse = .5 + .5 * math.sin(progress * math.tau * 2.2)
        rise = min(1.0, progress / .78)
        reveal = min(1.0, max(0.0, (progress - .38) / .52))
        reveal = reveal * reveal * (3 - 2 * reveal)

        # Animated Dark Zone backdrop: a subdued city silhouette, rain and
        # distant warning lights give the launch screen a game-world context.
        c.create_rectangle(0, 0, self.WIDTH, self.HEIGHT, fill="#070d14", outline="")
        for i, (bx, bw, bh) in enumerate(((34, 108, 168), (164, 74, 232),
                                           (274, 142, 126), (650, 122, 210),
                                           (786, 92, 260))):
            top = 520 - bh
            c.create_rectangle(bx, top, bx + bw, 520, fill="#0b151e", outline="#172936")
            for wx in range(bx + 14, bx + bw - 8, 22):
                for wy in range(top + 18, 500, 28):
                    phase = (i * 13 + wx + wy) % 11
                    if phase < 3:
                        c.create_rectangle(wx, wy, wx + 5, wy + 3,
                                           fill="#a34a1e" if phase == 0 else "#244252",
                                           outline="")
        # Slow rain streaks and a moving warning beacon.
        for i in range(26):
            rx = (i * 71 + progress * 180) % (self.WIDTH + 40) - 20
            ry = (i * 47 + progress * 260) % 520
            c.create_line(rx, ry, rx - 7, ry + 18,
                          fill="#203844" if i % 4 else "#5b3a2c", width=1)
        beacon_x = 96 + ((progress * 0.65) % 1.0) * 720
        c.create_oval(beacon_x - 3, 178, beacon_x + 3, 184,
                      fill="#ff6d10" if int(progress * 12) % 2 else "#63321d", outline="")
        c.create_text(24, 28, anchor="nw", text="THE DIVISION 2  //  DARK ZONE",
                      fill="#8395a2", font=("Segoe UI", 9, "bold"))
        c.create_text(self.WIDTH - 24, 28, anchor="ne", text="ISAC BOOT SEQUENCE",
                      fill="#b65325", font=("Segoe UI", 9, "bold"))

        # Dark Zone tactical scan: a faint city grid, sector marks and one
        # rogue signal make the intro feel like an in-game ISAC boot sequence.
        grid_alpha = min(1.0, progress / .22) * (1.0 - max(0.0, progress - .88) / .12)
        grid_color = self._color(.10 + .16 * grid_alpha)
        for gx in range(-360, 361, 45):
            c.create_line(cx + gx * scale, floor_y - 6 * scale,
                          cx + gx * .62 * scale, 220 * scale,
                          fill=grid_color, width=1)
        for gy in range(230, 506, 34):
            spread = (floor_y - gy) / 4.2
            c.create_line(cx - spread, gy, cx + spread, gy,
                          fill=grid_color, width=1)
        scan_x = cx - 310 * scale + ((progress * 1.35) % 1.0) * 620 * scale
        c.create_line(scan_x, 198 * scale, scan_x + 28 * scale, floor_y,
                      fill="#b84d24", width=1)
        c.create_text(cx - 292 * scale, 202 * scale, anchor="w",
                      text="DZ-01  //  ISAC SIGNAL",
                      fill="#aeb4bf", font=("Segoe UI", 8, "bold"))
        c.create_text(cx + 292 * scale, 202 * scale, anchor="e",
                      text="ROGUE ACTIVITY  0%" if progress < .56 else "ROGUE ACTIVITY  DETECTED",
                      fill="#ff4938" if progress >= .56 else "#737d8a",
                      font=("Segoe UI", 8, "bold"))
        if progress >= .48:
            threat = min(1.0, (progress - .48) / .3)
            tx, ty = cx + 210 * scale, 320 * scale
            tr = (9 + 14 * threat + 3 * pulse) * scale
            c.create_oval(tx-tr, ty-tr, tx+tr, ty+tr,
                          outline="#ff4938", width=1)
            c.create_oval(tx-3*scale, ty-3*scale, tx+3*scale, ty+3*scale,
                          fill="#ff4938", outline="")
            c.create_text(tx + 24 * scale, ty, anchor="w", text="ROGUE",
                          fill="#ff4938", font=("Segoe UI", 8, "bold"))

        # A restrained landing pad anchors the hologram without filling the screen.
        for i in range(3):
            rx = (52 + i * 34 + pulse * 4 + rise * 8) * scale
            ry = (7 + i * 2) * scale
            color = self._color(.28 + pulse * .30 - i * .055)
            c.create_oval(cx-rx, floor_y-ry, cx+rx, floor_y+ry,
                          outline=color, width=(2 if i == 0 else 1) * scale)
        c.create_line(cx-128*scale, floor_y, cx+128*scale, floor_y,
                      fill=self._color(.48 + pulse*.35), width=scale)
        for side in (-1, 1):
            c.create_line(cx + side*44*scale, floor_y-2*scale,
                          cx + side*104*scale, floor_y-88*rise*scale,
                          fill=self._color(.32 + pulse*.3), width=scale)

        # Several elliptical energy rings travel upward from the floor around the watch.
        for i in range(4):
            travel = (ease * 1.15 + i * .25) % 1.0
            # Smooth easing removes the abrupt start and stop of each rising ring.
            travel = travel * travel * (3 - 2 * travel)
            y = floor_y - travel * 235 * scale
            fade = math.sin(math.pi * travel)
            rx = (62 + 28 * travel + 6 * math.sin(progress * 6 + i)) * scale
            ry = (5 + 8 * travel) * scale
            color = self._color(.18 + .75 * fade)
            c.create_oval(cx-rx, y-ry, cx+rx, y+ry, outline=color,
                          width=(2 if fade > .66 else 1) * scale)
            if i % 2 == 0:
                # Small moving particles make the lift feel energetic without heavy effects.
                a = progress * 5 + i * 1.6
                px, py = cx + math.cos(a)*rx, y + math.sin(a)*ry
                c.create_oval(px-2*scale, py-2*scale, px+2*scale, py+2*scale,
                              fill=self.ORANGE, outline="")

        # Orbiting halo around the watch, with a subtle rotating perspective squeeze.
        orbit = progress * math.tau * 1.25
        for i in range(2):
            squeeze = .28 + .72 * abs(math.cos(orbit + i * .75))
            rx, ry = (79 + i*15) * scale * squeeze, (42 + i*7) * scale
            color = self._color(.36 + .32*pulse - i*.07)
            c.create_oval(cx-rx, watch_y-ry, cx+rx, watch_y+ry,
                          outline=color, width=(2 if i == 0 else 1) * scale)
        for i in range(3):
            c.create_arc(cx-92*scale, watch_y-54*scale, cx+92*scale, watch_y+54*scale,
                         start=(progress*480 + i*90) % 360, extent=42,
                         style="arc", outline=self.ORANGE if i == 0 else "#a24c20", width=2*scale)

        # Watch face: rotating hands and minute marks remain crisp on the transparent canvas.
        clock_r = 48 * scale
        c.create_oval(cx-clock_r, watch_y-clock_r, cx+clock_r, watch_y+clock_r,
                      outline=self.WHITE, width=2*scale)
        c.create_oval(cx-clock_r-8*scale, watch_y-clock_r-8*scale,
                      cx+clock_r+8*scale, watch_y+clock_r+8*scale,
                      outline=self._color(.5 + .4*pulse), width=scale)
        angle = progress * math.tau * 2.2
        for i in range(36):
            a = i * math.tau / 36 + angle
            inner = clock_r - (9 if i % 3 == 0 else 4) * scale
            outer = clock_r - scale
            color = self.ORANGE if i in (0, 1, 2, 3) else "#aeb4bf"
            c.create_line(cx+math.cos(a)*inner, watch_y+math.sin(a)*inner,
                          cx+math.cos(a)*outer, watch_y+math.sin(a)*outer,
                          fill=color, width=(2 if i % 3 == 0 else 1) * scale)
        hand = angle * 1.8 - math.pi/2
        c.create_line(cx, watch_y, cx+math.cos(hand)*33*scale,
                      watch_y+math.sin(hand)*33*scale,
                      fill=self.ORANGE, width=3*scale, capstyle="round")
        c.create_oval(cx-4*scale, watch_y-4*scale, cx+4*scale, watch_y+4*scale,
                      fill=self.WHITE, outline="")

        # The rotating SHD-inspired mark settles, then the app title unfolds beneath it.
        mark_progress = min(1.0, max(0.0, (progress - .2) / .8))
        mark_angle = (1-mark_progress) * math.tau * 2 + math.sin(progress * 7) * (1-mark_progress) * .3
        mark_radius = (13 + 17 * reveal) * scale
        mark_points = self._hex_points(cx, watch_y, mark_radius, mark_angle)
        c.create_polygon(*mark_points, fill="", outline=self.ORANGE, width=2*scale)
        c.create_oval(cx-4*scale, watch_y-4*scale, cx+4*scale, watch_y+4*scale,
                      fill=self.ORANGE, outline="")

        # A thin title rail fades in after the core locks on.
        flip = min(1.0, max(0.0, (progress - .35) / .55))
        flip = flip * flip * (3 - 2 * flip)
        panel_w = 560 * scale * math.sin(flip * math.pi / 2)
        panel_cy, panel_h = 400 * scale, 48 * scale
        c.create_rectangle(cx-panel_w/2, panel_cy-panel_h/2,
                           cx+panel_w/2, panel_cy+panel_h/2,
                           outline=self._color(.38 + reveal*.62), width=scale)
        if flip > .42:
            c.create_line(cx-panel_w/2+18*scale, panel_cy-panel_h/2,
                          cx-panel_w/2+18*scale, panel_cy+panel_h/2,
                          fill=self.ORANGE, width=2*scale)
            c.create_text(cx, panel_cy-5, text="TD2 LOOT ADVISOR", fill=self.WHITE,
                          font=("Segoe UI", round(18*scale), "bold"))
            c.create_text(cx, panel_cy+17*scale, text=f"ISAC OPERATIONS  ·  v{self.version}",
                          fill=self.MUTED, font=("Segoe UI", round(8*scale)))

        c.create_text(cx, 556*scale, text="I S A C   N E T W O R K   /   LINK INITIALIZING",
                      fill="#737d8a", font=("Segoe UI", round(8*scale)))
        progress_w = 148 * scale * progress
        c.create_line(cx-74*scale, 572*scale, cx-74*scale+progress_w, 572*scale,
                      fill=self.ORANGE, width=2*scale)

    def _tick(self):
        if self.closed:
            return
        try:
            if self.started is None:
                self.started = time.perf_counter()
            progress = min(1.0, (time.perf_counter() - self.started) * 1000 / self.DURATION_MS)
            self._draw_frame(progress)
            if progress >= 1:
                self.finish()
            else:
                self.win.after(24, self._tick)
        except tk.TclError:
            self.finish()

    def finish(self, _event=None):
        if self.closed:
            return
        self.closed = True
        try:
            if self.win.winfo_exists():
                self.win.destroy()
        except tk.TclError:
            pass
        try:
            if self.root.winfo_exists():
                self.root.deiconify()
                self.root.lift()
        except tk.TclError:
            pass
        callback, self.on_done = self.on_done, None
        if callback:
            callback()
