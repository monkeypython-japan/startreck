"""ガンナー: 武装操作とシールド自動展開を担当。"""
from __future__ import annotations
from game.coords import direction_to
from game.crew.bridge_crew import BridgeCrew
from game.constants import SHIELD_AUTO_BEAM_RATE, SHIELD_AUTO_MISSILE_RATE
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.objects.vessel import Vessel
    from game.objects.thing import Thing


class Gunner(BridgeCrew):
    def __init__(self, vessel: "Vessel") -> None:
        super().__init__(vessel)
        self._attack_queue: list[tuple["Thing", str]] = []  # (target, "missile"|"beam")
        self._manual_shield_rate: float = 0.0  # プレーヤーが手動で設定したシールド率

    def set_manual_shield_rate(self, rate: float) -> None:
        """プレーヤーが手動でシールド率を設定する。auto_shieldの戻り先として使われる。"""
        self._manual_shield_rate = max(0.0, min(rate, 100.0))
        if self.vessel.shield:
            self.vessel.shield.set_defense_rate(self._manual_shield_rate)

    def attack_missile(self, target: "Thing") -> None:
        self._attack_queue.append((target, "missile"))

    def attack_beam(self, target: "Thing") -> None:
        self._attack_queue.append((target, "beam"))

    def report_hit(self, hull_dmg: float, absorbed: float) -> None:
        """被弾をメッセージとして報告する。"""
        if absorbed > 0:
            self.vessel._report(
                f"被弾: シールド{absorbed:.0f}gj吸収 / 艦体{hull_dmg:.0f}gj ダメージ"
            )
        else:
            self.vessel._report(f"被弾: 艦体に {hull_dmg:.0f}gj ダメージ")

    def update(self, dt: float) -> None:
        self._auto_shield()
        self._process_attacks()

    def _auto_shield(self) -> None:
        """敵ビーム接近→50%, 自艦を狙うミサイル→100% で自動展開。"""
        if not self.vessel.radar or not self.vessel.shield:
            return
        from game.objects.beam import Beam
        from game.objects.missile import Missile
        enemy_iff = "K" if self.vessel.faction == "U" else "U"
        missile_threat = False
        beam_threat = False
        for c in self.vessel.radar.contacts:
            if isinstance(c, Beam) and c.iff == enemy_iff:
                beam_threat = True
            elif isinstance(c, Missile) and c.iff == enemy_iff:
                to_us = direction_to(c.pos, self.vessel.pos)
                if c.heading.x * to_us.x + c.heading.y * to_us.y > 0.5:
                    missile_threat = True
        if missile_threat:
            self.vessel.shield.set_defense_rate(SHIELD_AUTO_MISSILE_RATE)
        elif beam_threat:
            self.vessel.shield.set_defense_rate(SHIELD_AUTO_BEAM_RATE)
        else:
            # 脅威消滅時はプレーヤーの手動設定値に戻す（未設定なら0%）
            self.vessel.shield.set_defense_rate(self._manual_shield_rate)

    def _process_attacks(self) -> None:
        if not self._attack_queue:
            return
        target, weapon = self._attack_queue[0]
        if target.destroyed:
            self._attack_queue.pop(0)
            return
        uni = self.vessel.universe
        if weapon == "missile" and self.vessel.missile_launcher:
            m = self.vessel.missile_launcher.fire(target, self.vessel.radar)
            if m and uni:
                uni.add(m)
            self._attack_queue.pop(0)
        elif weapon == "beam" and self.vessel.beam_launcher and self.vessel.generator:
            b = self.vessel.beam_launcher.fire(target.pos, self.vessel.generator)
            if b and uni:
                uni.add(b)
            self._attack_queue.pop(0)
