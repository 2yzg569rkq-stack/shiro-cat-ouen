#!/usr/bin/env python3
"""白さんの迷い猫・保護猫ページを lost_cat_reposts.csv から作る。

使い方:
  python3 build_site.py <lost_cat_reposts.csvのパス> <出力フォルダ(docs)>

- 元の X の投稿を「埋め込み」で表示する（写真はコピーしない）。
  元の投稿が消されると、ページからも自然に表示されなくなる。
- 備考に【解決】【終了】【非表示】のどれかを書いた行は載せない
  （見つかった・里親さんが決まった・本人から頼まれた、など）。
- 拡散から14日以内は「いま探しています／募集中」に埋め込みで、
  それより前は「これまでに拡散した子」に文字とリンクだけで並べる。
"""
import csv
import html
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

JST = timezone(timedelta(hours=9))
RECENT_DAYS = 14
HIDE_MARKS = ("【解決】", "【終了】", "【非表示】")


def parse_dt(s):
    s = (s or "").strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=JST)
        except ValueError:
            pass
    return None


def load(csv_path):
    rows = []
    with open(csv_path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            url = (r.get("元の投稿URL") or "").strip()
            if not url.startswith("https://x.com/"):
                continue
            if any(m in (r.get("備考") or "") for m in HIDE_MARKS):
                continue
            r["_dt"] = parse_dt(r.get("拡散日時"))
            rows.append(r)
    rows.sort(key=lambda r: r["_dt"] or datetime.min.replace(tzinfo=JST), reverse=True)
    return rows


def e(s):
    return html.escape(s or "", quote=True)


def kind_group(kind):
    return "adopt" if "里親" in (kind or "") else "lost"


def card(r):
    kind = r.get("種類", "")
    badge_cls = "b-adopt" if kind_group(kind) == "adopt" else ("b-found" if "保護" in kind else "b-lost")
    return f"""
    <article class="card">
      <div class="meta">
        <span class="badge {badge_cls}">{e(kind)}</span>
        <span class="area">{e(r.get('地域'))}</span>
      </div>
      <p class="feat">{e(r.get('猫の特徴'))}</p>
      <blockquote class="twitter-tweet" data-dnt="true" data-lang="ja" data-conversation="none">
        <a href="{e(r['元の投稿URL'])}">元の投稿を X で見る</a>
      </blockquote>
      <p class="links"><a href="{e(r['元の投稿URL'])}" target="_blank" rel="noopener">元の投稿</a>
      ・拡散 {e((r.get('拡散日時') or '')[:10])}</p>
    </article>"""


def row_li(r):
    return (f"<li><span class=\"badge sm\">{e(r.get('種類'))}</span> "
            f"{e(r.get('地域'))}｜{e(r.get('猫の特徴'))} "
            f"<a href=\"{e(r['元の投稿URL'])}\" target=\"_blank\" rel=\"noopener\">元の投稿</a>"
            f" <span class=\"muted\">({e((r.get('拡散日時') or '')[:10])})</span></li>")


def build(rows, now):
    cutoff = now - timedelta(days=RECENT_DAYS)
    recent = [r for r in rows if r["_dt"] and r["_dt"] >= cutoff]
    older = [r for r in rows if not (r["_dt"] and r["_dt"] >= cutoff)]
    lost = [r for r in recent if kind_group(r.get("種類")) == "lost"]
    adopt = [r for r in recent if kind_group(r.get("種類")) == "adopt"]

    def section(items, empty):
        if not items:
            return f'<p class="empty">{empty}</p>'
        return '<div class="grid">' + "".join(card(r) for r in items) + "</div>"

    older_html = ""
    if older:
        older_html = ("<details><summary>これまでに拡散した子（" + str(len(older)) + "件）</summary><ul class=\"old\">"
                      + "".join(row_li(r) for r in older) + "</ul></details>")

    return TEMPLATE.format(
        updated=now.strftime("%Y年%-m月%-d日 %H:%M"),
        n_lost=len(lost), n_adopt=len(adopt), days=RECENT_DAYS,
        lost=section(lost, "いま載せている迷い猫の投稿はありません。"),
        adopt=section(adopt, "いま載せている里親募集の投稿はありません。"),
        older=older_html,
    )


TEMPLATE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>白さんの迷い猫・保護猫おうえん</title>
<meta name="description" content="元野良猫の白さん（@iphonexcom）が X で拡散した迷い猫・里親募集の猫たちの一覧です。">
<style>
:root{{--bg:#fbf8f3;--fg:#2b2622;--muted:#7a6f66;--card:#fff;--line:#eadfd3;--accent:#c9783a;--lost:#c2463b;--found:#3a7d5c;--adopt:#5a62b8}}
@media (prefers-color-scheme:dark){{:root{{--bg:#1d1a17;--fg:#efe8e0;--muted:#a69a8f;--card:#27231f;--line:#3a332d;--accent:#e09a5f}}}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--fg);font-family:"Hiragino Sans","Noto Sans JP",system-ui,sans-serif;line-height:1.75}}
.wrap{{max-width:1080px;margin:0 auto;padding:0 16px}}
header{{padding:40px 0 24px;border-bottom:1px solid var(--line)}}
h1{{font-size:clamp(1.5rem,4vw,2.1rem);margin:0 0 8px;letter-spacing:.02em}}
h1 span{{color:var(--accent)}}
.lead{{margin:0;color:var(--muted);max-width:44em}}
nav{{display:flex;gap:16px;flex-wrap:wrap;margin-top:16px;font-size:.95rem}}
nav a{{color:var(--accent);text-decoration:none;font-weight:600}}
h2{{font-size:1.3rem;margin:40px 0 4px}}
.sub{{color:var(--muted);margin:0 0 16px;font-size:.92rem}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px;align-items:start}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 14px 10px}}
.meta{{display:flex;gap:8px;align-items:center;flex-wrap:wrap}}
.badge{{font-size:.78rem;font-weight:700;color:#fff;border-radius:999px;padding:2px 10px;background:var(--muted)}}
.b-lost{{background:var(--lost)}}.b-found{{background:var(--found)}}.b-adopt{{background:var(--adopt)}}
.badge.sm{{font-size:.72rem;padding:1px 8px}}
.area{{font-weight:700}}
.feat{{margin:6px 0 4px;font-size:.92rem}}
.links{{font-size:.85rem;color:var(--muted);margin:6px 0 0}}
.links a,.old a,.twitter-tweet a{{color:var(--accent)}}
.twitter-tweet{{margin:8px 0!important}}
.empty{{color:var(--muted)}}
details{{margin-top:32px;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px 16px}}
summary{{cursor:pointer;font-weight:700}}
.old{{padding-left:1.1em;font-size:.92rem}}
.muted{{color:var(--muted)}}
.guide{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}}
.guide div{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px}}
.guide h3{{margin:0 0 6px;font-size:1.02rem}}
.guide ol{{margin:0;padding-left:1.2em;font-size:.92rem}}
footer{{margin:48px 0 32px;padding-top:16px;border-top:1px solid var(--line);color:var(--muted);font-size:.85rem}}
footer a{{color:var(--accent)}}
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>白さんの<span>迷い猫・保護猫</span>おうえん</h1>
  <p class="lead">元野良猫の白さんは、いまはおうちでのんびり暮らしています。白さんの X（<a href="https://x.com/iphonexcom" style="color:var(--accent)">@iphonexcom</a>）では、おうちを探している猫たちの投稿を毎日拡散しています。見かけた子がいたら、元の投稿の方へご連絡ください。</p>
  <nav><a href="#lost">迷い猫（{n_lost}）</a><a href="#adopt">里親募集（{n_adopt}）</a><a href="#guide">いなくなったら</a></nav>
</header>

<section id="lost">
  <h2>いま探しています</h2>
  <p class="sub">拡散から{days}日以内の迷い猫・保護された猫の投稿です。連絡先や最新の様子は、元の投稿でご確認ください。</p>
  {lost}
</section>

<section id="adopt">
  <h2>里親さん募集中</h2>
  <p class="sub">拡散から{days}日以内の里親募集の投稿です。譲渡の条件は、元の投稿をご覧ください。</p>
  {adopt}
</section>

{older}

<section id="guide">
  <h2>猫がいなくなったら</h2>
  <p class="sub">一般的な目安です。お住まいの地域の窓口もあわせてご確認ください。</p>
  <div class="guide">
    <div><h3>まず家のまわり</h3><ol><li>近くの物かげ・床下・車の下・物置を、名前を呼びながら静かに探す</li><li>夜や早朝の静かな時間にも探す</li><li>ごはんや使っていた猫砂を、出ていった場所の近くに置く</li></ol></div>
    <div><h3>届け出・問い合わせ</h3><ol><li>警察（遺失届）</li><li>保健所・動物愛護センター</li><li>近くの動物病院</li><li>マイクロチップがあれば、登録内容の確認</li></ol></div>
    <div><h3>知らせる</h3><ol><li>写真・特徴・いなくなった日と場所を書いたチラシ</li><li>SNS で地域名と #迷い猫 をつけて発信</li><li>見つかったら、発信した投稿にも一言お知らせを</li></ol></div>
  </div>
</section>

<footer>
  最終更新：{updated}（日本時間）<br>
  掲載している投稿は X の埋め込みで表示しており、写真や文章は元の投稿者さんのものです。見つかった・里親さんが決まった・載せないでほしい、などのときは <a href="https://x.com/iphonexcom">@iphonexcom</a> までお知らせください。すぐに外します。
</footer>
</div>
<script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
</body>
</html>
"""


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    rows = load(sys.argv[1])
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(build(rows, datetime.now(JST)), encoding="utf-8")
    print(f"wrote {out/'index.html'} ({len(rows)} posts)")


if __name__ == "__main__":
    main()
