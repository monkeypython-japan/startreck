"""ブリッジ要員: ナビゲーター・ガンナー・コマンダーの基底クラス。"""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.objects.vessel import Vessel


class BridgeCrew:
    def __init__(self, vessel: "Vessel") -> None:
        self.vessel: "Vessel" = vessel

    def report(self, msg: str) -> None:
        self.vessel.messages.append(msg)

    def update(self, dt: float) -> None:
        pass
