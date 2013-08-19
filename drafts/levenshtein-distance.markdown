title: Levenshtein distance（编辑距离）算法
date: 2013-8-2
tag: Levenshtein distance

在用Git的时候，如果一不小心把命令参数输入错了，比如把`show`写成了`slow`，Git会进行有好的提示：

```bash
$git slow
git: 'slow' is not a git command. See 'git --help'.

Did you mean this?
    show
```

一直很好奇这是基于什么算法找出来的相思结果，Google了一番，发现了一个NB的算法——Levenshtein distance，中文名叫“编辑距离”。关于这个算法的具体信息，可以参照[维基百科](http://en.wikipedia.org/wiki/Levenshtein_distance)。在这我就做个概述。

这个算法是用来计算两个字符串之间的不同的，就是把一个字符串A通过一些列变换（插入、删除、替换）得到字符串B的最少步骤。可以用来做拼写检查、DNA匹配等。

算法的基本原理就是中学时代就学过的动态规划。（太久没有接触数学了，遇到这个问题时还去查了很久的动态规划。。。）

这个算法的巧妙之处（至少是我认为）是用了一个矩阵来辅助计算。当时看到这个矩阵的时候深深地被震撼到了，看了两天愣是没弄明白。一开始打算找点汉语资料研究一下，结果发现网上的都是半吊子货，于是重新拾起Wikipedia，硬着头皮终于弄明白了。

鉴于解释这个算法需要画图，我也没个好用的工具，就放弃了。如果不明白，强烈建议看Wikipedia。结合推导公式和矩阵图，应该不难明白。

有个外国哥们基于这个算法又改进了一下，在原有的三种操作（插入、删除、替换）中又增加了一种“交换”，这对于拼写检查之类的还是很有用的。这种改进后的算法又叫[Damerau–Levenshtein distance](http://en.wikipedia.org/wiki/Damerau–Levenshtein_distance)。Git源码里就是采用的这种算法，具体代码可以查看[这里](https://github.com/git/git/blob/master/levenshtein.c)。需要注意的是，Git中把4中操作都加上了权值，这样更灵活一些。

为了更好的理解这个算法，我自己也基于Python实现了一下，代码放在了Gist上，可以访问[这里](https://gist.github.com/zqqf16/6137789)。PS：只是为了描述一下算法，并没有过多地考虑效率问题。

