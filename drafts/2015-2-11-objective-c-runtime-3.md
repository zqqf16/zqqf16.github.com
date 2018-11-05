---
layout: post
title: Objective-C Runtime（三）
date: 2015-2-11
tags:
    - Objective-C
    - iOS
---


> 从写完两篇 Runtime 相关文章至今，有了一些变化：
>
> 1. Apple 开源了10.10中的 Runtime 代码，并提供了打包下载的方式：[OS X 10.10 Source objc4-646](http://www.opensource.apple.com/tarballs/objc4/objc4-646.tar.gz)。
> 2. 最新的 Runtime 与之前看过的版本有些变化，几乎全都是用 C++ 实现。比如 `struct objc_class` 已经完完全全 C++ 化了。
>
> 本文基于最新的 Runtime 代码。

## 缘起

在文章 [从源码看 Objective-C 的对象模型（一）](posts/objective-c-ojbect-1.html)里曾提到过，clang 改写后的变量定义后面总是会有一些类似于 `__attribute__ ((used, section ("__DATA,__objc_data")))` 这样的代码，例如这样的：

```objective-c
extern "C" __declspec(dllexport) struct _class_t OBJC_CLASS_$_ClassOne __attribute__ ((used, section ("__DATA,__objc_data"))) = {
    0, // &OBJC_METACLASS_$_ClassOne,
    0, // &OBJC_CLASS_$_NSObject,
    0, // (void *)&_objc_empty_cache,
    0, // unused, was (void *)&_objc_empty_vtable,
    &_OBJC_CLASS_RO_$_ClassOne,
};
```

当时由于水平所限，不明白它的作用，后来随着慢慢地了解了一些有关 Mach-O 文件格式，以及一些 Runtime 加载代码，对这块有了更好的理解。

## Mach-O

首先来了解一下概念（来自 [Wikipedia](http://zh.wikipedia.org/zh/Mach-O)）:

> Mach-O 为 Mach Object 文件格式的缩写，它是一种用于可执行文件，目标代码，动态库，内核转储的文件格式。

跟 ELF、PE 等文件格式类似，Mach-O 文件内部也分成代码段、数据段等部分，偷一张 Apple 官方的图：

![Mach-O file format basic structure](https://developer.apple.com/library/mac/documentation/DeveloperTools/Conceptual/MachORuntime/art/mach_o_segments.gif)

可以用 size 命令来查看一个 Mach-O 文件（还有个图形化的工具叫“[MachOView](http://sourceforge.net/projects/machoview/)”）：

```bash
$ size -l -m -x test
Segment __PAGEZERO: 0x100000000 (vmaddr 0x0 fileoff 0)
Segment __TEXT: 0x1000 (vmaddr 0x100000000 fileoff 0)
	Section __text: 0x249 (addr 0x100000c00 offset 3072)
	Section __stubs: 0x30 (addr 0x100000e4a offset 3658)
	Section __stub_helper: 0x60 (addr 0x100000e7c offset 3708)
	Section __cstring: 0x33 (addr 0x100000edc offset 3804)
	Section __objc_methname: 0x3a (addr 0x100000f0f offset 3855)
	Section __objc_classname: 0xb (addr 0x100000f49 offset 3913)
	Section __objc_methtype: 0x27 (addr 0x100000f54 offset 3924)
	Section __unwind_info: 0x48 (addr 0x100000f7c offset 3964)
	Section __eh_frame: 0x30 (addr 0x100000fc8 offset 4040)
	total 0x3f0
Segment __DATA: 0x1000 (vmaddr 0x100001000 fileoff 4096)
	Section __nl_symbol_ptr: 0x10 (addr 0x100001000 offset 4096)
	Section __got: 0x8 (addr 0x100001010 offset 4112)
	Section __la_symbol_ptr: 0x40 (addr 0x100001018 offset 4120)
	Section __cfstring: 0x40 (addr 0x100001058 offset 4184)
	Section __objc_classlist: 0x8 (addr 0x100001098 offset 4248)
	Section __objc_imageinfo: 0x8 (addr 0x1000010a0 offset 4256)
	Section __objc_const: 0x158 (addr 0x1000010a8 offset 4264)
	Section __objc_selrefs: 0x18 (addr 0x100001200 offset 4608)
	Section __objc_classrefs: 0x8 (addr 0x100001218 offset 4632)
	Section __objc_superrefs: 0x8 (addr 0x100001220 offset 4640)
	Section __objc_ivar: 0x8 (addr 0x100001228 offset 4648)
	Section __objc_data: 0x50 (addr 0x100001230 offset 4656)
	total 0x280
Segment __LINKEDIT: 0x1000 (vmaddr 0x100002000 fileoff 8192)
total 0x100003000
```

可以看到，Mach-O 文件里把代码放在了“\_\_TEXT”这个段（Segment）里，数据放在了“\_\_DATA”里，而这两个段里面有分了很多节（Section）。

*习惯上都称 Section 为段，为了不至于混淆，下文都用英文单词来表示。*

要查看这些 Section 里面的内容，就得用 otool（MachOView）这样的工具了，比如查看“\_\_TEXT”里面的“\_\_cstring”：

```bash
$ otool -v -s __TEXT __cstring test       
test:
Contents of (__TEXT,__cstring) section
0x0000000100000edc  Hello, World!
0x0000000100000eea  Default
0x0000000100000ef2  name
0x0000000100000ef7  T@"NSString",&,N,V_name
```

这个 Section 里面存放着不可变的 C 语言字符串，也就是代码里的字符串字面量。如果你的程序里以这种方式保存着密码等关键信息，那得小心了，很容易就会被识破。

好了，再回过头看文章开始的例子 `__attribute__ ((used, section ("__DATA,__objc_data")))`就好理解了，这段代码的作用就是把“OBJC\_CLASS\_$\_ClassOne \_\_attribute\_\_”这个全局变量放在 Mach-O 文件的 “\_\_DATA” Segment 中的 “\_\_objc\_data” Section 里。还有很多类似的代码，其目的就是把数据归类存放在不同的 Section 中。

##作用

*没有找到官方文档来说明为什么要分成这些 Section ，下面仅是我个人理解*

在 Objective-C 中，当用到某个类对象时，是在运行时动态查找的，并不是像 C 那样在编译时期就确定的。比如调用`[ClassOne alloc]` ，内部实现上会先调用 `objc_getClass("ClassOne")` 函数来查找“ClassOne”这个类，找到后再调用其“alloc”方法。在编译时，调用者并不知道“ClassOne”的具体地址，只知道它的名字，运行时会拿着这个名字去找。这也体现了语言的动态性。

通过看 Runtime 代码可知，“objc\_getClass”函数会从一个全局的类列表里查找该类，而这个全局的类列表则是在程序初始化时从“\_\_DATA,\_\_objc\_classlist”这个 Section（从clang 改写后的代码里看，这里存放着类对象的指针）中读取的（objc-runtime-new.mm)。

把这些类对象放在一个 Section 里，在编译时期不用把每个类的地址都保存下来，创建类列表时只要遍历一下这个 Section 就可以了。

PS：这也是 class-dump 等工具的工作原理。

##参考链接

[OS X ABI Mach-O File Format Reference](https://developer.apple.com/library/mac/documentation/DeveloperTools/Conceptual/MachORuntime/index.html)