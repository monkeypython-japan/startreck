"""座標系ユーティリティ。宇宙は 0〜10 × 0〜10 の閉じた座標系。"""
from __future__ import annotations
import math
from typing import NamedTuple

SPACE_SIZE = 10.0
GRID = 0.001  # 1 grid = 0.001 座標単位


class Vec2(NamedTuple):
    x: float
    y: float

    def __add__(self, other: Vec2) -> Vec2:  # type: ignore[override]
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vec2) -> Vec2:  # type: ignore[override]
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> Vec2:  # type: ignore[override]
        return Vec2(self.x * scalar, self.y * scalar)

    def __truediv__(self, scalar: float) -> Vec2:
        return Vec2(self.x / scalar, self.y / scalar)

    def length(self) -> float:
        return math.hypot(self.x, self.y)

    def normalized(self) -> Vec2:
        n = self.length()
        if n == 0.0:
            return Vec2(0.0, 0.0)
        return Vec2(self.x / n, self.y / n)

    def perpendicular(self) -> Vec2:
        """自身に直交する単位ベクトルを返す（反時計回り90度）。"""
        return Vec2(-self.y, self.x).normalized()


def wrap(v: float) -> float:
    """座標値を 0〜SPACE_SIZE の閉じた範囲に折り返す。"""
    return v % SPACE_SIZE


def wrap_vec(p: Vec2) -> Vec2:
    return Vec2(wrap(p.x), wrap(p.y))


def _delta(a: float, b: float) -> float:
    """閉じた座標系での1次元最短変位（-SPACE_SIZE/2 〜 +SPACE_SIZE/2）。"""
    d = (b - a) % SPACE_SIZE
    if d > SPACE_SIZE / 2:
        d -= SPACE_SIZE
    return d


def displacement(src: Vec2, dst: Vec2) -> Vec2:
    """閉じた座標系でのsrcからdstへの最短変位ベクトルを返す。"""
    return Vec2(_delta(src.x, dst.x), _delta(src.y, dst.y))


def distance(a: Vec2, b: Vec2) -> float:
    """閉じた座標系でのユークリッド距離（座標単位）。"""
    d = displacement(a, b)
    return math.hypot(d.x, d.y)


def distance_grid(a: Vec2, b: Vec2) -> float:
    """grid単位での距離を返す。"""
    return distance(a, b) / GRID


def sector(pos: Vec2) -> tuple[int, int]:
    """座標からセクタ番号 (0〜9, 0〜9) を返す。"""
    sx = min(int(pos.x), 9)
    sy = min(int(pos.y), 9)
    return sx, sy


def direction_to(src: Vec2, dst: Vec2) -> Vec2:
    """srcからdstへの方位単位ベクトルを返す（閉じた座標系考慮）。"""
    return displacement(src, dst).normalized()
