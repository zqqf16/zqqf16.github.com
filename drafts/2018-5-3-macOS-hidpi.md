---
layout: post
title: 修复 macOS 不支持某些屏幕 HiDPI 显示的方法
date: 2018-5-3
tags:
    - macOS
image:
    feature: https://z_blog.oss-cn-hangzhou.aliyuncs.com/blog/IMG_0618.JPG?x-oss-process=style/jpg
excerpt: >
    macOS 的 HiDPI 显示模式对很多显示器的支持都有问题，有些屏幕即使是自家的（比如 iPad 屏），也死活不能完美地支持。
---

## 起因

多年前，高价搞到了一块 iPad5 屏幕的驱动版，想用一个二手的 iPad5 显示屏做一个 Macbook 的移动显示器。屏幕的分辨率是 2048x1536，HiDPI 模式下也就是 1024x768。买的时候没想那么多，想当然地认为既然 iOS 都支持这个分辨率，macOS 自然不再话下。

然而事情并非如此，严重低估了 BugOS 的实力，屏幕插上之后，系统能识别出屏幕型号：Apple，但是死活不能支持 1024x768 HiDPI，甚至更奇葩的是，各种其他分辨率下的 HiDPI 都支持，唯独不支持正常的。当时试尽了各种方法，改 Plist，SwitchResX 等等，最终无功而返。反而 Window 10 支持得特别好，这个显示器后来只能作为我的台式机专用了。

## 转机

后来在逛淘宝的时候，发现现在市面上的 HDMI 转 edp 驱动版已经很成熟了，一块驱动板加一个 13 寸的 2k 屏也很便宜，于是“贼心”不死打算再试一把。

新买的屏幕是 2560x1440 分辨率的，转成 HiDPI 也就是 1280x720。然而，bugOS 问题依旧，死活不支持 1280x720 HiDPI ……

后来偶然间搜到了一个帖子：[Make 1280×720 HiDPI Work on a 16:9 WQHD Display](http://blog.thefelt.net/make-1280x720-hidpi-work-on-a-169-wqhd-display/)，里面提到了一个解决方法，把分辨率设置成 2558x1440，也就是 HiDPI 下的 1279x720，问题果然得到了解决……当时心中大概奔腾过了一万只草泥马……

后来又用这个方法，把 iPad 拿块屏的分辨率改成了 2046x1534（1023x767 HiDPI），果然也好用了……

不得不感叹 macOS 的神奇逻辑

## 后来

发现市面上 3D 打印的价格已经很便宜，当年设计了一个外壳，淘宝询价要 800+，现在同样的外壳大概只要 150 不到。于是就兴高采烈地去淘宝打印了外壳，拿回来给 iPad 屏幕组装上，开机，发现屏幕碎了……

所以，DIY 这个显示器的整个过程中，唯一的收获就是 macOS 如果不支持某些分辨率下的 HiDPI，不妨把分辨率改小2像素试试～

-EOF-