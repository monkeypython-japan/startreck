"""メッセージウィンドウ: クルーログをスクロール表示する。"""
from __future__ import annotations
import pygame

MSG_BG = (8, 10, 18)
MSG_BORDER = (60, 60, 80)
MSG_TEXT = (170, 190, 170)
TITLE_COLOR = (100, 160, 100)
PADDING = 5
LINE_H = 18


class MessageWindow:
    def __init__(self, rect: pygame.Rect, font: pygame.font.Font) -> None:
        self.rect = rect
        self.font = font
        self.messages: list[str] = []
        self._max = 300
        self._scroll = 0

    def add(self, message: str) -> None:
        self.messages.append(message)
        if len(self.messages) > self._max:
            self.messages = self.messages[-self._max:]
        text_h = self.rect.height - PADDING * 2 - LINE_H
        max_scroll = max(0, len(self.messages) * LINE_H - text_h)
        self._scroll = max_scroll

    def scroll(self, delta: int) -> None:
        text_h = self.rect.height - PADDING * 2 - LINE_H
        max_scroll = max(0, len(self.messages) * LINE_H - text_h)
        self._scroll = max(0, min(max_scroll, self._scroll + delta))

    def draw(self, screen: pygame.Surface) -> None:
        pygame.draw.rect(screen, MSG_BG, self.rect)

        title = self.font.render("─── クルーログ ───", True, TITLE_COLOR)
        screen.blit(title, (self.rect.left + PADDING, self.rect.top + PADDING))

        text_rect = pygame.Rect(
            self.rect.left + PADDING,
            self.rect.top + PADDING + LINE_H,
            self.rect.width - PADDING * 2,
            self.rect.height - PADDING * 2 - LINE_H,
        )
        old_clip = screen.get_clip()
        screen.set_clip(text_rect)

        y = text_rect.top - self._scroll
        for msg in self.messages:
            if text_rect.top <= y + LINE_H and y <= text_rect.bottom:
                surf = self.font.render(msg, True, MSG_TEXT)
                screen.blit(surf, (text_rect.left, y))
            y += LINE_H

        screen.set_clip(old_clip)
        pygame.draw.rect(screen, MSG_BORDER, self.rect, 1)
