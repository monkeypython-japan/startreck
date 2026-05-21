"""座標系ユーティリティのテスト。"""
import math
import pytest
from game.coords import (
    Vec2, wrap, wrap_vec, distance, distance_grid,
    sector, direction_to, displacement,
)


def test_wrap_normal():
    assert wrap(5.0) == 5.0

def test_wrap_overflow():
    assert wrap(10.5) == pytest.approx(0.5)

def test_wrap_underflow():
    assert wrap(-0.5) == pytest.approx(9.5)

def test_wrap_vec():
    p = wrap_vec(Vec2(10.5, -0.5))
    assert p.x == pytest.approx(0.5)
    assert p.y == pytest.approx(9.5)

def test_distance_simple():
    a = Vec2(1.0, 1.0)
    b = Vec2(2.0, 2.0)
    assert distance(a, b) == pytest.approx(math.sqrt(2))

def test_distance_wrap():
    # x軸ラップ: 0.1 と 9.9 は 0.2 の距離
    a = Vec2(0.1, 5.0)
    b = Vec2(9.9, 5.0)
    assert distance(a, b) == pytest.approx(0.2)

def test_distance_grid():
    a = Vec2(0.0, 0.0)
    b = Vec2(0.001, 0.0)  # 1 grid
    assert distance_grid(a, b) == pytest.approx(1.0)

def test_sector():
    assert sector(Vec2(3.5, 7.2)) == (3, 7)
    assert sector(Vec2(0.0, 0.0)) == (0, 0)
    assert sector(Vec2(9.999, 9.999)) == (9, 9)

def test_direction_to_simple():
    src = Vec2(0.0, 0.0)
    dst = Vec2(1.0, 0.0)
    d = direction_to(src, dst)
    assert d.x == pytest.approx(1.0)
    assert d.y == pytest.approx(0.0)

def test_direction_to_wrap():
    # wrapで最短経路は逆方向
    src = Vec2(0.5, 5.0)
    dst = Vec2(9.5, 5.0)  # 直線距離9.0 vs ラップ距離1.0
    d = direction_to(src, dst)
    assert d.x < 0  # 左方向（ラップ経路）

def test_displacement_wrap():
    src = Vec2(0.1, 5.0)
    dst = Vec2(9.9, 5.0)
    disp = displacement(src, dst)
    assert disp.x == pytest.approx(-0.2)  # 左方向が最短
