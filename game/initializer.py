"""ゲーム初期配置: 仕様書の配置ルールに従ってオブジェクトを生成・配置する。"""
from __future__ import annotations
import math
import random
from game.coords import Vec2, wrap_vec, GRID, distance_grid
from game.universe import Universe
from game.objects.star import Star
from game.objects.base_station import BaseStation
from game.vessels.destroyer import Destroyer
from game.vessels.heavy_cruiser import HeavyCruiser
from game.vessels.special_ship import SpecialShip
from game.constants import (
    STAR_COUNT_MIN, STAR_COUNT_MAX,
    FLEET_COUNT, FLEET_SIZE, BASE_COUNT,
    FLEET_ORBIT_RADIUS,
)

SPACE_SIZE = 10.0
MIN_BASE_SEPARATION = 1.5   # 基地同士の最小距離 (座標単位)
STAR_GRID_N = 4             # 恒星配置用グリッド (4×4 = 16セル)


def _random_pos() -> Vec2:
    return Vec2(random.uniform(0, SPACE_SIZE), random.uniform(0, SPACE_SIZE))


def _place_stars_uniform(count: int) -> list[Vec2]:
    """恒星を宇宙全体に均等分布させる（ジッタードグリッド法）。
    4×4 グリッドの 16 セルから count 個をランダムに選び、セル内でランダム配置する。
    """
    cell = SPACE_SIZE / STAR_GRID_N
    cells = [(i, j) for i in range(STAR_GRID_N) for j in range(STAR_GRID_N)]
    random.shuffle(cells)
    margin = cell * 0.15
    positions = []
    for i, j in cells[:count]:
        x = i * cell + random.uniform(margin, cell - margin)
        y = j * cell + random.uniform(margin, cell - margin)
        positions.append(Vec2(x, y))
    return positions


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


def _nearest_base(pos: Vec2, bases: list[BaseStation]) -> BaseStation:
    return min(bases, key=lambda b: distance_grid(pos, b.pos))


def _place_faction_fleet(
    universe: Universe,
    bases: list[BaseStation],
    faction: str,
) -> list[HeavyCruiser]:
    """艦隊 FLEET_COUNT 組（重巡1 + 駆逐 FLEET_SIZE）を配置し、旗艦リストを返す。"""
    from game.crew.bot_fleet_commander import BotFleetCommander
    from game.crew.navigator import Navigator
    from game.crew.gunner import Gunner

    flagships: list[HeavyCruiser] = []
    for i in range(FLEET_COUNT):
        # 艦隊は対応する基地の近傍に配置（ラウンドロビンで基地を割り当て）
        home_base = bases[i % len(bases)]
        angle = random.uniform(0, 2 * math.pi)
        r = FLEET_ORBIT_RADIUS * 2 * GRID
        flagship_pos = wrap_vec(Vec2(
            home_base.pos.x + math.cos(angle) * r,
            home_base.pos.y + math.sin(angle) * r,
        ))
        flagship = HeavyCruiser(flagship_pos, faction=faction)

        # BotFleetCommander に差し替え（ホームは割り当て基地）
        fleet_cmd = BotFleetCommander(flagship)
        fleet_cmd.set_home(home_base)
        flagship.bridge.commander = fleet_cmd

        orbit_positions = _orbit_positions(flagship_pos, FLEET_ORBIT_RADIUS, FLEET_SIZE)
        for pos in orbit_positions:
            d = Destroyer(pos, faction=faction)
            d.bridge.commander.set_home(flagship)
            fleet_cmd.add_fleet_member(d)
            universe.add(d)

        universe.add(flagship)
        flagships.append(flagship)
    return flagships


def initialize(universe: Universe) -> SpecialShip:
    """宇宙を初期化してプレーヤーの特務艦を返す。"""

    # 恒星 (10〜15個、均等分布)
    star_count = random.randint(STAR_COUNT_MIN, STAR_COUNT_MAX)
    for pos in _place_stars_uniform(star_count):
        universe.add(Star(pos))

    # 連邦基地 (5個)
    fed_base_positions = _place_bases(BASE_COUNT)
    fed_bases: list[BaseStation] = []
    for pos in fed_base_positions:
        base = BaseStation(pos, faction="U")
        universe.add(base)
        fed_bases.append(base)

    # クリンゴン基地 (5個)
    kl_base_positions = _place_bases(BASE_COUNT)
    kl_bases: list[BaseStation] = []
    for pos in kl_base_positions:
        base = BaseStation(pos, faction="K")
        universe.add(base)
        kl_bases.append(base)

    # 連邦艦隊 (3組 × 重巡1 + 駆逐10)
    _place_faction_fleet(universe, fed_bases, faction="U")

    # クリンゴン艦隊 (3組 × 重巡1 + 駆逐10)
    _place_faction_fleet(universe, kl_bases, faction="K")

    # プレーヤー特務艦 (ランダムな連邦基地の近傍)
    home_base = random.choice(fed_bases)
    player_pos = wrap_vec(Vec2(
        home_base.pos.x + random.uniform(-0.1, 0.1),
        home_base.pos.y + random.uniform(-0.1, 0.1),
    ))
    player_ship = SpecialShip(player_pos)
    player_ship.attach_player()
    universe.add(player_ship)

    universe._initialized = True
    # 恒星・僚艦の初期インテグレータ登録 (最初のティック前に確定させる)
    universe._sync_fleet_integrators()
    return player_ship
