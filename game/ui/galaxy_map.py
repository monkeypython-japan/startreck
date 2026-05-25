"""全天マップ: プレーヤー艦を常に中央に固定し宇宙全体を表示する。"""
from __future__ import annotations
import pygame
from game.coords import Vec2, GRID
from game.ui.draw_utils import draw_dashed_line, draw_dashed_circle, draw_star, draw_asterisk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.universe import Universe
    from game.objects.thing import Thing
    from game.vessels.special_ship import SpecialShip

MAP_BG = (5, 5, 15)
HIGHLIGHT_COLOR = (255, 255, 80)
GRID_COLOR = (50, 65, 95)       # 破線グリッド色
RADAR_RING_COLOR = (160, 160, 255)
MISSILE_RANGE_COLOR = (255, 60, 60, 35)
BEAM_RANGE_COLOR = (60, 130, 255, 28)


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
        return (60, 120, 255) if obj.faction == "U" else (200, 60, 60)
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
    from game.vessels.heavy_cruiser import HeavyCruiser
    from game.objects.vessel import Vessel
    from game.objects.missile import Missile
    from game.objects.beam import Beam
    if isinstance(obj, Star):
        return max(6, int(obj.size * 1.8))  # 2倍サイズの75%
    if isinstance(obj, BaseStation):
        return 7
    if isinstance(obj, SpecialShip):
        return 7
    if isinstance(obj, HeavyCruiser):
        return 8  # 二重丸の内円半径
    if isinstance(obj, Vessel):
        return 5
    if isinstance(obj, (Missile, Beam)):
        return 2
    return 3


class GalaxyMap:
    """プレーヤー中央固定の全天マップ。スケール: マップ幅 = 宇宙全体 (10 座標単位)。"""

    def __init__(self, rect: pygame.Rect, player: "SpecialShip") -> None:
        self.rect = rect
        self.player = player
        self.selected: "Thing | None" = None
        # 1 座標単位 = rect.width / 10 px
        self._scale: float = rect.width / 10.0
        # ジャンプスクロールアニメーション
        self._anim_offset: "Vec2 | None" = None   # 現在の表示オフセット (player.pos への加算値)
        self._anim_from: "Vec2 | None" = None     # 開始オフセット
        self._anim_elapsed: float = 0.0
        self._anim_duration: float = 0.5

    # ── アニメーション ───────────────────────────────────────────

    def start_jump_anim(self, from_pos: Vec2, to_pos: Vec2) -> None:
        """ジャンプスクロールアニメーションを開始する。"""
        dx = from_pos.x - to_pos.x
        dy = from_pos.y - to_pos.y
        if dx > 5.0: dx -= 10.0
        elif dx < -5.0: dx += 10.0
        if dy > 5.0: dy -= 10.0
        elif dy < -5.0: dy += 10.0
        offset = Vec2(dx, dy)
        self._anim_from = offset
        self._anim_offset = offset
        self._anim_elapsed = 0.0

    def update(self, dt: float) -> None:
        if self._anim_offset is None:
            return
        self._anim_elapsed += dt
        t = min(1.0, self._anim_elapsed / self._anim_duration)
        if t >= 1.0:
            self._anim_offset = None
            self._anim_from = None
        else:
            factor = 1.0 - t
            self._anim_offset = Vec2(
                self._anim_from.x * factor,
                self._anim_from.y * factor,
            )

    # ── 座標変換 ────────────────────────────────────────────────

    def world_to_screen(self, pos: Vec2) -> tuple[int, int]:
        """ラッピングを考慮してプレーヤー中心のスクリーン座標へ変換。"""
        if self._anim_offset:
            cx = self.player.pos.x + self._anim_offset.x
            cy = self.player.pos.y + self._anim_offset.y
        else:
            cx, cy = self.player.pos.x, self.player.pos.y
        dx = pos.x - cx
        dy = pos.y - cy
        if dx > 5.0: dx -= 10.0
        elif dx < -5.0: dx += 10.0
        if dy > 5.0: dy -= 10.0
        elif dy < -5.0: dy += 10.0
        return (
            int(self.rect.centerx + dx * self._scale),
            int(self.rect.centery + dy * self._scale),
        )

    def screen_to_world(self, sx: int, sy: int) -> Vec2:
        dx = (sx - self.rect.centerx) / self._scale
        dy = (sy - self.rect.centery) / self._scale
        return Vec2(
            (self.player.pos.x + dx) % 10.0,
            (self.player.pos.y + dy) % 10.0,
        )

    def contains(self, sx: int, sy: int) -> bool:
        return bool(self.rect.collidepoint(sx, sy))

    def find_object_at(self, sx: int, sy: int, objects: list) -> "Thing | None":
        best, best_dist = None, 16.0
        for obj in objects:
            ox, oy = self.world_to_screen(obj.pos)
            d = ((ox - sx) ** 2 + (oy - sy) ** 2) ** 0.5
            if d < best_dist:
                best_dist, best = d, obj
        return best

    # ── 描画サブルーチン ────────────────────────────────────────

    def _draw_grid(self, surface: pygame.Surface) -> None:
        """破線のセクタグリッドを描画する。"""
        if self._anim_offset:
            px = self.player.pos.x + self._anim_offset.x
            py = self.player.pos.y + self._anim_offset.y
        else:
            px, py = self.player.pos.x, self.player.pos.y
        w, h = self.rect.width, self.rect.height
        # SRCALPHA サーフェスに半透明で描画してから blit
        gs = pygame.Surface((w, h), pygame.SRCALPHA)
        color = (*GRID_COLOR, 90)  # 半透明
        for i in range(10):
            # 縦線 (world_x = i)
            dx = float(i) - px
            if dx > 5.0: dx -= 10.0
            elif dx < -5.0: dx += 10.0
            sx = int(w / 2 + dx * self._scale)
            if -2 <= sx <= w + 2:
                draw_dashed_line(gs, color, (sx, 0), (sx, h), dash=6, gap=4)
            # 横線 (world_y = i)
            dy = float(i) - py
            if dy > 5.0: dy -= 10.0
            elif dy < -5.0: dy += 10.0
            sy = int(h / 2 + dy * self._scale)
            if -2 <= sy <= h + 2:
                draw_dashed_line(gs, color, (0, sy), (w, sy), dash=6, gap=4)
        surface.blit(gs, self.rect.topleft)

    def _draw_range_circles(self, surface: pygame.Surface) -> None:
        if self._anim_offset is not None:
            return  # アニメーション中は射程円を非表示
        """射程範囲の半透明円とレーダー破線円をプレーヤー中心に描画する。"""
        cx, cy = self.rect.centerx, self.rect.centery
        overlay = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        ocx, ocy = self.rect.width // 2, self.rect.height // 2

        # ミサイル射程 (半透明赤)
        if self.player.missile_launcher and self.player.missile_launcher.stock > 0:
            m_px = int(self.player.missile_launcher.missile_range * GRID * self._scale)
            if m_px > 0:
                pygame.draw.circle(overlay, MISSILE_RANGE_COLOR, (ocx, ocy), m_px)

        # ビーム射程 (半透明青)
        if self.player.beam_launcher:
            b_px = int(self.player.beam_launcher.beam_range * GRID * self._scale)
            if b_px > 0:
                pygame.draw.circle(overlay, BEAM_RANGE_COLOR, (ocx, ocy), b_px)

        surface.blit(overlay, self.rect.topleft)

        # レーダー範囲 (破線円)
        if self.player.radar:
            r_px = int(self.player.radar.scan_range * GRID * self._scale)
            draw_dashed_circle(surface, RADAR_RING_COLOR, (cx, cy), r_px, dash=8, gap=5)

    def _active_contact_ids(self, universe: "Universe") -> set:
        """自艦・僚艦のレーダーに現在捕捉されているオブジェクトの ID セットを返す。"""
        ids: set = set()
        if self.player.radar:
            for c in self.player.radar.contacts:
                ids.add(c.id)
        from game.objects.vessel import Vessel
        for obj in universe.objects:
            if (isinstance(obj, Vessel) and obj.faction == self.player.faction
                    and obj is not self.player and obj.radar):
                for c in obj.radar.contacts:
                    ids.add(c.id)
        return ids

    def _draw_objects(self, surface: pygame.Surface, universe: "Universe") -> None:
        from game.objects.vessel import Vessel
        from game.objects.beam import Beam
        from game.vessels.heavy_cruiser import HeavyCruiser

        active_ids = self._active_contact_ids(universe)
        draw_list = list(universe.objects)
        # 自艦が破壊されて universe から削除されていても常に描画する
        if self.player not in draw_list:
            draw_list.append(self.player)

        for obj in draw_list:
            sx, sy = self.world_to_screen(obj.pos)
            if not (self.rect.left - 20 <= sx <= self.rect.right + 20 and
                    self.rect.top - 20 <= sy <= self.rect.bottom + 20):
                continue
            color = _color_for(obj)
            r = _radius_for(obj)

            # 自艦撃沈時はバツ印で表示
            if obj is self.player and obj.destroyed:
                d = r + 3
                pygame.draw.line(surface, (255, 60, 60), (sx - d, sy - d), (sx + d, sy + d), 3)
                pygame.draw.line(surface, (255, 60, 60), (sx + d, sy - d), (sx - d, sy + d), 3)
                continue

            from game.objects.star import Star as StarObj
            if isinstance(obj, StarObj):
                draw_asterisk(surface, color, sx, sy, r)
            else:
                pygame.draw.circle(surface, color, (sx, sy), r)
            # 旗艦・連邦基地は外側に二重丸を追加
            from game.objects.base_station import BaseStation as BS
            if isinstance(obj, HeavyCruiser) or (isinstance(obj, BS) and obj.faction == "U"):
                pygame.draw.circle(surface, color, (sx, sy), r + 4, 1)
            if obj is self.selected:
                pygame.draw.circle(surface, HIGHLIGHT_COLOR, (sx, sy), r + 4, 1)
            # アクティブレーダー捕捉中の印 (白点)
            if obj.id in active_ids:
                pygame.draw.circle(surface, (255, 255, 255), (sx, sy), 2)
            if isinstance(obj, Vessel) and obj.speed > 0:
                ex = int(sx + obj.heading.x * 16)
                ey = int(sy + obj.heading.y * 16)
                pygame.draw.line(surface, color, (sx, sy), (ex, ey), 2)
            if isinstance(obj, Beam):
                # origin を tip 相対でラッピングして描画（境界跨ぎで逆方向になるのを防ぐ）
                ddx = obj.origin.x - obj.pos.x
                ddy = obj.origin.y - obj.pos.y
                if ddx > 5.0: ddx -= 10.0
                elif ddx < -5.0: ddx += 10.0
                if ddy > 5.0: ddy -= 10.0
                elif ddy < -5.0: ddy += 10.0
                ox = int(sx + ddx * self._scale)
                oy = int(sy + ddy * self._scale)
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
            r = int(ex["max_r"] * (1.0 - t))
            v = int(255 * (1.0 - t))
            if r > 0:
                pygame.draw.circle(surface, (v, v, v), (sx, sy), r)
        surface.set_clip(old_clip)

    # ── メイン描画 ──────────────────────────────────────────────

    def draw(self, surface: pygame.Surface, universe: "Universe") -> None:
        pygame.draw.rect(surface, MAP_BG, self.rect)
        self._draw_grid(surface)
        self._draw_range_circles(surface)

        old_clip = surface.get_clip()
        surface.set_clip(self.rect)
        self._draw_objects(surface, universe)
        surface.set_clip(old_clip)

        pygame.draw.rect(surface, (60, 60, 80), self.rect, 1)
