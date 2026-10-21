#!/usr/bin/env python3
"""ポータル（index.html）の各カードにサムネイル画像と学年バッジを付ける。

使い方（リポジトリ直下で）:
    python3 tools/make_thumbs.py          # 全カードのサムネイルを撮り直し、index.html を更新
    python3 tools/make_thumbs.py --new    # サムネイルがまだ無いカードだけ撮る

- 各カードがリンクしている教材HTMLの1画面目を撮影し、thumbs/<教材名>.jpg に保存する。
- カードの絵文字は消さずに残す。<body class="thumbs"> のときだけサムネイル表示になり、
  class を外すと元の絵文字表示に戻る（画像が読めないときも絵文字が出る）。
- 撮影には Playwright（Chromium）を使う。
"""
import json, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, 'index.html')
THUMBS = os.path.join(ROOT, 'thumbs')
GRADE = {'el': '小学生', '1': '中1', '2': '中2', '3': '中3', 'hs': '高校生'}

THUMB_RE = re.compile(r'<div class="thumb(?: has-img)?"([^>]*)>(.*?)</div>', re.S)


def grade_label(g):
    parts = g.split()
    if parts == ['1', '2', '3']:
        return '中1〜中3'
    return '・'.join(GRADE.get(p, p) for p in parts)


def find_cards(html):
    """yield (match, target_href, grade) for every card thumb that links somewhere"""
    for m in THUMB_RE.finditer(html):
        head = html[:m.start()]
        a = head.rfind('<a href="')
        d = head.rfind('<div class="card material-item"')
        if d > a:   # card with pill buttons: use the first pill
            pm = re.search(r'<a href="([^"]+)" class="pill"', html[m.end():])
            href = pm.group(1) if pm else None
        else:
            href = re.match(r'<a href="([^"]+)"', head[a:]).group(1)
        if not href or href == '#' or not href.split('?')[0].endswith('.html'):
            continue
        gm = list(re.finditer(r'data-grade="([^"]+)"', head))
        grade = gm[-1].group(1) if gm else ''
        yield m, href.split('?')[0], grade


def emoji_of(inner):
    m = re.search(r'<span class="temoji">(.*?)</span>', inner, re.S)
    return m.group(1) if m else inner.strip()


def shoot(targets):
    os.makedirs(THUMBS, exist_ok=True)
    js = r"""
const { chromium } = require('playwright');
const targets = %s;
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const p = await b.newPage({ viewport: { width: 820, height: 470 }, deviceScaleFactor: 1 });
  for (const [src, out] of targets) {
    try {
      await p.goto('file://' + src, { waitUntil: 'load' });
      await p.addStyleTag({ content: '.controlbar,.nop,#editBtn,#printBtn{display:none!important} html,body{background:#F4F2EC!important} .sheet{margin-top:14px!important}' });
      await p.waitForTimeout(250);
      // 図のある教材は、最初に図が出てくる大問から写す（タイトルだけのサムネイルにしない）
      await p.evaluate(() => {
        const svg = document.querySelector('.sheet svg.fig');
        if (!svg) return;
        const q = svg.closest('.q') || svg;
        window.scrollTo(0, q.getBoundingClientRect().top + window.scrollY - 12);
      });
      await p.waitForTimeout(150);
      await p.screenshot({ path: out, type: 'jpeg', quality: 72 });
      console.log('ok', out);
    } catch (e) { console.log('ng', src, String(e).slice(0, 120)); }
  }
  await b.close();
})();
""" % json.dumps(targets)
    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as f:
        f.write(js)
    env = dict(os.environ, NODE_PATH='/opt/npm-tools/node_modules')
    subprocess.run(['node', f.name], env=env, check=True)
    # shrink: 820x470 -> 410x235
    from PIL import Image
    for _, out in targets:
        if os.path.exists(out):
            im = Image.open(out).convert('RGB')
            im = im.resize((410, 235), Image.LANCZOS)
            im.save(out, 'JPEG', quality=70, optimize=True, progressive=True)


def main():
    only_new = '--new' in sys.argv
    html = open(INDEX, encoding='utf-8').read()
    cards = list(find_cards(html))
    targets, seen = [], set()
    for _, href, _ in cards:
        name = os.path.splitext(os.path.basename(href))[0]
        out = os.path.join(THUMBS, name + '.jpg')
        if href in seen or (only_new and os.path.exists(out)):
            continue
        seen.add(href)
        targets.append([os.path.join(ROOT, href), out])
    if targets:
        shoot(targets)
    # rewrite thumbs (idempotent)
    out_parts, pos = [], 0
    for m, href, grade in find_cards(html):
        name = os.path.splitext(os.path.basename(href))[0]
        if not os.path.exists(os.path.join(THUMBS, name + '.jpg')):
            continue
        attrs = m.group(1)
        gcls = 'gb-' + grade if grade in GRADE else 'gb-multi'
        badge = '<span class="gbadge %s">%s</span>' % (gcls, grade_label(grade)) if grade else ''
        new = ('<div class="thumb has-img"%s><span class="temoji">%s</span>'
               '<img class="timg" src="thumbs/%s.jpg" alt="" loading="lazy" '
               'onerror="this.parentNode.classList.add(\'noimg\');this.remove()">%s</div>'
               % (attrs, emoji_of(m.group(2)), name, badge))
        out_parts.append(html[pos:m.start()]); out_parts.append(new); pos = m.end()
    out_parts.append(html[pos:])
    html2 = ''.join(out_parts)
    open(INDEX, 'w', encoding='utf-8').write(html2)
    print('cards:', len(cards), 'shot:', len(targets))


if __name__ == '__main__':
    main()
