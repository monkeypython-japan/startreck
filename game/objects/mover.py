"""移動体: 速度と方位ベクトルを持つ物体。"""
from __future__ import annotations
from game.coords import Vec2, wrap_vec, direction_to, GRID
from game.objects.thing import Thing


class Mover(Thing):
    def __init__(
        self,
        pos: Vec2,
        size: float,
        durability: float,
    ) -> None:
        super().__init__(pos, size, durability)
        self.heading: Vec2 = Vec2(1.0, 0.0)  # 移動方位単位ベクトル
        self.speed: float = 0.0              # grid/sec

    def set_heading_to(self, target: Vec2) -> None:
        """targetへの方位に向ける（閉じた座標系考慮）。"""
        h = direction_to(self.pos, target)
        if h.length() > 0:
            self.heading = h

    def update(self, dt: float) -> None:
        if self.speed != 0.0:
            delta = self.heading * (self.speed * dt * GRID)
            self.pos = wrap_vec(Vec2(self.pos.x + delta.x, self.pos.y + delta.y))

    def accelerate(self, new_speed: float, max_speed: float) -> float:
        """速度を変更し消費エネルギー量を返す。慣性なし。"""
        new_speed = max(0.0, min(new_speed, max_speed))
        cost = abs(new_speed - self.speed)  # gj (1 grid/sec の変化で 1 gj)
        self.speed = new_speed
        return cost

    def stop(self) -> float:
        """停止し消費エネルギー量を返す。"""
        return self.accelerate(0.0, max_speed=self.speed)
