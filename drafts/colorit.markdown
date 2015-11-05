---
title: Colorit——一个给终端输出上色的工具
date: 2013-11-12
tags: python
---

平时自己写脚本的时候总喜欢给输出信息加点颜色，比如之前写的查找CVS diff中改动文件的[脚本](https://gist.github.com/zqqf16/7094628)。方法很简单，就是输出一些ASCII控制码，比如`\033[;31m`代表红色之类的。

用的多了，感觉老是拼字符串也不是个办法，索性规整了一下，写了人生中第一个正经的python模块。。。

```python
#!/usr/bin/env python
#-*- coding: utf-8 -*-

from __future__ import print_function

__all__ = ['paint', 'colors', 'attributes']
__version__ = '1.0'

_FORMAT = '\033[{}m\033[{};{}m{}\033[0m'

colors = ['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white']
attributes = ['blod', 'underscore', 'blink', 'reverse', 'concealed']

_FOREGROUND = dict(zip(colors, list(range(30, 38))))
_BACKGROUND = dict(zip(colors, list(range(40, 48))))
_attributes = dict(zip(attributes, [1, 4, 5, 7, 8]))

def paint(foreground, background=None, attribute=None):
    fg = _FOREGROUND.get(foreground, 39)
    bg = _BACKGROUND.get(background, 49)
    att = _attributes.get(attribute, 0)

    return lambda s: _FORMAT.format(att, bg, fg, s)

if __name__ == '__main__':
    def print_row(b):
        for f in colors:
            p = paint(f, b)
            print(p('{:^8}'.format(f)), end=' ')
        print('')

    print_row(None)
    for b in colors:
        print_row(b)
```

用的时候也很方便：

```python
p = paint(foreground, background=None, attribute=None)
p(string)
```

比如输出字体为绿色，背景为黄色的文字：

```python
p = paint('green', 'yellow')
print(p('Hello World'))
```

可以访问我的[Github](https://github.com/zqqf16/colorit)查看完整代码。

最后，附一张完整的颜色图（`python colorit.py`）：

![colors](https://raw.github.com/zqqf16/colorit/master/examples/all.png)
