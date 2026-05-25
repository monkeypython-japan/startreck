"""BOTフリートコマンダー: 艦隊旗艦の自律AIコマンダー。傘下駆逐艦への攻撃目標割り当てを担う。"""
from __future__ import annotations
from game.crew.bot_commander import BotCommander
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.objects.vessel import Vessel


class BotFleetCommander(BotCommander):
    def __init__(self, vessel: "Vessel") -> None:
        super().__init__(vessel)
        self._fleet: list["Vessel"] = []

    def add_fleet_member(self, vessel: "Vessel") -> None:
        self._fleet.append(vessel)

    def tick(self) -> None:
        # 最近傍の敵基地を毎ティック算出し、艦隊全体（自身含む）に割り当て
        base_record = self._nearest_enemy_base_record()
        target_base_id = base_record.id if base_record else None
        self.set_attack_target(target_base_id)
        for member in self._fleet:
            if not member.destroyed and member.bridge and member.bridge.commander:
                member.bridge.commander.set_attack_target(target_base_id)
        super().tick()
