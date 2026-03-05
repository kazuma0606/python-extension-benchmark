# python-extension-benchmark 追加実装ロードマップ

## 現状

- ベンチマーク実行済み（Pure Python / C / C++ / Cython / Rust）
- 結果はJSON出力のみ
- リポジトリ：https://github.com/kazuma0606/python-extension-benchmark

---

## Phase 1 — API化

**目的**：ベンチマーク実行をHTTP経由で呼び出せるようにする

**技術スタック**：FastAPI

**実装内容**

- ベンチマーク実行エンドポイント（REST）
- 実行中の進捗をリアルタイム配信（WebSocket）
- 結果取得エンドポイント

```python
# WebSocketでリアルタイム進捗配信
@app.websocket("/ws/benchmark")
async def benchmark_ws(websocket: WebSocket):
    await websocket.accept()
    async for progress in run_benchmark():
        await websocket.send_json({
            "scenario": progress.scenario,
            "implementation": progress.impl,
            "status": "running",
            "elapsed_ms": progress.elapsed
        })

# 結果取得
@app.get("/results/{run_id}", response_model=BenchmarkResult)
async def get_results(run_id: str) -> BenchmarkResult:
    ...
```

---

## Phase 2 — UI実装

**目的**：ベンチマーク設定・実行・結果確認をブラウザで操作できるようにする

**技術スタック**：Next.js + shadcn/ui + Recharts

**画面構成**

```
├ ベンチマーク設定パネル（シナリオ選択・言語選択）
├ 実行ボタン → WebSocketでリアルタイム進捗バー
├ 結果ダッシュボード
│   ├ 棒グラフ（実行時間比較）
│   ├ レーダーチャート（総合評価）
│   └ テーブル（詳細数値）
└ 過去の実行履歴
```

---

## Phase 3 — 永続化

**目的**：実行履歴の保存・過去結果との比較を可能にする

**技術スタック**：PostgreSQL + SQLAlchemy or Tortoise-ORM

**採用理由**

- ベンチマーク結果はスキーマが固定されている
- 「Rustの先週比」などの集計クエリが書きやすい
- NoSQLは現時点では過剰設計

**管理データ**

- 実行履歴（実行日時・シナリオ・言語・結果）
- 環境情報（CPU・メモリ・OSなど）

---

## Phase 4 — メトリクス監視

**目的**：時系列でのパフォーマンス変化を監視・可視化する

**技術スタック**：Prometheus + Grafana

**実装内容**

```python
from prometheus_client import Histogram, Gauge

benchmark_duration = Histogram(
    "benchmark_duration_ms",
    "Benchmark execution time",
    labelnames=["scenario", "implementation"]
)

memory_usage = Gauge(
    "benchmark_memory_mb",
    "Memory usage during benchmark",
    labelnames=["scenario", "implementation"]
)
```

**Grafanaで実現できること**

- 実装別・シナリオ別のパーセンタイル分布
- パフォーマンスの経時変化
- 基準値からの逸脱アラート

---

## 全体アーキテクチャ

```
[Next.js + shadcn/ui]
        ↓ REST / WebSocket
     [FastAPI]
        ↓
  [benchmark runner]
        ↓
[C / C++ / Cython / Rust]
        ↓
   [PostgreSQL]
        ↓
[Prometheus + Grafana]
```

---

## Docker Compose構成（最終形）

```yaml
services:
  frontend:     # Next.js + shadcn/ui
  api:          # FastAPI
  db:           # PostgreSQL
  prometheus:   # メトリクス収集
  grafana:      # 可視化
```

`docker-compose up` 一発で全環境が起動する構成を目指す。

---

## 実装順序まとめ

| Phase | 内容 | 技術 |
|---|---|---|
| Phase 1 | API化 | FastAPI + WebSocket |
| Phase 2 | UI実装 | Next.js + shadcn/ui |
| Phase 3 | 永続化 | PostgreSQL |
| Phase 4 | メトリクス監視 | Prometheus + Grafana |

*ログ収集はstructlogで構造化ログをファイル出力し、Prometheusが収集する構成のため別途NoSQLは不要。*
