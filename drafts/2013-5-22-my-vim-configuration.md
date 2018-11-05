---
layout: post
title: 我的Vim配置
date: 2013-5-22
tags:
    - vim-pathogen
    - github
    - vim
---


之前，我的Vim配置一直是通过Ubuntu One来保存和备份的。但是Ubuntu One的网络实在是不敢恭维，时好时坏。因此就在寻求一种比较靠谱的备份方式。

后来有一次在看别人博客的时候，发现了一个神器“vim-pathogen”。关于它的详细介绍我就不罗嗦了，下载及查看可以到[这里](https://github.com/tpope/vim-pathogen)。

用一句话概括就是它是管理Vim插件的插件。用它加上Github的配合，可以完美地实现配置备份。

**详细步骤**

- 在.vim下新建文件夹bundle，以后所有的插件都放到此目录。

- 添加pathogen插件：

```bash
git submoudle add git://github.com/tpope/vim-pathogen.git bundle/vim-pathogen
```

- 修改.vimrc，在开头加上  

```vim
" pathogen
runtime bundle/vim-pathogen/autoload/pathogen.vim
execute pathogen#infect()
```

- 以后如果需要增加插件，只需在bundle目录下加一个git的submoudle即可。升级插件可以用

```bash
git submodule foreach git pull origin master
```

- 可以在Github上新建个项目，把.vim目录下的所有内容提交上去，可以做到方便的更新与备份。

最后，大家可以参考一下我的vim配置：[Github](https://github.com/zqqf16/zqq-vim)

主要装了以下插件：

- Python的缩进插件：indent-python
- 深色养眼的主题：lucius
- 文件浏览插件：nerdtree
- 看代码神器：taglist
- powerline插件：vim-powerline

上一张截图![vim](/static/img/my-vim.png)

参考文章：[liluo.org](http://liluo.org/blog/2012/05/using-git-submodule-and-vim-pathogen-for-vim-configuraction-management/)