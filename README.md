# Media Converter

画像・動画を高画質のまま別フォーマットに変換する Windows 用ツールです。

---

## ダウンロード

[Releases](../../releases/latest) から `MediaConverter_Setup.exe` をダウンロードしてインストールしてください。

---

## 対応フォーマット

| 変換先 | 変換元 |
|--------|--------|
| **PNG** | JPG / HEIC / RAW (CR3, CR2, NEF, ARW) など |
| **JPG** | PNG / HEIC / RAW (CR3, CR2, NEF, ARW) など |
| **MP4** | MOV / AVI / MKV / MP4 など動画全般 |

---

## 使い方

1. 変換したいフォーマットのボタンをクリック
2. ファイルを選択
3. 保存先フォルダを選択
4. 自動で変換が始まります

---

## 動画変換について

MP4 変換には **FFmpeg** が必要です。

**インストール方法：**
1. [FFmpeg 公式サイト](https://ffmpeg.org/download.html) からダウンロード
2. 解凍して `ffmpeg.exe` / `ffprobe.exe` を `C:\ffmpeg\bin\` などに置く
3. そのフォルダを環境変数 `PATH` に追加する

**エンコーダーの選び方：**

| 選択肢 | 向いている人 |
|--------|-------------|
| CPU (libx264) | 確実に動かしたい・GPU を使いたくない |
| GPU (NVIDIA NVENC) | NVIDIA のグラフィックカードを積んでいる |
| GPU (Intel QSV) | Intel 内蔵グラフィックスを使っている |

---

## 動作環境

- Windows 10 / 11

---

## クレジット

Created by [Aki](https://github.com/Irony-s9c)
