---
title: 命令行下的有道翻译
date: 2013-5-20
tags: 翻译
---

像我这种英语比较差劲的人来说，一个好点的翻译工具十分重要。Linux下哪个用着都不顺手，每次都用在线的google翻译。介于google经常性的抽风，此方案十分不靠谱，于是乎就像自己写个。

一次偶然的机会，发现了有道这个靠谱的工具提供了十分方便的API可供调用，就花了一点时间，写了个Python版的~。

有道的数据接口如下：

```html
http://fanyi.youdao.com/openapi.do?keyfrom=<keyfrom>&key=<key>&type=data&doctype=<doctype>&version=1.1&q=要翻译的文本
```

> 版本：1.1，请求方式：get，编码方式：utf-8  
> 主要功能：中英互译，同时获得有道翻译结果和有道词典结果（可能没有）  
> 参数说明：  
> 　type - 返回结果的类型，固定为data  
> 　doctype - 返回结果的数据格式，xml或json或jsonp  
> 　version - 版本，当前最新版本为1.1  
> 　q - 要翻译的文本，不能超过200个字符，需要使用utf-8编码  
> errorCode：  
> 　0 - 正常  
> 　20 - 要翻译的文本过长  
> 　30 - 无法进行有效的翻译  
> 　40 - 不支持的语言类型  
> 　50 - 无效的key  

详见[官网](http://fanyi.youdao.com/openapi?path=data-mode)

Python实现的代码如下：

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import sys
import json

green = '\033[0;32m%s\033[0m: \033[0;34m%s\033[0m'

opener = urllib2.build_opener()
msg = sys.argv[1]
url_utf = 'http://fanyi.youdao.com/fanyiapi.do?keyfrom=asdfksljl&key=908880018&type=data&doctype=json&version=1.1&q=' + msg 

result_json = opener.open(url_utf).read()
result = json.loads(result_json)

for tran in result['translation']:
    print green % (u'翻译', tran)

try:
    print u'读音: ' + result['basic']['phonetic']
except:
    pass
try:
    for explain in result['basic']['explains']:
        print u'解释: ' + explain
except:
    pass

try:
    for web in result['web']:
        value_str = ''
        for value in web['value']:
            value_str += value + ', '
        print u'[' + web['key'] + '] ' + value_str
except:
    pass
```

或见[Gist](https://gist.github.com/zqqf16/5610235)

把上面的脚本命名为“t”，放在`~/bin`下，需要翻译的时候打开终端输入`t 文本`即可~

![图片](/static/img/youdao-translation.png)

PS: 用的时候最好自己去申请一个Key~
