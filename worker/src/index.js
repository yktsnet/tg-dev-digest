// GitHub Actions の schedule は混雑すると数時間遅れるため、Cloudflare の Cron Trigger から
// workflow_dispatch を叩いて定刻に起動する。dispatch は数秒で走り始める。
export default {
  async scheduled(_controller, env) {
    await dispatch(env, fetch);
  },
};

export async function dispatch(env, fetchImpl) {
  const url = `https://api.github.com/repos/${env.REPO}/actions/workflows/${env.WORKFLOW}/dispatches`;
  const res = await fetchImpl(url, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.GITHUB_TOKEN}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      // GitHub API は User-Agent の無いリクエストを拒否する
      "User-Agent": "tg-dev-digest-trigger",
    },
    body: JSON.stringify({ ref: env.REF || "main" }),
  });
  if (res.status !== 204) {
    // 例外にしておくと Workers のログと Cron の実行履歴に失敗として残る
    throw new Error(`dispatch failed: ${res.status} ${await res.text()}`);
  }
}
