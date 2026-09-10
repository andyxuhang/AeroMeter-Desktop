"""Pure contract 1.0.0 measurement helpers; no device access or pressure zeroing."""
import math


def coefficient(sigma, mean, minimum_mean):
    if sigma is None or mean is None or not math.isfinite(sigma) or not math.isfinite(mean):
        return None
    return sigma / mean * 100 if sigma >= 0 and mean >= minimum_mean else None


class VolumeIntegrator:
    def __init__(self):
        self.previous = None

    def reset(self):
        self.previous = None

    def add(self, flow, dt, invalid=False):
        if invalid or not math.isfinite(flow):
            self.reset()
            return 0.0
        current = flow if flow > 0.5 else 0.0
        previous, self.previous = self.previous, current
        if previous is None or not 0 < dt < 1:
            return 0.0
        return (previous + current) * 0.5 * dt / 60
