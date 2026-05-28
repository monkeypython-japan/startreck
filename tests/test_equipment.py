"""装備のユニットテスト。"""
import pytest
from game.coords import Vec2
from game.objects.thing import Thing
from game.objects.mover import Mover
from game.objects.star import Star
from game.equipment.generator import Generator
from game.equipment.shield import Shield
from game.equipment.integrator import Integrator
from game.equipment.radar import Radar


def make_owner(pos=None):
    return Thing(pos or Vec2(5.0, 5.0), size=1.0, durability=1000.0)


# --- Generator ---

def test_generator_produces_energy():
    owner = make_owner()
    gen = Generator(owner, capacitor_max=500.0, rate_max=10.0, fuel_max=1000.0)
    gen.capacitor = 0.0
    gen.update(1.0)  # 1秒で10gj生産
    assert gen.capacitor == pytest.approx(10.0)

def test_generator_does_not_exceed_max():
    owner = make_owner()
    gen = Generator(owner, capacitor_max=500.0, rate_max=10.0, fuel_max=1000.0)
    gen.capacitor = 498.0
    gen.update(1.0)
    assert gen.capacitor == pytest.approx(500.0)

def test_generator_fuel_consumed():
    owner = make_owner()
    gen = Generator(owner, capacitor_max=500.0, rate_max=10.0, fuel_max=1000.0)
    gen.capacitor = 0.0
    gen.update(1.0)
    assert gen.fuel == pytest.approx(990.0)  # 1:1変換

def test_generator_stops_at_no_fuel():
    owner = make_owner()
    gen = Generator(owner, capacitor_max=500.0, rate_max=10.0, fuel_max=5.0)
    gen.capacitor = 0.0
    gen.fuel = 3.0
    gen.update(1.0)
    assert gen.fuel == pytest.approx(0.0)
    assert gen.capacitor == pytest.approx(3.0)

def test_generator_request_energy():
    owner = make_owner()
    gen = Generator(owner, capacitor_max=500.0, rate_max=10.0, fuel_max=1000.0)
    gen.capacitor = 100.0
    provided = gen.request_energy(60.0)
    assert provided == pytest.approx(60.0)
    assert gen.capacitor == pytest.approx(40.0)

def test_generator_request_energy_insufficient():
    owner = make_owner()
    gen = Generator(owner, capacitor_max=500.0, rate_max=10.0, fuel_max=1000.0)
    gen.capacitor = 30.0
    provided = gen.request_energy(60.0)
    assert provided == pytest.approx(30.0)

def test_generator_consume_energy_fail():
    owner = make_owner()
    gen = Generator(owner, capacitor_max=500.0, rate_max=10.0, fuel_max=1000.0)
    gen.capacitor = 10.0
    assert not gen.consume_energy(20.0)
    assert gen.capacitor == pytest.approx(10.0)  # 消費されていない


# --- Shield ---

def test_shield_absorbs_damage():
    owner = make_owner()
    shield = Shield(owner, max_defense_energy=500.0, recovery_rate=1.0,
                    recovery_energy_cost=5.0, deploy_energy_cost=2.0)
    shield.set_defense_rate(100.0)
    remaining = shield.absorb(200.0)
    assert remaining == pytest.approx(0.0)

def test_shield_partial_defense():
    owner = make_owner()
    shield = Shield(owner, max_defense_energy=500.0, recovery_rate=1.0,
                    recovery_energy_cost=5.0, deploy_energy_cost=2.0)
    shield.set_defense_rate(50.0)  # 250gj まで吸収可能
    remaining = shield.absorb(300.0)
    assert remaining == pytest.approx(50.0)  # 300 - 250 = 50

def test_shield_rate_drops_after_hit():
    owner = make_owner()
    shield = Shield(owner, max_defense_energy=500.0, recovery_rate=1.0,
                    recovery_energy_cost=5.0, deploy_energy_cost=2.0)
    shield.set_defense_rate(100.0)
    shield.absorb(250.0)  # 250/500*100 = 50% 低下
    assert shield.current_rate == pytest.approx(50.0)

def test_shield_recovery():
    owner = make_owner()
    gen = Generator(owner, capacitor_max=10000.0, rate_max=100.0, fuel_max=100000.0)
    shield = Shield(owner, max_defense_energy=500.0, recovery_rate=10.0,
                    recovery_energy_cost=5.0, deploy_energy_cost=2.0)
    shield.set_defense_rate(100.0)
    shield.current_rate = 50.0
    shield.update(1.0, gen)
    assert shield.current_rate == pytest.approx(60.0)  # 10%/sec 回復

def test_shield_no_recovery_without_energy():
    owner = make_owner()
    gen = Generator(owner, capacitor_max=500.0, rate_max=10.0, fuel_max=1000.0)
    gen.capacitor = 0.0
    shield = Shield(owner, max_defense_energy=500.0, recovery_rate=10.0,
                    recovery_energy_cost=5.0, deploy_energy_cost=2.0)
    shield.set_defense_rate(100.0)
    shield.current_rate = 50.0
    shield.update(1.0, gen)
    assert shield.current_rate == pytest.approx(50.0)  # エネルギー不足で回復なし

def test_shield_deploy_cost():
    owner = make_owner()
    # capacitor_max=1000, reserve=100gj, capacitor=200 → available=100gj
    gen = Generator(owner, capacitor_max=1000.0, rate_max=100.0, fuel_max=100000.0)
    gen.capacitor = 200.0
    shield = Shield(owner, max_defense_energy=500.0, recovery_rate=1.0,
                    recovery_energy_cost=5.0, deploy_energy_cost=2.0)
    shield.set_defense_rate(50.0)
    shield.current_rate = 50.0
    shield.update(1.0, gen)
    # 展開コスト: 50% * 2 gj/%/sec * 1sec = 100 gj、available=100gj なので全額消費
    # キャパシタは reserve(100gj) まで下がる
    assert gen.capacitor == pytest.approx(100.0)


def test_shield_deploy_cost_respects_reserve():
    owner = make_owner()
    # capacitor がすでに reserve 以下の場合はシールドにエネルギーを供給しない
    gen = Generator(owner, capacitor_max=1000.0, rate_max=100.0, fuel_max=100000.0)
    gen.capacitor = 80.0  # reserve(100gj) 未満
    shield = Shield(owner, max_defense_energy=500.0, recovery_rate=1.0,
                    recovery_energy_cost=5.0, deploy_energy_cost=2.0)
    shield.set_defense_rate(50.0)
    shield.current_rate = 50.0
    shield.update(1.0, gen)
    # available=0 なのでキャパシタは変化しない
    assert gen.capacitor == pytest.approx(80.0)


# --- Integrator ---

def test_integrator_records_object():
    owner = make_owner()
    integrator = Integrator(owner)
    target = make_owner(Vec2(3.0, 3.0))
    integrator.record(target, game_time=5)
    record = integrator.get(target.id)
    assert record is not None
    assert record.pos == target.pos
    assert record.last_seen == 5

def test_integrator_query_by_faction():
    owner = make_owner()
    integrator = Integrator(owner)
    from game.objects.vessel import Vessel
    v_fed = Vessel(Vec2(1.0, 1.0), size=0.1, durability=500.0, max_speed=10.0, faction="U")
    v_kli = Vessel(Vec2(2.0, 2.0), size=0.1, durability=500.0, max_speed=10.0, faction="K")
    integrator.record(v_fed, 0)
    integrator.record(v_kli, 0)
    klingons = integrator.query(faction="K")
    assert len(klingons) == 1
    assert klingons[0].faction == "K"


# --- Radar ---

def test_radar_detects_nearby():
    owner = make_owner(Vec2(5.0, 5.0))
    integrator = Integrator(owner)
    radar = Radar(owner, scan_range=500.0, integrator=integrator)
    near = Thing(Vec2(5.1, 5.0), size=1.0, durability=100.0)   # 100 grid 離れている
    far = Thing(Vec2(6.0, 5.0), size=1.0, durability=100.0)    # 1000 grid 離れている
    radar.scan([near, far], game_time=0)
    assert near in radar.contacts
    assert far not in radar.contacts

def test_radar_records_to_integrator():
    owner = make_owner(Vec2(5.0, 5.0))
    integrator = Integrator(owner)
    radar = Radar(owner, scan_range=500.0, integrator=integrator)
    target = Thing(Vec2(5.1, 5.0), size=1.0, durability=100.0)
    radar.scan([target], game_time=3)
    assert integrator.get(target.id) is not None
