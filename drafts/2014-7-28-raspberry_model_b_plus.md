---
layout: post
title: 树莓派 Model B+ 入手小记
date: 2014-7-28
tags: 树莓派
---


在买树莓派之前，我认为比较理想的板子是这样的：

1. 性能强
2. 兼容性强，可支持的系统比较多，外设驱动完善
3. 有 SATA，读写速度快
4. 功率小，省电
5. 社区支持完善

前后考虑了多款板子，包括 Cubieboard、Bananapi、Radxa 以及刚刚开始预定的 HummingBoard。

Cubieboard 社区比较完善，有 SATA，兼容性好，性能稍强。Bananapi 可以看做一个有 SATA 的树莓派。Radxa 性能强悍，没有 SATA，但社区支持太差了。HummingBoard 刚开始预订，性能强悍，有 SATA，但社区及兼容性未知。

后来我明确了一下需求，发现对硬件的要求远远小于软件，这种板子玩的就是可玩性。正好赶上树莓派 Model B+ 发布了，虽然 CPU 和内存的参数还是那么可怜，但是电器性能提升不少。于是果断出手。（感谢伟大的淘宝，在官方发布一周之后就有货了）

开箱照：

![开箱照](https://z_blog.oss-cn-hangzhou.aliyuncs.com/blog/IMG_0735.JPG?x-oss-process=style/jpg)

到手时候发现树莓派是真的小，比图片看上去小多了。板子整体感觉就是金属部件都比较亮，应该是有电镀层。由于刚刚发布不就，可以保证是百分百英国原厂~

找了一个老掉牙的 8G TF 卡，刷上 Debian，开机启动：

![工作照](https://z_blog.oss-cn-hangzhou.aliyuncs.com/blog/IMG_0737.JPG?x-oss-process=style/jpg)

进行完一些设置之后就进桌面了，第一感觉是还算流畅，至少鼠标右键没有卡顿。但是由于 CPU 以及 TF 卡太烂，每打开一个程序都需要加载半天。CPU 占用率也是忽上忽下，打开浏览器轻轻松松百分之百~

这里不得不提的一点，我插上了一个两三年前的 USB 无线网卡，竟然原生支持！兼容性的好处体现的淋漓尽致。

好了，就这么多了，我要开始我的树莓派之旅了~