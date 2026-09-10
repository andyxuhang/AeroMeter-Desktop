"""AeroMeter product shim over the reusable Galeon device protocol."""
from galeon_protocol.measurement import *  # noqa: F401,F403

# Discovery is a product concern, not part of the common wire protocol.
DEVICE_NAME_PREFIX = "AeroMeter"
