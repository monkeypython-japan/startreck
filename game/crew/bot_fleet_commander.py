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

    def accept_join_request(self, vessel: "Vessel") -> bool:
        """編入リクエストを受け取り、即座に承認して艦隊に加える。"""
        self.add_fleet_member(vessel)
        return True

    def update_fleet_target(self) -> None:
        """インテグレータの最新情報をもとに艦隊全体の攻撃目標を即時更新する。
        インテグレータ更新直後（敵基地新規発見時など）に呼ばれる。"""
        base_record = self._nearest_enemy_base_record()
        target_base_id = base_record.id if base_record else None
        self.set_attack_target(target_base_id)
        for member in self._fleet:
            if not member.destroyed and member.bridge and member.bridge.commander:
                member.bridge.commander.set_attack_target(target_base_id)

    def tick(self) -> None:
        self.update_fleet_target()
        super().tick()
