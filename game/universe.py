"""宇宙: ゲームのメインループとオブジェクト管理。"""
from __future__ import annotations
from game.objects.thing import Thing


class Universe:
    def __init__(self) -> None:
        self.objects: list[Thing] = []
        self.time: int = 0          # ゲーム開始からの秒数
        self._elapsed: float = 0.0

    def add(self, obj: Thing) -> None:
        self.objects.append(obj)
        from game.objects.vessel import Vessel
        if isinstance(obj, Vessel):
            obj.universe = self

    def remove_destroyed(self) -> None:
        self.objects = [o for o in self.objects if not o.destroyed]

    def update(self, dt: float) -> None:
        self.remove_destroyed()
        for obj in list(self.objects):
            obj.update(dt)
        self._check_weapon_collisions()
        self._elapsed += dt
        while self._elapsed >= 1.0:
            self._elapsed -= 1.0
            self.time += 1
            self._tick()

    def _check_weapon_collisions(self) -> None:
        from game.objects.missile import Missile
        from game.objects.beam import Beam
        non_weapons = [o for o in self.objects
                       if not isinstance(o, (Missile, Beam))]
        for obj in list(self.objects):
            if isinstance(obj, Missile):
                obj.check_detonation(non_weapons)
            elif isinstance(obj, Beam):
                obj.check_damage(non_weapons)

    def _tick(self) -> None:
        """1秒ごとのゲームロジック: AI意思決定・勝敗判定。"""
        from game.objects.vessel import Vessel
        for obj in list(self.objects):
            if (isinstance(obj, Vessel)
                    and obj.bridge
                    and obj.bridge.commander):
                obj.bridge.commander.tick()

    @property
    def victory(self) -> str | None:
        """勝者を返す。ゲーム継続中は None。未初期化は None。"""
        if not self.objects:
            return None
        from game.objects.base_station import BaseStation
        from game.objects.vessel import Vessel

        bases = [o for o in self.objects
                 if isinstance(o, BaseStation) and o.faction == "U"]
        klingons = [o for o in self.objects
                    if isinstance(o, Vessel) and o.faction == "K"]
        if not bases:
            return "K"
        if not klingons:
            return "U"
        return None
