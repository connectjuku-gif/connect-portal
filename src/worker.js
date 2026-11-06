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

    const res = await env.ASSETS.fetch(request);
    return addHomeButton(request, res);
  },
};

// ---- すべての教材ページに「ポータルへ戻る」ボタンを付ける（ファイル自体は書きかえない） ----
// 印刷時・ほかのページの中（iframe）・ダウンロードして開いたとき（file:）は表示しない。
const HOME_BUTTON = `<a id="connect-home-btn" href="/" title="教材ポータルのトップへ戻る">← ポータル</a>
<style>
#connect-home-btn{position:fixed;left:12px;bottom:12px;z-index:2147483000;background:#1F3A5F;color:#fff;
font:600 13px/1 "Hiragino Kaku Gothic ProN","Yu Gothic","Meiryo",sans-serif;padding:9px 14px;border-radius:999px;
text-decoration:none;box-shadow:0 2px 8px rgba(0,0,0,.25);opacity:.88}
#connect-home-btn:hover{opacity:1}
@media print{#connect-home-btn{display:none!important}}
</style>
<script>(function(){var b=document.getElementById('connect-home-btn');if(!b)return;
try{if(window.self!==window.top||location.protocol==='file:')b.remove();}catch(e){b.remove();}})();</script>`;

function addHomeButton(request, res) {
  const type = res.headers.get("Content-Type") || "";
  if (!type.includes("text/html")) return res;
  const path = new URL(request.url).pathname;
  if (path === "/" || path === "/index.html" || path === "/index") return res;
  return new HTMLRewriter()
    .on("body", { element(el) { el.append(HOME_BUTTON, { html: true }); } })
    .transform(res);
}
