"""ブリッジ: 要員（ナビゲーター・ガンナー・コマンダー）を保持する（フェーズ3で本実装）。"""
from __future__ import annotations
from game.equipment.equipment import Equipment
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.objects.thing import Thing
    from game.equipment.radar import Radar


class Bridge(Equipment):
    def __init__(self, owner: "Thing", radar: "Radar") -> None:
        super().__init__(owner)
        self.radar: "Radar" = radar
        self.navigator = None
        self.gunner = None
        self.commander = None
