---
layout: post
title: 在 Swift 中使用 QuickJS
date: 2021-12-21
tags:
    - swift
    - quickjs
excerpt: >
    在 Swift 项目中嵌入 QuickJS 引擎，实现 Swift 与 Javascript 代码的相互调用，并基于 NSRunloop 实现了 Javascript 的异步IO机制。
---

## 前言

去年用 Swift 写了一个处理日志的 macOS app，其中有个比较核心的功能，可以导入自定义脚本来过滤或者分析日志。
一开始选择的脚本语言是 Python，并且用 [PythonKit](https://github.com/pvieito/PythonKit) 实现了 Swift 与 Python 的集成。

但是，PythonKit [加载 Python 库](https://github.com/pvieito/PythonKit/blob/839ef68d9fe5c85ab212272fffbe54e229374d5c/PythonKit/PythonLibrary.swift#L98)的版本会跟当前系统相关。
比如，如果我的默认Pyhton版本是2.7，那么在我电脑上被加载的是2.7，而其他人电脑上可能就是3.x，这样就会导致处理日志的脚本做不到100%兼容各种环境。

因此决定引入 Javascript 作为替代的脚本语言，JS 引擎选择了一直想尝试的 [QuickJS](https://bellard.org/quickjs/)。

## 集成

QuickJS 的代码非常精悍，如果作为库来使用，核心的 C 文件只有5个(`quickjs.c`、`quickjs-libc.c`、`libregexp.c`、`libunicode.c`、`cutils.c`)，而且绝大多数代码都集中在`quickjs.c`、`quickjs-libc.c`这两个文件里。

编译条件也极其简单，不像传统的 C 语言工程，需要 `./configure` 或者安装一大堆依赖。把这几个文件拖到 Xcode 工程里，直接 Run 就能编过。

## 简单使用

启动一个 QuickJS 引擎步骤非常简单，大致分成以下几步：

1. 创建一个 **Runtime**：`JS_NewRuntime`
2. 创建一个 **Context**：`JS_NewContext`
3. 执行 JS 代码：`JS_Eval`

详细的例子可以参考 [qjsc.c](https://github.com/bellard/quickjs/blob/master/qjsc.c) 或者其它 demo。

## 封装

为了使上层使用起来更方便，我做了一个 Swift Package，把 C 语言接口包装成了更 Swift 的方式，代码在：https://github.com/zqqf16/QuickJS-Swift。

调用者只需要在你的 `Package.swift` 文件里加上

```swift
.package(url: "https://github.com/zqqf16/QuickJS-Swift.git", .branch("master")),
```

就可以了。

### Swift 调用 JS 代码

```swift
import QuickJS

let runtime = JSRuntime()!
let context = runtime.createContext()!

let jsCode = "var i = 10; i;"
let result = context.eval(jsCode).int
print("Result is \(result!)") //10
```

### 用 Swift 实现一个 Module

```swift
import QuickJS

let runtime = JSRuntime()!
let context = runtime.createContext()!

// Create a module named "Magic" with two functions "getMagic" and "getMagic2"
context.module("Magic") {
    JSModuleFunction("getMagic", argc: 0) { context, this, argc, argv in
        return 10
    }
    JSModuleFunction("getMagic2", argc: 0) { context, this, argc, argv in
        return 20
    }
}

let getMagic = """
"use strict";
import { getMagic, getMagic2 } from 'swift'
globalThis.magic = getMagic();
globalThis.magic2 = getMagic2();
"""

context.eval(getMagic, type: .module)

let magic = context.eval("magic;").int
print("Magic is \(magic!)") //10

let magic2 = context.eval("magic2;").int
print("Magic2 is \(magic2!)") //20
```

## Runloop

在 Nodejs 或者其它实现（比如 [txiki](https://github.com/saghul/txiki.js)）里，异步 IO 都是通过 `libuv` 来处理的，既然用了 Swift，就打算用 NSRunloop 了。

参考了一下 txiki 代码，把 runloop 实现成了一个 [module](https://github.com/zqqf16/QuickJS-Swift/blob/master/Sources/QuickJS/JSRunloop.swift)

核心的原理很简单，就是 JS 在调用 `setTimeout` 等方法时，Swift 创建一个 NSTimer 插到 runloop 中，timer 触发的时候再去调用 JS 的 callback 代码。

使用：

```swift
let runtime = JSRuntime()!
let context = runtime.createContext()!
context.enableRunloop()
  
let jsCode = """
"use strict";
import * as rl from "Runloop";
rl.setTimeout(function(){ console.log("Hello Runloop"); }, 3000);
"""

let _ = context.eval(jsCode, type: .module)
  
// waiting for 3 seconds
// Hello Runloop
```

目前还是在demo阶段，只支持 `setTimeout` 一个方法😂

- 待续 - 