title: ProxyChains 及其原理
date: 2015-6-25
tag: 链接

## 前言

Shadowsocks 是一个非常好用的 SOCKS 代理程序，尤其在 Mac 上，基本上只要支持系统代理的应用都直接可以一键爬墙了。

但是有些底层的应用，比如那些传统的 Unix 命令行工具，就不会搭理系统的代理了，甚至绝大多数压根就不支持 SOCKS 代理。

以前，我一般都会用 L2TP 或 IPSec 这样的底层 VPN 来搞定，不仅麻烦，而且越来越不稳定（原因你懂的……）。

直到后来发现了 ProxyChains。

## 安装以及使用

ProxyChains 的项目地址在 [Github](https://github.com/rofl0r/proxychains-ng)

在 Mac 下安装十分简单：

```bash
brew install proxychains-ng
```

然后编辑配置文件 **/usr/local/etc/proxychains.conf**，在末尾加上：

``` conf
# Shadowsocks
socks5 127.0.0.1 1080
```

> 2015-9-15 更新
>
> OS X El Capitan v10.11 之后，Apple 推出了一个叫 **System Integrity Protection** 的新功能：
> > A new security policy that applies to every running process, including privileged code and code that runs out of the sandbox. The policy extends additional protections to components on disk and at run-time, only allowing system binaries to be modified by the system installer and software updates. **Code injection and runtime attachments to system binaries are no longer permitted**.

> 如果开启了 SIP，可能导致 ProxyChains 失效。解决方法是进入 Recovery 模式，在终端执行 `csrutil disable`，禁止 SIP。
>
> 其中的风险请自行判断:-)

使用方法也很简单，比如 ping：

```bash
$ proxychains4 ping -c 2 www.google.com
[proxychains] config file found: /usr/local/Cellar/proxychains-ng/4.7/etc/proxychains.conf
[proxychains] preloading /usr/local/Cellar/proxychains-ng/4.7/lib/libproxychains4.dylib
[proxychains] DLL init
PING www.google.com (216.58.221.132): 56 data bytes
64 bytes from 216.58.221.132: icmp_seq=0 ttl=41 time=65.601 ms
64 bytes from 216.58.221.132: icmp_seq=1 ttl=41 time=66.572 ms

--- www.google.com ping statistics ---
2 packets transmitted, 2 packets received, 0.0% packet loss
round-trip min/avg/max/stddev = 65.601/66.087/66.572/0.486 ms
```

当然，需要先启动 Shadowsocks。

## 原理

在其主页上，它是这样描述的：

> proxychains ng (new generation) - a preloader which hooks calls to sockets in dynamically linked programs and redirects it through one or more socks/http proxies. continuation of the unmaintained proxychains project.

简单的说就是这个程序 Hook 了 sockets 相关的操作，让普通程序的 sockets 数据走 SOCKS/HTTP 代理。

其核心就是利用了 **LD\_PRELOAD** 这个环境变量（Mac 上是 **DYLD\_INSERT\_LIBRARIES**）。

在 Unix 系统中，如果设置了 LD\_PRELOAD 环境变量，那么在程序运行时，动态链接器会先加载该环境变量所指定的动态库。也就是说，这个动态库的加载优先于任何其它的库，包括 libc。

ProxyChains 创建了一个叫 libproxychains4.so（Mac 上是 libproxychains4.dylib）的动态库。里面重写了 `connect`、`close` 以及 `sendto` 等与 socket 相关的函数，通过这些函数发出的数据将会走代理，详细代码可以参考 libproxychains.c。

在主程序里，它会读取配置文件，查找 libproxychains4 所在位置，把这些信息存入环境变量后执行子程序。这样子程序里对 socket 相关的函数调用就会被 Hook 了，对子程序来说，跟代理相关的东西都是透明的。

可以用 printenv 程序来查看增加的环境变量，在 Mac 上，输出结果类似于：

```bash
$ proxychains4 printenv
[proxychains] config file found: /usr/local/Cellar/proxychains-ng/4.7/etc/proxychains.conf
[proxychains] preloading /usr/local/Cellar/proxychains-ng/4.7/lib/libproxychains4.dylib
[proxychains] DLL init
...
PROXYCHAINS_CONF_FILE=/usr/local/Cellar/proxychains-ng/4.7/etc/proxychains.conf
DYLD_INSERT_LIBRARIES=/usr/local/Cellar/proxychains-ng/4.7/lib/libproxychains4.dylib
DYLD_FORCE_FLAT_NAMESPACE=1
```

一共设置了三个环境变量，其中 **PROXYCHAINS\_CONF\_FILE** 保存的是配置文件路径，**DYLD\_INSERT\_LIBRARIES** 保存的是动态库路径，在 Mac 中，必须使**DYLD\_FORCE\_FLAT\_NAMESPACE** 为 1 才能保证 **DYLD\_INSERT\_LIBRARIES** 起作用。

其实还有个一劳永逸的方法：

手动设置这三个环境变量

```bash
$ export PROXYCHAINS_CONF_FILE=/usr/local/Cellar/proxychains-ng/4.7/etc/proxychains.conf
$ export DYLD_INSERT_LIBRARIES=/usr/local/Cellar/proxychains-ng/4.7/lib/libproxychains4.dylib
$ export DYLD_FORCE_FLAT_NAMESPACE=1
```

这样在当前 shell 中运行的所有程序的网络请求都会走代理了。


## 参考链接

1. [警惕 UNIX 下的 LD_PRELOAD 环境变量](http://blog.csdn.net/haoel/article/details/1602108)
2. [利用 LD_PRELOAD 进行 hook](http://hbprotoss.github.io/posts/li-yong-ld_preloadjin-xing-hook.html)
3. [Mac 下安装及配置 ProxyChains-NG 实现终端下代理](http://www.dreamxu.com/proxychains-ng/)
4. [dyld - the dynamic link editor](https://developer.apple.com/library/mac/documentation/Darwin/Reference/ManPages/man1/dyld.1.html)
