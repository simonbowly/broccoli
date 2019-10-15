
try:
    from .version import BROCCOLI_GITHASH
except ImportError:
    BROCCOLI_GITHASH = "unknown"
