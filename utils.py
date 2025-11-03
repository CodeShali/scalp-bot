import csv
import json
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pytz
import yaml

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
STATE_FILE = DATA_DIR / "state.json"
TRADE_LOG_FILE = DATA_DIR / "trades.csv"
CONFIG_CACHE: Optional[Dict[str, Any]] = None
EASTERN_TZ = pytz.timezone("US/Eastern")


def ensure_directories() -> None:
    """Ensure required runtime directories exist."""
    for directory in (DATA_DIR, LOG_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def load_config(path: Optional[str] = None, force_reload: bool = False) -> Dict[str, Any]:
    """Load YAML configuration into memory.

    Args:
        path: Optional override path for the config file.
        force_reload: Force re-read from disk when True.

    Returns:
        Parsed configuration dictionary.
    """
    global CONFIG_CACHE

    if CONFIG_CACHE is not None and not force_reload:
        return CONFIG_CACHE

    config_path = Path(path) if path else BASE_DIR / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        CONFIG_CACHE = yaml.safe_load(f)

    return CONFIG_CACHE


def setup_logging(config: Dict[str, Any]) -> None:
    """Configure logging based on config.yaml settings."""
    ensure_directories()

    logging_config = config.get("logging", {})
    level_name = logging_config.get("level", "INFO")
    file_path = logging_config.get("file", "logs/bot.log")
    log_file = (BASE_DIR / file_path).resolve()
    log_file.parent.mkdir(parents=True, exist_ok=True)

    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    handlers: List[logging.Handler] = []

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter(log_format, date_format))
    handlers.append(stream_handler)

    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    handlers.append(file_handler)

    logging.basicConfig(level=level_name, handlers=handlers, force=True)


def read_state() -> Dict[str, Any]:
    """Load runtime state from disk."""
    ensure_directories()
    if not STATE_FILE.exists():
        return {}

    with STATE_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_state(state: Dict[str, Any]) -> None:
    """Persist runtime state to disk."""
    ensure_directories()
    with STATE_FILE.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def update_state(updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update the persisted state with additional keys."""
    state = read_state()
    state.update(updates)
    write_state(state)
    return state


def append_trade_log(record: Dict[str, Any]) -> None:
    """Append a trade record to the CSV trade log."""
    ensure_directories()
    is_new_file = not TRADE_LOG_FILE.exists()

    with TRADE_LOG_FILE.open("a", encoding="utf-8", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=[
            "timestamp",
            "ticker",
            "direction",
            "strike",
            "expiration",
            "entry_price",
            "exit_price",
            "contracts",
            "pnl_pct",
            "exit_reason",
        ])
        if is_new_file:
            writer.writeheader()
        writer.writerow(record)


def parse_time_range(range_str: str) -> Tuple[int, int]:
    """Parse a HH:MM-HH:MM range into integer minute offsets."""
    start_str, end_str = range_str.split("-")
    start_minutes = _time_str_to_minutes(start_str)
    end_minutes = _time_str_to_minutes(end_str)
    return start_minutes, end_minutes


def _time_str_to_minutes(hhmm: str) -> int:
    hours, minutes = map(int, hhmm.split(":"))
    return hours * 60 + minutes


def within_trading_windows(dt: Any, windows: Iterable[str]) -> bool:
    """Return True if datetime is within any of the configured trading windows."""
    if dt.tzinfo is None:
        dt = EASTERN_TZ.localize(dt)
    else:
        dt = dt.astimezone(EASTERN_TZ)

    minutes = dt.hour * 60 + dt.minute
    for window in windows:
        start, end = parse_time_range(window)
        if start <= minutes <= end:
            return True
    return False


def eastern_now() -> datetime:
    """Return the current timezone-aware datetime in US/Eastern."""
    return datetime.now(pytz.utc).astimezone(EASTERN_TZ)


def ensure_timezone(dt: Any) -> datetime:
    """Ensure a datetime is timezone aware in Eastern Time."""
    if dt.tzinfo is None:
        return EASTERN_TZ.localize(dt)
    return dt.astimezone(EASTERN_TZ)


def minutes_between(dt_start: Any, dt_end: Any) -> float:
    """Return the difference in minutes between two datetimes."""
    dt_start = ensure_timezone(dt_start)
    dt_end = ensure_timezone(dt_end)
    diff = dt_end - dt_start
    return diff.total_seconds() / 60.0


def rolling_iv_rank(iv_values: List[float], current_iv: float) -> Optional[float]:
    """Compute implied volatility rank (0-100) from historical IV values."""
    if not iv_values:
        return None
    max_iv = max(iv_values)
    min_iv = min(iv_values)
    if max_iv == min_iv:
        return 50.0
    return (current_iv - min_iv) / (max_iv - min_iv) * 100


def weighted_score(metrics: Dict[str, float], weights: Dict[str, float]) -> float:
    """Compute weighted score given metrics and weight mapping."""
    score = 0.0
    for key, weight in weights.items():
        score += metrics.get(key, 0.0) * weight
    return score


def chunk_list(items: List[Any], size: int) -> Iterable[List[Any]]:
    """Yield successive chunks from list."""
    for i in range(0, len(items), size):
        yield items[i:i + size]
