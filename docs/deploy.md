# Deploy

fork したリポジトリの GitHub Actions で、毎日 Telegram に届くようにする手順。

## 1. Telegram の Bot を作る

1. Telegram で BotFather に `/newbot` を送り、Bot を作ってトークンを受け取る
2. 作った Bot に何か1通送る
3. ブラウザで `https://api.telegram.org/bot<トークン>/getUpdates` を開き、`chat.id` の値を控える

## 2. Anthropic の API キーを用意する

[Anthropic Console](https://console.anthropic.com/) でキーを発行する。キーを用意しない場合は選別が飛ばされ、はてブと Zenn の新着が全件「未選別」で届く。

## 3. secrets を登録する

fork したリポジトリの Settings → Secrets and variables → Actions → Secrets に3つ登録する。

| 名前 | 値 |
|---|---|
| `ANTHROPIC_API_KEY` | 2 のキー |
| `TELEGRAM_BOT_TOKEN` | 1 のトークン |
| `TELEGRAM_CHAT_ID` | 1 の `chat.id` |

`gh` を使うならこう打つ（値は標準入力から渡る）。

```bash
gh secret set ANTHROPIC_API_KEY
gh secret set TELEGRAM_BOT_TOKEN
gh secret set TELEGRAM_CHAT_ID
```

## 4. 試しに動かす

Actions タブで `digest` を選び、Run workflow から `dry_run` にチェックを入れて起動する。送らずに、選別の結果とメッセージがログに出る。

問題が無ければ `dry_run` を外してもう一度起動し、Telegram に届くことを確かめる。初回の実行で `state` ブランチが作られ、送った URL が `seen.txt` に入る。

以後は毎日 UTC 13:27（JST 22:27）に動く。時刻は `.github/workflows/digest.yml` の `cron` で変える。schedule は混雑すると数時間遅れることがある。

## 配信元を一時的に絞る

Settings → Secrets and variables → Actions → Variables に `DIGEST_SOURCES` を置くと、`digest.toml` のうちその配信元だけを送る（例: `hatena,zenn` で Trending を止める）。恒常的に変えるなら `digest.toml` の `enabled = false` のほうが履歴に残る。
