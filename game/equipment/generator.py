"""ジェネレータ: 燃料からエネルギーを生産してキャパシタに蓄積する。"""
from __future__ import annotations
from game.equipment.equipment import Equipment
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.objects.thing import Thing


class Generator(Equipment):
    def __init__(
        self,
        owner: "Thing",
        capacitor_max: float,
        rate_max: float,
        fuel_max: float,
    ) -> None:
        super().__init__(owner)
        self.capacitor_max: float = capacitor_max    # gj
        self.capacitor: float = capacitor_max        # キャパシタ現在量 (gj)
        self.rate_max: float = rate_max              # 最大発生率 (gj/sec)
        self.rate: float = rate_max                  # 現在の発生率 (gj/sec)
        self.fuel_max: float = fuel_max              # gj
        self.fuel: float = fuel_max                  # 現在燃料量 (gj)
        self.fuel_consumed: float = 0.0              # 累計燃料消費量（ログ用）

    def update(self, dt: float) -> None:
        """燃料を消費してキャパシタを充填する。燃料1gj→エネルギー1gj。"""
        if self.fuel <= 0.0 or self.capacitor >= self.capacitor_max:
            return
        produced = min(self.rate * dt, self.fuel, self.capacitor_max - self.capacitor)
        self.fuel -= produced
        self.fuel_consumed += produced
        self.capacitor += produced

    def request_energy(self, amount: float) -> float:
        """エネルギーをキャパシタから提供する。実際に提供できた量を返す。"""
        provided = min(amount, self.capacitor)
        self.capacitor -= provided
        return provided

    def consume_energy(self, amount: float) -> bool:
        """エネルギーを消費する。不足時は False を返す（消費はしない）。"""
        if self.capacitor < amount:
            return False
        self.capacitor -= amount
        return True

    def set_rate(self, rate: float) -> None:
        self.rate = max(0.0, min(rate, self.rate_max))

    def refuel(self) -> None:
        self.fuel = self.fuel_max

    def recharge(self) -> None:
        self.capacitor = self.capacitor_max
