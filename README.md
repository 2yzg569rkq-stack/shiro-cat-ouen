# 白さんの迷い猫・保護猫おうえんページ

## 中身
- build_site.py … lost_cat_reposts.csv からページ（docs/index.html）を作る
- docs/index.html … 今日の3件で作ったページ

## 更新のしかた（Mac）
    python3 build_site.py ~/TapoHourlyXPipeline/data/lost_cat_reposts.csv docs

## 見つかった・決まった子を外すとき
lost_cat_reposts.csv のその行の「備考」に【解決】【終了】【非表示】のどれかを書き足して、もう一度作る。

## GitHub Pages で公開（はじめの1回）
1. GitHub で新しいリポジトリを作る（例：shiro-cat-ouen、Public）
2. このフォルダの中身をそのリポジトリに入れる
3. Settings → Pages → Branch を main / docs にして Save
4. 数分後、https://<GitHubのユーザー名>.github.io/shiro-cat-ouen/ で見られる
