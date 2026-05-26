"""BOTガードコマンダー: ホーム拠点防衛に特化した自律AIコマンダー。"""
from __future__ import annotations
import math
from game.coords import Vec2, GRID, distance_grid, direction_to, wrap_vec
from game.crew.bot_commander import BotCommander
from game.constants import (
    SUPPLY_RANGE, BOT_EVADE_DAMAGE_RATE,
    GUARD_HOME_MIN, GUARD_HOME_MAX, GUARD_THREAT_RANGE,
    GUARD_SUPPLY_DAMAGE_RATE, GUARD_SUPPLY_FUEL_RATE, GUARD_SUPPLY_MISSILE_RATE,
)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.objects.vessel import Vessel
    from game.objects.thing import Thing
    from game.equipment.integrator import ObjectRecord


class BotGuardCommander(BotCommander):
    """ホーム（基地または旗艦）周辺 200〜1000 grid を守るガードコマンダー。"""

    def tick(self) -> None:
        if not self.vessel.integrator or not self.vessel.radar:
            return

        if self.home is not None and self.home.destroyed:
            self._reassign_home()

        if not self._under_attack():
            if self.vessel.bridge and self.vessel.bridge.gunner:
                self.vessel.bridge.gunner.set_manual_shield_rate(0.0)

        # 積極的補給: 親クラスより低い閾値で補給へ向かう
        if self._needs_supply():
            self._go_supply()
            return

        # 中破以上は回避行動（親と同じ閾値）
        nav = self.vessel.bridge.navigator if self.vessel.bridge else None
        if self.vessel.damage >= self.vessel.durability * BOT_EVADE_DAMAGE_RATE:
            if nav and not nav._flee_evading:
                nav.start_flee_evasion()
            return
        if nav and nav._flee_evading:
            nav.end_flee_evasion()

        target = self._select_guard_target()
        if target is None:
            self._guard_position()
            return

        dist = distance_grid(self.vessel.pos, target.pos)
        # 射程外かつ目標がホームから遠すぎる場合は追尾しない
        if (dist > self._missile_range()
                and self.home
                and distance_grid(target.pos, self.home.pos) > GUARD_HOME_MAX * 1.3):
            self._guard_position()
            return

        if dist <= self._missile_range():
            self._attack_missile(target)
        elif dist <= self._beam_range():
            self._attack_beam(target)
        else:
            if nav:
                nav.set_destination(target.pos, speed=self.vessel.max_speed)

    # ── 補給 ──────────────────────────────────────────────────────

    def _needs_supply(self) -> bool:
        if self.home is None or self.home.destroyed:
            return False
        v = self.vessel
        if v.damage >= v.durability * GUARD_SUPPLY_DAMAGE_RATE:
            return True
        if v.generator and v.generator.fuel / v.generator.fuel_max < GUARD_SUPPLY_FUEL_RATE:
            return True
        if (v.missile_launcher
                and v.missile_launcher.stock / v.missile_launcher.capacity < GUARD_SUPPLY_MISSILE_RATE):
            return True
        return False

    def _go_supply(self) -> None:
        """ホームへ移動して補給を受ける。"""
        supply = self.home if (self.home and not self.home.destroyed) else self._nearest_supply()
        if supply is None:
            return
        if distance_grid(self.vessel.pos, supply.pos) <= SUPPLY_RANGE:
            self.vessel.supply_full()
        elif self.vessel.bridge and self.vessel.bridge.navigator:
            self.vessel.bridge.navigator.set_destination(supply.pos, speed=self.vessel.max_speed)

    # ── 攻撃目標選択 ─────────────────────────────────────────────

    def _select_guard_target(self) -> "ObjectRecord | None":
        """ガード専用優先順位: ホーム攻撃者 → 自艦攻撃者 → ホーム接近中の敵 → 最近傍敵基地"""
        if not self.vessel.integrator:
            return None
        enemy_f = self._enemy_faction()
        records = [r for r in self.vessel.integrator.query(faction=enemy_f)
                   if r.obj_type != "BaseStation"]

        # 1. ホームへの攻撃者（ホーム周辺で敵の武器が向かっている艦）
        home_attacker = self._find_home_attacker(records)
        if home_attacker:
            return home_attacker

        # 2. 自艦への攻撃者
        if self._attacker_id:
            r = self._find_record_by_id(self._attacker_id)
            if r and r.faction == enemy_f:
                return r
            self._attacker_id = None

        # 3. ホーム近傍でホームに接近中の敵（最もホームから遠いものを優先）
        approaching = self._find_approaching_enemy(records)
        if approaching:
            return approaching

        # 4. 最近傍の敵基地
        return self._nearest_enemy_base_record()

    def _find_home_attacker(self, records: list["ObjectRecord"]) -> "ObjectRecord | None":
        """ホームへ向かう敵兵器の発射元（= ホームへの攻撃者）を返す。"""
        if not self.home or not self.vessel.radar:
            return None
        home_pos = self.home.pos
        from game.objects.missile import Missile
        from game.objects.beam import Beam
        enemy_iff = self._enemy_faction()
        attacker_ids: set[str] = set()
        for contact in self.vessel.radar.contacts:
            if isinstance(contact, (Missile, Beam)) and contact.iff == enemy_iff:
                dir_to_home = direction_to(contact.pos, home_pos)
                dot = contact.heading.x * dir_to_home.x + contact.heading.y * dir_to_home.y
                if dot > 0.5:
                    if isinstance(contact, Missile) and contact.source_id:
                        attacker_ids.add(contact.source_id)
                    elif isinstance(contact, Beam) and contact.owner:
                        attacker_ids.add(contact.owner.id)
        for r in records:
            if r.id in attacker_ids:
                return r
        return None

    def _find_approaching_enemy(self, records: list["ObjectRecord"]) -> "ObjectRecord | None":
        """ホームから GUARD_THREAT_RANGE 以内でホームに接近中の敵を返す（最遠優先）。"""
        if not self.home:
            return None
        home_pos = self.home.pos
        candidates: list[tuple[float, "ObjectRecord"]] = []
        for r in records:
            d_home = distance_grid(r.pos, home_pos)
            if d_home > GUARD_THREAT_RANGE:
                continue
            dir_to_home = direction_to(r.pos, home_pos)
            dot = r.heading.x * dir_to_home.x + r.heading.y * dir_to_home.y
            if dot > 0.3:
                candidates.append((d_home, r))
        if not candidates:
            return None
        # ホームから最も遠い脅威を先に排除（ホームから離れた位置で撃破）
        return max(candidates, key=lambda x: x[0])[1]

    # ── ポジション管理 ────────────────────────────────────────────

    def _guard_position(self) -> None:
        """ホーム周辺 200〜1000 grid のゾーンに位置取りする。"""
        if not self.home or not self.vessel.bridge:
            return
        nav = self.vessel.bridge.navigator
        if not nav:
            return
        home_pos = self.home.pos
        dist = distance_grid(self.vessel.pos, home_pos)
        mid_dist = (GUARD_HOME_MIN + GUARD_HOME_MAX) / 2  # 600 grid
        if dist < GUARD_HOME_MIN or dist > GUARD_HOME_MAX:
            # 適切な距離（中間点）に移動
            away = direction_to(home_pos, self.vessel.pos)
            if away.length() < 0.001:
                # ホームと重なっている場合は任意方向に移動
                away = Vec2(1.0, 0.0)
            target = wrap_vec(Vec2(
                home_pos.x + away.x * mid_dist * GRID,
                home_pos.y + away.y * mid_dist * GRID,
            ))
            nav.set_destination(target, speed=self.vessel.max_speed)

    # ── ホーム再割り当て ──────────────────────────────────────────

    def _reassign_home(self) -> None:
        """ホームが破壊されたとき、最近傍の基地または旗艦を新たなホームに設定する。"""
        if not self.vessel.universe:
            self.home = None
            return
        from game.objects.base_station import BaseStation
        from game.objects.vessel import Vessel
        from game.crew.bot_fleet_commander import BotFleetCommander
        faction = self.vessel.faction
        pos = self.vessel.pos
        candidates: list["Thing"] = []
        for obj in self.vessel.universe.objects:
            if isinstance(obj, BaseStation) and obj.faction == faction:
                candidates.append(obj)
            elif (isinstance(obj, Vessel) and obj is not self.vessel
                  and obj.faction == faction and obj.bridge
                  and isinstance(obj.bridge.commander, BotFleetCommander)):
                candidates.append(obj)
        self.home = min(candidates, key=lambda o: distance_grid(pos, o.pos)) if candidates else None
