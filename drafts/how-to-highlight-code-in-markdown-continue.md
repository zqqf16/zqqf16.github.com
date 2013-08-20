title: 高亮Markdown中的代码（续）
date: 2013-8-20
tag: python
     markdown

之前写过一篇文章（[高亮Markdown中的代码](/posts/how-to-highlight-code-in-markdown.html))，介绍了python-markdown2中高亮代码的方法。后来在使用中我发现了一个`fenced code blocks`的bug，如果代码中间有空行，它会把换行之后的部分当成嵌套的。生成的文件中会有一堆类似这样的部分：

```html
<span class="k">class</span> <span class="nc">
```

后来到其Github上一搜，发现很多人都有类似问题，比如[这里](https://github.com/trentm/python-markdown2/issues/109)。也有人给出了[解决方案](https://github.com/trentm/python-markdown2/pull/117)。

但是这个Pull request已经提出4个月了，原作者至今没有通过，而且整个代码也有近1年没有动过了。Clone了一份它的代码，发现如果想自定义扩展的话比较困难。无奈之下从新研究起了曾经被我抛弃的Python-Markdown。结果发现原来它也有很多扩展，而且比Markdown2中的更多。更重要的是提供了扩展的接口，很方便地写自己的扩展。于是就在peanut中替换了markdown2，代码如下：

```python
md = markdown.Markdown(extensions=['fenced_code', 'codehilite', 'meta'])
#do something
html = md.reset().convert(content.strip(' \n'))
```

`fenced_code`用来识别

	```python
	```

这样的代码段，`codehilite`用来高亮代码，`meta`用来识别文章信息，比如：

	title: 高亮Markdown中的代码（续）
	date: 2013-8-20
	tag: python
         markdown

过度完毕，问题搞定~