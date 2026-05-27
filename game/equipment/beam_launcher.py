"""ビーム発射機: エネルギーを消費してビームを発射する。"""
from __future__ import annotations
from game.coords import direction_to
from game.equipment.equipment import Equipment
from game.constants import BEAM_ENERGY_COST_RATE
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from game.objects.thing import Thing
    from game.objects.beam import Beam
    from game.equipment.generator import Generator


class BeamLauncher(Equipment):
    def __init__(
        self,
        owner: "Thing",
        iff: str,
        beam_power: float,
        beam_speed: float,
        beam_range: float,
        reload_time: float = 0.0,
        on_report: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(owner)
        self.iff: str = iff
        self.beam_power: float = beam_power
        self.beam_speed: float = beam_speed
        self.beam_range: float = beam_range  # grid
        self._reload_time: float = reload_time
        self._reload_remaining: float = 0.0
        self._on_report: Callable[[str], None] | None = on_report
        self.shots_fired: int = 0   # 累計発射数（ログ用）
        self.hits: int = 0          # 累計命中数（ログ用）

    def update(self, dt: float) -> None:
        if self._reload_remaining > 0.0:
            self._reload_remaining = max(0.0, self._reload_remaining - dt)

    @property
    def required_energy(self) -> float:
        return self.beam_power * BEAM_ENERGY_COST_RATE

    def fire(self, target_pos, generator: "Generator") -> "Beam | None":
        """ビームを発射して Beam オブジェクトを返す。装填中・エネルギー不足なら None。"""
        if self._reload_remaining > 0.0:
            if self._on_report:
                self._on_report(f"ビーム装填中 残り{self._reload_remaining:.1f}秒")
            return None
        if not generator.consume_energy(self.required_energy):
            if self._on_report:
                self._on_report("ビーム発射不可: エネルギー不足")
            return None
        from game.objects.beam import Beam
        heading = direction_to(self.owner.pos, target_pos)
        b = Beam(
            origin=self.owner.pos,
            heading=heading,
            iff=self.iff,
            power=self.beam_power,
            speed=self.beam_speed,
            max_range=self.beam_range,
            owner=self.owner,
            on_report=self._on_report,
            on_hit=self._on_beam_hit,
        )
        self.shots_fired += 1
        self._reload_remaining = self._reload_time
        if self._on_report:
            self._on_report(f"ビーム発射 消費:{self.required_energy:.0f}gj")
        return b

    def _on_beam_hit(self) -> None:
        self.hits += 1

    @property
    def ready(self) -> bool:
        return self._reload_remaining <= 0.0
