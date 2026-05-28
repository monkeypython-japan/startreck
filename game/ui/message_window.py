"""メッセージウィンドウ: クルーログをスクロール表示する。"""
from __future__ import annotations
import pygame
from game.ui.draw_utils import LCARS_GOLD, draw_lcars_header

MSG_BG = (8, 10, 18)
MSG_TEXT = (170, 190, 170)
MSG_ALERT = (255, 60, 60)
PADDING = 5
LINE_H = 18
HDR_H = 22


class MessageWindow:
    def __init__(self, rect: pygame.Rect, font: pygame.font.Font) -> None:
        self.rect = rect
        self.font = font
        self.messages: list[tuple[str, tuple]] = []
        self._max = 300
        self._scroll = 0

    def add(self, message: str, color: tuple | None = None) -> None:
        self.messages.append((message, color or MSG_TEXT))
        if len(self.messages) > self._max:
            self.messages = self.messages[-self._max:]
        text_h = self.rect.height - PADDING * 2 - HDR_H
        max_scroll = max(0, len(self.messages) * LINE_H - text_h)
        self._scroll = max_scroll

    def add_alert(self, message: str) -> None:
        self.add(message, MSG_ALERT)

    def scroll(self, delta: int) -> None:
        text_h = self.rect.height - PADDING * 2 - HDR_H
        max_scroll = max(0, len(self.messages) * LINE_H - text_h)
        self._scroll = max(0, min(max_scroll, self._scroll + delta))

    def draw(self, screen: pygame.Surface) -> None:
        pygame.draw.rect(screen, MSG_BG, self.rect)
        draw_lcars_header(screen, self.rect, "COMMUNICATIONS", LCARS_GOLD, self.font,
                          height=HDR_H)

        text_rect = pygame.Rect(
            self.rect.left + PADDING,
            self.rect.top + HDR_H + PADDING,
            self.rect.width - PADDING * 2,
            self.rect.height - HDR_H - PADDING * 2,
        )
        old_clip = screen.get_clip()
        screen.set_clip(text_rect)

        y = text_rect.top - self._scroll
        for msg, color in self.messages:
            if text_rect.top <= y + LINE_H and y <= text_rect.bottom:
                surf = self.font.render(msg, True, color)
                screen.blit(surf, (text_rect.left, y))
            y += LINE_H

        screen.set_clip(old_clip)
        pygame.draw.rect(screen, LCARS_GOLD, self.rect, 1)
