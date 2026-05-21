"""基地: 静止オブジェクト、補給機能を持つ。"""
from __future__ import annotations
from game.coords import Vec2
from game.objects.thing import Thing
from game.constants import BASE_DURABILITY, BASE_SIZE


class BaseStation(Thing):
    def __init__(self, pos: Vec2, faction: str = "U") -> None:
        super().__init__(pos, size=BASE_SIZE, durability=BASE_DURABILITY)
        self.faction: str = faction  # "U": 連邦, "K": クリンゴン
