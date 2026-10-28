"""Full-body Agent background scene for the existing, non-interactive underlay.

The scene owns only Canvas images and decorative shapes.  Mouse events remain
with the application's normal widgets; the owner calls :meth:`fire` on a left
click.  All expensive source-image work happens at load/resize time, while
rifle rotations use a small cache of cropped, quantized frames.
"""

from __future__ import annotations

from collections import OrderedDict
import math
from pathlib import Path
import time

from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageTk
import tkinter as tk


_RESAMPLE = getattr(Image, "Resampling", Image).LANCZOS
_ROTATE_RESAMPLE = getattr(Image, "Resampling", Image).BICUBIC


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _load_rgba(path: Path) -> Image.Image:
    if not path.is_file():
        raise FileNotFoundError(f"Agent scene asset is missing: {path}")
    with Image.open(path) as source:
        image = source.convert("RGBA")
    # Generated transparent assets can contain a few nearly invisible pixels
    # along the border.  Cropping those keeps the animation pivot predictable.
    bounds = image.getchannel("A").point(lambda alpha: 255 if alpha > 8 else 0).getbbox()
    if bounds is None:
        raise ValueError(f"Agent scene asset is empty: {path}")
    return image.crop(bounds)


def _dim_rgba(image: Image.Image, background: str, amount: float) -> Image.Image:
    if amount <= 0:
        return image
    alpha = image.getchannel("A")
    rgb = Image.blend(image.convert("RGB"), Image.new("RGB", image.size, background), amount)
    result = rgb.convert("RGBA")
    result.putalpha(alpha)
    return result


class AgentScene:
    """A full-height agent and pointer-aimed rifle, drawn behind the main UI.

    ``pointer_fn`` must return coordinates relative to the underlay Canvas.
    ``variant='agentgun'`` enables rifle and firing, while ``agenteyes`` keeps
    the same body and uses a subtle pointer-driven parallax for the gaze pose.
    No Tk event bindings or extra windows are created here.
    """

    FIRE_DURATION = 1.15
    MAX_AIM_DEGREES = 55.0
    ANGLE_STEP = 3.0
    GUN_CACHE_SIZE = 16

    def __init__(
        self,
        canvas: tk.Canvas,
        pointer_fn,
        color: str = "#ff6d10",
        bg: str = "#0f1116",
        dim: float = 0.0,
        variant: str = "agentgun",
        asset_dir: str | Path | None = None,
    ) -> None:
        self.cv = canvas
        self.pointer_fn = pointer_fn
        self.color = color
        self.bg = bg
        self.dim = _clamp(float(dim), 0.0, 0.85)
        self.variant = variant
        self.alive = True

        assets = Path(asset_dir) if asset_dir is not None else Path(__file__).resolve().parent / "art" / "agents"
        self._assets = assets
        self._body_source = _load_rgba(assets / "field_agent.png")
        self._rifle_source = _load_rgba(assets / "assault_rifle.png")
        backdrop_path = assets / "city_backdrop.png"
        if not backdrop_path.is_file():
            raise FileNotFoundError(f"Agent scene asset is missing: {backdrop_path}")
        with Image.open(backdrop_path) as source:
            self._city_source = source.convert("RGB")

        self._size = (0, 0)
        self._prepared_variant = None
        self._bg_photo = None
        self._body_photo = None
        self._flash_photos: tuple[ImageTk.PhotoImage, ...] = ()
        self._rifle_scaled = None
        self._rifle_mirrored = None
        self._gun_cache: OrderedDict[tuple[bool, int], tuple[ImageTk.PhotoImage, int, int]] = OrderedDict()
        self._items: dict[str, int] = {}
        self._body_x = self._body_y = 0.0
        self._body_w = self._body_h = 0
        self._pivot_x = self._pivot_y = 0.0
        self._gun_w = self._gun_h = self._gun_square = 0
        self._grip_x = self._grip_y = 0.0
        self._muzzle_x = self._muzzle_y = 0.0

        self._aim_angle = 0.0  # screen coordinates: positive angles point down
        self._aim_side = 1     # 1 points right; -1 points left
        self._last_render = time.monotonic()
        self.fire_until = 0.0
        self._fire_started = 0.0
        self._shot_angle = 0.0
        self._shot_side = 1

    @property
    def firing(self) -> bool:
        return self.variant == "agentgun" and time.monotonic() < self.fire_until

    def fire(self) -> None:
        """Start a cosmetic slow-motion shot; no game input is generated."""
        if not self.alive or self.variant != "agentgun":
            return
        now = time.monotonic()
        self._fire_started = now
        self.fire_until = now + self.FIRE_DURATION
        self._shot_angle = self._aim_angle
        self._shot_side = self._aim_side

    def _prepare(self, width: int, height: int) -> None:
        """Create the city and body Photos once per Canvas size change."""
        self._size = (width, height)
        self._prepared_variant = self.variant
        self._items.clear()
        self._gun_cache.clear()
        self.cv.delete("all")

        city = ImageOps.fit(self._city_source, (width, height), method=_RESAMPLE, centering=(0.50, 0.50))
        if self.dim:
            city = Image.blend(city, Image.new("RGB", city.size, self.bg), self.dim)
        self._bg_photo = ImageTk.PhotoImage(city, master=self.cv)
        self._items["background"] = self.cv.create_image(0, 0, anchor="nw", image=self._bg_photo)

        ratio = self._body_source.width / self._body_source.height
        body_height = min(int(height * 0.90), int(width * 0.52 / max(ratio, 0.01)))
        body_height = max(80, body_height)
        body_width = max(1, round(body_height * ratio))
        self._body_w, self._body_h = body_width, body_height
        self._body_x = width * 0.68 - body_width * 0.5
        self._body_y = height * 0.98 - body_height
        body = self._body_source.resize((body_width, body_height), _RESAMPLE)
        body = _dim_rgba(body, self.bg, self.dim * 0.68)
        self._body_photo = ImageTk.PhotoImage(body, master=self.cv)
        self._items["body"] = self.cv.create_image(self._body_x, self._body_y, anchor="nw", image=self._body_photo)

        # The agent asset is standing with both hands in front of the vest.
        # The rifle grip is anchored at that chest/hand position, not at the
        # character's waist or at the center of the entire window.
        self._pivot_x = self._body_x + body_width * 0.49
        self._pivot_y = self._body_y + body_height * 0.277

        gun_width = max(80, min(round(body_height * 0.57), round(width * 0.49)))
        gun_height = max(1, round(gun_width * self._rifle_source.height / self._rifle_source.width))
        self._gun_w, self._gun_h = gun_width, gun_height
        rifle = self._rifle_source.resize((gun_width, gun_height), _RESAMPLE)
        self._rifle_scaled = _dim_rgba(rifle, self.bg, self.dim * 0.55)
        self._rifle_mirrored = ImageOps.mirror(self._rifle_scaled)

        # Fractions are measured on the cropped rifle: grip near the rear of
        # the receiver, muzzle at the right edge of the barrel.
        self._grip_x, self._grip_y = gun_width * 0.365, gun_height * 0.57
        self._muzzle_x, self._muzzle_y = gun_width * 0.975, gun_height * 0.37
        radius = math.hypot(max(self._grip_x, gun_width - self._grip_x),
                            max(self._grip_y, gun_height - self._grip_y))
        self._gun_square = max(128, int(math.ceil(radius * 2 + 10)))
        self._flash_photos = self._make_flash_photos(max(50, min(130, int(height * 0.11))))

        if self.variant == "agentgun":
            self._items["tracer"] = self.cv.create_line(0, 0, 0, 0, fill="#ffba60", width=2, state="hidden")
            self._items["bullet"] = self.cv.create_oval(0, 0, 0, 0, fill="#fff4be", outline="", state="hidden")
            self._items["spark"] = self.cv.create_line(0, 0, 0, 0, fill="#ff7a28", width=2, state="hidden")
            self._items["flash"] = self.cv.create_image(0, 0, image=self._flash_photos[0], state="hidden")

    def _make_flash_photos(self, size: int) -> tuple[ImageTk.PhotoImage, ...]:
        photos = []
        for opacity in (1.0, 0.62, 0.30):
            base = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(base)
            c = size / 2
            draw.ellipse((c - size * .23, c - size * .23, c + size * .23, c + size * .23),
                         fill=(255, 134, 25, int(130 * opacity)))
            base = base.filter(ImageFilter.GaussianBlur(size * .10))
            draw = ImageDraw.Draw(base)
            rays = []
            for i in range(16):
                angle = i * math.pi / 8
                length = size * (.46 if i % 2 == 0 else .20)
                rays.append((c + length * math.cos(angle), c + length * math.sin(angle)))
            draw.polygon(rays, fill=(255, 205, 75, int(190 * opacity)))
            draw.ellipse((c - size * .09, c - size * .09, c + size * .09, c + size * .09),
                         fill=(255, 248, 210, int(245 * opacity)))
            photos.append(ImageTk.PhotoImage(base, master=self.cv))
        return tuple(photos)

    def _gun_frame(self, side: int, angle: float) -> tuple[ImageTk.PhotoImage, int, int]:
        bucket = int(round(_clamp(angle, -self.MAX_AIM_DEGREES, self.MAX_AIM_DEGREES) / self.ANGLE_STEP))
        key = (side < 0, bucket)
        frame = self._gun_cache.get(key)
        if frame is not None:
            self._gun_cache.move_to_end(key)
            return frame

        mirrored = side < 0
        gun = self._rifle_mirrored if mirrored else self._rifle_scaled
        square = Image.new("RGBA", (self._gun_square, self._gun_square), (0, 0, 0, 0))
        center = self._gun_square // 2
        grip_x = self._gun_w - self._grip_x if mirrored else self._grip_x
        square.alpha_composite(gun, (round(center - grip_x), round(center - self._grip_y)))
        # PIL rotates counterclockwise in screen space; the mirrored rifle
        # needs the opposite sign to aim toward the same pointer height.
        rotation = (bucket * self.ANGLE_STEP) * (1 if mirrored else -1)
        rotated = square.rotate(rotation, resample=_ROTATE_RESAMPLE, expand=False)
        bounds = rotated.getchannel("A").getbbox()
        if bounds is None:
            raise ValueError("The rotated rifle image has no visible pixels")
        photo = ImageTk.PhotoImage(rotated.crop(bounds), master=self.cv)
        frame = (photo, bounds[0] - center, bounds[1] - center)
        self._gun_cache[key] = frame
        if len(self._gun_cache) > self.GUN_CACHE_SIZE:
            self._gun_cache.popitem(last=False)
        return frame

    def _pointer_target(self) -> tuple[int, float, float]:
        try:
            x, y = self.pointer_fn()
        except Exception:
            return self._aim_side, self._aim_angle, 0.0
        dx, dy = x - self._pivot_x, y - self._pivot_y
        side = self._aim_side
        if dx > 20:
            side = 1
        elif dx < -20:
            side = -1
        angle = math.degrees(math.atan2(dy, max(20.0, abs(dx))))
        return side, _clamp(angle, -self.MAX_AIM_DEGREES, self.MAX_AIM_DEGREES), dx

    def _muzzle(self, side: int, angle: float, pivot_x: float, pivot_y: float) -> tuple[float, float]:
        dx = self._muzzle_x - self._grip_x
        if side < 0:
            dx = -dx
        dy = self._muzzle_y - self._grip_y
        rotation = math.radians(angle * (1 if side < 0 else -1))
        # PIL/screen-space counterclockwise transform.
        return (pivot_x + dx * math.cos(rotation) + dy * math.sin(rotation),
                pivot_y - dx * math.sin(rotation) + dy * math.cos(rotation))

    def _hide_shot(self) -> None:
        for name in ("tracer", "bullet", "spark", "flash"):
            item = self._items.get(name)
            if item is not None:
                self.cv.itemconfigure(item, state="hidden")

    def _render_shot(self, now: float, muzzle_x: float, muzzle_y: float, side: int, angle: float,
                     canvas_width: int) -> None:
        elapsed = now - self._fire_started
        if elapsed < 0 or elapsed >= self.FIRE_DURATION:
            self._hide_shot()
            return
        progress = elapsed / self.FIRE_DURATION
        direction_x = side * math.cos(math.radians(angle))
        direction_y = math.sin(math.radians(angle))

        # A visible projectile advances slowly for roughly 0.85 s.  The
        # tracer fades before the recoil finishes, making the short effect
        # read as slow motion instead of a single static muzzle flash.
        travel = _clamp(elapsed / 0.84, 0.0, 1.0)
        distance = max(180, canvas_width * 0.36) * (1 - (1 - travel) ** 1.35)
        bx, by = muzzle_x + direction_x * distance, muzzle_y + direction_y * distance
        if travel < 1:
            self.cv.coords(self._items["tracer"], muzzle_x, muzzle_y, bx, by)
            self.cv.itemconfigure(self._items["tracer"], state="normal",
                                  fill="#ffe1a1" if progress < .28 else "#bc692e",
                                  width=3 if progress < .28 else 2)
            radius = max(2.5, 5 * (1 - .45 * travel))
            self.cv.coords(self._items["bullet"], bx - radius, by - radius, bx + radius, by + radius)
            self.cv.itemconfigure(self._items["bullet"], state="normal")
        else:
            self.cv.itemconfigure(self._items["tracer"], state="hidden")
            self.cv.itemconfigure(self._items["bullet"], state="hidden")

        if elapsed < .34:
            flash_index = 0 if elapsed < .12 else 1 if elapsed < .23 else 2
            self.cv.coords(self._items["flash"], muzzle_x, muzzle_y)
            self.cv.itemconfigure(self._items["flash"], image=self._flash_photos[flash_index], state="normal")
        else:
            self.cv.itemconfigure(self._items["flash"], state="hidden")

        if .13 < elapsed < .72:
            fall = (elapsed - .13) / .59
            shell_x = self._pivot_x + side * self._gun_w * .12 - side * fall * self._gun_w * .24
            shell_y = self._pivot_y - self._gun_h * .18 + fall * fall * self._gun_h * .9
            self.cv.coords(self._items["spark"], shell_x - 4, shell_y - 2, shell_x + 4, shell_y + 2)
            self.cv.itemconfigure(self._items["spark"], state="normal")
        else:
            self.cv.itemconfigure(self._items["spark"], state="hidden")

    def render(self) -> None:
        if not self.alive:
            return
        try:
            width = max(100, self.cv.winfo_width())
            height = max(100, self.cv.winfo_height())
            if (width, height) != self._size or self.variant != self._prepared_variant:
                self._prepare(width, height)

            now = time.monotonic()
            dt = _clamp(now - self._last_render, 0.0, 0.25)
            self._last_render = now
            side, target_angle, pointer_dx = self._pointer_target()
            self._aim_side = side
            smoothing = 1 - math.exp(-dt / .09)
            self._aim_angle += (target_angle - self._aim_angle) * smoothing

            # The photo itself stays fixed in memory; a tiny parallax suggests
            # breathing/gaze without distorting the person or blocking UI.
            breath = math.sin(now * 1.7) * 1.5
            gaze = _clamp(pointer_dx / max(1, width), -.45, .45) * 9 if self.variant == "agenteyes" else 0
            self.cv.coords(self._items["body"], self._body_x + gaze, self._body_y + breath)
            if self.variant != "agentgun":
                return

            active_shot = now < self.fire_until
            render_side = self._shot_side if active_shot else self._aim_side
            render_angle = self._shot_angle if active_shot else self._aim_angle
            frame, ox, oy = self._gun_frame(render_side, render_angle)
            recoil = 0.0
            if active_shot:
                elapsed = now - self._fire_started
                recoil = 17.0 * math.sin(math.pi * _clamp(elapsed / .82, 0, 1)) * math.exp(-elapsed * 1.7)
            direction_x = render_side * math.cos(math.radians(render_angle))
            direction_y = math.sin(math.radians(render_angle))
            pivot_x = self._pivot_x + gaze - direction_x * recoil
            pivot_y = self._pivot_y + breath - direction_y * recoil
            gun_id = self._items.get("gun")
            if gun_id is None:
                gun_id = self.cv.create_image(pivot_x + ox, pivot_y + oy, anchor="nw", image=frame)
                self._items["gun"] = gun_id
                # The dynamic shot shapes are created during resize; keep the
                # weapon below those shapes for a readable muzzle flash.
                for name in ("tracer", "bullet", "spark", "flash"):
                    self.cv.tag_raise(self._items[name], gun_id)
            else:
                self.cv.coords(gun_id, pivot_x + ox, pivot_y + oy)
                self.cv.itemconfigure(gun_id, image=frame)

            muzzle_x, muzzle_y = self._muzzle(render_side, render_angle, pivot_x, pivot_y)
            if active_shot:
                self._render_shot(now, muzzle_x, muzzle_y, render_side, render_angle, width)
            else:
                self._hide_shot()
        except tk.TclError:
            self.alive = False

