title: 用Graphviz画数据结构图
date: 2013-5-16
tag: graphviz

近来上班研究前人代码，数据结构很是个复杂。笔和纸基本满足不了要求，所以研究了一下用Graphviz这个利器绘制数据结构图。

废话不多说，上代码：

```dot
digraph g {
	graph [ rankdir = "LR" ];
	node [shape = record];

	a [
		label = "<f> struct a|<f0> int i|<f1> char str[10]"
	];

	b [
		label = "<f> struct b|<f0> struct a *p|char name[100]"
	];

	"b":f0 -> "a":f;
}
```

把上述代码保存到`example.dot`，然后执行：`dot -Tpng example.dot -o example.png`

绘出的图如下：
![graph](/static/img/graphviz.png)

更多实例，请参考[Graphviz官网](http://www.graphviz.org/Gallery.php)
