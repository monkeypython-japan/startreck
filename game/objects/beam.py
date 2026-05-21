"""ビーム: 先端が進みながら周辺オブジェクトにダメージを与える移動体。"""
from __future__ import annotations
from game.coords import Vec2, distance_grid, direction_to, GRID
from game.objects.mover import Mover
from game.constants import (
    BEAM_FULL_DAMAGE_RANGE,
    BEAM_PARTIAL_DAMAGE_RANGE,
    BEAM_PARTIAL_DAMAGE_RATE,
)
from typing import Callable


class Beam(Mover):
    def __init__(
        self,
        origin: Vec2,
        heading: Vec2,
        iff: str,
        power: float,
        speed: float,
        max_range: float,
        on_report: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(origin, size=0.0, durability=1.0)
        self.origin: Vec2 = origin
        self.heading = heading.normalized()
        self.speed = speed          # grid/sec
        self.iff: str = iff
        self.power: float = power   # gj
        self.max_range: float = max_range   # grid
        self.traveled: float = 0.0          # grid
        self._on_report: Callable[[str], None] | None = on_report

    def update(self, dt: float) -> None:
        if self.destroyed:
            return
        move_grid = self.speed * dt
        self.traveled += move_grid
        if self.traveled >= self.max_range:
            self.destroyed = True
            return
        super().update(dt)

    def check_damage(self, objects: list) -> None:
        """先端周辺のオブジェクトにダメージを与える。"""
        if self.destroyed:
            return
        from game.objects.star import Star
        for obj in objects:
            if obj is self:
                continue
            dist = distance_grid(self.pos, obj.pos) - obj.size
            if isinstance(obj, Star):
                if dist <= 0:
                    self.destroyed = True
                    return
                continue
            if dist <= BEAM_FULL_DAMAGE_RANGE:
                dmg = self.power
            elif dist <= BEAM_PARTIAL_DAMAGE_RANGE:
                dmg = self.power * BEAM_PARTIAL_DAMAGE_RATE
            else:
                continue
            obj.receive_damage(dmg)
            self.destroyed = True
            if self._on_report:
                self._on_report(
                    f"ビーム命中: {type(obj).__name__} に {dmg:.0f}gj ダメージ"
                )
            return
