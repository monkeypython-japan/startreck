"""恒星: 不破壊・静止オブジェクト。"""
from __future__ import annotations
from game.coords import Vec2
from game.objects.thing import Thing
from game.constants import STAR_SIZE


class Star(Thing):
    def __init__(self, pos: Vec2) -> None:
        super().__init__(pos, size=STAR_SIZE, durability=float("inf"))

    def receive_damage(self, amount: float) -> None:
        pass  # 恒星は破壊されない
