"""BOTコマンダー: NPC艦艇の自律AIコマンダー。"""
from __future__ import annotations
from game.coords import Vec2, distance_grid, direction_to, wrap_vec
from game.crew.commander import Commander
from game.constants import BOT_EVADE_DAMAGE_RATE, BOT_RETREAT_DAMAGE_RATE, BOT_SUPPLY_FUEL_RATE, BOT_SUPPLY_MISSILE_RATE
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.objects.vessel import Vessel
    from game.objects.thing import Thing
    from game.equipment.integrator import ObjectRecord


class BotCommander(Commander):
    def __init__(self, vessel: "Vessel") -> None:
        super().__init__(vessel)
        self.home: "Thing | None" = None
        self._attacker_id: str | None = None
        self._assigned_base_id: str | None = None

    def set_home(self, obj: "Thing") -> None:
        self.home = obj

    def tick(self) -> None:
        if not self.vessel.integrator or not self.vessel.radar:
            return

        # ホームが破壊されていれば生き残ったホームに再割り当て
        if self.home is not None and self.home.destroyed:
            self._reassign_home()

        # 自艦への攻撃がない場合はシールドを0に設定する
        if not self._under_attack():
            if self.vessel.bridge and self.vessel.bridge.gunner:
                self.vessel.bridge.gunner.set_manual_shield_rate(0.0)

        # 補給条件（HP低下・燃料不足・ミサイル不足）を満たす場合はホームへ退避
        if self._needs_supply():
            self._retreat()
            return

        # 中破時は回避行動
        nav = self.vessel.bridge.navigator if self.vessel.bridge else None
        if self.vessel.damage >= self.vessel.durability * BOT_EVADE_DAMAGE_RATE:
            if nav and not nav._flee_evading:
                nav.start_flee_evasion()
            if nav and nav._flee_evading:
                return
            # レーダー範囲内に敵がなく逃避が即終了した場合は補給退避へ
            self._retreat()
            return

        # 回避行動中だが閾値を下回った場合（補給後）は回避を解除
        if nav and nav._flee_evading:
            nav.end_flee_evasion()

        # 攻撃目標の選択（優先: 攻撃者 → 割り当て基地 → 近傍敵基地 → 近傍敵艦）
        enemy_record = self._select_attack_target()
        if enemy_record is None:
            self._patrol()
            return

        dist = distance_grid(self.vessel.pos, enemy_record.pos)
        missile_range = self._missile_range()
        beam_range = self._beam_range()

        # ミサイル射程内 → ミサイル、ビーム射程内 → ビーム、射程外 → 接近
        if dist <= missile_range:
            self._attack_missile(enemy_record)
        elif dist <= beam_range:
            self._attack_beam(enemy_record)
        else:
            self._move_toward(enemy_record.pos)

    def on_attacked_by(self, attacker_id: str) -> None:
        """被弾時に攻撃者IDを記憶する。"""
        self._attacker_id = attacker_id

    def set_attack_target(self, base_id: str | None) -> None:
        """フリートコマンダーから割り当てられた攻撃目標基地IDを設定する。"""
        self._assigned_base_id = base_id

    # --- private helpers ---

    def _enemy_faction(self) -> str:
        return "K" if self.vessel.faction == "U" else "U"

    def _find_record_by_id(self, obj_id: str) -> "ObjectRecord | None":
        if not self.vessel.integrator:
            return None
        return self.vessel.integrator.get(obj_id)

    def _nearest_enemy_vessel(self) -> "ObjectRecord | None":
        """最近傍の敵艦（BaseStation除く）を返す。"""
        if not self.vessel.integrator:
            return None
        records = [
            r for r in self.vessel.integrator.query(faction=self._enemy_faction())
            if r.obj_type != "BaseStation"
        ]
        if not records:
            return None
        pos = self.vessel.pos
        return min(records, key=lambda r: distance_grid(pos, r.pos))

    def _nearest_enemy_base_record(self) -> "ObjectRecord | None":
        """最近傍の敵基地レコードを返す。"""
        if not self.vessel.integrator:
            return None
        records = [
            r for r in self.vessel.integrator.query(faction=self._enemy_faction())
            if r.obj_type == "BaseStation"
        ]
        if not records:
            return None
        pos = self.vessel.pos
        return min(records, key=lambda r: distance_grid(pos, r.pos))

    def _select_attack_target(self) -> "ObjectRecord | None":
        """攻撃優先順位: 攻撃者 → 割り当て基地 → 近傍敵基地 → 近傍敵艦"""
        # 1. 攻撃者への反撃
        if self._attacker_id:
            r = self._find_record_by_id(self._attacker_id)
            if r and r.faction == self._enemy_faction():
                return r
            self._attacker_id = None
        # 2. 割り当て敵基地
        if self._assigned_base_id:
            r = self._find_record_by_id(self._assigned_base_id)
            if r:
                return r
            self._assigned_base_id = None
        # 3. 最近傍の敵基地
        base_r = self._nearest_enemy_base_record()
        if base_r:
            return base_r
        # 4. 最近傍の敵艦
        return self._nearest_enemy_vessel()

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

    def _needs_supply(self) -> bool:
        """HP・燃料・ミサイルのいずれかが補給閾値以下なら True。"""
        v = self.vessel
        if v.damage >= v.durability * BOT_RETREAT_DAMAGE_RATE:
            return True
        if v.generator and v.generator.fuel / v.generator.fuel_max < BOT_SUPPLY_FUEL_RATE:
            return True
        if (v.missile_launcher and v.missile_launcher.capacity > 0
                and v.missile_launcher.stock / v.missile_launcher.capacity < BOT_SUPPLY_MISSILE_RATE):
            return True
        return False

    def _retreat(self) -> None:
        supply = (self.home if (self.home and not self.home.destroyed)
                  else self._nearest_supply())
        if supply is None:
            return
        from game.constants import SUPPLY_RANGE
        if distance_grid(self.vessel.pos, supply.pos) <= SUPPLY_RANGE:
            self.vessel.supply_full()
            self._patrol()
        elif self.vessel.bridge and self.vessel.bridge.navigator:
            self.vessel.bridge.navigator.set_destination(supply.pos, speed=self.vessel.max_speed)

    def _nearest_supply(self) -> "Thing | None":
        """最寄りの味方補給地点（基地または補給フラグ艦）を探す。"""
        if not self.vessel.universe:
            return None
        from game.objects.base_station import BaseStation
        from game.objects.vessel import Vessel
        candidates = [
            o for o in self.vessel.universe.objects
            if (isinstance(o, BaseStation) and o.faction == self.vessel.faction)
            or (isinstance(o, Vessel) and o is not self.vessel
                and o.faction == self.vessel.faction and o.supply_provider)
        ]
        if not candidates:
            return None
        pos = self.vessel.pos
        return min(candidates, key=lambda o: distance_grid(pos, o.pos))

    def _under_attack(self) -> bool:
        """自艦に向かう敵武器がレーダー範囲内にあるか確認する。"""
        if not self.vessel.radar:
            return False
        from game.objects.beam import Beam
        from game.objects.missile import Missile
        from game.coords import direction_to
        enemy_iff = "K" if self.vessel.faction == "U" else "U"
        for c in self.vessel.radar.contacts:
            if isinstance(c, Beam) and c.iff == enemy_iff:
                return True
            if isinstance(c, Missile) and c.iff == enemy_iff:
                to_us = direction_to(c.pos, self.vessel.pos)
                if c.heading.x * to_us.x + c.heading.y * to_us.y > 0.5:
                    return True
        return False

    def _reassign_home(self) -> None:
        """ホームが破壊されたとき、生き残った同勢力の適切なホームに再割り当てする。"""
        if not self.vessel.universe:
            self.home = None
            return
        from game.objects.base_station import BaseStation
        faction = self.vessel.faction
        pos = self.vessel.pos
        if isinstance(self.home, BaseStation):
            # 旗艦の場合: 最近傍の味方基地に再割り当て
            candidates = [o for o in self.vessel.universe.objects
                          if isinstance(o, BaseStation) and o.faction == faction]
            self.home = min(candidates, key=lambda o: distance_grid(pos, o.pos)) if candidates else None
        else:
            # 駆逐艦の場合: 最近傍の味方旗艦の BotFleetCommander に編入リクエストを送る
            from game.crew.bot_fleet_commander import BotFleetCommander
            from game.objects.vessel import Vessel
            candidates = [
                o for o in self.vessel.universe.objects
                if isinstance(o, Vessel) and o is not self.vessel
                and o.faction == faction
                and o.bridge and isinstance(o.bridge.commander, BotFleetCommander)
            ]
            if candidates:
                nearest = min(candidates, key=lambda o: distance_grid(pos, o.pos))
                fleet_cmd = nearest.bridge.commander
                if fleet_cmd.accept_join_request(self.vessel):
                    self.home = nearest
            else:
                self.home = None

    def on_flee_evasion_ended(self) -> None:
        """ナビゲーターからの回避行動終了通知。次の tick() で通常行動に戻る。"""
        pass

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
