"""BOTコマンダー: NPC艦艇の自律AIコマンダー。"""
from __future__ import annotations
from game.coords import Vec2, distance_grid, direction_to, wrap_vec
from game.crew.commander import Commander
from game.constants import BOT_RETREAT_DAMAGE_RATE
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.objects.vessel import Vessel
    from game.objects.thing import Thing
    from game.equipment.integrator import ObjectRecord


class BotCommander(Commander):
    def __init__(self, vessel: "Vessel") -> None:
        super().__init__(vessel)
        self.home: "Thing | None" = None

    def set_home(self, obj: "Thing") -> None:
        self.home = obj

    def tick(self) -> None:
        if not self.vessel.integrator or not self.vessel.radar:
            return

        # 大破時は補給地点へ退避
        if self.vessel.damage >= self.vessel.durability * BOT_RETREAT_DAMAGE_RATE:
            self._retreat()
            return

        # 最近傍の敵を探す
        enemy_record = self._nearest_enemy()
        if enemy_record is None:
            self._patrol()
            return

        dist = distance_grid(self.vessel.pos, enemy_record.pos)
        missile_range = self._missile_range()
        beam_range = self._beam_range()

        # 射程内なら攻撃、射程外なら接近
        if dist <= beam_range:
            self._attack_beam(enemy_record)
        elif dist <= missile_range:
            self._attack_missile(enemy_record)
        else:
            self._move_toward(enemy_record.pos)

    # --- private helpers ---

    def _enemy_faction(self) -> str:
        return "K" if self.vessel.faction == "U" else "U"

    def _nearest_enemy(self) -> "ObjectRecord | None":
        records = self.vessel.integrator.query(faction=self._enemy_faction())
        if not records:
            return None
        pos = self.vessel.pos
        return min(records, key=lambda r: distance_grid(pos, r.pos))

    def _find_target_object(self, record: "ObjectRecord") -> "Thing | None":
        """レーダー接触 or 宇宙オブジェクトから実体を取得する。"""
        target = self.vessel.radar.find_contact(record.id)
        if target:
            return target
        if self.vessel.universe:
            for obj in self.vessel.universe.objects:
                if obj.id == record.id:
                    return obj
        return None

    def _missile_range(self) -> float:
        ml = self.vessel.missile_launcher
        if ml is None:
            return 0.0
        return ml.missile_speed * ml.missile_flight_time

    def _beam_range(self) -> float:
        bl = self.vessel.beam_launcher
        return bl.beam_range if bl else 0.0

    def _move_toward(self, pos: Vec2) -> None:
        nav = self.vessel.bridge.navigator if self.vessel.bridge else None
        if nav:
            nav.set_destination(pos, speed=self.vessel.max_speed)

    def _attack_missile(self, record: "ObjectRecord") -> None:
        target = self._find_target_object(record)
        if target and not target.destroyed and self.vessel.bridge and self.vessel.bridge.gunner:
            self.vessel.bridge.gunner.attack_missile(target)

    def _attack_beam(self, record: "ObjectRecord") -> None:
        target = self._find_target_object(record)
        if target and not target.destroyed and self.vessel.bridge and self.vessel.bridge.gunner:
            self.vessel.bridge.gunner.attack_beam(target)

    def _retreat(self) -> None:
        supply = self._nearest_supply()
        if supply and self.vessel.bridge and self.vessel.bridge.navigator:
            self.vessel.bridge.navigator.set_destination(supply.pos, speed=self.vessel.max_speed)

    def _nearest_supply(self) -> "Thing | None":
        """最寄りの味方補給地点（基地または補給フラグ艦）を探す。"""
        if not self.vessel.universe:
            return None
        from game.objects.base_station import BaseStation
        candidates = [
            o for o in self.vessel.universe.objects
            if isinstance(o, BaseStation) and o.faction == self.vessel.faction
        ]
        if not candidates:
            return None
        pos = self.vessel.pos
        return min(candidates, key=lambda o: distance_grid(pos, o.pos))

    def _patrol(self) -> None:
        """敵不在時はホームから離れる方向に最大速度で索敵移動する。"""
        nav = self.vessel.bridge.navigator if self.vessel.bridge else None
        if not nav or not self.home:
            return
        away_dir = direction_to(self.home.pos, self.vessel.pos)
        if away_dir.length() == 0.0:
            return
        target = wrap_vec(Vec2(
            self.vessel.pos.x + away_dir.x * 2.0,
            self.vessel.pos.y + away_dir.y * 2.0,
        ))
        nav.set_destination(target, speed=self.vessel.max_speed)
