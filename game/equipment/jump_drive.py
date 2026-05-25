"""ジャンプドライブ: 特務艦専用。味方基地への瞬時移動。"""
from __future__ import annotations
import math
import random
from game.coords import Vec2, GRID, wrap_vec
from game.equipment.equipment import Equipment
from game.constants import JUMP_ENERGY_RATE, JUMP_LANDING_RADIUS
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from game.objects.thing import Thing
    from game.objects.base_station import BaseStation
    from game.equipment.generator import Generator


class JumpDrive(Equipment):
    def __init__(
        self,
        owner: "Thing",
        capacitor_max: float,
        on_report: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(owner)
        self.capacitor_max: float = capacitor_max
        self._on_report: Callable[[str], None] | None = on_report
        self.jump_origin: Vec2 | None = None  # UI がアニメーション開始後に None に戻す

    @property
    def required_energy(self) -> float:
        return self.capacitor_max * JUMP_ENERGY_RATE

    def jump(self, target: "BaseStation", generator: "Generator") -> bool:
        """ジャンプを実行。成功すれば True、エネルギー不足なら False。"""
        if generator.capacitor < self.required_energy:
            if self._on_report:
                self._on_report("ジャンプ不可: エネルギー不足")
            return False
        generator.consume_energy(self.required_energy)
        self.jump_origin = Vec2(self.owner.pos.x, self.owner.pos.y)
        angle = random.uniform(0, 2 * math.pi)
        radius = JUMP_LANDING_RADIUS * GRID
        dx = math.cos(angle) * radius
        dy = math.sin(angle) * radius
        self.owner.pos = wrap_vec(Vec2(target.pos.x + dx, target.pos.y + dy))
        # ジャンプ後は自動停止
        self.owner.speed = 0.0
        from game.objects.vessel import Vessel
        if isinstance(self.owner, Vessel) and self.owner.bridge and self.owner.bridge.navigator:
            self.owner.bridge.navigator.stop()
        if self._on_report:
            self._on_report(f"ジャンプ完了: {target.pos} 近傍に移動")
        return True
