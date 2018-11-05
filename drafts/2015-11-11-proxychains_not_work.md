---
layout: post
title: OS X 上 ProxyChains 失效的原因
date: 2015-11-11
tags: ProxyChains
excerpt: 分析了几种可能导致在 OS X 上 ProxyChains 失效的原因，并提供了几条解决方案。
---


最近遇到很多同学反应 ProxyChains 失效的问题，于是就花了点时间研究了一下。

排除配置错误以及 SOCKS 代理本身的问题，在 OS X 10.11 上，最大的可能就是[前一篇文章](proxychains.html)中说的 SIP。摘录 [Wikipedia](https://en.wikipedia.org/wiki/System_Integrity_Protection) 上面的一段话：

> The kernel stops all processes without specific privileges from writing to flagged files and folders and prevents **code injection** and runtime attachment (like debugging) with respect to flagged processes or processes signed with an Apple private entitlement key

其次，就是 dyld 了，前面说过，ProxyChains 是基于 **DYLD\_** 环境变量的，dyld 在链接动态库的时候会进行一些条件判断，并不是每个应用都允许有 DYLD\_。

``` c
switch (sRestrictedReason) {
    case restrictedNot:
        break;
    case restrictedBySetGUid:
        dyld::log("main executable (%s) is setuid or setgid\n", sExecPath);
        break;
    case restrictedBySegment:
        dyld::log("main executable (%s) has __RESTRICT/__restrict section\n", sExecPath);
        break;
    case restrictedByEntitlements:
        dyld::log("main executable (%s) is code signed with entitlements\n", sExecPath);
        break;
}
```

*注：以上代码来自 [dyld.cpp](http://www.opensource.apple.com/source/dyld/dyld-353.2.3/src/dyld.cpp)*

从上面这段 dyld 注释的 log 相关代码来看，以下三种情况会清空 DYLD\_ 环境变量：

1. 可执行程序被设置了 **setuid** 或 **setgid** 权限
2. 可执行文件中存在 **\_\_RESTRICT,\_\_restrict** 这个段
3. 应用程序被 **entitlements** 签过名

第一点很好理解，毕竟是为了安全，比如 “sudo”、“passwd” 这样的程序肯定是要保护的。

第二点玩 iOS 越狱开发的应该很熟悉，很多讲 iOS 安全的都会建议在 Xcode 的 “Other Linker Flags” 中加上这样一行：

`-Wl,-sectcreate,__RESTRICT,__restrict,/dev/null`

目的就是在生成的可执行文件中插入一个空的  **\_\_RESTRICT,\_\_restrict** 段，这样就能在越狱的设备上阻止一部分恶意 Hook 了。

第三点暂时还没研究。

所以，在遇到 ProxyChains 不好使的时候，应该：

1. 如果是 OS X 11.11，并且可执行文件在 **/System**、 **/bin**、 **/sbin**、**/usr** 这些目录中，先看一下 SIP 关闭没。
   
2. 看一下可执行文件属性，如果有 **setuid** 或 **setgid** 权限，那就放弃吧，安全第一。
   
3. 看一下可执行文件中是否有 **\_\_RESTRICT,\_\_restrict**，如果有，而且十分想用，那么用二进制编辑器打开，把这个段改个名吧。（如果被签名了那就算了）
   
4. entitlements 签名我也不知道怎么看。
   
5. 换一下程序执行思路
   
    比如: `sudo pip install xxx`
   
    如果这样执行：`proxychains sudo pip install xxx`，肯定不行，因为 sudo 有 setuid，所以 DYLD\_ 环境变量传到这就丢掉了。
   
    应该这样：`sudo proxychains pip install xxx`，让 pip 作为 proxychains 的直接子进程。

另外，关闭 SIP 有潜在的风险，需谨慎。