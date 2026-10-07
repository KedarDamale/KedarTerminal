"""Monotonic eight-phase loop; missed frames never accumulate drift."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Frame:
    language: str
    phase: str
    step: int


def frame_at(elapsed: float, config: dict) -> Frame:
    a = config["animation"]
    durations = [a[k] for k in ("write_on_seconds", "hold_seconds", "write_off_seconds", "gap_seconds")]
    t = elapsed % (2 * sum(durations))
    for language in ("en", "mr"):
        for phase, duration in zip(("write", "hold", "erase", "gap"), durations):
            if t < duration:
                fraction = t / duration
                step = {"write": round(fraction * a["steps"]), "hold": a["steps"],
                        "erase": round((1 - fraction) * a["steps"]), "gap": 0}[phase]
                return Frame(language, phase, step)
            t -= duration
    return Frame("en", "write", 0)
