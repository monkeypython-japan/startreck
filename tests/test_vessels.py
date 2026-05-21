"""艦艇・乗組員・AIのテスト。"""
import pytest
from game.coords import Vec2, distance_grid
from game.universe import Universe
from game.vessels.destroyer import Destroyer
from game.vessels.heavy_cruiser import HeavyCruiser
from game.vessels.special_ship import SpecialShip
from game.objects.vessel import Vessel


def make_universe_with_two_destroyers():
    uni = Universe()
    fed = Destroyer(Vec2(2.0, 5.0), faction="U")
    kli = Destroyer(Vec2(8.0, 5.0), faction="K")
    uni.add(fed)
    uni.add(kli)
    return uni, fed, kli


# --- 艦種生成 ---

def test_destroyer_created():
    d = Destroyer(Vec2(5.0, 5.0), faction="U")
    assert d.faction == "U"
    assert d.generator is not None
    assert d.shield is not None
    assert d.radar is not None
    assert d.missile_launcher is not None
    assert d.beam_launcher is not None
    assert d.bridge.navigator is not None
    assert d.bridge.commander is not None

def test_heavy_cruiser_supply_provider():
    hc = HeavyCruiser(Vec2(5.0, 5.0), faction="K")
    assert hc.supply_provider is True

def test_special_ship_jump_drive():
    ss = SpecialShip(Vec2(5.0, 5.0))
    assert ss.jump_drive is not None
    assert ss.faction == "U"


# --- Vessel 装備連携 ---

def test_vessel_shield_absorbs_before_hull():
    d = Destroyer(Vec2(5.0, 5.0), faction="U")
    d.shield.set_defense_rate(100.0)
    d.receive_damage(100.0)
    assert d.damage == pytest.approx(0.0)  # シールドが全部吸収

def test_vessel_set_speed_consumes_energy():
    d = Destroyer(Vec2(5.0, 5.0), faction="U")
    initial_cap = d.generator.capacitor
    d.set_speed(5.0)  # 5 gj 消費
    assert d.generator.capacitor == pytest.approx(initial_cap - 5.0)

def test_vessel_supply_full():
    d = Destroyer(Vec2(5.0, 5.0), faction="U")
    d.damage = 200.0
    d.generator.fuel = 0.0
    d.missile_launcher.stock = 0
    d.supply_full()
    assert d.damage == pytest.approx(0.0)
    assert d.generator.fuel == pytest.approx(d.generator.fuel_max)
    assert d.missile_launcher.stock == d.missile_launcher.capacity


# --- 宇宙との統合 ---

def test_universe_sets_vessel_universe_ref():
    uni = Universe()
    d = Destroyer(Vec2(5.0, 5.0), faction="U")
    uni.add(d)
    assert d.universe is uni

def test_vessels_detect_and_fire():
    """レーダー範囲内 (700 grid) に配置したBOT艦がミサイルを発射することを確認。"""
    uni = Universe()
    # 700 grid: レーダー範囲 750 grid 内 かつ ビーム射程 500 grid 外 → ミサイル発射
    fed = Destroyer(Vec2(4.65, 5.0), faction="U")
    kli = Destroyer(Vec2(5.35, 5.0), faction="K")
    uni.add(fed)
    uni.add(kli)
    from game.objects.missile import Missile
    # 2秒分更新 (1秒 tick で AI が判断 → ガンナーがミサイル発射)
    for _ in range(120):
        uni.update(1.0 / 60)
    missiles = [o for o in uni.objects if isinstance(o, Missile)]
    assert len(missiles) > 0

def test_missile_fired_at_enemy():
    """BOTがミサイル射程内 (700 grid) に入ったらミサイルを発射することを確認。"""
    uni = Universe()
    # 700 grid: レーダー範囲 750 grid 内, ミサイル射程 1000 grid 内, ビーム射程 500 grid 外
    fed = Destroyer(Vec2(4.65, 5.0), faction="U")
    kli = Destroyer(Vec2(5.35, 5.0), faction="K")
    uni.add(fed)
    uni.add(kli)
    from game.objects.missile import Missile
    for _ in range(120):
        uni.update(1.0 / 60)
    missiles = [o for o in uni.objects if isinstance(o, Missile)]
    assert len(missiles) > 0

def test_vessel_destroyed_after_enough_damage():
    d = Destroyer(Vec2(5.0, 5.0), faction="U")
    d.shield.set_defense_rate(0.0)
    d.receive_damage(d.durability)
    assert d.destroyed
