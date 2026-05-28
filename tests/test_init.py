"""ゲーム初期化・勝敗判定のテスト。"""
import pytest
from game.universe import Universe
from game.initializer import initialize
from game.objects.star import Star
from game.objects.base_station import BaseStation
from game.objects.vessel import Vessel
from game.vessels.special_ship import SpecialShip
from game.vessels.heavy_cruiser import HeavyCruiser
from game.vessels.destroyer import Destroyer
from game.vessels.guard_destroyer import GuardDestroyer
from game.constants import (
    STAR_COUNT_MIN, STAR_COUNT_MAX,
    FLEET_COUNT, FLEET_SIZE, BASE_COUNT,
    GUARD_PER_BASE, GUARD_PER_FLAGSHIP,
)


def build_universe():
    uni = Universe()
    player = initialize(uni)
    return uni, player


def test_stars_count():
    uni, _ = build_universe()
    stars = [o for o in uni.objects if isinstance(o, Star)]
    assert STAR_COUNT_MIN <= len(stars) <= STAR_COUNT_MAX


def test_federation_bases():
    uni, _ = build_universe()
    bases = [o for o in uni.objects if isinstance(o, BaseStation) and o.faction == "U"]
    assert len(bases) == BASE_COUNT


def test_klingon_bases():
    uni, _ = build_universe()
    bases = [o for o in uni.objects if isinstance(o, BaseStation) and o.faction == "K"]
    assert len(bases) == BASE_COUNT


def test_federation_flagships():
    uni, _ = build_universe()
    flagships = [o for o in uni.objects
                 if type(o) is HeavyCruiser and o.faction == "U"]
    assert len(flagships) == FLEET_COUNT


def test_federation_destroyers():
    uni, _ = build_universe()
    fed = [o for o in uni.objects
           if type(o) is Destroyer and o.faction == "U"]
    assert len(fed) == FLEET_COUNT * FLEET_SIZE


def test_klingon_flagships():
    uni, _ = build_universe()
    flagships = [o for o in uni.objects
                 if type(o) is HeavyCruiser and o.faction == "K"]
    assert len(flagships) == FLEET_COUNT


def test_federation_guard_destroyers():
    uni, _ = build_universe()
    guards = [o for o in uni.objects if isinstance(o, GuardDestroyer) and o.faction == "U"]
    expected = BASE_COUNT * GUARD_PER_BASE + FLEET_COUNT * GUARD_PER_FLAGSHIP
    assert len(guards) == expected


def test_klingon_guard_destroyers():
    uni, _ = build_universe()
    guards = [o for o in uni.objects if isinstance(o, GuardDestroyer) and o.faction == "K"]
    expected = BASE_COUNT * GUARD_PER_BASE + FLEET_COUNT * GUARD_PER_FLAGSHIP
    assert len(guards) == expected


def test_klingon_destroyers():
    uni, _ = build_universe()
    kli = [o for o in uni.objects
           if type(o) is Destroyer and o.faction == "K"]
    assert len(kli) == FLEET_COUNT * FLEET_SIZE


def test_player_ship_is_special_ship():
    uni, player = build_universe()
    assert isinstance(player, SpecialShip)
    assert player in uni.objects
    assert player.faction == "U"


def test_all_vessels_full_load():
    uni, _ = build_universe()
    for obj in uni.objects:
        if isinstance(obj, Vessel) and obj.generator:
            assert obj.generator.fuel == pytest.approx(obj.generator.fuel_max)
            assert obj.generator.capacitor == pytest.approx(obj.generator.capacitor_max)
        if isinstance(obj, Vessel) and obj.missile_launcher:
            assert obj.missile_launcher.stock == obj.missile_launcher.capacity


def test_victory_none_at_start():
    uni, _ = build_universe()
    assert uni.victory is None


def test_victory_klingon_wins_when_all_fed_bases_destroyed():
    uni, _ = build_universe()
    for obj in list(uni.objects):
        if isinstance(obj, BaseStation) and obj.faction == "U":
            obj.destroyed = True
    uni.remove_destroyed()
    assert uni.victory == "K"


def test_victory_federation_wins_when_all_klingon_bases_destroyed():
    uni, _ = build_universe()
    for obj in list(uni.objects):
        if isinstance(obj, BaseStation) and obj.faction == "K":
            obj.destroyed = True
    uni.remove_destroyed()
    assert uni.victory == "U"


def test_victory_none_before_initialize():
    uni = Universe()
    assert uni.victory is None


def test_base_separation():
    """連邦-クリンゴン間の最小距離が 5000 grid 以上であることを確認（クロス陣営距離優先）。
    同陣営内の距離は制約なし（近くなることを許容）。"""
    from game.coords import distance_grid
    from game.objects.base_station import BaseStation as BS
    uni, _ = build_universe()
    fed_bases = [o for o in uni.objects if isinstance(o, BS) and o.faction == "U"]
    kli_bases = [o for o in uni.objects if isinstance(o, BS) and o.faction == "K"]
    for f in fed_bases:
        for k in kli_bases:
            d = distance_grid(f.pos, k.pos)
            assert d >= 5000.0, f"連邦-クリンゴン基地の間隔不足: {d:.0f} grid"


def test_federation_bases_in_left_half():
    """連邦基地が x セクタ 0〜4 (x < 5.0) に配置されることを確認。"""
    uni, _ = build_universe()
    bases = [o for o in uni.objects if isinstance(o, BaseStation) and o.faction == "U"]
    for b in bases:
        assert b.pos.x < 5.0, f"連邦基地が右半分に配置された: x={b.pos.x}"


def test_klingon_bases_in_right_half():
    """クリンゴン基地が x セクタ 5〜9 (x >= 5.0) に配置されることを確認。"""
    uni, _ = build_universe()
    bases = [o for o in uni.objects if isinstance(o, BaseStation) and o.faction == "K"]
    for b in bases:
        assert b.pos.x >= 5.0, f"クリンゴン基地が左半分に配置された: x={b.pos.x}"
