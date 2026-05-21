"""ポップアップメニュー: オブジェクトクリック時のコンテキストメニュー。"""
from __future__ import annotations
import pygame
from typing import Callable

MENU_BG = (18, 20, 32)
MENU_BORDER = (90, 110, 150)
HOVER_BG = (45, 65, 100)
TEXT_COLOR = (215, 215, 235)
DISABLED_COLOR = (90, 90, 110)
ITEM_H = 26
ITEM_W = 200
PAD = 4


class MenuItem:
    def __init__(self, label: str, callback: Callable[[], None], enabled: bool = True) -> None:
        self.label = label
        self.callback = callback
        self.enabled = enabled


class PopupMenu:
    def __init__(self, font: pygame.font.Font, screen_w: int = 1200, screen_h: int = 800) -> None:
        self.font = font
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.visible = False
        self.items: list[MenuItem] = []
        self._x = 0
        self._y = 0
        self._hover = -1

    def show(self, x: int, y: int, items: list[MenuItem]) -> None:
        self.items = items
        self.visible = True
        self._hover = -1
        total_h = len(items) * ITEM_H + PAD * 2
        total_w = ITEM_W + PAD * 2
        self._x = min(x, self.screen_w - total_w - 2)
        self._y = min(y, self.screen_h - total_h - 2)

    def hide(self) -> None:
        self.visible = False
        self.items = []

    def handle_mouse_motion(self, mx: int, my: int) -> None:
        if not self.visible:
            return
        self._hover = -1
        for i in range(len(self.items)):
            iy = self._y + PAD + i * ITEM_H
            if self._x + PAD <= mx <= self._x + PAD + ITEM_W and iy <= my <= iy + ITEM_H:
                self._hover = i

    def handle_click(self, mx: int, my: int) -> bool:
        """メニュー内クリックならコールバック実行して True、外ならメニュー閉じて False。"""
        if not self.visible:
            return False
        menu_rect = pygame.Rect(self._x, self._y,
                                ITEM_W + PAD * 2, len(self.items) * ITEM_H + PAD * 2)
        if not menu_rect.collidepoint(mx, my):
            self.hide()
            return False
        for i, item in enumerate(self.items):
            iy = self._y + PAD + i * ITEM_H
            if iy <= my <= iy + ITEM_H and item.enabled:
                self.hide()
                item.callback()
                return True
        return True

    def draw(self, screen: pygame.Surface) -> None:
        if not self.visible:
            return
        total_h = len(self.items) * ITEM_H + PAD * 2
        total_w = ITEM_W + PAD * 2
        pygame.draw.rect(screen, MENU_BG, (self._x, self._y, total_w, total_h))
        pygame.draw.rect(screen, MENU_BORDER, (self._x, self._y, total_w, total_h), 1)
        for i, item in enumerate(self.items):
            iy = self._y + PAD + i * ITEM_H
            if i == self._hover and item.enabled:
                pygame.draw.rect(screen, HOVER_BG, (self._x + PAD, iy, ITEM_W, ITEM_H))
            color = TEXT_COLOR if item.enabled else DISABLED_COLOR
            surf = self.font.render(item.label, True, color)
            screen.blit(surf, (self._x + PAD * 2, iy + (ITEM_H - surf.get_height()) // 2))
