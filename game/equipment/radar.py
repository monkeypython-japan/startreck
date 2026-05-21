"""レーダー: 探索範囲内のオブジェクトを検出しインテグレータに報告する。"""
from __future__ import annotations
from game.coords import Vec2, distance_grid, GRID
from game.equipment.equipment import Equipment
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.objects.thing import Thing
    from game.equipment.integrator import Integrator


class Radar(Equipment):
    def __init__(self, owner: "Thing", scan_range: float, integrator: "Integrator") -> None:
        super().__init__(owner)
        self.scan_range: float = scan_range  # grid
        self.integrator: "Integrator" = integrator
        self.contacts: list["Thing"] = []

    def scan(self, all_objects: list["Thing"], game_time: int) -> None:
        """探索範囲内のオブジェクトを検出してインテグレータに記録する。"""
        origin = self.owner.pos
        self.contacts = [
            obj for obj in all_objects
            if obj is not self.owner and distance_grid(origin, obj.pos) <= self.scan_range
        ]
        for obj in self.contacts:
            self.integrator.record(obj, game_time)

    def in_range(self, pos: Vec2) -> bool:
        return distance_grid(self.owner.pos, pos) <= self.scan_range

    def find_contact(self, obj_id: str) -> "Thing | None":
        return next((c for c in self.contacts if c.id == obj_id), None)
