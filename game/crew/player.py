"""プレイヤー: 人間操作のコマンダー（Phase 5 で本実装）。"""
from __future__ import annotations
from game.crew.commander import Commander
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.objects.vessel import Vessel


class Player(Commander):
    def __init__(self, vessel: "Vessel") -> None:
        super().__init__(vessel)

    def tick(self) -> None:
        pass  # プレイヤーは tick ではなく UI イベントで操作する
