"""Animation suspension checks with fake Tk callbacks; no desktop window needed."""
from pathlib import Path
from types import SimpleNamespace
import sys
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image
import fx
import ui_art
import view3d


class FakeRoot:
    def __init__(self):
        self._td2_suspend_animations = True
        self._td2_animation_multiplier = 1.0
        self.jobs = []
        self.draws = 0
        self.pointer = (-1, -1)

    def _root(self): return self
    def state(self): return "normal"
    def winfo_viewable(self): return True
    def after(self, delay, callback):
        self.jobs.append((delay, callback)); return str(len(self.jobs))
    def after_cancel(self, job): pass
    def winfo_width(self): return 16
    def winfo_rootx(self): return 0
    def winfo_rooty(self): return 0
    def winfo_height(self): return 16
    def winfo_pointerxy(self): return self.pointer
    def delete(self, *args): self.draws += 1
    def create_oval(self, *args, **kwargs): self.draws += 1; return self.draws
    def coords(self, *args): pass
    def itemconfigure(self, *args, **kwargs): pass


class FakeWindow:
    def __init__(self): self.status = "normal"
    def state(self): return self.status
    def withdraw(self): self.status = "withdrawn"
    def deiconify(self): self.status = "normal"
    def geometry(self, *args): return "16x16+0+0"


class AnimationTests(unittest.TestCase):
    def test_trail_pauses_without_drawing_and_resumes(self):
        root = FakeRoot()
        trail = fx.TrailFX(root)
        trail.alive, trail.win, trail.cv = True, FakeWindow(), root
        trail._tick()
        self.assertEqual(root.draws, 0)
        self.assertEqual(root.jobs[-1][0], 300)
        self.assertTrue(trail.alive)
        root._td2_suspend_animations = False
        root.pointer = (5, 5)
        root.jobs[-1][1]()
        self.assertEqual(root.draws, 1)
        self.assertEqual(root.jobs[-1][0], 40)

    def test_watch_keeps_last_frame_and_resumes(self):
        root = FakeRoot()
        draws = []
        watch = fx.WatchBackground(root)
        watch.alive, watch.win = True, FakeWindow()
        watch.watch = SimpleNamespace(render=lambda: draws.append(1))
        watch._active = lambda: False
        watch._client_rect = lambda: (0, 0, 16, 16)
        watch._geo, watch._n, watch._last_z = (0, 0, 16, 16), 0, time.time()
        watch._tick()
        self.assertEqual(draws, [])
        self.assertEqual(watch.win.state(), "normal")
        self.assertEqual(root.jobs[-1][0], 300)
        root._td2_suspend_animations = False
        root.jobs[-1][1]()
        self.assertEqual(draws, [1])
        self.assertTrue(watch.alive)

    def banner(self):
        root = FakeRoot()
        banner = ui_art.Banner.__new__(ui_art.Banner)
        banner.cv, banner._jobs, banner.alive = root, {}, True
        banner._wh = lambda: (16, 16)
        banner.shown = []
        banner._show = lambda image, **kwargs: banner.shown.append(image)
        banner._compose = lambda image: image
        return root, banner

    def test_banner_video_retains_frame_while_paused(self):
        root, banner = self.banner()
        image = Image.new("RGB", (16, 16))
        banner._vframe, banner.video_on, banner.flash_state = image, True, None
        banner._video_tick()
        self.assertIs(banner._vframe, image)
        self.assertEqual(banner.shown, [])
        self.assertEqual(root.jobs[-1][0], 300)
        root._td2_suspend_animations = False
        root.jobs[-1][1]()
        self.assertEqual(banner.shown, [image])
        self.assertIsNone(banner._vframe)
        self.assertTrue(banner.video_on)

    def test_banner_fade_resumes_from_same_step(self):
        root, banner = self.banner()
        a, b = Image.new("RGB", (16, 16)), Image.new("RGB", (16, 16), "white")
        banner._fade(a, b, 2)
        self.assertEqual(banner.shown, [])
        root._td2_suspend_animations = False
        root.jobs[-1][1]()
        self.assertEqual(len(banner.shown), 1)
        self.assertEqual(banner.shown[0].getpixel((0, 0))[0], int(255 * 3 / 7))
        self.assertEqual(root.jobs[-1][0], 45)

    def test_banner_rotation_does_not_advance_while_paused(self):
        root, banner = self.banner()
        banner.paths, banner.idx, banner.interval = ["a", "b"], 0, 15
        banner.flash_state, banner.video_on = None, False
        banner._fitted = lambda path: path
        rendered = []
        banner._render = lambda **kwargs: rendered.append(1)
        banner.next()
        self.assertEqual((banner.idx, rendered), (0, []))
        root._td2_suspend_animations = False
        root.jobs[-1][1]()
        self.assertEqual((banner.idx, rendered), (1, [1]))

    def test_3d_spin_preserves_angle_then_resumes(self):
        root, rendered = FakeRoot(), []
        scene = SimpleNamespace(_root=lambda: root, _alive=True, auto_spin=True,
                                _drag=None, yaw=0, _spin_delay=40,
                                winfo_ismapped=lambda: True, render=lambda: rendered.append(1), after=root.after)
        scene.spin = lambda step=0.012, every=40: view3d.Scene3D.spin(scene, step, every)
        scene.spin()
        self.assertEqual((scene.yaw, rendered), (0, []))
        self.assertEqual(root.jobs[-1][0], 300)
        root._td2_suspend_animations = False
        root.jobs[-1][1]()
        self.assertGreater(scene.yaw, 0)
        self.assertEqual(rendered, [1])

    def test_sprite_spin_keeps_frame_and_pulse_while_paused(self):
        root, rendered = FakeRoot(), []
        sprite = SimpleNamespace(_root=lambda: root, _alive=True, _pulse=0, frame=0, n=48,
                                 model="operator", auto_spin=True, _drag=None, status={},
                                 winfo_ismapped=lambda: True, render=lambda: rendered.append(1), after=root.after)
        sprite.spin = lambda every=110: view3d.SpriteAgentView.spin(sprite, every)
        sprite.spin()
        self.assertEqual((sprite.frame, sprite._pulse, rendered), (0, 0, []))
        root._td2_suspend_animations = False
        root.jobs[-1][1]()
        self.assertEqual((sprite.frame, rendered), (1, [1]))

    def test_video_worker_does_not_advance_decoder_while_paused(self):
        paused, decoded, frames, sleeps = [True], [], [], []
        player = fx.VideoFX(".", lambda image: frames.append(image), lambda: (16, 16),
                            dim=0, pause_fn=lambda: paused[0])
        def source(path):
            decoded.append(1)
            yield Image.new("RGB", (16, 16))
        player._frames_pil = source
        def on_frame(image):
            frames.append(image); player.alive = False
        player.on_frame, player.alive = on_frame, True
        def sleep(delay):
            sleeps.append(delay)
            if paused[0]:
                self.assertEqual(decoded, [])
                paused[0] = False
        with patch("fx.list_videos", return_value=[Path("fake.webp")]), patch("fx.video_backend", return_value="pil"), patch("fx.time.sleep", side_effect=sleep):
            player._run()
        self.assertEqual((len(decoded), len(frames)), (1, 1))
        self.assertEqual(sleeps[0], 0.3)

    def test_animation_multiplier_reduces_frequency(self):
        root, banner = self.banner()
        root._td2_animation_multiplier = 0.5
        self.assertEqual(fx._animation_budget(root, 40)[1], 80)
        self.assertEqual(banner._animation_budget(40)[1], 80)
        self.assertEqual(view3d._animation_budget(root, 40)[1], 80)
        root._td2_animation_multiplier = float("nan")
        self.assertEqual(fx._animation_budget(root, 40)[1], 40)


if __name__ == "__main__":
    unittest.main()
