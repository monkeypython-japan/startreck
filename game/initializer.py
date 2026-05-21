"""ゲーム初期配置: 仕様書の配置ルールに従ってオブジェクトを生成・配置する。"""
from __future__ import annotations
import math
import random
from game.coords import Vec2, wrap_vec, GRID
from game.universe import Universe
from game.objects.star import Star
from game.objects.base_station import BaseStation
from game.vessels.destroyer import Destroyer
from game.vessels.heavy_cruiser import HeavyCruiser
from game.vessels.special_ship import SpecialShip
from game.constants import (
    STAR_COUNT_MIN, STAR_COUNT_MAX,
    KLINGON_FLEET_COUNT, KLINGON_FLEET_SIZE,
    FEDERATION_BASE_COUNT, FEDERATION_FLEET_SIZE,
    FLEET_ORBIT_RADIUS,
)

SPACE_SIZE = 10.0
MIN_BASE_SEPARATION = 1.5   # 基地同士の最小距離 (座標単位)


def _random_pos() -> Vec2:
    return Vec2(random.uniform(0, SPACE_SIZE), random.uniform(0, SPACE_SIZE))


def _random_sector_center() -> Vec2:
    sx = random.randint(0, 9)
    sy = random.randint(0, 9)
    return Vec2(sx + 0.5, sy + 0.5)


def _orbit_positions(center: Vec2, radius_grid: float, count: int) -> list[Vec2]:
    """中心から radius_grid 離れた円上に count 個の等間隔点を返す。"""
    r = radius_grid * GRID
    return [
        wrap_vec(Vec2(
            center.x + math.cos(2 * math.pi * i / count) * r,
            center.y + math.sin(2 * math.pi * i / count) * r,
        ))
        for i in range(count)
    ]


def _place_bases(n: int) -> list[Vec2]:
    """基地を互いに MIN_BASE_SEPARATION 以上離れた位置に配置する。"""
    positions: list[Vec2] = []
    attempts = 0
    while len(positions) < n and attempts < 1000:
        attempts += 1
        candidate = _random_sector_center()
        if all(
            abs(candidate.x - p.x) + abs(candidate.y - p.y) >= MIN_BASE_SEPARATION
            for p in positions
        ):
            positions.append(candidate)
    return positions


def initialize(universe: Universe) -> SpecialShip:
    """宇宙を初期化してプレーヤーの特務艦を返す。"""

    # 恒星 (20〜30個)
    star_count = random.randint(STAR_COUNT_MIN, STAR_COUNT_MAX)
    for _ in range(star_count):
        universe.add(Star(_random_pos()))

    # 連邦基地 (5個、互いに離れたセクタ)
    base_positions = _place_bases(FEDERATION_BASE_COUNT)
    fed_bases: list[BaseStation] = []
    for pos in base_positions:
        base = BaseStation(pos, faction="U")
        universe.add(base)
        fed_bases.append(base)

    # 連邦駆逐艦 (基地ごとに 10 隻、基地から 150 grid の円軌道上)
    for base in fed_bases:
        orbit_positions = _orbit_positions(base.pos, FLEET_ORBIT_RADIUS, FEDERATION_FLEET_SIZE)
        for pos in orbit_positions:
            d = Destroyer(pos, faction="U")
            d.bridge.commander.set_home(base)
            universe.add(d)

    # クリンゴン艦隊 (3艦隊 × 重巡1 + 駆逐10)
    for _ in range(KLINGON_FLEET_COUNT):
        flagship_pos = _random_sector_center()
        flagship = HeavyCruiser(flagship_pos, faction="K")
        universe.add(flagship)
        orbit_positions = _orbit_positions(flagship_pos, FLEET_ORBIT_RADIUS, KLINGON_FLEET_SIZE)
        for pos in orbit_positions:
            d = Destroyer(pos, faction="K")
            d.bridge.commander.set_home(flagship)
            universe.add(d)

    # プレーヤー特務艦 (ランダムな基地の近傍)
    home_base = random.choice(fed_bases)
    player_pos = wrap_vec(Vec2(
        home_base.pos.x + random.uniform(-0.1, 0.1),
        home_base.pos.y + random.uniform(-0.1, 0.1),
    ))
    player_ship = SpecialShip(player_pos)
    player_ship.attach_player()
    universe.add(player_ship)

    universe._initialized = True
    return player_ship
