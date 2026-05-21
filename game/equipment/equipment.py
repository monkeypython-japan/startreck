"""装備: 艦艇に構成として保持される基底クラス。"""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.objects.thing import Thing


class Equipment:
    def __init__(self, owner: "Thing") -> None:
        self.owner: "Thing" = owner

    def update(self, dt: float) -> None:
        pass
