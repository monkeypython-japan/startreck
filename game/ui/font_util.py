"""日本語対応フォントを返すユーティリティ。"""
import os
import pygame

# macOS のヒラギノフォントパス (日本語を確実にカバー)
_FONT_PATHS = [
    "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴシック W5.ttc",
]

_FALLBACK_SYSFONTS = [
    "applesdgothicneo",
    "applegothic",
    "hiraginosansgb",
]


def make_font(size: int) -> pygame.font.Font:
    """日本語グリフを持つフォントを返す。ヒラギノが最優先。"""
    for path in _FONT_PATHS:
        if os.path.exists(path):
            return pygame.font.Font(path, size)
    for name in _FALLBACK_SYSFONTS:
        try:
            f = pygame.font.SysFont(name, size)
            if f.size("撃")[0] > 4:
                return f
        except Exception:
            pass
    return pygame.font.SysFont("monospace", size)
