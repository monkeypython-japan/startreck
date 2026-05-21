"""ミサイル・ビームのテスト。"""
import pytest
from game.coords import Vec2
from game.objects.thing import Thing
from game.objects.star import Star
from game.objects.missile import Missile
from game.objects.beam import Beam
from game.objects.mover import Mover
from game.equipment.integrator import Integrator
from game.equipment.radar import Radar
from game.equipment.missile_nav import MissileNavigation


def make_owner(pos=None):
    return Thing(pos or Vec2(5.0, 5.0), size=1.0, durability=1000.0)


# --- Missile ---

def test_missile_moves_toward_target():
    target = make_owner(Vec2(6.0, 5.0))
    owner = make_owner(Vec2(5.0, 5.0))
    integrator = Integrator(owner)
    radar = Radar(owner, scan_range=2000.0, integrator=integrator)
    radar.scan([target], 0)
    m = Missile(Vec2(5.0, 5.0), iff="U", power=500.0, speed=100.0, flight_time=10.0)
    nav = MissileNavigation(m, owner, radar)
    nav.set_target(target, 100.0)
    m.set_nav(nav)
    m.heading = Vec2(1.0, 0.0)
    m.update(0.1)
    assert m.pos.x > 5.0

def test_missile_expires():
    m = Missile(Vec2(5.0, 5.0), iff="U", power=500.0, speed=100.0, flight_time=1.0)
    m.heading = Vec2(1.0, 0.0)
    m.update(1.0)
    assert m.destroyed

def test_missile_detonates_on_contact():
    target = make_owner(Vec2(5.0, 5.005))  # 5 grid 離れた先
    m = Missile(Vec2(5.0, 5.0), iff="U", power=500.0, speed=100.0, flight_time=10.0)
    m.pos = Vec2(5.0, 5.005)  # 目標のすぐ近く
    owner = make_owner()
    integrator = Integrator(owner)
    radar = Radar(owner, scan_range=2000.0, integrator=integrator)
    nav = MissileNavigation(m, owner, radar)
    nav.set_target(target, 100.0)
    m.set_nav(nav)
    m.check_detonation([target])
    assert target.damage == pytest.approx(500.0)
    assert m.destroyed

def test_missile_no_detonate_out_of_range():
    target = make_owner(Vec2(5.0, 6.0))  # 1000 grid 以上離れている
    m = Missile(Vec2(5.0, 5.0), iff="U", power=500.0, speed=100.0, flight_time=10.0)
    owner = make_owner()
    integrator = Integrator(owner)
    radar = Radar(owner, scan_range=2000.0, integrator=integrator)
    nav = MissileNavigation(m, owner, radar)
    nav.set_target(target, 100.0)
    m.set_nav(nav)
    m.check_detonation([target])
    assert target.damage == pytest.approx(0.0)
    assert not m.destroyed


# --- Beam ---

def test_beam_moves():
    b = Beam(Vec2(5.0, 5.0), Vec2(1.0, 0.0), iff="U",
             power=250.0, speed=200.0, max_range=500.0)
    b.update(0.1)
    assert b.traveled == pytest.approx(20.0)  # 200*0.1 = 20 grid

def test_beam_expires_at_max_range():
    b = Beam(Vec2(5.0, 5.0), Vec2(1.0, 0.0), iff="U",
             power=250.0, speed=200.0, max_range=500.0)
    b.update(2.5)  # 200 * 2.5 = 500 grid
    assert b.destroyed

def test_beam_full_damage_range():
    b = Beam(Vec2(5.0, 5.0), Vec2(1.0, 0.0), iff="U",
             power=250.0, speed=200.0, max_range=1000.0)
    b.pos = Vec2(5.005, 5.0)  # 先端を設定
    target = Thing(Vec2(5.005, 5.0), size=0.0, durability=1000.0)  # 先端と同じ位置
    b.check_damage([target])
    assert target.damage == pytest.approx(250.0)  # 100%ダメージ
    assert b.destroyed

def test_beam_partial_damage_range():
    b = Beam(Vec2(5.0, 5.0), Vec2(1.0, 0.0), iff="U",
             power=250.0, speed=200.0, max_range=1000.0)
    # 先端から15 grid の位置にターゲット
    b.pos = Vec2(5.0, 5.0)
    target = Thing(Vec2(5.015, 5.0), size=0.0, durability=1000.0)
    b.check_damage([target])
    assert target.damage == pytest.approx(250.0 * 0.25)  # 25%ダメージ

def test_beam_destroyed_by_star():
    b = Beam(Vec2(5.0, 5.0), Vec2(1.0, 0.0), iff="U",
             power=250.0, speed=200.0, max_range=1000.0)
    # 恒星の表面 (サイズ5 grid) の内側に先端を置く
    star = Star(Vec2(5.0, 5.0))  # 同じ位置
    b.pos = Vec2(5.0, 5.0)
    b.check_damage([star])
    assert b.destroyed
    assert not star.destroyed  # 恒星は破壊されない
