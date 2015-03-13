title: 谈谈 iOS8 中的 Network Extension
tag: iOS8
tag: Network Extension
date: 2014-10-14

> 由于工作原因，对 iOS 的 VPN 方面比较关心，于是基本上就在第一时间发现并研究了 Network Extension（以下简称 NE）。

## 介绍

NE 向应用开放了 VPN（Personal VPN）的权限，开发者可以创建、修改、删除 VPN 配置，启动、停止 VPN，以及获取 VPN 状态等。目前只支持 IPSec 和 IKEv2。

可能是 NE 的受众太小，只有我们这样的厂商才会关心，所以 Apple 连个官方文档头没提供，目前所能掌握的东西只有头文件里的注释。

推荐读者在看这篇文章之前先阅读一篇外国友人写的[教程](http://ramezanpour.net/post/2014/08/03/configure-and-manage-vpn-connections-programmatically-in-ios-8/)，他把步骤描述的很详细，基本上照着一步步做就行了。我当时也是看了这篇文章，然后根据自己摸索才弄明白的。这里只点出需要注意的重点。

## 准备工作
你需要 Enable App ID 中的 “VPN Configuration & Control”，然后在应用的 “Capabilities” 中打开 “Personal VPN”，这时候 Xcode 会完成一些初始化工作。

最后，链接上 “NetworkExtension.framework”，然后在代码里`#import <NetworkExtension/NetworkExtension.h>`就 OK 了。

## 工作流程

NE 的工作流程基本上分为以下几步：

**加载系统配置**

这步很重要，初次操作 NE 时一定别忘了先加载，否则将会出现一些莫名其妙的问题。

```objective-c
// init VPN manager
self.vpnManager = [NEVPNManager sharedManager];

// load config from perference
[_vpnManager loadFromPreferencesWithCompletionHandler:^(NSError *error) {
    // Do something
}];
```

这里需要说明一下，NE 需要给系统安装一个配置文件（类似于 mobileconfig）才能工作，应用在退出后可以在系统设置的 VPN 选项中手动开启 VPN。这个配置文件和 NEVPNManager 是不会自动同步的，也就是说每次操作 NEVPNManager，都必须先从配置文件加载内容，如果做了修改，一定要记得保存。

而且，如果手动在系统设置里面把配置文件删除，NEVPNManager 的内容还是会存在的。所以，每次启动 VPN 之前都应该加载一下配置，确保配置文件存在。

**添加或修改 IPSec 或 IKEv2 配置信息（以 IPSec 为例）**

```objective-c
// config IPSec protocol
NEVPNProtocolIPSec *p = [[NEVPNProtocolIPSec alloc] init];
p.username = @"[Your username]";
p.serverAddress = @"[Your server address]";;

// get password persistent reference from keychain
p.passwordReference = [self searchKeychainCopyMatching:@"VPN_PASSWORD"];

// PSK
p.authenticationMethod = NEVPNIKEAuthenticationMethodSharedSecret;
p.sharedSecretReference = [self searchKeychainCopyMatching:@"PSK"];

/*
// certificate
p.identityData = [NSData dataWithContentsOfFile:[[NSBundle mainBundle] pathForResource:@"client" ofType:@"p12"]];
p.identityDataPassword = @"[Your certificate import password]";
*/

p.localIdentifier = @"[VPN local identifier]";
p.remoteIdentifier = @"[VPN remote identifier]";

p.useExtendedAuthentication = YES;
p.disconnectOnSleep = NO;
```

上面的代码应该放到`loadFromPreferencesWithCompletionHandler`的 block 中执行，这样可以确保系统配置已经加载完成。

IPSec 协议里的密码以及预共享密钥都需要是一个 KeyChain 中密码的永久引用（persistent reference）。

如果用证书来作为 IKE 的认证方式，而且 Server 端用的是自签发证书，则需要手工将 CA 导入到 iOS 设备。目前 Apple 还没提供添加授信证书的方法。

**保存配置**

```objective-c
[_vpnManager saveToPreferencesWithCompletionHandler:^(NSError *error) {
        NSLog(@"Save config failed [%@]", error.localizedDescription);
}];
```

**启动 VPN**

```objective-c
NSError *startError;
[_vpnManager.connection startVPNTunnelAndReturnError:&startError];
if (startError) {
    NSLog("Start VPN failed: [%@]", startError.localizedDescription);
}
```

根据目前的测试结果来看，`startVPNTunnelAndReturnError`只会在配置有误的时候才会返回 Error。其他时候，比如协议协商失败、连接超时等系统都会直接弹出对话框。

## 坑

由于没有官方文档说明，不知道是调用方式不对还是 NE 本身不稳定，开发过程中遇到了很多大坑：

1. 上面提到的，系统配置文件和 NEVPNManager 内容不同步，需要监听 “NEVPNConfigurationChangeNotification” 消息。
2.  NEVPNManager 的操作基本上都是异步的，改配置时必须确保 load 完成，启动 VPN 时必须确保 save 完成。
3.  有时候创建、保存配置一切正常，但是启动时就会提示 “未知错误”。这时候需要在系统设置里面手动启动一次 VPN，然后程序就可以正常启动了……有时候手动启动也不成，那就得把配置文件删除，然后重新安装……
	
	> 2015-3-13 更新解决方法：
	>
	> 在调用 NEVPNManager 的 `saveToPreferencesWithCompletionHandler` 方法前，应将它的 `enabled` 属性置成 “YES”。

4.  配置 IPSec 协议时，密码相关的（证书密码除外）必须得是 KeyChain 的永久引用，即`kSecReturnPersistentRef`需要是 YES。
5.  获取 VPN 状态时，NEVPNConnection 的 status 属性是不支持 KVO 的，需要监听 “NEVPNStatusDidChangeNotification” 事件。这点应该是 By-design 的，但是这个问题当时困扰我很久……

## 完整代码

上文提到的国际友人曾经遇到了一些问题（可以查看他文章下面的评论），这种问题基本上是因为坑#2 导致的。为了向他解释我的代码没问题，我根据他的代码写了一个简单的 Demo。没写全，但是基本可用。我这一切正常，他说他复制过去还有问题……

> **2014-12-19 更新**
> 
> 如果`localIdentifier`和`remoteIdentifier`设置的不对也可能导致这个问题。我测试的 IPSec 服务端把这两个字段去掉了，所以一直没注意~

*以下代码来自 Gist，需自备梯子～*

<script src="https://gist.github.com/zqqf16/cbcbd2254e6cb965f1a3.js"></script>
