import shutil
import subprocess
from pathlib import Path


class BackgroundFrames:
    def __init__(self, address: str):
        binary = shutil.which("kitten") or shutil.which("kitty")
        if not binary:
            raise ValueError("Kitty is not installed")
        self.prefix = [binary, "@", "--to", address]

    def show(self, image: Path) -> None:
        # --all is scoped to the unique owned socket, never other Kitty instances.
        # Older kitten CLIs omit cscaled even when Kitty supports it in config.
        subprocess.run(self.prefix + ["set-background-image", "--all", "--layout", "configured", str(image)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=3)

    def windows(self) -> str:
        return subprocess.check_output(self.prefix + ["ls"], text=True, timeout=3)
