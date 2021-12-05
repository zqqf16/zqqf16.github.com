---
layout: post
title: 清理 Safari HSTS 记录
date: 2017-10-12
excerpt: 解决网站从 HTTPS 切换到 HTTP 之后，Safari 无法访问的问题
---

之前用来放博客的 vps 在这次清洗活动中阵亡，思考再三，还是回到了 Github Pages。这点访问量不值得再折腾了...

迁移过程还算正常，用脚本把 Ghost 的数据库里的文章重新转换成 markdown 文件，并且全面接入 jekyll。

然而，由于以前启用了 HTTPS，而现在只能用 HTTP，Safari 在访问的时候总是强制转换成 HTTPS（HSTS机制），进而导致无法访问。

解决方法：

1. 关掉 Safari
2. `killall nsurlstoraged`
3. `rm -f ~/Library/Cookies/HSTS.plist` 
4. `launchctl start /System/Library/LaunchAgents/com.apple.nsurlstoraged.plist` 

参考链接 [https://apple.stackexchange.com/a/288002](https://apple.stackexchange.com/a/288002)