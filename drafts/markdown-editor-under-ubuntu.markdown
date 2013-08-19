title: Ubuntu下好用的Markdown编辑器
date: 2013-6-4
tag: markdown
tag: ubuntu
tag: retext

之前在Ubuntu下一直用Vim来编辑Markdown，纯英文还好，但是Vim里输入汉语实在是忒复杂了。

后来在Ubuntu软件中心里面搜"Markdown"，发现了一个不错的编辑器——ReText。

可以直接用apt-get来安装：

```bash
$ sudo apt-get install retext
```

在某些情况下，工具栏的图标显示不出来。后来搜到了这篇[文章](http://www.e0356.com/2013/02/242)，完美的解决了这个问题。

在Ubuntu下直接执行：

```bash
$ gsettings get org.gnome.desktop.interface icon-theme
```

我这显示的是'ubuntu-mono-dark'。

打开“～/.config/ReText\ project/ReText.conf”，加入

    iconThem=ubuntu-mono-dark
    
重新打开ReText就OK了~

![图片](/static/img/retext.png)
