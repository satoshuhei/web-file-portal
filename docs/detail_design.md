# 詳細設計書

## 1. 画面/機能詳細
### 1.1 ファイル一覧
- 入力
  - path: パンくず/現在フォルダ
  - name, folder, regex, bulk
  - date_from, date_to
  - ext (チェック), ext_free (自由入力)
- 振る舞い
  - path指定時は該当プレフィックスの直下のみ表示。
  - 検索条件が1つでもあれば検索モード。
  - 検索モードは結果一覧のパス列を表示。
- ソート
  - ディレクトリ優先、名前の昇順。

### 1.2 プレビュー
- PDF: application/pdf で返却。
- テキスト: 最大200KBまで読み取り、UTF-8として表示。
- それ以外: テキスト扱いで表示。

### 1.3 ダウンロード
- 単体ファイル: FileResponse で返却。
- フォルダ/複数: ZIP生成して返却。

### 1.4 検索結果ZIP
- 検索条件がない場合は400。
- 結果なしは404。

## 2. バッチ詳細
### 2.1 sync_file_index
1. ルートパス検証。
2. テナントを取得/作成。
3. 走査しフォルダ/ファイルを列挙。
4. FileEntryを作成/更新。
5. 未検出の既存エントリを削除 (no-deleteで抑止)。
6. ProcessLogを更新。

## 3. データモデル詳細
### 3.1 Tenant
- name: 表示名
- slug: 識別子 (unique)
- is_active: 有効フラグ
- created_at: 作成日時

### 3.2 FileEntry
- file_id: UUID
- tenant_id: 外部キー
- name: ファイル名
- relative_path: ルートからの相対パス
- extension: 拡張子
- size_bytes: サイズ
- modified_at: 更新日時
- is_dir: ディレクトリフラグ
- owner: 所有者

### 3.3 AuditLog
- tenant_id, action, actor, target, detail, created_at

### 3.4 ProcessLog
- tenant_id, job_name, status, message
- started_at, finished_at
- created_count, updated_count, deleted_count, scanned_count

## 4. 関数/ロジック詳細 (files.views)
### 4.1 _normalize_path
- バックスラッシュをスラッシュに統一し前後の"/"を除去。

### 4.2 _resolve_path
- ルート配下に限定することでパストラバーサルを防止。

### 4.3 _apply_filters
- name/folder/extension/dateでQuerySetを絞り込み。
- bulk/regexはアプリ側で追加フィルタ。

### 4.4 _zip_response
- SpooledTemporaryFileでZIPを生成しFileResponseで返却。

## 5. インタフェース詳細
### 5.1 HTTP
- GET /files/preview?path=
- GET /files/download?path=
- GET /files/download-bulk?name=&folder=&regex=&bulk=&date_from=&date_to=&ext=&ext_free=
- POST /files/download-selected (form-data: selected[])

### 5.2 環境変数
- APP_LOCAL_STORAGE_ROOT: 共有フォルダルート
- APP_DEFAULT_TENANT: 同期時の既定テナント
- APP_DEFAULT_OWNER: 同期時の既定所有者

## 6. 例外設計
- 400: 必須パラメータ不足、検索条件不備
- 404: パス未検出
- 405: メソッド不許可

## 7. UML
- シーケンス図: [docs/uml/sequence_search_download.puml](docs/uml/sequence_search_download.puml)
- シーケンス図(画像): [docs/uml/images/sequence_search_download.png](docs/uml/images/sequence_search_download.png)
- シーケンス図(バッチ): [docs/uml/sequence_sync_file_index.puml](docs/uml/sequence_sync_file_index.puml)
- シーケンス図(バッチ画像): [docs/uml/images/sequence_sync_file_index.png](docs/uml/images/sequence_sync_file_index.png)
- クラス図: [docs/uml/class.puml](docs/uml/class.puml)
- クラス図(画像): [docs/uml/images/class.png](docs/uml/images/class.png)
- ER図: [docs/uml/er.puml](docs/uml/er.puml)
- ER図(画像): [docs/uml/images/er.png](docs/uml/images/er.png)
