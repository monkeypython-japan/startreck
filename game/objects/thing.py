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
        self.name: str = ""
        self.pos: Vec2 = pos
        self.size: float = size          # grid
        self.durability: float = durability  # gj
        self.damage: float = 0.0            # 蓄積ダメージ (gj)
        self.destroyed: bool = False

    def receive_damage(self, amount: float) -> float:
        """ダメージを適用し、実際に船体に与えたダメージ量を返す。"""
        if self.destroyed:
            return 0.0
        self.damage += amount
        if self.damage >= self.durability:
            self.destroyed = True
        return amount

    def update(self, dt: float) -> None:
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(pos={self.pos}, destroyed={self.destroyed})"
