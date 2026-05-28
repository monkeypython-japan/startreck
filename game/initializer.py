"""ゲーム初期配置: 仕様書の配置ルールに従ってオブジェクトを生成・配置する。"""
from __future__ import annotations
import math
import random
import time
from itertools import combinations
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
    GUARD_PER_BASE, GUARD_PER_FLAGSHIP,
    GUARD_HOME_MIN, GUARD_HOME_MAX,
)

SPACE_SIZE = 10.0
STAR_GRID_N = 4             # 恒星配置用グリッド (4×4 = 16セル)

# 基地配置の最適解キャッシュ（初回計算後に再利用）
_JOINT_BASE_CACHE: dict[int, list[tuple[list[Vec2], list[Vec2]]]] = {}


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


def _place_bases_joint(n: int) -> tuple[list[Vec2], list[Vec2]]:
    """連邦・クリンゴン基地を合同配置する。

    連邦は x=0-4 の 50 セクター、クリンゴンは x=5-9 の 50 セクターから選択。
    第1優先: 連邦-クリンゴン間の最小距離（toroidal）を最大化。
    第2優先: 同陣営内の最小距離を最大化。
    結果はキャッシュするため2回目以降は即座に返る。
    """
    if n in _JOINT_BASE_CACHE:
        return random.choice(_JOINT_BASE_CACHE[n])

    fed_s = [Vec2(sx + 0.5, sy + 0.5) for sx in range(5) for sy in range(10)]
    kli_s = [Vec2(sx + 0.5, sy + 0.5) for sx in range(5, 10) for sy in range(10)]
    NF, NK = len(fed_s), len(kli_s)

    # 距離行列を事前計算（sqrt を O(1) ルックアップに変換）
    dk  = [[distance_grid(fed_s[i], kli_s[j]) for j in range(NK)] for i in range(NF)]
    dff = {(i, j): distance_grid(fed_s[i], fed_s[j]) for i in range(NF) for j in range(i + 1, NF)}
    dkk = {(i, j): distance_grid(kli_s[i], kli_s[j]) for i in range(NK) for j in range(i + 1, NK)}

    n_combos = math.comb(NF, n)
    SLOW_THRESHOLD = 100_000
    if n_combos >= SLOW_THRESHOLD:
        print(f"基地配置を計算中... ({n_combos:,} 通りの連邦配置を探索)")
    t0 = time.monotonic()

    best_cross = -1.0
    best_same  = -1.0
    best: list[tuple[tuple[int, ...], tuple[int, ...]]] = []

    for fi in combinations(range(NF), n):
        # 連邦同陣営最小距離
        fed_same = (min(dff[fi[a], fi[b]] for a in range(n) for b in range(a + 1, n))
                    if n > 1 else float("inf"))

        # 各クリンゴンセクターのリーチ（最寄りの連邦基地までの距離）
        reach = [min(dk[f][k] for f in fi) for k in range(NK)]

        # リーチ降順でソート → n 番目が「この連邦配置で達成可能な最大 min_cross」
        kli_sorted = sorted(range(NK), key=lambda k: -reach[k])
        min_cross = reach[kli_sorted[n - 1]]

        if min_cross < best_cross - 1e-9:
            continue  # プルーニング

        # min_cross を達成できるクリンゴンセクター群（インデックス昇順）
        viable = sorted(k for k in range(NK) if reach[k] >= min_cross - 1e-9)

        # viable 内で同陣営最小距離を最大化するクリンゴン配置を選ぶ
        best_local_same = -1.0
        best_local_ki: tuple[int, ...] = ()
        for ki in combinations(viable, n):
            kli_same = (min(dkk[ki[a], ki[b]] for a in range(n) for b in range(a + 1, n))
                        if n > 1 else float("inf"))
            combined_same = min(fed_same, kli_same)
            if combined_same > best_local_same:
                best_local_same = combined_same
                best_local_ki = ki

        if not best_local_ki:
            continue

        if min_cross > best_cross + 1e-9:
            best_cross = min_cross
            best_same  = best_local_same
            best = [(fi, best_local_ki)]
        elif abs(min_cross - best_cross) <= 1e-9:
            if best_local_same > best_same + 1e-9:
                best_same = best_local_same
                best = [(fi, best_local_ki)]
            elif abs(best_local_same - best_same) <= 1e-9:
                best.append((fi, best_local_ki))

    elapsed = time.monotonic() - t0
    if n_combos >= SLOW_THRESHOLD:
        print(f"基地配置決定: クロス最小 {best_cross:.0f} grid, 同陣営最小 {best_same:.0f} grid, "
              f"{len(best)} 種の最適配置 ({elapsed:.1f}秒)")

    results = [
        ([fed_s[i] for i in fi], [kli_s[i] for i in ki])
        for fi, ki in best
    ]
    _JOINT_BASE_CACHE[n] = results
    return random.choice(results)


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


def _place_guard_fleet(
    universe: Universe,
    bases: list[BaseStation],
    flagships: list[HeavyCruiser],
    faction: str,
) -> None:
    """全基地に GUARD_PER_BASE 隻、全旗艦に GUARD_PER_FLAGSHIP 隻の護衛型駆逐艦を配置する。"""
    from game.vessels.guard_destroyer import GuardDestroyer
    mid_dist = (GUARD_HOME_MIN + GUARD_HOME_MAX) / 2  # 600 grid

    for base in bases:
        positions = _orbit_positions(base.pos, mid_dist, GUARD_PER_BASE)
        for pos in positions:
            guard = GuardDestroyer(pos, faction=faction)
            guard.bridge.commander.set_home(base)
            universe.add(guard)

    for flagship in flagships:
        positions = _orbit_positions(flagship.pos, mid_dist, GUARD_PER_FLAGSHIP)
        for pos in positions:
            guard = GuardDestroyer(pos, faction=faction)
            guard.bridge.commander.set_home(flagship)
            universe.add(guard)


def initialize(universe: Universe) -> SpecialShip:
    """宇宙を初期化してプレーヤーの特務艦を返す。"""
    from game import names
    names.reset_counters()

    # 恒星 (10〜15個、均等分布)
    star_count = random.randint(STAR_COUNT_MIN, STAR_COUNT_MAX)
    for pos in _place_stars_uniform(star_count):
        universe.add(Star(pos))

    # 連邦・クリンゴン基地を合同配置（クロス陣営距離優先）
    fed_base_positions, kl_base_positions = _place_bases_joint(BASE_COUNT)

    fed_bases: list[BaseStation] = []
    for pos in fed_base_positions:
        base = BaseStation(pos, faction="U")
        universe.add(base)
        fed_bases.append(base)
        universe.initial_base_positions.append({"pos": pos, "faction": "U"})

    kl_bases: list[BaseStation] = []
    for pos in kl_base_positions:
        base = BaseStation(pos, faction="K")
        universe.add(base)
        kl_bases.append(base)
        universe.initial_base_positions.append({"pos": pos, "faction": "K"})

    # 連邦艦隊 (3組 × 重巡1 + 駆逐10)
    fed_flagships = _place_faction_fleet(universe, fed_bases, faction="U")

    # クリンゴン艦隊 (3組 × 重巡1 + 駆逐10)
    kl_flagships = _place_faction_fleet(universe, kl_bases, faction="K")

    # 護衛型巡洋艦 (基地×10隻 + 旗艦×5隻)
    _place_guard_fleet(universe, fed_bases, fed_flagships, faction="U")
    _place_guard_fleet(universe, kl_bases, kl_flagships, faction="K")

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
