# Startreck 実装計画

## 概要

BASICで書かれた往年のテキストゲーム「Star Trek」をPythonによるリアルタイムGUIゲームとして実装するプロジェクト。仕様書 `startreck-sprec.md`（レビュー10回を経て完成）に基づき、5フェーズに分けて実装を進めた。

---

## 技術スタック

| 項目 | 内容 |
|------|------|
| 言語 | Python 3.12 |
| 依存管理 | uv |
| GUI | pygame 2.6.1 |
| テスト | pytest |
| VCS | Git（フェーズごとにブランチを分けて実装） |

---

## ディレクトリ構成

```
startreck/
├── pyproject.toml
├── main.py                        # エントリポイント
├── game/
│   ├── constants.py               # 仕様書の全数値定数
│   ├── coords.py                  # 座標系ユーティリティ
│   ├── universe.py                # 宇宙クラス・ゲームループ管理
│   ├── initializer.py             # 初期配置ロジック
│   ├── objects/
│   │   ├── thing.py               # 物体（基底）
│   │   ├── mover.py               # 移動体
│   │   ├── vessel.py              # 艦艇
│   │   ├── missile.py             # ミサイル
│   │   ├── beam.py                # ビーム
│   │   ├── star.py                # 恒星
│   │   └── base_station.py        # 基地
│   ├── equipment/
│   │   ├── equipment.py           # 装備基底
│   │   ├── generator.py           # ジェネレータ
│   │   ├── shield.py              # シールド
│   │   ├── radar.py               # レーダー
│   │   ├── integrator.py          # インテグレータ（全天マップ）
│   │   ├── bridge.py              # ブリッジ
│   │   ├── missile_launcher.py    # ミサイルランチャー
│   │   ├── beam_launcher.py       # ビーム発射機
│   │   ├── missile_nav.py         # ミサイルナビゲーション
│   │   └── jump_drive.py          # ジャンプドライブ
│   ├── crew/
│   │   ├── bridge_crew.py         # ブリッジ要員基底
│   │   ├── navigator.py           # ナビゲーター
│   │   ├── gunner.py              # ガンナー
│   │   ├── commander.py           # コマンダー基底
│   │   ├── bot_commander.py       # BOTコマンダー（NPC用）
│   │   └── player.py              # プレーヤー（人間操作）
│   ├── vessels/
│   │   ├── heavy_cruiser.py       # 重巡洋艦（クリンゴン旗艦）
│   │   ├── destroyer.py           # 駆逐艦（連邦・クリンゴン共通）
│   │   └── special_ship.py        # 特務艦 U.S.S. YUKIKAZE
│   └── ui/
│       ├── font_util.py           # 日本語対応フォントユーティリティ
│       ├── game_ui.py             # メインUI統合管理
│       ├── map_view.py            # 宇宙マップ描画（800×800、1:1）
│       ├── message_window.py      # クルーログ（スクロール対応）
│       ├── status_panel.py        # 自艦ステータスパネル
│       └── popup_menu.py          # コンテキストポップアップメニュー
└── tests/
    ├── test_coords.py
    ├── test_equipment.py
    ├── test_objects.py
    ├── test_vessels.py
    ├── test_weapons.py
    └── test_init.py               # 69テスト、全通過
```

---

## オブジェクト継承・構成関係

```
物体 (Thing)
├── 恒星 (Star)          — 不破壊、静止
├── 基地 (BaseStation)   — 静止、補給機能
└── 移動体 (Mover)
    ├── 艦艇 (Vessel)    — 装備を構成として保持
    │   ├── 重巡洋艦 (HeavyCruiser)   クリンゴン旗艦
    │   ├── 駆逐艦 (Destroyer)        連邦・クリンゴン共通
    │   └── 特務艦 (SpecialShip)      プレーヤー機、ジャンプドライブ搭載
    ├── ミサイル (Missile)
    └── ビーム (Beam)

装備（Vessel に構成として保持、継承ではない）
├── Generator        燃料→エネルギー変換、キャパシタ管理
├── Shield           被弾吸収・回復・エネルギー消費
├── Radar            探知範囲内オブジェクトをスキャン
├── Integrator       各艦独立の全天マップ（僚艦と共有しない）
├── Bridge           要員ホルダー
├── MissileLauncher  ミサイル発射・在庫管理
├── BeamLauncher     ビーム発射・エネルギー消費
└── JumpDrive        特務艦専用、連邦基地への瞬時移動

ブリッジ要員（装備ではない）
├── Navigator    移動目標への航行・回避機動
├── Gunner       攻撃キュー管理・シールド自動展開
└── Commander
    ├── BotCommander   NPC艦艇用 AI（1秒ティック）
    └── Player         プレーヤー操作（UI イベント経由）
```

---

## 座標系・物理モデル

| 項目 | 仕様 |
|------|------|
| 座標空間 | 0〜10 × 0〜10、閉じた系（端を超えると反対側へ） |
| グリッド単位 | 1 grid = 0.001 座標単位 |
| エネルギー単位 | gj（ギガジュール）。移動・武装・シールド・燃料すべて同単位 |
| 移動コスト | 速度変化量 (grid/sec) × 1 gj、慣性なし |
| ジェネレータ | 燃料 1gj → エネルギー 1gj（1:1変換） |
| シールド | 被弾後に `吸収量 / 最大防御エネルギー × 100%` だけ現在防御率が低下 |
| ビームダメージ | 先端から 10 grid 以内: 100%、10〜20 grid: 25% |
| ミサイル誘導 | 母艦レーダー範囲内の目標のみ追尾、範囲外は直進 |

---

## ゲームループ設計

60 FPS の pygame ループで `dt`（秒）ベースの連続更新。

```
毎フレーム:
  universe.update(dt)
  ├─ 破壊フラグ確認 → 削除
  ├─ 全オブジェクトの update(dt)
  │    Vessel: レーダースキャン → ナビゲーター → ガンナー → 位置更新
  │            → ジェネレータ充填 → シールド回復/消費
  ├─ 武器衝突検知・ダメージ適用
  ├─ elapsed += dt; elapsed ≥ 1.0 → tick()
  │    全 Vessel の BotCommander.tick() を呼ぶ（AI 意思決定）
  └─ 勝敗判定（_initialized フラグが True の場合のみ）
```

---

## 実装フェーズと進捗

### Phase 1: プロジェクト基盤 + コアオブジェクト　✅
**ブランチ:** `phase/1-core`

- `pyproject.toml`（uv/pygame/pytest）
- `coords.py`: `Vec2`、`wrap()`、`distance_grid()`、`direction_to()` 等
- `constants.py`: 仕様書の全数値
- `Thing`、`Mover`、`Universe` の骨格
- **バグ修正:** オブジェクト未配置時に勝敗判定が即発火する問題 → `_initialized` フラグで対処

---

### Phase 2: 装備の実装　✅
**ブランチ:** `phase/2-equipment`

- `Generator`: 毎フレーム `rate × dt` でキャパシタに充填
- `Shield`: `absorb()` で防御率を低下、`update()` で回復とエネルギー消費
- `Radar` + `Integrator`: 探知範囲内をスキャンし艦固有の全天マップに記録
- `MissileLauncher` / `BeamLauncher`: 発射オブジェクト生成
- `MissileNavigation`: 母艦レーダー連動の追尾制御
- `Beam`: tip から距離に応じたダメージ判定、恒星接触で消滅
- **バグ修正:** ミサイルの初期方位に `direction_to()` を使用（座標ラッピング対応）

---

### Phase 3: 艦艇・要員・BOT AI　✅
**ブランチ:** `phase/3-crew`

- `Vessel._init_equipment()`: 全装備を一括初期化
- `Destroyer` / `HeavyCruiser` / `SpecialShip`: 定数から各装備を初期化
- `Navigator`: 目的地への進路計算、到着判定 (20 grid 以内)、回避機動
- `Gunner`: 攻撃キュー処理、ビーム検知→シールド 50%、ミサイル検知→100%
- `BotCommander.tick()`:
  1. ダメージ ≥ 80% → ホームへ退避
  2. 敵が射程内 → 攻撃（ビーム優先）
  3. 敵が射程外 → 接近
  4. 敵なし → ホームから 150 grid 円軌道で待機

---

### Phase 4: ゲーム初期化・勝敗判定　✅
**ブランチ:** `phase/4-init`

- `initializer.py`:
  - 恒星 20〜30 個をランダム配置
  - 連邦基地 5 個（互いに 1.5 座標単位以上離れたセクタ中心）
  - 連邦駆逐艦：基地ごとに 10 隻、150 grid 円軌道
  - クリンゴン艦隊 3 個：重巡 1 + 駆逐 10、150 grid 円軌道
  - 特務艦：ランダムな連邦基地の近傍に配置
  - 全艦艇を満載状態でスタート
- `Universe.victory`: 連邦基地全滅 → K 勝利、クリンゴン艦全滅 → U 勝利
- pytest 69 テスト（座標・装備・艦艇・武器・初期化・勝敗）全通過

---

### Phase 5: UI 実装　✅
**ブランチ:** `phase/5-ui`

ウィンドウレイアウト（1200 × 800px）：

```
┌────────────────────────┬───────────────┐
│                        │ ステータス    │
│   マップ               │ パネル        │
│   800 × 800 px         │ (810,5)       │
│   （1:1 アスペクト比）  ├───────────────┤
│                        │ クルーログ    │
│                        │ (810,340)     │
└────────────────────────┴───────────────┘
```

- **MapView** (`map_view.py`): 800×800 正方形エリア、セクタグリッド、オブジェクトを色・形で描画、速度矢印、ビーム軌跡、選択ハイライト
- **StatusPanel** (`status_panel.py`): HP/シールド/キャパシタ/燃料をバー表示、ジャンプドライブ状態、連邦基地・クリンゴン残数
- **MessageWindow** (`message_window.py`): クルーログのスクロール表示、マウスホイール対応
- **PopupMenu** (`popup_menu.py`): コンテキスト依存メニュー（敵艦→攻撃、基地→移動/ジャンプ、空白→移動速度選択、自艦→シールド/ジャンプ先選択）
- **GameUI** (`game_ui.py`): 全コンポーネント統合、イベントルーティング
- **font_util.py**: ヒラギノ角ゴシック W3 を優先ロードし、日本語表示を保証

**操作方法:**

| 操作 | 動作 |
|------|------|
| マップ左クリック（空白） | 移動速度選択メニュー |
| マップ左クリック（敵艦） | ミサイル攻撃 / ビーム攻撃 / 接近 |
| マップ左クリック（連邦基地） | 移動 / ジャンプ |
| マップ左クリック（自艦） | 停止 / シールド設定 / ジャンプ先選択 |
| マウスホイール | クルーログスクロール |
| スペースキー | 即時停止 |
| S キー | シールドのオン/オフ切り替え |
| ESC | 終了 |

---

## ブランチ戦略

```
main
├── phase/1-core      → main にマージ済み
├── phase/2-equipment → main にマージ済み
├── phase/3-crew      → main にマージ済み
├── phase/4-init      → main にマージ済み
└── phase/5-ui        → main にマージ済み
```

各フェーズはブランチで実装 → ユーザーテスト → コミット → `main` へ `--no-ff` マージ。

---

## 起動方法

```bash
uv run python main.py   # ゲーム起動
uv run pytest           # テスト実行（69テスト）
```
