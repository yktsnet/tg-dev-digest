[🇯🇵 日本語](deploy.md) | [🇬🇧 English](deploy.en.md)

# Deploy

How to get the digest on Telegram every day using GitHub Actions in your fork.

## 1. Create a Telegram bot

1. Send `/newbot` to BotFather on Telegram, create a bot, and receive its token
2. Send any message to the bot you created
3. Open `https://api.telegram.org/bot<token>/getUpdates` in a browser and note the value of `chat.id`

## 2. Get an Anthropic API key

Issue a key in the [Anthropic Console](https://console.anthropic.com/). Without a key the filter is skipped, and all new Hatena Bookmark and Zenn items arrive marked "未選別" (unfiltered).

## 3. Register secrets

In your fork, go to Settings → Secrets and variables → Actions → Secrets and register three secrets.

| Name | Value |
|---|---|
| `ANTHROPIC_API_KEY` | The key from step 2 |
| `TELEGRAM_BOT_TOKEN` | The token from step 1 |
| `TELEGRAM_CHAT_ID` | The `chat.id` from step 1 |

With `gh` (each value is read from standard input):

```bash
gh secret set ANTHROPIC_API_KEY
gh secret set TELEGRAM_BOT_TOKEN
gh secret set TELEGRAM_CHAT_ID
```

## 4. Try it

In the Actions tab, choose `digest`, click Run workflow, check `dry_run`, and start it. Nothing is sent; the filter result and the messages appear in the log.

If it looks right, run it again without `dry_run` and confirm the message arrives on Telegram. The first run creates the `state` branch and records the sent URLs in `seen.txt`.

From then on it runs daily at UTC 13:27 (JST 22:27). Change the time with `cron` in `.github/workflows/digest.yml`. GitHub schedules, however, can be delayed by hours when busy. If you want it on time, add step 5.

## 5. Start on time (optional)

`worker/` is a Worker that only calls `workflow_dispatch` from a Cloudflare Workers Cron Trigger. A dispatch starts within seconds. Keep the schedule as a fallback for days the Worker does not run. A delayed schedule run that arrives after the Worker sees that the `state` branch was updated within the last 20 hours and exits without doing anything.

1. Create a fine-grained personal access token on GitHub. Limit repository access to this repository and permissions to Actions: Read and write
2. Change `vars.REPO` in `worker/wrangler.jsonc` to your repository
3. Deploy

```bash
cd worker
npx wrangler login
npx wrangler secret put GITHUB_TOKEN   # paste the token from step 1
npx wrangler deploy
```

To change the time, set `triggers.crons` in `wrangler.jsonc` and `cron` in `digest.yml` to the same value.

## Narrowing sources temporarily

Putting `DIGEST_SOURCES` in Settings → Secrets and variables → Actions → Variables sends only those sources from `digest.toml` (for example `hatena,zenn` stops Trending). For a lasting change, `enabled = false` in `digest.toml` is better because it stays in history.
