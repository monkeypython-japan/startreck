"""オブジェクト命名: 名前プールとカウンタ管理。"""
from __future__ import annotations
import random

# ── 連邦基地 (星座名) ────────────────────────────────────────────
_FED_BASE_POOL_SRC = [
    "Orion", "Andromeda", "Perseus", "Cassiopeia", "Cygnus",
    "Lyra", "Aquila", "Hercules", "Virgo", "Leo",
    "Gemini", "Taurus", "Scorpius", "Sagittarius", "Draco",
    "Pegasus", "Aquarius", "Canis Major", "Centaurus", "Corvus",
    "Crater", "Columba", "Vela", "Puppis",
]
_fed_base_pool: list[str] = []


def next_fed_base_name() -> str:
    global _fed_base_pool
    if not _fed_base_pool:
        _fed_base_pool = _FED_BASE_POOL_SRC.copy()
        random.shuffle(_fed_base_pool)
    return _fed_base_pool.pop()


# ── クリンゴン基地 (ロシア・中国の河川・山脈) ───────────────────
_KLI_BASE_POOL_SRC = [
    "Lena", "Yenisei", "Volga", "Amur", "Angara",
    "Irtysh", "Kolyma", "Ob", "Altai", "Sayan",
    "Yangtze", "Huang He", "Kunlun", "Tian Shan", "Qilian",
]
_kli_base_pool: list[str] = []


def next_kli_base_name() -> str:
    global _kli_base_pool
    if not _kli_base_pool:
        _kli_base_pool = _KLI_BASE_POOL_SRC.copy()
        random.shuffle(_kli_base_pool)
    return _kli_base_pool.pop()


# ── 連邦艦艇 (欧米首都) ─────────────────────────────────────────
_FED_VESSEL_POOL_SRC = [
    "London", "Paris", "Berlin", "Madrid", "Rome",
    "Vienna", "Brussels", "Amsterdam", "Stockholm", "Oslo",
    "Copenhagen", "Helsinki", "Warsaw", "Prague", "Budapest",
    "Athens", "Lisbon", "Dublin", "Ottawa", "Washington",
    "Canberra", "Wellington", "Bern", "Reykjavik", "Riga",
    "Tallinn", "Vilnius", "Bratislava", "Ljubljana", "Zagreb",
]
_fed_vessel_pool: list[str] = []


def next_fed_vessel_name() -> str:
    global _fed_vessel_pool
    if not _fed_vessel_pool:
        _fed_vessel_pool = _FED_VESSEL_POOL_SRC.copy()
        random.shuffle(_fed_vessel_pool)
    return _fed_vessel_pool.pop()


# ── クリンゴン艦艇 (番号制) ─────────────────────────────────────
_kli_heavy_counter: int = 0
_kli_destroyer_counter: int = 0
_kli_guard_counter: int = 0


def next_kli_heavy_name() -> str:
    global _kli_heavy_counter
    _kli_heavy_counter += 1
    return f"C-{_kli_heavy_counter}"


def next_kli_destroyer_name() -> str:
    global _kli_destroyer_counter
    _kli_destroyer_counter += 1
    return f"D-{_kli_destroyer_counter}"


def next_kli_guard_name() -> str:
    global _kli_guard_counter
    _kli_guard_counter += 1
    return f"G-{_kli_guard_counter}"


# ── リセット ─────────────────────────────────────────────────────
def reset_counters() -> None:
    """ゲームリセット時に呼び出す。プールとカウンタを全て初期化する。"""
    global _fed_base_pool, _kli_base_pool, _fed_vessel_pool
    global _kli_heavy_counter, _kli_destroyer_counter, _kli_guard_counter
    _fed_base_pool = []
    _kli_base_pool = []
    _fed_vessel_pool = []
    _kli_heavy_counter = 0
    _kli_destroyer_counter = 0
    _kli_guard_counter = 0
