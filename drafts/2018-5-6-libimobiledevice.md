---
layout: post
title: 安利一套iOS开发工具-libimobiledevice
date: 2018-5-6
tags:
    - iOS
    - libimobiledevice
excerpt: >
    libimobiledevice 是一个跨平台的连接 iOS 设备的软件库，基于它实现了一系列工具，可以极大地提高 iOS 开发效率
---

## 前言

公司项目大了之后，Xcode 调试控制台输出的内容已经被各种各样的东西冲得七零八落。有时候自己加的 log 还没看见就被冲没了，影响调试效率。

在 Xcode 还能支持插件的时代，可以用一些插件来过滤 log，但现在的版本已经不能用了。在搜索第三方 log 替代方案时，发现了 libimobiledevice。

## 简介

libimobiledevice 是一个跨平台的连接 iOS 设备的软件库，可以用来操作 iOS 设备，比如读取设备信息、读取设备日志、获取设备屏幕截图、浏览 Document 文件夹等功能。Appium、iTools 等工具也是基于这个库。

### 安装

`brew install --HEAD libimobiledevice`

`--HEAD` 是为了基于最新代码安装，libimobiledevice 需要随着 iOS 版本升级来做调整，需要保持最新。

### 使用

**实时查看系统日志**

`idevicesyslog`

由于 NSLog、DDlog 等默认会写到 iOS 系统日志里，所以这个工具可以用来实时查看调试日志。

可以跟 grep、awk、sed 等命令组合来添加过滤条件:

`idevicesyslog | grep your_app_name `

或者过滤掉一些乱七八糟的内容:

`idevicesyslog | grep -v xxx`

**获取设备截图**

`idevicescreenshot`

**查看设备信息**

`ideviceinfo`

**查看设备上已安装应用**

`ideviceinstaller -l`

**挂载应用的 Document 目录**

需要安装 ifuse

`brew cask install osxfuse ; brew install ifuse` 

创建挂载点

`sudo mkdir /Volumes/you_app_name.app`

挂载 App 目录

```shell
mkdir /tmp/you_app_id
ifuse --container you.app.id /tmp/you_app_id
```

`you.app.id` 可以通过 `ideviceinstaller -l` 得到，`-o allow_other` 可以让非 root 用户来访问。

打开目录

`open /tmp/you_app_id`

**其它**

libimobiledevice 提供了一些列 idevice 开头的工具，比如：

- idevice_id
- idevicedebug
- ideviceinfo
- idevicescreenshot
- idevicebackup
- idevicedebugserverproxy
- idevicename
- idevicesyslog
- idevicebackup2
- idevicediagnostics
- idevicenotificationproxy
- idevicecrashreport       
- ideviceenterrecovery
- idevicepair
- idevicedate
- ideviceimagemounter
- ideviceprovision

有兴趣的可以自己研究一下使用方法

-EOF-