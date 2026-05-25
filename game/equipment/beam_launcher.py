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
        on_report: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(owner)
        self.iff: str = iff
        self.beam_power: float = beam_power
        self.beam_speed: float = beam_speed
        self.beam_range: float = beam_range  # grid
        self._on_report: Callable[[str], None] | None = on_report
        self._active_beam: "Beam | None" = None

    @property
    def required_energy(self) -> float:
        return self.beam_power * BEAM_ENERGY_COST_RATE

    def fire(self, target_pos, generator: "Generator") -> "Beam | None":
        """ビームを発射して Beam オブジェクトを返す。前のビーム飛行中・エネルギー不足なら None。"""
        if self._active_beam is not None and not self._active_beam.destroyed:
            if self._on_report:
                self._on_report("ビーム発射不可: 前のビームが飛行中")
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
        )
        self._active_beam = b
        if self._on_report:
            self._on_report(f"ビーム発射 消費:{self.required_energy:.0f}gj")
        return b
