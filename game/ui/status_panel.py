"""ステータスパネル: プレーヤー艦の状態をバー付きで表示する。"""
from __future__ import annotations
import pygame
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.vessels.special_ship import SpecialShip
    from game.universe import Universe

PANEL_BG = (8, 10, 18)
PANEL_BORDER = (60, 60, 80)
TITLE_COLOR = (120, 180, 255)
LABEL_COLOR = (130, 130, 150)
VALUE_COLOR = (200, 210, 220)
BAR_BG = (35, 38, 52)
BAR_TEXT_COLOR = (255, 255, 255)
BAR_TEXT_SHADOW = (0, 0, 0)
DIVIDER = (50, 55, 70)
PADDING = 8
LINE_H = 19
BAR_H = 11
BAR_LABEL_W = 44


def _bar(screen: pygame.Surface, x: int, y: int, w: int, ratio: float, color: tuple) -> None:
    pygame.draw.rect(screen, BAR_BG, (x, y, w, BAR_H))
    fill = int(w * max(0.0, min(1.0, ratio)))
    if fill > 0:
        pygame.draw.rect(screen, color, (x, y, fill, BAR_H))


def _bar_text(font: pygame.font.Font, screen: pygame.Surface, text: str, x: int, y: int) -> None:
    """バー上の値テキストを黒影付きで描画する（バー色に関わらず読める）。"""
    screen.blit(font.render(text, True, BAR_TEXT_SHADOW), (x + 1, y + 1))
    screen.blit(font.render(text, True, BAR_TEXT_COLOR), (x, y))


class StatusPanel:
    def __init__(self, rect: pygame.Rect, font: pygame.font.Font) -> None:
        self.rect = rect
        self.font = font

    def draw(self, screen: pygame.Surface, universe: "Universe", player: "SpecialShip") -> None:
        pygame.draw.rect(screen, PANEL_BG, self.rect)
        x = self.rect.left + PADDING
        w = self.rect.width - PADDING * 2
        y = self.rect.top + PADDING

        screen.blit(self.font.render("U.S.S. YUKIKAZE", True, TITLE_COLOR), (x, y))
        y += LINE_H

        info = f"Time:{universe.time:>5}s   Objects:{len(universe.objects)}"
        screen.blit(self.font.render(info, True, LABEL_COLOR), (x, y))
        y += LINE_H
        pygame.draw.line(screen, DIVIDER, (x, y), (x + w, y))
        y += 5

        if player.destroyed:
            screen.blit(self.font.render("★  撃 墜  ★", True, (255, 60, 60)), (x, y))
            pygame.draw.rect(screen, PANEL_BORDER, self.rect, 1)
            return

        sec = f"{int(player.pos.x)}-{int(player.pos.y)}"
        screen.blit(
            self.font.render(f"Pos ({player.pos.x:.2f}, {player.pos.y:.2f})  Sec {sec}", True, VALUE_COLOR),
            (x, y),
        )
        y += LINE_H
        screen.blit(
            self.font.render(f"Speed: {player.speed:.1f} g/s  (max {player.max_speed})", True, VALUE_COLOR),
            (x, y),
        )
        y += LINE_H + 3

        # HP バー
        hp_ratio = 1.0 - player.damage / player.durability
        hp_color = (70, 200, 70) if hp_ratio > 0.5 else (210, 150, 40) if hp_ratio > 0.25 else (220, 55, 55)
        screen.blit(self.font.render("HP", True, LABEL_COLOR), (x, y))
        _bar(screen, x + BAR_LABEL_W, y, w - BAR_LABEL_W, hp_ratio, hp_color)
        val = f"{player.durability - player.damage:.0f}/{player.durability:.0f}gj"
        _bar_text(self.font, screen, val, x + BAR_LABEL_W + 2, y)
        y += LINE_H

        # シールド バー
        if player.shield:
            shield_r = player.shield.current_rate / 100.0
            screen.blit(self.font.render("SH", True, LABEL_COLOR), (x, y))
            _bar(screen, x + BAR_LABEL_W, y, w - BAR_LABEL_W, shield_r, (55, 155, 220))
            sh_val = f"{player.shield.current_rate:.0f}% (設定:{player.shield.set_rate:.0f}%)"
            _bar_text(self.font, screen, sh_val, x + BAR_LABEL_W + 2, y)
            y += LINE_H

        # キャパシタ バー
        if player.generator:
            cap_r = player.generator.capacitor / player.generator.capacitor_max
            screen.blit(self.font.render("CAP", True, LABEL_COLOR), (x, y))
            _bar(screen, x + BAR_LABEL_W, y, w - BAR_LABEL_W, cap_r, (90, 170, 255))
            cap_val = f"{player.generator.capacitor:.0f}/{player.generator.capacitor_max:.0f}gj"
            _bar_text(self.font, screen, cap_val, x + BAR_LABEL_W + 2, y)
            y += LINE_H

            fuel_r = player.generator.fuel / player.generator.fuel_max
            screen.blit(self.font.render("FUEL", True, LABEL_COLOR), (x, y))
            _bar(screen, x + BAR_LABEL_W, y, w - BAR_LABEL_W, fuel_r, (200, 155, 55))
            fuel_val = f"{player.generator.fuel:.0f}/{player.generator.fuel_max:.0f}gj"
            _bar_text(self.font, screen, fuel_val, x + BAR_LABEL_W + 2, y)
            y += LINE_H

        # ミサイル残弾
        if player.missile_launcher:
            m_val = f"Missiles: {player.missile_launcher.stock} / {player.missile_launcher.capacity}"
            screen.blit(self.font.render(m_val, True, VALUE_COLOR), (x, y))
            y += LINE_H

        # ジャンプドライブ
        if player.jump_drive and player.generator:
            ready = player.generator.capacitor >= player.jump_drive.required_energy
            j_txt = f"Jump: {'READY' if ready else f'要 {player.jump_drive.required_energy:.0f}gj'}"
            j_color = (80, 255, 190) if ready else (130, 130, 150)
            screen.blit(self.font.render(j_txt, True, j_color), (x, y))
            y += LINE_H

        y += 3
        pygame.draw.line(screen, DIVIDER, (x, y), (x + w, y))
        y += 5

        from game.objects.base_station import BaseStation
        from game.objects.vessel import Vessel
        fed_bases = sum(1 for o in universe.objects if isinstance(o, BaseStation) and o.faction == "U")
        klingons = sum(1 for o in universe.objects if isinstance(o, Vessel) and o.faction == "K")
        screen.blit(
            self.font.render(f"Fed Bases: {fed_bases}    Klingons: {klingons}", True, VALUE_COLOR),
            (x, y),
        )

        pygame.draw.rect(screen, PANEL_BORDER, self.rect, 1)
