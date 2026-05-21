"""物体: すべてのゲームオブジェクトの基底クラス。"""
from __future__ import annotations
import uuid
from game.coords import Vec2


class Thing:
    def __init__(
        self,
        pos: Vec2,
        size: float,
        durability: float,
    ) -> None:
        self.id: str = str(uuid.uuid4())
        self.pos: Vec2 = pos
        self.size: float = size          # grid
        self.durability: float = durability  # gj
        self.damage: float = 0.0            # 蓄積ダメージ (gj)
        self.destroyed: bool = False

    def receive_damage(self, amount: float) -> None:
        if self.destroyed:
            return
        self.damage += amount
        if self.damage >= self.durability:
            self.destroyed = True

    def update(self, dt: float) -> None:
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(pos={self.pos}, destroyed={self.destroyed})"
