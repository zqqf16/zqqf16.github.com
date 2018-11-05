---
layout: post
title: 高亮Markdown中的代码
date: 2013-4-26
tags: python
---


Markdown语法标准中并没有一种方法来标明代码语言的种类。所以要想用Javascript来进行代码高亮的话就需要手动加一些类似于`<code class="python">`的HTML标签，显得十分Ugly。

于是乎想从Server端入手，想到了Pygments这个神器。但问题又来了。。。

初步打算用

    ```python
    print 'hello'
    ```

这样的方式来指明代码种类。先把代码段用正则匹配出来，根据语言种类调用Pygments进行着色。然后再把其它部分连同着色后的的代码段一起Markdown转换。

后来越想越觉得不太靠谱，还是有点Ugly。

于是乎继续Google，终于发现了一个完美的方法，并对Markdown2刮目相看。

一直用Markdown2这个Python写的解释器来转换Markdown脚本，之前光看名字还觉得这玩意是个山寨货。今天研究发现，这货还挺好用。

Markdown2提供了一个代码高亮的扩展：[fenced code blocks](https://github.com/trentm/python-markdown2/wiki/fenced-code-blocks), 它能自动匹配这样的代码，并调用Pygments进行着色。

    ```python
    print "hi"
    ```

使用方法也很简单：

```python
html = markdown2.markdown("some markdown", ..., extras=["fenced-code-blocks"])
```

问题圆满解决~

更多Markdown2扩展请参考[Wiki](https://github.com/trentm/python-markdown2/wiki/Extras)