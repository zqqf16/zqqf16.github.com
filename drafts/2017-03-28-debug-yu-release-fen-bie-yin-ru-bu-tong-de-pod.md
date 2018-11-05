---
layout: post
title: Debug 与 Release 分别引入不同的 Pod
date: 2017-03-28
tags: 
    - Xcode Tips
---

有时候会碰到这样的情况，一个以二进制形式分发的 Pod，需要区分 Debug 与 Release 环境，比如 Debug 不加密、Release 加密。
在上家公司，遇到这种情况会做两个静态库，一个叫 xxx.a，另一个叫 xxx_dev.a。开发或者测试的时候手动切换。

其实，CocoaPods 本身有更好的解决方法。

假设要做一个叫 Foo 的 pod，以 Framework 的形式分发，可以写两个 Podspec 文件：


```ruby
# FooDebug.podspec

Pod::Spec.new do |s|
  s.name = 'FooDebug'
  s.ios.vendored_frameworks = 'Debug/Foo.framework'

  # ...
end
```

```ruby
# FooRelease.podspec

Pod::Spec.new do |s|
  s.name = 'FooRelease'
  s.ios.vendored_frameworks = 'Release/Foo.framework'

  # ...
end
```

两个不同名字的 Pod，但是 **framework 的名字是一样的**，分别在 Debug 与 Release 目录下。

在主工程 Bar 的 Podfile 里，这样写：

```ruby
pod 'FooDebug', :git => 'https://xxx/xxx/foo.git', :configurations => ['Debug']
pod 'FooRelease', :git => 'https://xxx/xxx/foo.git', :configurations => ['Release']
```

这样，在 Debug 与 Release 下，会分别引用 FooDebug 与 FooRelease 了。

同时，由于 framework 的名字是相同的，所以在代码里引入头文件时诸如 `#include <Foo/Foo.h>` 这样的写法不受影响。