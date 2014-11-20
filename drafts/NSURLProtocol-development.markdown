title: NSURLProtocol 开发笔记
date: 2014-11-1
tag: iOS
tag: NSURLProtocol

前一段时间一直在研究 iOS 应用内的 HTTP 代理问题，在 iOS 6之前可以用 [AppProxyCap](https://github.com/freewizard/AppProxyCap) 这样的 Hack 方法实现，但从 iOS7 开始就不能用了。

虽然 NSURLSession 提供了设置代理的方法，但是它只是针对单个 Session 的，没法实现全局的，尤其是 UIWebView 的代理。

无奈之下，只能选择 NSURLProtocol 这个不完美的实现方案了，为什么说它是不完美的，下文将有介绍。

raywenderlich.com 上有一篇详细的 NSURLProtocol [教程](http://www.raywenderlich.com/59982/nsurlprotocol-tutorial)，很好的讲解了它的用法。按照惯例我这里就不重复了，只说一下我做的工程中遇到的难点。

##原理

NSURLProtocol 可以用来处理自定义的 URL Scheme，或者是改写对已经存在的 Scheme 的处理方式。比如，我可以定义一个 URLProtocol 来处理“certificate://xxx.pem" 这样的 URL 请求，用来查找目录下的证书并返回。这样当我用 NSURLConnection 发送这样的请求的时候，得到的将是证书内容。再比如，我可以定义一个 URLProtocol 来处理发到后台 Server 的 HTTP 请求，把请求中的 user-agent 改成 Server 端能识别的形式。

NSURLProtocol 的作用是全局的，也就是说一旦注册之后，所有的 NSURLRequest （包括 UIWebView 发送的） 都会先经 URLProtocol 处理，这也就是为什么能用它来实现全局代理的原因（忽略掉 CFNetwork）。

用 NSURLPRotocol 来实现全局 HTTP 代理时，需要用自定义的 URLProtocol 来处理所有的 HTTP/HTTPS 请求，然后再用 NSURLSession 或者 CFNetwork 这样支持代理的库把请求通过 HTTP 代理转发出去，并把结果返回给上层调用者。（这个调用者在 NSURLProtocol 里就是`client`这个属性）

##为 NSURLSession 设置代理

为 NSURLSession 设置代理可以通过为其指定一个 NSURLSessionConfiguration 来实现，比如：

```objective-c
NSURLSessionConfiguration *configuration = [NSURLSessionConfiguration defaultSessionConfiguration];
configuration.connectionProxyDictionary =
@{(NSString *)kCFStreamPropertyHTTPProxyHost: @"127.0.0.1",
  (NSString *)kCFStreamPropertyHTTPProxyPort: @8080};
NSURLSession *session = [NSURLSession sessionWithConfiguration:configuration delegate:self delegateQueue:[NSOperationQueue currentQueue]];
```

这里有几点需要注意：

1. connectionProxyDictionary 字典的 Key 一定得正确，据我的搜索结果，网上很多例子都不对……其实这些 Key 可以从函数`CFNetworkCopySystemProxySettings()`返回的结果中获取。
2. `kCFStreamPropertyHTTPProxyPort`对应的 Value 类型一定得是 **NSNumber**，这是用大量时间换回来的教训……

**Authentication Challenge**

如果要发送的请求比较简单，不涉及到证书、用户认证等复杂情况，或者即使涉及到这些情况，但处理方式比较简单，在 URLProtocol 内部就可以处理时，NSURLProtocol 还算是比较完美的。但是一旦需求比较复杂，比如某些时候需要上层的代码来处理用户认证，这时候 NSURLProtocol 机制就不完美了，因为它做不到对上层调用者的透明。

用过 NSURLSession 的一般都明白，处理 Authentication 的 Challenge 可以在 NSURLSessionTaskDelegate 协议的`URLSession:task:didReceiveChallenge:completionHandler:`方法中做一些处理，之后调用 `completionHandler` 就可以了。

但是如果用了 NSRULProtocol，并且想要让上层代码来处理 Challenge 时就比较困难了。自定义的 URLProtocol 和它的上层调用者之间只能通过`NSURLProtocolClient`协议来通信。这个协议（`URLProtocol:didReceiveAuthenticationChallenge:
`）并没有实现将 `completionHandler` 传递过去的方法。这就导致上层调用者的 Challenge 处理方法（比如`connection:willSendRequestForAuthenticationChallenge:
`）在这种情况下是无效的。

因此，必须得用另外的方式解决 Challenge。

Apple 有个示例程序 [CustomHTTPProtocol](https://developer.apple.com/library/ios/samplecode/CustomHTTPProtocol/Listings/Read_Me_About_CustomHTTPProtocol_txt.html)，它的实现方式是为类对象（注意，是**类对象**）添加了代理。当 CustomHTTPProtocol 收到 Chellenge 时，会调用代理来完成进一步工作，然后再将结果返回给 CustomHTTPProtocol 实例，后者会调用`completionHandler`来发送结果。（这里涉及上下文切换，状态保存等，而且需要注意调用过程中的多线程问题，其代码中有比较详细的描述。）

NSURLProtocol 的实例化过程对开发者来说是不透明的，也就是说无法通过自定义代码控制，这也就是为啥 CustomHTTPProtocol 要为类对象实现代理。

但是问题又来了，如果遇到奇葩的情况，比如有些请求我想处理 Challenge，有请求又不想处理，该咋办捏？

这时候就应该祭出 NSURLProtocol 的`setProperty:forKey:inRequest:`方法了，这个方法可以为 URLRequest 设置一个属性，当处理 Challenge 时可以通过检查这个属性来判断是否需要处理。

先到这吧，如有问题再补充~

##参考链接

1. *AppProxyCap: [https://github.com/freewizard/AppProxyCap/issues/7](https://github.com/freewizard/AppProxyCap/issues/7)*
2. *NSURLProtocol Tutorial: [http://www.raywenderlich.com/59982/nsurlprotocol-tutorial](http://www.raywenderlich.com/59982/nsurlprotocol-tutorial)*
3. *CustomHTTPProtocol: [https://developer.apple.com/library/ios/samplecode/CustomHTTPProtocol/](https://developer.apple.com/library/ios/samplecode/CustomHTTPProtocol/Listings/Read_Me_About_CustomHTTPProtocol_txt.html)*
