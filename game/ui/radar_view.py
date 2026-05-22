"""レーダービュー: 現在スキャン結果を白背景でプレーヤー中心に表示する。"""
from __future__ import annotations
import math
import pygame
from game.coords import Vec2, GRID
from game.ui.draw_utils import draw_dashed_line, draw_dashed_circle
from game.ui.font_util import make_font
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.objects.thing import Thing
    from game.vessels.special_ship import SpecialShip

RADAR_BG = (255, 255, 255)
HIGHLIGHT_COLOR = (220, 160, 0)
GRID_COLOR = (160, 170, 190)
RADAR_RING_COLOR = (80, 100, 180)

# 白背景用の暗めの色
def _color_for(obj) -> tuple:
    from game.objects.star import Star
    from game.objects.base_station import BaseStation
    from game.vessels.special_ship import SpecialShip
    from game.objects.vessel import Vessel
    from game.objects.missile import Missile
    from game.objects.beam import Beam
    if isinstance(obj, Star):
        return (160, 140, 0)
    if isinstance(obj, BaseStation):
        return (200, 100, 0) if obj.faction == "U" else (160, 0, 0)
    if isinstance(obj, SpecialShip):
        return (180, 140, 0)
    if isinstance(obj, Vessel):
        return (0, 80, 200) if obj.faction == "U" else (200, 0, 0)
    if isinstance(obj, Missile):
        return (0, 140, 0) if obj.iff == "U" else (180, 80, 0)
    if isinstance(obj, Beam):
        return (0, 100, 200) if obj.iff == "U" else (180, 0, 0)
    return (100, 100, 100)


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
        return 7
    if isinstance(obj, Vessel):
        return 5
    if isinstance(obj, (Missile, Beam)):
        return 2
    return 3


_sector_font: pygame.font.Font | None = None


def _get_sector_font() -> pygame.font.Font:
    global _sector_font
    if _sector_font is None:
        _sector_font = make_font(10)
    return _sector_font


class RadarView:
    """レーダー範囲をビュー全体に写像したズームビュー。背景は白。"""

    def __init__(self, rect: pygame.Rect, player: "SpecialShip") -> None:
        self.rect = rect
        self.player = player
        self.selected: "Thing | None" = None

    @property
    def _scale(self) -> float:
        """px per 座標単位。レーダーレンジがビュー半幅に対応。"""
        if self.player.radar is None:
            return 50.0
        radar_units = self.player.radar.scan_range * GRID
        return (self.rect.width / 2) / radar_units

    # ── 座標変換 ────────────────────────────────────────────────

    def world_to_screen(self, pos: Vec2) -> tuple[int, int]:
        dx = pos.x - self.player.pos.x
        dy = pos.y - self.player.pos.y
        if dx > 5.0: dx -= 10.0
        elif dx < -5.0: dx += 10.0
        if dy > 5.0: dy -= 10.0
        elif dy < -5.0: dy += 10.0
        return (
            int(self.rect.centerx + dx * self._scale),
            int(self.rect.centery + dy * self._scale),
        )

    def screen_to_world(self, sx: int, sy: int) -> Vec2:
        scale = self._scale
        dx = (sx - self.rect.centerx) / scale
        dy = (sy - self.rect.centery) / scale
        return Vec2(
            (self.player.pos.x + dx) % 10.0,
            (self.player.pos.y + dy) % 10.0,
        )

    def contains(self, sx: int, sy: int) -> bool:
        return bool(self.rect.collidepoint(sx, sy))

    def find_object_at(self, sx: int, sy: int) -> "Thing | None":
        contacts = self.player.radar.contacts if self.player.radar else []
        # 自艦も含める
        from game.vessels.special_ship import SpecialShip
        all_objs = list(contacts)
        if self.player not in all_objs:
            all_objs.append(self.player)
        best, best_dist = None, 16.0
        for obj in all_objs:
            ox, oy = self.world_to_screen(obj.pos)
            d = ((ox - sx) ** 2 + (oy - sy) ** 2) ** 0.5
            if d < best_dist:
                best_dist, best = d, obj
        return best

    # ── 描画サブルーチン ────────────────────────────────────────

    def _draw_grid(self, surface: pygame.Surface) -> None:
        """破線のセクタグリッドとセクター番号を描画する（白背景用の暗めの色）。"""
        px, py = self.player.pos.x, self.player.pos.y
        scale = self._scale
        w, h = self.rect.width, self.rect.height
        gs = pygame.Surface((w, h), pygame.SRCALPHA)
        color = (*GRID_COLOR, 100)
        font = _get_sector_font()
        sector_color = (120, 130, 160)

        x_screen: dict[int, int] = {}  # sector_x → screen_x (左端)
        y_screen: dict[int, int] = {}  # sector_y → screen_y (上端)

        for i in range(10):
            dx = float(i) - px
            if dx > 5.0: dx -= 10.0
            elif dx < -5.0: dx += 10.0
            sx = int(w / 2 + dx * scale)
            x_screen[i] = sx
            if -2 <= sx <= w + 2:
                draw_dashed_line(gs, color, (sx, 0), (sx, h), dash=6, gap=4)
            dy = float(i) - py
            if dy > 5.0: dy -= 10.0
            elif dy < -5.0: dy += 10.0
            sy = int(h / 2 + dy * scale)
            y_screen[i] = sy
            if -2 <= sy <= h + 2:
                draw_dashed_line(gs, color, (0, sy), (w, sy), dash=6, gap=4)

        surface.blit(gs, self.rect.topleft)

        # セクター番号をグリッド左上に描画
        rx, ry = self.rect.left, self.rect.top
        old_clip = surface.get_clip()
        surface.set_clip(self.rect)
        for sx_idx in range(10):
            sx = x_screen[sx_idx]
            for sy_idx in range(10):
                sy = y_screen[sy_idx]
                label = f"{sx_idx},{sy_idx}"
                lsurf = font.render(label, True, sector_color)
                surface.blit(lsurf, (rx + sx + 2, ry + sy + 1))
        surface.set_clip(old_clip)

    def _draw_objects(self, surface: pygame.Surface) -> None:
        from game.objects.vessel import Vessel
        from game.objects.beam import Beam

        contacts = self.player.radar.contacts if self.player.radar else []
        # 自艦は常に中央に描画
        from game.vessels.special_ship import SpecialShip
        draw_list = list(contacts)
        if self.player not in draw_list:
            draw_list.append(self.player)

        for obj in draw_list:
            sx, sy = self.world_to_screen(obj.pos)
            if not self.rect.collidepoint(sx, sy):
                continue
            color = _color_for(obj)
            r = _radius_for(obj)

            # 自艦撃沈時はバツ印で表示
            if obj is self.player and obj.destroyed:
                d = r + 3
                pygame.draw.line(surface, (200, 0, 0), (sx - d, sy - d), (sx + d, sy + d), 3)
                pygame.draw.line(surface, (200, 0, 0), (sx + d, sy - d), (sx - d, sy + d), 3)
                continue

            pygame.draw.circle(surface, color, (sx, sy), r)
            if obj is self.selected:
                pygame.draw.circle(surface, HIGHLIGHT_COLOR, (sx, sy), r + 4, 1)
            if isinstance(obj, Vessel) and obj.speed > 0:
                ex = int(sx + obj.heading.x * 16)
                ey = int(sy + obj.heading.y * 16)
                pygame.draw.line(surface, color, (sx, sy), (ex, ey), 2)
            if isinstance(obj, Beam):
                # origin を tip 相対でラッピングして描画（境界跨ぎで逆方向になるのを防ぐ）
                scale = self._scale
                ddx = obj.origin.x - obj.pos.x
                ddy = obj.origin.y - obj.pos.y
                if ddx > 5.0: ddx -= 10.0
                elif ddx < -5.0: ddx += 10.0
                if ddy > 5.0: ddy -= 10.0
                elif ddy < -5.0: ddy += 10.0
                ox = int(sx + ddx * scale)
                oy = int(sy + ddy * scale)
                pygame.draw.line(surface, color, (ox, oy), (sx, sy), 1)

    def draw_explosions(self, surface: pygame.Surface, explosions: list) -> None:
        """爆発エフェクトを描画する。"""
        now_ms = pygame.time.get_ticks()
        old_clip = surface.get_clip()
        surface.set_clip(self.rect)
        for ex in explosions:
            elapsed = (now_ms - ex["start_ms"]) / 1000.0
            t = elapsed / ex["duration"]
            if t >= 1.0:
                continue
            sx, sy = self.world_to_screen(ex["pos"])
            if not self.rect.collidepoint(sx, sy):
                continue
            r = int(ex["max_r"] * (1.0 - t))
            v = int(200 * (1.0 - t))
            if r > 0:
                pygame.draw.circle(surface, (v, v // 2, 0), (sx, sy), r)
        surface.set_clip(old_clip)

    # ── メイン描画 ──────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, RADAR_BG, self.rect)
        self._draw_grid(surface)

        old_clip = surface.get_clip()
        surface.set_clip(self.rect)
        self._draw_objects(surface)
        surface.set_clip(old_clip)

        # レーダー範囲円 (破線)
        r_px = self.rect.width // 2 - 2
        draw_dashed_circle(surface, RADAR_RING_COLOR,
                           (self.rect.centerx, self.rect.centery), r_px, dash=8, gap=5)

        pygame.draw.rect(surface, (120, 130, 160), self.rect, 1)
