"""シールド: ダメージを防御しエネルギーを消費しながら回復する。"""
from __future__ import annotations
from game.equipment.equipment import Equipment
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.objects.thing import Thing
    from game.equipment.generator import Generator


class Shield(Equipment):
    def __init__(
        self,
        owner: "Thing",
        max_defense_energy: float,
        recovery_rate: float,
        recovery_energy_cost: float,
        deploy_energy_cost: float,
    ) -> None:
        super().__init__(owner)
        self.max_defense_energy: float = max_defense_energy  # gj
        self.set_rate: float = 0.0      # 設定防御率 (%)
        self.current_rate: float = 0.0  # 現在防御率 (%)
        self.recovery_rate: float = recovery_rate            # %/sec
        self.recovery_energy_cost: float = recovery_energy_cost  # gj/%
        self.deploy_energy_cost: float = deploy_energy_cost      # gj/%/sec

    def set_defense_rate(self, rate: float) -> None:
        self.set_rate = max(0.0, min(rate, 100.0))
        # 設定値が変わったら current_rate を即座に新設定値に合わせる
        # (上げ: 即時展開 / 下げ: 即時解除)
        self.current_rate = self.set_rate

    def absorb(self, incoming_damage: float) -> float:
        """ダメージを吸収し、艦体に届くダメージ量を返す。

        被弾後、現在防御率は (吸収量 / 最大防御エネルギー * 100%) だけ低下する。
        """
        if self.current_rate <= 0.0:
            return incoming_damage
        absorbable = self.max_defense_energy * self.current_rate / 100.0
        absorbed = min(incoming_damage, absorbable)
        self.current_rate = max(0.0, self.current_rate - absorbed / self.max_defense_energy * 100.0)
        return incoming_damage - absorbed

    def update(self, dt: float, generator: "Generator") -> None:
        """展開エネルギー消費と、設定防御率までの回復処理。"""
        if self.current_rate <= 0.0 and self.set_rate <= 0.0:
            return

        # 展開中は現在防御率に応じてエネルギーを消費
        deploy_cost = self.current_rate * self.deploy_energy_cost * dt
        generator.consume_energy(deploy_cost)

        # 設定防御率に達していなければ回復
        if self.current_rate < self.set_rate:
            recover_amount = min(self.recovery_rate * dt, self.set_rate - self.current_rate)
            recover_cost = recover_amount * self.recovery_energy_cost
            if generator.consume_energy(recover_cost):
                self.current_rate += recover_amount
