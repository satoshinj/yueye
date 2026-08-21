# 閲覧 · Yueye (阅页)

<p align="center">
  <strong>閲覧権限を持つオンライン文書を、検索可能なオフラインコピーとして保存。</strong>
</p>

<p align="center">
  <a href="https://yueye.jingzhiacademy.com/"><img src="https://img.shields.io/badge/公式サイト-yueye.jingzhiacademy.com-blue?style=flat-square" alt="Website" /></a>
  <a href="https://github.com/satoshinj/yueye/releases"><img src="https://img.shields.io/github/v/release/satoshinj/yueye?style=flat-square&color=success" alt="Release" /></a>
  <img src="https://img.shields.io/badge/プラットフォーム-Windows%2010%20%2F%2011-lightgrey?style=flat-square" alt="Platform" />
  <img src="https://img.shields.io/badge/ライセンス-MIT-orange?style=flat-square" alt="License" />
</p>

<p align="center">
  <a href="README.md">简体中文</a> |
  <a href="README_EN.md">English</a> |
  <b>日本語</b> |
  <a href="README_KO.md">한국어</a> |
  <a href="README_ES.md">Español</a> |
  <a href="README_FR.md">Français</a> |
  <a href="README_DE.md">Deutsch</a> |
  <a href="README_RU.md">Русский</a>
</p>

---

> [!IMPORTANT]
> **コンプライアンスに関する注意事項**：本ツールは、利用者が**ログイン済みで閲覧権限を有する**コンテンツを個人用オフライン閲覧として保存するためにのみ設計されています。権限外のページはサーバーから送信されません。プロテクト解除、CAPTCHA突破、スライダー認証の自動代行は行いません。詳細は [DISCLAIMER.md](DISCLAIMER.md) をご覧ください。

---

## ✨ 主な機能

| 機能モジュール | 概要 | 特徴・メリット |
|---|---|---|
| **スマートルート判定** | Web記事 / 分割ビューア / 全体スクリーンショット 自動選択 | DOM記事は**テキスト型PDF**（検索可能・サイズ90%削減）を出力。Canvasはネイティブピクセルを抽出 |
| **超高速パフォーマンス** | `canvas.toDataURL` 直接読込 + ハッシュ安定プローブ | **26ms/頁**（通常のスクリーンショットより8倍高速）、待機0.75秒/頁、100頁を数秒でエクスポート |
| **動的ページめくり探索** | 入力欄 → 次へボタン → スクロールコンテナ → キーボード | **固定セレクタ不要**。実行時に有効なページ送り手法を自律検出・固定 |
| **耐障害性と即時停止** | ビューア事前読み込み + 指数バックオフ + ミリ秒停止 | 遮蔽ポップアップの自動回避。「停止」ボタンでミリ秒単位で即時終了 |
| **多様なブラウザ対応** | Edge, Chrome, 360, QQ Browser, Brave, Cent などを自動認識 | 残留ロック（`SingletonLock`）自動削除、自動制御バナー非表示、社内プロキシ・SSLエラー透過 |
| **多彩なフォーマット & ページ範囲** | PDF（テキスト/画像）/ Word / Markdown / プレーンテキスト / 画像 | 指定ページ範囲（例：`1-10`）対応。バックグラウンド非同期出力でUIがフリーズしません |

---

## 🚀 クイックスタート

### 方法 A：ポータブル版（推奨・Python環境不要）

1. [GitHub Releases](https://github.com/satoshinj/yueye/releases) から `Yueye-v1.0.3-win-x64.zip` をダウンロードして展開。
2. `阅页.exe` をダブルクリック：
   - 最初に **「登录浏览器」(ブラウザログイン)** をクリックし、対象サイトにログイン（ログイン状態は長期保存されます）。
   - 文書URLを貼り付け、形式とページ範囲を選択して **「开始抓取」(開始)** をクリック。

### 方法 B：CLI コマンドライン（バッチ処理・自動化）

```cmd
# 文書全体を PDF として出力
阅页.exe --url "https://..." --format pdf

# 1〜10ページを Markdown として指定フォルダに出力
阅页.exe --url "https://..." --format markdown --range 1-10 --out ./output

# 指定したブラウザパスで実行
阅页.exe --url "https://..." --browser "C:\Path\To\Chrome.exe"
```

### 方法 C：ソースコードから実行（開発者向け）

```bash
git clone https://github.com/satoshinj/yueye.git
cd yueye
pip install -r requirements.txt
playwright install chromium
python app.py
```

---

## 📊 プラットフォーム互換性

| タイプ | 対象サイト | 処理方式 | 検証状況 |
|---|---|---|---|
| **専用アダプター** | Doc88 (道客巴巴) | 専用ページ送りアダプター + 注釈レイヤー除外 | ✅ 実機検証済み |
| **構造アダプター** | RenrenDoc (人人文库) | 専用 DOM 抽出およびナビゲーション | ⚠️ アダプター実装済み、個別未検証 |
| **汎用構造検出** | Book118, Docin, Baidu 文庫, MBA智庫, 360文庫, 淘豆網 など | `AutoReader` 動的ページ送り & ピクセル探知 | ⚠️ 汎用構造検出（サイト仕様変更により変化） |

> 📌 **取得可否はお使いのアカウント権限に依存します。**

---

## 🛠️ テストとビルド

```bash
# 11組のオフライン回帰テストを実行（外部ネットワーク不要）
python tests/test_engine.py

# ポータブル版のビルドと自動セルフテストの実行
build.bat
```

---

## 📝 ライセンスと免責事項

本ソフトウェアは [MIT License](LICENSE) に基づいて公開されています。

ご利用前に必ず **[DISCLAIMER.md](DISCLAIMER.md)** をお読みください。
