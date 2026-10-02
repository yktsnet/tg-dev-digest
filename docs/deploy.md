[🇯🇵 日本語](deploy.md) | [🇬🇧 English](deploy.en.md)

# Deploy

fork したリポジトリの GitHub Actions で、毎日 Telegram に届くようにする手順。

## 1. Telegram の Bot を作る

1. Telegram で BotFather に `/newbot` を送り、Bot を作ってトークンを受け取る
2. 作った Bot に何か1通送る
3. ブラウザで `https://api.telegram.org/bot<トークン>/getUpdates` を開き、`chat.id` の値を控える

## 2. Gemini の API キーを用意する

[Google AI Studio](https://aistudio.google.com/apikey) でキーを発行する。1日1回の選別なら無料枠に収まる。キーを用意しない場合は選別が飛ばされ、はてブと Zenn の新着が全件「未選別」で届く。

## 3. secrets を登録する

fork したリポジトリの Settings → Secrets and variables → Actions → Secrets に3つ登録する。

| 名前 | 値 |
|---|---|
| `GEMINI_API_KEY` | 2 のキー |
| `TELEGRAM_BOT_TOKEN` | 1 のトークン |
| `TELEGRAM_CHAT_ID` | 1 の `chat.id` |

`gh` を使うならこう打つ（値は標準入力から渡る）。

```bash
gh secret set GEMINI_API_KEY
gh secret set TELEGRAM_BOT_TOKEN
gh secret set TELEGRAM_CHAT_ID
```

## 4. 試しに動かす

Actions タブで `digest` を選び、Run workflow から `dry_run` にチェックを入れて起動する。送らずに、選別の結果とメッセージがログに出る。

問題が無ければ `dry_run` を外してもう一度起動し、Telegram に届くことを確かめる。初回の実行で `state` ブランチが作られ、送った URL が `seen.txt` に入る。

以後は毎日 UTC 13:27（JST 22:27）に動く。時刻は `.github/workflows/digest.yml` の `cron` で変える。ただし GitHub の schedule は混雑すると数時間遅れる。定刻に届けたい場合は次の 5 を足す。

## 5. 定刻に起動する（任意）

`worker/` は、Cloudflare Workers の Cron Trigger から `workflow_dispatch` を叩いて定刻に起動するだけの Worker。dispatch は数秒で走り始める。schedule は残しておき、Worker が動かなかった日の保険にする。Worker の実行後に遅れて来た schedule は、`state` ブランチが20時間以内に更新されているのを見て何もせずに終わる。

1. GitHub で fine-grained personal access token を作る。Repository access はこのリポジトリだけ、Permissions は Actions の Read and write だけにする
2. `worker/wrangler.jsonc` の `vars.REPO` を自分のリポジトリに書き換える
3. デプロイする

```bash
cd worker
npx wrangler login
npx wrangler secret put GITHUB_TOKEN   # 1 のトークンを貼る
npx wrangler deploy
```

時刻を変えるときは、`wrangler.jsonc` の `triggers.crons` と `digest.yml` の `cron` を同じ値にそろえる。

## 配信元を一時的に絞る

Settings → Secrets and variables → Actions → Variables に `DIGEST_SOURCES` を置くと、`digest.toml` のうちその配信元だけを送る（例: `hatena,zenn` で Trending を止める）。恒常的に変えるなら `digest.toml` の `enabled = false` のほうが履歴に残る。
