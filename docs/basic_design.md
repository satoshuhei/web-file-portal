# 基本設計書

## 1. システム構成
- Webアプリ: Django (テンプレートレンダリング)
- DB: SQLite
- ストレージ: ローカルファイルシステム (APP_LOCAL_STORAGE_ROOT)
- バッチ: Django管理コマンド

## 2. アーキテクチャ概要
- Web画面はDBのFileEntryを参照して一覧/検索を行う。
- ファイル実体の読み出しはローカルストレージから行う。
- バッチ同期でDBとファイルシステムを整合させる。

## 3. 主要コンポーネント
### 3.1 core
- トップページの表示。

### 3.2 files
- 一覧/検索/プレビュー/ダウンロードを提供。
- パストラバーサル対策を含む。

### 3.3 tenants
- テナント情報を保持。

### 3.4 audit
- 監査ログ/処理ログの保持。

### 3.5 authz
- 認可拡張のためのプレースホルダ。

## 4. 画面設計
### 4.1 トップ
- 概要説明カードを表示。

### 4.2 ファイル検索/一覧
- パンくず表示。
- 条件入力: 名前/フォルダ/正規表現/一括/更新日/拡張子。
- 結果一覧: 選択チェック、種類、更新日、サイズ、DLリンク。
- 検索中のみ「検索結果ZIP」を表示。

## 5. バッチ設計
### 5.1 sync_file_index
- APP_LOCAL_STORAGE_ROOT を走査しFileEntryを更新。
- 既存にないパスは作成、変更は更新。
- 存在しないパスは削除 (no-delete指定で抑止)。
- ProcessLogに結果を保存。

### 5.2 seed_sample_data
- 開発用サンプルデータとファイルを作成。

## 6. データ設計(概略)
- Tenant
- FileEntry
- AuditLog
- ProcessLog

## 7. インタフェース設計(概要)
- Web: /files/ 配下のエンドポイント
- CLI: manage.py 管理コマンド

## 8. 設定
- .env で環境変数を指定
  - APP_LOCAL_STORAGE_ROOT
  - APP_DEFAULT_TENANT
  - APP_DEFAULT_OWNER
  - DJANGO_SECRET_KEY
  - DJANGO_DEBUG
  - DJANGO_ALLOWED_HOSTS

## 9. 例外/エラーハンドリング
- 入力不備は400/404/405で返却。
- バッチ失敗時はProcessLogに記録。

## 10. 関連図
- クラス図: [docs/uml/class.puml](docs/uml/class.puml)
- クラス図(画像): [docs/uml/images/class.png](docs/uml/images/class.png)
- ER図: [docs/uml/er.puml](docs/uml/er.puml)
- ER図(画像): [docs/uml/images/er.png](docs/uml/images/er.png)
- コンポーネント図: [docs/uml/component.puml](docs/uml/component.puml)
- コンポーネント図(画像): [docs/uml/images/component.png](docs/uml/images/component.png)
