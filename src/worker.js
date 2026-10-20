// CONNECT教材ポータル — 簡易Basic認証つきの静的ファイル配信
// 講師全員で共有するID・パスワードはここで管理しています。
// 変更したい場合は下の BASIC_AUTH_USER / BASIC_AUTH_PASS を書き換えて push してください。

const BASIC_AUTH_USER = "connect";
const BASIC_AUTH_PASS = "nakano-juku2026";

function unauthorized() {
  return new Response("このページを見るにはIDとパスワードが必要です。", {
    status: 401,
    headers: {
      "WWW-Authenticate": 'Basic realm="CONNECT教材ポータル", charset="UTF-8"',
      "Content-Type": "text/plain; charset=UTF-8",
    },
  });
}

export default {
  async fetch(request, env) {
    const authHeader = request.headers.get("Authorization");

    if (!authHeader || !authHeader.startsWith("Basic ")) {
      return unauthorized();
    }

    let decoded;
    try {
      decoded = atob(authHeader.slice(6));
    } catch (e) {
      return unauthorized();
    }

    const sep = decoded.indexOf(":");
    const user = sep === -1 ? decoded : decoded.slice(0, sep);
    const pass = sep === -1 ? "" : decoded.slice(sep + 1);

    if (user !== BASIC_AUTH_USER || pass !== BASIC_AUTH_PASS) {
      return unauthorized();
    }

    return env.ASSETS.fetch(request);
  },
};
