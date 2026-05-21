"""マップビュー: 800×800 正方形エリアに宇宙を描画する。"""
from __future__ import annotations
import pygame
from game.coords import Vec2
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.universe import Universe
    from game.objects.thing import Thing

MAP_BG = (5, 5, 15)
GRID_COLOR = (30, 35, 50)
HIGHLIGHT_COLOR = (255, 255, 80)


def _color_for(obj) -> tuple:
    from game.objects.star import Star
    from game.objects.base_station import BaseStation
    from game.vessels.special_ship import SpecialShip
    from game.objects.vessel import Vessel
    from game.objects.missile import Missile
    from game.objects.beam import Beam
    if isinstance(obj, Star):
        return (220, 220, 60)
    if isinstance(obj, BaseStation):
        return (255, 140, 0) if obj.faction == "U" else (200, 60, 60)
    if isinstance(obj, SpecialShip):
        return (255, 255, 100)
    if isinstance(obj, Vessel):
        return (100, 160, 255) if obj.faction == "U" else (255, 80, 80)
    if isinstance(obj, Missile):
        return (100, 255, 100) if obj.iff == "U" else (255, 120, 40)
    if isinstance(obj, Beam):
        return (80, 220, 255) if obj.iff == "U" else (255, 60, 60)
    return (160, 160, 160)


def _radius_for(obj) -> int:
    from game.objects.star import Star
    from game.objects.base_station import BaseStation
    from game.vessels.special_ship import SpecialShip
    from game.objects.vessel import Vessel
    from game.objects.missile import Missile
    from game.objects.beam import Beam
    if isinstance(obj, Star):
        return max(3, int(obj.size * 0.8))
    if isinstance(obj, BaseStation):
        return 7
    if isinstance(obj, SpecialShip):
        return 6
    if isinstance(obj, Vessel):
        return 4
    if isinstance(obj, (Missile, Beam)):
        return 2
    return 3


class MapView:
    def __init__(self, rect: pygame.Rect) -> None:
        self.rect = rect
        self.selected: "Thing | None" = None

    def world_to_screen(self, pos: Vec2) -> tuple[int, int]:
        x = int(pos.x / 10.0 * self.rect.width) + self.rect.left
        y = int(pos.y / 10.0 * self.rect.height) + self.rect.top
        return x, y

    def screen_to_world(self, sx: int, sy: int) -> Vec2:
        wx = (sx - self.rect.left) / self.rect.width * 10.0
        wy = (sy - self.rect.top) / self.rect.height * 10.0
        return Vec2(wx, wy)

    def contains(self, sx: int, sy: int) -> bool:
        return bool(self.rect.collidepoint(sx, sy))

    def find_object_at(self, sx: int, sy: int, objects: list) -> "Thing | None":
        """クリック座標に最も近いオブジェクトを返す (15px 以内)。"""
        best = None
        best_dist = 16.0
        for obj in objects:
            ox, oy = self.world_to_screen(obj.pos)
            d = ((ox - sx) ** 2 + (oy - sy) ** 2) ** 0.5
            if d < best_dist:
                best_dist = d
                best = obj
        return best

    def draw(self, screen: pygame.Surface, universe: "Universe") -> None:
        pygame.draw.rect(screen, MAP_BG, self.rect)

        # セクタグリッド線
        for i in range(1, 10):
            x = self.rect.left + int(i / 10 * self.rect.width)
            y = self.rect.top + int(i / 10 * self.rect.height)
            pygame.draw.line(screen, GRID_COLOR, (x, self.rect.top), (x, self.rect.bottom))
            pygame.draw.line(screen, GRID_COLOR, (self.rect.left, y), (self.rect.right, y))

        from game.objects.vessel import Vessel
        from game.objects.beam import Beam
        for obj in universe.objects:
            sx, sy = self.world_to_screen(obj.pos)
            color = _color_for(obj)
            r = _radius_for(obj)
            pygame.draw.circle(screen, color, (sx, sy), r)

            if obj is self.selected:
                pygame.draw.circle(screen, HIGHLIGHT_COLOR, (sx, sy), r + 4, 1)

            if isinstance(obj, Vessel) and obj.speed > 0:
                ex = int(sx + obj.heading.x * 14)
                ey = int(sy + obj.heading.y * 14)
                pygame.draw.line(screen, color, (sx, sy), (ex, ey), 2)

            if isinstance(obj, Beam):
                ox, oy = self.world_to_screen(obj.origin)
                pygame.draw.line(screen, color, (ox, oy), (sx, sy), 1)

        pygame.draw.rect(screen, (60, 60, 80), self.rect, 1)
