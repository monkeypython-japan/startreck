"""コマンダー: ナビゲーター・ガンナーに指示を出す基底クラス。"""
from __future__ import annotations
from game.crew.bridge_crew import BridgeCrew
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.objects.vessel import Vessel


class Commander(BridgeCrew):
    def __init__(self, vessel: "Vessel") -> None:
        super().__init__(vessel)

    def tick(self) -> None:
        """1秒ごとに呼ばれる意思決定メソッド。サブクラスで実装。"""
        pass
