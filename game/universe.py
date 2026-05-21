"""宇宙: ゲームのメインループとオブジェクト管理。"""
from __future__ import annotations
from typing import TYPE_CHECKING
from game.objects.thing import Thing

if TYPE_CHECKING:
    pass


class Universe:
    def __init__(self) -> None:
        self.objects: list[Thing] = []
        self.time: int = 0          # ゲーム開始からの秒数
        self._elapsed: float = 0.0  # 次のtickまでの累積時間

    def add(self, obj: Thing) -> None:
        self.objects.append(obj)

    def remove_destroyed(self) -> None:
        self.objects = [o for o in self.objects if not o.destroyed]

    def update(self, dt: float) -> None:
        self.remove_destroyed()
        for obj in self.objects:
            obj.update(dt)
        self._elapsed += dt
        while self._elapsed >= 1.0:
            self._elapsed -= 1.0
            self.time += 1
            self._tick()

    def _tick(self) -> None:
        """1秒ごとのゲームロジック処理（AI判断・勝敗判定など）。"""
        pass

    @property
    def victory(self) -> str | None:
        """勝者を返す。ゲーム継続中は None。"""
        from game.objects.base_station import BaseStation
        from game.objects.vessel import Vessel

        bases = [o for o in self.objects if isinstance(o, BaseStation) and o.faction == "U"]
        klingons = [o for o in self.objects if isinstance(o, Vessel) and o.faction == "K"]
        if not bases:
            return "K"  # クリンゴン勝利
        if not klingons:
            return "U"  # 連邦勝利
        return None
