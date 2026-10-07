import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

from kedar_terminal.assets import build, validate
from kedar_terminal.controller import run
from kedar_terminal.install import install, restore
from kedar_terminal.performance import monitor, processes, shell_startup, tree
from kedar_terminal.settings import atomic_json, load
from kedar_terminal.timeline import frame_at

ROOT = Path(__file__).resolve().parents[1]


class TimelineTests(unittest.TestCase):
    def setUp(self):
        self.config = load(ROOT / "config/animation.toml")

    def test_eight_phases_and_ten_cycles(self):
        for cycle in range(10):
            offset = cycle * 10.8
            expected = [(0.1, "en", "write"), (1.9, "en", "hold"), (3.9, "en", "erase"),
                        (5.1, "en", "gap"), (5.5, "mr", "write"), (7.3, "mr", "hold"),
                        (9.3, "mr", "erase"), (10.5, "mr", "gap")]
            for t, language, phase in expected:
                frame = frame_at(offset + t, self.config)
                self.assertEqual((frame.language, frame.phase), (language, phase))

    def test_reveal_erase_and_late_frames(self):
        reveal = [frame_at(i / 100, self.config).step for i in range(180)]
        erase = [frame_at(3.8 + i / 100, self.config).step for i in range(120)]
        self.assertEqual(reveal, sorted(reveal))
        self.assertEqual(erase, sorted(erase, reverse=True))
        self.assertEqual(frame_at(10800 + 0.7, self.config), frame_at(0.7, self.config))

    def test_invalid_settings(self):
        original = (ROOT / "config/animation.toml").read_text()
        for replacement in ('fps = 0', 'fps = 12.5', 'fps = 31'):
            with tempfile.TemporaryDirectory() as d:
                path = Path(d) / "animation.toml"
                path.write_text(original.replace("fps = 12", replacement))
                with self.assertRaises(ValueError):
                    load(path)


class AssetTests(unittest.TestCase):
    def test_preserves_unrelated_destination(self):
        with tempfile.TemporaryDirectory() as d:
            output = Path(d)
            unrelated = output / "keep.txt"
            unrelated.write_text("preserve me")
            with self.assertRaises(ValueError):
                build(load(ROOT / "config/animation.toml"), ROOT / "assets/landscape.png", output)
            self.assertEqual(unrelated.read_text(), "preserve me")

    def test_manifest_shaping_and_corruption(self):
        config = load(ROOT / "config/animation.toml")
        config["appearance"].update(width=320, height=320)
        config["animation"]["steps"] = 2
        with tempfile.TemporaryDirectory() as d:
            output = Path(d) / "frames"
            manifest = build(config, ROOT / "assets/landscape.png", output)
            self.assertEqual(len(manifest["files"]), 6)
            self.assertEqual(validate(config, output)["dimensions"], [320, 320])
            from PIL import Image, ImageChops
            base, en, mr = [Image.open(output / f) for f in ("blank.png", "en-002.png", "mr-002.png")]
            self.assertIsNotNone(ImageChops.difference(base, en).getbbox())
            self.assertIsNotNone(ImageChops.difference(base, mr).getbbox())
            self.assertIsNotNone(ImageChops.difference(en, mr).getbbox())
            (output / "mr-002.png").write_bytes(b"corrupt")
            with self.assertRaises(ValueError):
                validate(config, output)


class InstallationTests(unittest.TestCase):
    def test_backup_restore_and_preserve_unrelated_configuration(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "profile"
            self.assertIsNone(install(ROOT, target))
            (target / "kitty.conf").write_text("original customization")
            backup = install(ROOT, target)
            self.assertEqual((backup / "kitty.conf").read_text(), "original customization")
            saved = restore(backup, target)
            self.assertEqual((target / "kitty.conf").read_text(), "original customization")
            self.assertTrue((saved / "fish/config.fish").is_file())


class ControllerTests(unittest.TestCase):
    def test_no_retransmission_during_hold_and_scoped_cleanup(self):
        config = load(ROOT / "config/animation.toml")
        # Beginning with a whole-word hold makes duplicate transmission observable.
        config["animation"].update(write_on_seconds=0.05, fps=30)
        with tempfile.TemporaryDirectory() as d:
            runtime = Path(d)
            config_path = runtime / "animation.toml"
            text = (ROOT / "config/animation.toml").read_text().replace("write_on_seconds = 1.8", "write_on_seconds = 0.05").replace("fps = 12", "fps = 30")
            config_path.write_text(text)
            child = subprocess.Popen(["sleep", "0.30"])
            with patch("kedar_terminal.controller.BackgroundFrames") as cls:
                run(child, runtime, "unix:/owned.sock", config_path, runtime, "animated")
                paths = [call.args[0].name for call in cls.return_value.show.call_args_list]
                self.assertEqual(paths.count("en-022.png"), 1)
                self.assertLessEqual(len(paths), 3)
                cls.assert_called_once_with("unix:/owned.sock")
            child.wait()

    def test_failure_is_bounded_and_static(self):
        with tempfile.TemporaryDirectory() as d:
            runtime = Path(d)
            path = runtime / "animation.toml"
            path.write_bytes((ROOT / "config/animation.toml").read_bytes())
            child = subprocess.Popen(["sleep", "2.2"])
            with patch("kedar_terminal.controller.BackgroundFrames") as cls:
                cls.return_value.show.side_effect = OSError("control failed")
                run(child, runtime, "unix:/owned.sock", path, runtime, "animated")
                self.assertEqual(cls.return_value.show.call_count, 4)
                self.assertEqual(json.loads((runtime / "status.json").read_text())["mode"], "static")
            child.wait()


class PerformanceTests(unittest.TestCase):
    def test_tree(self):
        sample = {1: {"ppid": 0}, 2: {"ppid": 1}, 3: {"ppid": 2}, 4: {"ppid": 0}}
        self.assertEqual(set(tree(sample, [1])), {1, 2, 3})

    def test_live_report_and_pty_readiness(self):
        with tempfile.TemporaryDirectory() as d:
            report = monitor([os.getpid()], 0.25, 0.1, "test", Path(d) / "test")
            self.assertGreaterEqual(report["samples"], 2)
            self.assertGreater(report["rss_mean_mib"], 0)
            self.assertTrue((Path(d) / "test.csv").is_file())
            self.assertGreater(shell_startup("/bin/bash", 3)["median_ms"], 0)


if __name__ == "__main__":
    unittest.main()
