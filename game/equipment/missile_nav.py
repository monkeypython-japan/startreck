"""ミサイルナビゲーション: 母艦レーダーで目標を追尾する。"""
from __future__ import annotations
from game.coords import direction_to
from game.equipment.equipment import Equipment
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.objects.thing import Thing
    from game.objects.mover import Mover
    from game.equipment.radar import Radar


class MissileNavigation(Equipment):
    def __init__(self, owner: "Mover", mothership: "Thing", radar: "Radar") -> None:
        super().__init__(owner)
        self.mothership: "Thing" = mothership
        self.radar: "Radar" = radar
        self.target: "Thing | None" = None
        self.missile_speed: float = 0.0  # grid/sec

    def set_target(self, target: "Thing", speed: float) -> None:
        self.target = target
        self.missile_speed = speed

    def update(self, dt: float) -> None:
        from game.objects.mover import Mover
        missile: Mover = self.owner  # type: ignore[assignment]

        if self.target is None:
            return

        # 母艦が破壊された場合は更新停止（現在の進路を維持）
        if self.mothership.destroyed:
            return

        # 目標が母艦のレーダー範囲内にある場合のみ追尾
        if self.radar.in_range(self.target.pos):
            missile.heading = direction_to(missile.pos, self.target.pos)

        missile.speed = self.missile_speed
