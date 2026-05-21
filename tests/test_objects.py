"""物体・移動体のテスト。"""
import pytest
from game.coords import Vec2
from game.objects.thing import Thing
from game.objects.mover import Mover
from game.objects.star import Star
from game.universe import Universe


def make_thing():
    return Thing(Vec2(1.0, 1.0), size=1.0, durability=100.0)

def make_mover():
    return Mover(Vec2(0.0, 0.0), size=1.0, durability=100.0)


def test_damage_accumulates():
    t = make_thing()
    t.receive_damage(30.0)
    assert t.damage == pytest.approx(30.0)
    assert not t.destroyed

def test_destroyed_when_exceeds_durability():
    t = make_thing()
    t.receive_damage(100.0)
    assert t.destroyed

def test_no_damage_after_destroyed():
    t = make_thing()
    t.receive_damage(200.0)
    t.receive_damage(50.0)
    assert t.damage == pytest.approx(200.0)  # 破壊後は加算されない

def test_mover_moves():
    m = make_mover()
    m.heading = Vec2(1.0, 0.0)
    m.speed = 10.0  # grid/sec
    m.update(1.0)   # 1秒後
    assert m.pos.x == pytest.approx(0.010)  # 10 grid = 0.010 座標単位

def test_mover_accelerate_cost():
    m = make_mover()
    cost = m.accelerate(5.0, max_speed=20.0)
    assert cost == pytest.approx(5.0)  # 5 gj
    assert m.speed == pytest.approx(5.0)

def test_mover_stop():
    m = make_mover()
    m.speed = 8.0
    cost = m.stop()
    assert cost == pytest.approx(8.0)
    assert m.speed == pytest.approx(0.0)

def test_mover_wrap():
    m = make_mover()
    m.heading = Vec2(1.0, 0.0)
    m.speed = 10000  # 猛スピードで反対側に出る
    m.update(1.0)
    assert 0.0 <= m.pos.x < 10.0

def test_star_indestructible():
    s = Star(Vec2(5.0, 5.0))
    s.receive_damage(9999999)
    assert not s.destroyed

def test_universe_removes_destroyed():
    uni = Universe()
    t = make_thing()
    uni.add(t)
    t.destroyed = True
    uni.update(0.016)
    assert t not in uni.objects

def test_universe_ticks_time():
    uni = Universe()
    for _ in range(65):
        uni.update(1.0 / 60)
    assert uni.time >= 1
