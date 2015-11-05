---
title: Requests抓取网页的编码问题
date: 2013-7-18
tags:
    - python
    - request
    - encoding
---

经常在各大python论坛上看到有关爬虫的问题，实在是搞不明白这玩意儿除了对做搜索引擎还能有啥用。今天本着好奇的态度，打算试一试。

一番Google之后，发现了个很NB的库**Requests**，比之前我用过的liburl2等http库简单多了。出于测试的目的，打算抓取一下我的博客。

```python
#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import requests

r = requests.get('http://zqqf16.info')

print(r.content)
print(r.encoding)
```

打印内容的时候一切正常，但是`encoding`却显示的是`ISO-8859-1`。我的页面上明明写着`<meta http-equiv="Content-Type" content="text/html;charset=utf-8">`，但结果却不是utf-8，百思不得其解，难道是我的html格式不对？

为了验证这个问题，我抓取了一下百度的首页，它的encoding显示的是'utf-8'，而他的头部写的格式和我的一样。

这下迷茫了，Google了很长时间也没找到答案，只能仔细翻看官方的文档了。

终于，在[文档里](http://docs.python-requests.org/en/latest/user/advanced.html#encodings)发现了这么一段：

> When you receive a response, Requests makes a guess at the encoding to use for decoding the response when you call the Response.text method. Requests will first check for an encoding in the HTTP header, and if none is present, will use charade to attempt to guess the encoding.

> The only time Requests will not do this is if no explicit charset is present in the HTTP headers and the Content-Type header contains text. In this situation, RFC 2616 specifies that the default charset must be ISO-8859-1. Requests follows the specification in this case. If you require a different encoding, you can manually set the Response.encoding property, or use the raw Response.content.

这我才明白了，原来HTTP头部也有个“Content-Type”字段，requests会先去找HTTP头部的这个字段，如果没有，就调用“charade”来猜测编码。而默认的编码格式正是“ISO-8859-1”。

用chrome的调试工具看了一下baidu.com的Response Header，有这样一句“Content-Type:text/html;charset=utf-8”。而我的[zqqf16.info](http://zqqf16.info)却没有。这就是为什么我的编码格式识别不出来的原因。

由于我的博客在Github上，没法控制他的HTTP server的行为。为了能让requests识别出UTF-8，我在之前的代码里加了一句，为其指定了编码格式。

```python
r.encoding = 'utf-8'
```

问题搞定了，多看看官方文档还是很有帮助滴。
