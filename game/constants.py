"""仕様書に定義された全数値定数。"""

# --- 艦種パラメータ ---

HEAVY_CRUISER = dict(
    max_speed=5,          # grid/sec
    size=0.3,             # grid
    durability=2000,      # gj
    missile_capacity=150,
    capacitor_max=2000,   # gj
    generator_rate_max=20,  # gj/sec
    fuel_max=22500,       # gj  (+50%)
    radar_range=1000,     # grid
    supply_provider=True,
)

DESTROYER = dict(
    max_speed=10,
    size=0.1,
    durability=500,
    missile_capacity=20,
    capacitor_max=500,
    generator_rate_max=10,
    fuel_max=1500,
    radar_range=750,
    supply_provider=False,
)

SPECIAL_SHIP = dict(
    max_speed=20,
    size=0.15,
    durability=2000,
    missile_capacity=50,
    capacitor_max=2000,
    generator_rate_max=30,
    fuel_max=7500,
    radar_range=1500,
    supply_provider=False,
    has_jump_drive=True,
)

# --- 兵装（標準艦） ---

MISSILE_STANDARD = dict(
    power=500,        # gj
    speed=100,        # grid/sec
    flight_time=5,    # sec
)

BEAM_STANDARD = dict(
    power=250,        # gj
    speed=300,        # grid/sec
    range=750,        # grid
)

SHIELD_STANDARD = dict(
    max_defense_energy=250,    # gj
    recovery_rate=0.5,         # %/sec
    recovery_energy_cost=0.25,  # gj/%
    deploy_energy_cost=0.25,   # gj/%/sec
)

# --- 兵装（特務艦） ---

MISSILE_SPECIAL = dict(
    power=500,
    speed=150,
    flight_time=7.5,
)

BEAM_SPECIAL = dict(
    power=250,
    speed=300,
    range=1500,
)

SHIELD_SPECIAL = dict(
    max_defense_energy=375,
    recovery_rate=1.0,
    recovery_energy_cost=0.25,
    deploy_energy_cost=1.0,
)

# --- ビームダメージ範囲 ---
BEAM_FULL_DAMAGE_RANGE = 10    # grid  先端から10 grid以内: 100%
BEAM_PARTIAL_DAMAGE_RANGE = 20  # grid  10〜20 grid: 25%
BEAM_PARTIAL_DAMAGE_RATE = 0.25

# --- ビーム発射コスト ---
BEAM_ENERGY_COST_RATE = 1.10  # ビーム威力の110%

# --- ビーム連射 ---
BEAM_RELOAD_TIME = 1.0        # sec  標準艦の発射間隔。特務艦は 0.0（制限なし）

# --- メッセージ ---
REPORT_ALERT = "\x00"  # このプレフィックスを付けると赤字で表示される

# --- 移動コスト ---
MOVE_ENERGY_PER_SPEED = 1.0  # gj per grid/sec の速度変化

# --- 武装制限 ---
MISSILE_RELOAD_TIME = 5.0     # sec  ミサイル装填時間（特務艦は適用外）

# --- 補給 ---
SUPPLY_RANGE = 150            # grid
SUPPLY_TIME = 60              # sec
SUPPLY_MIN_STOCK_RATE = 0.20  # 在庫20%以下になる補給はしない

# --- ジャンプドライブ ---
JUMP_ENERGY_RATE = 0.50       # キャパシタ容量の50%を消費
JUMP_LANDING_RADIUS = 150     # grid  目標基地からの着地半径

# --- シールド自動展開（ガンナー） ---
SHIELD_AUTO_BEAM_RATE = 50    # %  ビーム検知時
SHIELD_AUTO_MISSILE_RATE = 100  # %  ミサイル検知時
SHIELD_AUTO_THREAT_RANGE = 300  # grid  シールド自動展開の脅威検知距離
SHIELD_CAPACITOR_RESERVE_RATE = 0.10  # キャパシタ容量のこの割合を常に確保する
GUNNER_INTERCEPT_RANGE = 500  # grid  ビーム迎撃を試みる敵ミサイルの最大距離

# --- BOT AI ---
BOT_EVADE_DAMAGE_RATE    = 0.70  # 蓄積ダメージが耐久性の70%以上で回避行動
BOT_RETREAT_DAMAGE_RATE  = 0.80  # 蓄積ダメージが耐久性の80%以上で補給退避
BOT_SUPPLY_FUEL_RATE     = 0.20  # 燃料残量がこの率以下で補給退避
BOT_SUPPLY_MISSILE_RATE  = 0.10  # ミサイル残量がこの率以下で補給退避
BOT_HOME_ORBIT_RADIUS = 150     # grid

# --- 初期配置 ---
STAR_COUNT_MIN = 10
STAR_COUNT_MAX = 15
FLEET_COUNT = 5               # 艦隊数 (両軍共通)
FLEET_SIZE = 10               # 駆逐艦数 per 艦隊 (旗艦1隻 + 駆逐艦10隻)
BASE_COUNT = 3                # 基地数 (両軍共通)
FLEET_ORBIT_RADIUS = 150      # grid  旗艦・基地からの初期配置半径
GUARD_PER_BASE = 10           # 護衛型巡洋艦 per 基地
GUARD_PER_FLAGSHIP = 5        # 護衛型巡洋艦 per 旗艦

# --- 護衛型巡洋艦 (BotGuardCommander) ---
GUARD_HOME_MIN = 200          # grid  ホームからの最小距離
GUARD_HOME_MAX = 1000         # grid  ホームからの最大距離
GUARD_THREAT_RANGE = 600      # grid  ホーム周辺の脅威検出範囲
GUARD_SUPPLY_DAMAGE_RATE = 0.35   # ダメージがこれ以上で補給
GUARD_SUPPLY_FUEL_RATE   = 0.30   # 燃料比率がこれ以下で補給
GUARD_SUPPLY_MISSILE_RATE = 0.30  # ミサイル比率がこれ以下で補給

# --- 恒星 ---
STAR_SIZE = 5  # grid
STAR_DURABILITY = float("inf")

# --- 基地 ---
BASE_DURABILITY = 20000  # gj
BASE_SIZE = 1            # grid
BASE_RADAR_RANGE = 1000  # grid
