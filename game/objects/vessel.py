"""艦艇: 武装・装備を持つ移動体（フェーズ3で本実装）。"""
from __future__ import annotations
from game.coords import Vec2
from game.objects.mover import Mover


class Vessel(Mover):
    def __init__(
        self,
        pos: Vec2,
        size: float,
        durability: float,
        max_speed: float,
        faction: str,
    ) -> None:
        super().__init__(pos, size, durability)
        self.max_speed: float = max_speed  # grid/sec
        self.faction: str = faction        # "U": 連邦, "K": クリンゴン
        self.supply_provider: bool = False
        self.supplying: bool = False
