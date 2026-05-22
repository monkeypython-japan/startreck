"""描画ユーティリティ: 破線・破線円などの共通描画ヘルパー。"""
from __future__ import annotations
import math
import pygame


def draw_dashed_line(
    surface: pygame.Surface,
    color: tuple,
    start: tuple[int, int],
    end: tuple[int, int],
    dash: int = 6,
    gap: int = 4,
    width: int = 1,
) -> None:
    x1, y1 = start
    x2, y2 = end
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    if length == 0:
        return
    ux, uy = dx / length, dy / length
    pos = 0.0
    drawing = True
    while pos < length:
        seg = min(dash if drawing else gap, length - pos)
        if drawing:
            ax = int(x1 + ux * pos)
            ay = int(y1 + uy * pos)
            bx = int(x1 + ux * (pos + seg))
            by = int(y1 + uy * (pos + seg))
            pygame.draw.line(surface, color, (ax, ay), (bx, by), width)
        pos += seg
        drawing = not drawing


def draw_star(
    surface: pygame.Surface,
    color: tuple,
    cx: int,
    cy: int,
    outer_r: int,
    inner_r: int | None = None,
) -> None:
    """5角星を描画する。inner_r 省略時は outer_r * 0.42。"""
    if outer_r < 2:
        return
    if inner_r is None:
        inner_r = max(1, int(outer_r * 0.42))
    pts = []
    for i in range(10):
        angle = math.pi * i / 5 - math.pi / 2  # 上向きから開始
        r = outer_r if i % 2 == 0 else inner_r
        pts.append((int(cx + math.cos(angle) * r), int(cy + math.sin(angle) * r)))
    pygame.draw.polygon(surface, color, pts)


def draw_dashed_circle(
    surface: pygame.Surface,
    color: tuple,
    center: tuple[int, int],
    radius: int,
    dash: int = 8,
    gap: int = 5,
    width: int = 1,
) -> None:
    """破線の円を弧の連続として描画する。"""
    if radius <= 1:
        return
    circumference = 2 * math.pi * radius
    if circumference == 0:
        return
    dash_angle = (dash / circumference) * 2 * math.pi
    gap_angle = (gap / circumference) * 2 * math.pi
    step = dash_angle + gap_angle
    if step <= 0:
        return
    angle = 0.0
    cx, cy = center
    while angle < 2 * math.pi:
        a_end = min(angle + dash_angle, 2 * math.pi)
        n = max(2, int(radius * (a_end - angle) / 1.5))
        pts = [
            (
                int(cx + math.cos(angle + (a_end - angle) * t / (n - 1)) * radius),
                int(cy + math.sin(angle + (a_end - angle) * t / (n - 1)) * radius),
            )
            for t in range(n)
        ]
        if len(pts) >= 2:
            pygame.draw.lines(surface, color, False, pts, width)
        angle += step
