---
layout: post
title: 在 macOS 上编译 libimobiledevice
date: 2018-8-22
tags:
    - iOS
    - libimobiledevice
excerpt: 编译 libimobiledevice 以及静态库，修复 OpenSSL could not be found 问题。
---

## 前言

最近给 [SYM](http://github.com/zqqf16/SYM) 添加了一个新功能：可以直接导入 iOS 设备上的崩溃日志，这个功能是通过 libimobiledevice 实现的。编译静态库的过程中踩了一些坑，在这里记录一下。

## 编译步骤

### 准备工作

**安装编译工具**

```shell
brew install automake autoconf libtool
```

**安装依赖库**

```shell
brew install libplist usbmuxd
```

### 准备 OpenSSL

如果不想用 libimobiledevice 的库，而是直接用编译好的可执行文件，OpenSSL 可以省略，用  GnuTLS 代替。详见[官方文档](https://github.com/libimobiledevice/libimobiledevice)。

用 OpenSSL 的好处是集成到其它 App 时，可以直接用 OpenSSL 的库，GnuTLS 的库怎么用还没研究……

**下载 OpenSSL 代码**

```shell
wget https://www.openssl.org/source/openssl-1.0.2p.tar.gz -O openssl.tar.gz
tar vzxf openssl.tar.gz
cd openssl-1.0.2p
```

**编译 **

```shell
./Configure darwin64-x86_64-cc
```

如果需要指定支持的 macOS 最小版本，可以这样：

```shell
./Configure darwin64-x86_64-cc -mmacosx-version-min=10.11
```

这样可以避免集成到 App 时 Xcode 的 warning。

**创建 pc 文件**

```shell
touch openssl.pc
```

写入以下内容：

```
prefix=/path/to/your/openssl-1.0.2p
exec_prefix=${prefix}
libdir=${exec_prefix}/lib
includedir=${prefix}/include

Name: OpenSSL
Description: Secure Sockets Layer and cryptography libraries and tools
Version: 1.0.2p
Requires: libssl libcrypto
```

**添加 pkg-config 路径**

```shell
export PKG_CONFIG_PATH=/path/to/your/openssl-1.0.2p
```

这一步是为了 pkg-config 能够索引到刚才编译的 OpenSSL。

### 编译 libimobiledevice

**下载 libimobiledevice 代码**

```shell
wget https://github.com/libimobiledevice/libimobiledevice/archive/master.zip -O libimobiledevice.zip
unzip libimobiledevice.zip
cd libimobiledevice-master
```

**配置 & 编译**

```shell
./autogen.sh
make
```

如果需要指定 macOS 的最小版本，可以这样：

```shell
make CFLAGS='-g -O2 -mmacosx-version-min=10.11' CXXFLAGS='-g -O2 -mmacosx-version-min=10.11'
```

## 集成

libimobiledevice 的库在 `libimobiledevice-master/src/.libs` 目录下，比如静态库是 **libimobiledevice.a**。头文件在 `libimobiledevice-master/include` 目录

OpenSSL 的库在 `openssl-1.0.2p` 目录下，静态库是 **libcrypto.a** 和 **libssl.a**。头文件在 `openssl-1.0.2p/include` 目录。

如果集成到 App，还需要 [**libplist**](https://github.com/libimobiledevice/libplist) 以及 [**libusbmuxd**](https://github.com/libimobiledevice/libusbmuxd) 两个库，可以直接用 brew 安装的那个，或者也可以自己编译，步骤与编译 libimobiledevice 类似，但是要简单很多，不依赖 OpenSSL。

最后，欢迎体验最新版本的 [SYM](https://github.com/zqqf16/SYM/releases/latest)。

-EOF-