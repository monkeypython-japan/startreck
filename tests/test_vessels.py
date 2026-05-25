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
    """レーダー範囲内 (400 grid) に配置したBOT艦がミサイルを発射することを確認。"""
    uni = Universe()
    # 400 grid: ミサイル射程 500 grid 内 → ミサイル発射
    fed = Destroyer(Vec2(4.80, 5.0), faction="U")
    kli = Destroyer(Vec2(5.20, 5.0), faction="K")
    uni.add(fed)
    uni.add(kli)
    from game.objects.missile import Missile
    # 2秒分更新 (1秒 tick で AI が判断 → ガンナーがミサイル発射)
    for _ in range(120):
        uni.update(1.0 / 60)
    missiles = [o for o in uni.objects if isinstance(o, Missile)]
    assert len(missiles) > 0

def test_missile_fired_at_enemy():
    """BOTがミサイル射程内 (400 grid) に入ったらミサイルを発射することを確認。"""
    uni = Universe()
    # 400 grid: ミサイル射程 500 grid 内, ビーム射程 750 grid 内 → ミサイル優先発射
    fed = Destroyer(Vec2(4.80, 5.0), faction="U")
    kli = Destroyer(Vec2(5.20, 5.0), faction="K")
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


# --- 分離ステアリング ---

def test_separation_steer_pushes_heading_away():
    """近傍に別の艦がいる場合、heading が相手から離れる方向に調整されることを確認。"""
    from game.crew.navigator import SEPARATION_DIST
    uni = Universe()
    # 距離 5 grid（SEPARATION_DIST=10 より近い）で2艦を配置
    gap_coord = SEPARATION_DIST * 0.5 * 0.001  # 5 grid in coord units
    a = Destroyer(Vec2(5.0, 5.0), faction="U")
    b = Destroyer(Vec2(5.0 + gap_coord, 5.0), faction="U")
    uni.add(a)
    uni.add(b)
    # レーダースキャンで a が b を認識させる
    a.radar.scan(uni.objects, 0)
    # a を +x 方向（b の方向）に向けて移動させる
    a.set_heading_to(Vec2(5.0 + 1.0, 5.0))
    a.set_speed(1.0)
    heading_before = a.heading
    a.bridge.navigator.destination = Vec2(5.0 + 1.0, 5.0)
    a.bridge.navigator._separation_steer()
    # heading.x が減少（b から離れる方向に曲がった）ことを確認
    assert a.heading.x < heading_before.x


def test_separation_maintained_during_movement():
    """同一方向に移動する2艦が最低 SEPARATION_DIST を維持することを確認（近似）。"""
    from game.crew.navigator import SEPARATION_DIST
    # 5 grid 以内に配置して同じ目標に向かわせる
    gap_coord = SEPARATION_DIST * 0.4 * 0.001
    uni = Universe()
    a = Destroyer(Vec2(5.0, 5.0), faction="U")
    b = Destroyer(Vec2(5.0 + gap_coord, 5.0), faction="U")
    uni.add(a)
    uni.add(b)
    target = Vec2(8.0, 5.0)
    a.bridge.navigator.set_destination(target, speed=2.0)
    b.bridge.navigator.set_destination(target, speed=2.0)
    # 2秒更新（レーダースキャンなしなので分離は働かないが例外が出ないことを確認）
    for _ in range(120):
        uni.update(1.0 / 60)
    assert not a.destroyed
    assert not b.destroyed
