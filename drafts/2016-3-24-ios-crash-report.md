---
layout: post
title: iOS Crash Report 的加载地址、dSYM 与 UUID
date: 2016-3-24
tags:
    - iOS
    - Crash Report
excerpt: 在做 Crash report 收集与符号化相关工作时，遇到了一些问题，比如加载地址、dSYM 等，在此做一些整理
---


## 前言

关于 Crash report 的符号化问题，网上能搜到很多教程，在通常情况下能够满足要求，在此不在赘述。 只想说一下奇葩的情况，比如我们公司这样自己收集 Crash report 的。

最近在做与 Crash report 相关的工作，趁机整理一下遇到的问题。

## 加载地址

在符号化 Crash report 的过程中，如果用 atos，具体的命令是这样的：

```shell
atos [-o executable] [-l loadAddress] [-arch architecture] [address ...]
```

iOS 为了防止破解保系统序安全，程序每次执行时的加载地址是随机的。应该从哪找这个加载地址呢？

正常的做法是从 Crash report 中的 **Binary Images** 这个段中来找，比如：

```
Binary Images:
0x100058000 - 0x10006bfff TheElements arm64 <77b672e2b9f53b0f95adbc4f68cb80d6> /var/mobile/Containers/Bundle/Application/CB86658C-F349-4C7A-B73B-CE3B4502D5A4/TheElements.app/TheElements
...
```

*注：例子来源于 Apple 官方文档，下同。*

意思就是从 0x100058000 到 0x10006bfff 这段地址空间是 “TheElements” 这个二进制镜像的，所以应用程序的加载地址就是 **0x100058000**。

上述情况是针对 iOS 系统产生的 Crash report，由于我们自己收集的 report 中并没有 “Binary Images”，所以这个方法就失效了，只能另辟蹊径。

先看一下堆栈：（再精简的 Crash report 也应该有堆栈吧……）

```
0   TheElements               0x00000001000effdc 0x1000e4000 + 49116
1   UIKit                     0x000000018ca5c2ec -[UIViewAnimationState sendDelegateAnimationDidStop:finished:] + 184
2   UIKit                     0x000000018ca5c1f4 -[UIViewAnimationState animationDidStop:finished:] + 100
3   QuartzCore                0x000000018c380f60 CA::Layer::run_animation_callbacks(void*) + 292
4   libdispatch.dylib         0x0000000198fb9368 _dispatch_client_callout + 12
5   libdispatch.dylib         0x0000000198fbd97c _dispatch_main_queue_callback_4CF + 928
6   CoreFoundation            0x000000018822dfa0 __CFRUNLOOP_IS_SERVICING_THE_MAIN_DISPATCH_QUEUE__ + 8
7   CoreFoundation            0x000000018822c048 __CFRunLoopRun + 1488
8   CoreFoundation            0x00000001881590a0 CFRunLoopRunSpecific + 392
9   GraphicsServices          0x00000001912fb5a0 GSEventRunModal + 164
10  UIKit                     0x000000018ca8aaa0 UIApplicationMain + 1484
11  TheElements               0x00000001000e9800 0x1000e4000 + 22528
12  libdyld.dylib             0x0000000198fe2a04 start + 0
```

注意包含 “TheElements” 的条目，后面的偏移量全都是 `0x1000e4000 + XXX` 的形式，这个 “0x1000e4000” 就是 “TheElements” 的加载地址。

网上能搜到的资料基本上就到此为止了，但是在实践中发现了一个问题：上面的 Crash report 是在 release 版本中产生的，没有包涵任何的调试符号，如果是在 Debug 模式下，也就是包含了调试符号之后，生成的 Crash Report 是这样的：

```
...
24  GraphicsServices          0x18fa2b6fc GSEventRunModal + 168
25  UIKit                     0x18add2fac UIApplicationMain + 1488
26  TheElements               0x1000fd2f4 main (main.m:55)
27  libdyld.dylib             0x198176a08 start + 4
```

不再是“加载地址＋偏移量”的模式了，变成了“符号＋偏移量”，无法从这样的堆栈信息里找到加载地址。

那么为什么会出现这样的行为呢？

很遗憾，水平有限，没搜到官方的文档说明，只能从源码入手了。

在 iOS 中，常用的获取堆栈的方法是 `[NSThread callStackReturnAddresses]`，在[官方文档](https://developer.apple.com/library/mac/documentation/Cocoa/Reference/Foundation/Classes/NSThread_Class/#//apple_ref/occ/clm/NSThread/callStackSymbols)里说这个方法返回的堆栈信息跟 `backtrace_symbols` 函数一样，这个函数的实现在 Libc 的 [gen/backtrace.c](http://opensource.apple.com/source/Libc/Libc-1082.20.4/gen/backtrace.c) 文件内，关键代码如下：

```c
// ...
if (info->dli_sname) {
    symbol = info->dli_sname;
    symbol_offset = (uintptr_t)addr - (uintptr_t)info->dli_saddr;
} else if(info->dli_fname) {
    symbol = image;
    symbol_offset = (uintptr_t)addr - (uintptr_t)info->dli_fbase;
} else if(0 < snprintf(symbuf, sizeof(symbuf), "0x%lx", (uintptr_t)info->dli_saddr)) {
    symbol = symbuf;
    symbol_offset = (uintptr_t)addr - (uintptr_t)info->dli_saddr;
} else {
    symbol_offset = (uintptr_t)addr;
}
// ...
```

这段代码在判断堆栈地址显示的的格式，其中，`info` 是 `Dl_info` 类型的，定义在 dlfcn.h 文件内：

```c
typedef struct dl_info {
    const char      *dli_fname;     /* Pathname of shared object */
    void            *dli_fbase;     /* Base address of shared object */
    const char      *dli_sname;     /* Name of nearest symbol */
    void            *dli_saddr;     /* Address of nearest symbol */
} Dl_info;
```

因此上面的代码就好理解了，当 `dli_sname` （也就是最近的符号）存在的时候，就用 “最近的符号＋与最近符号的偏移量” 这种格式，当 `dli_sname` 不存在时（也就是在非 Debug 模式下），就用 “二进制加载地址＋与加载地址偏移量” 的格式。

至此，上面的问题就有了答案。

仅凭堆栈信息，是不能够在 Debug 模式下取得加载地址的， 需要在 Crash report 增加额外的字段，获取加载地址的方法如下：

```c
#include <mach-o/dyld.h>

uintptr_t get_load_address(void) {
    const struct mach_header *exe_header = NULL;
    for (uint32_t i = 0; i < _dyld_image_count(); i++) {
        const struct mach_header *header = _dyld_get_image_header(i);
        if (header->filetype == MH_EXECUTE) {
            exe_header = header;
            break;
        }
    }

    return exe_header;
}
```

## dSYM 文件

符号化 Crash report 另一个关键点是要找到对应的 dSYM 文件，这个 dSYM 文件其实就是编译时，给编译器加 `-g` 选项产生的带有调试符号的二进制文件（在 OS X／iOS 上也就是 Mach-O 文件）。可以用 file 以及 otool 命令查看一下：

```shell
~|⇒ file Test 
Test: Mach-O 64-bit dSYM companion file x86_64

~|⇒ otool -hV Test 
Test:
Mach header
      magic cputype cpusubtype  caps    filetype ncmds sizeofcmds      flags
MH_MAGIC_64  X86_64        ALL  0x00        DSYM     7       4408 0x00000000
```

用 `otool -lV ` 命令可以看到里面有一些叫 “__DWARF” 的段，里面就是各种调试信息。现在的 OS X／iOS  系统中调试信息是用一个叫 “DWARF” 的格式存储的，这是一个调试文件格式的标准，详见[http://dwarfstd.org](http://dwarfstd.org) 。

## UUID

可执行文件与 dSYM 文件是通过 UUID 来关联的，在 Mach-O 文件的 Load Command 结构里有个叫 “uuid_command” 的字段，用来存储这个二进制文件的 UUID，在编译时设定，与他对应的 dSYM 文件具有相同的 UUID。

可以用 otool 或者 dwarfdump 命令查看，比如：

```shell
~|⇒ dwarfdump -u Test
UUID: DBEC12D1-9A61-33DF-BC39-E2ED2CB1D8F1 (x86_64) Test
~|⇒ otool -lV Test | grep uuid    
    uuid DBEC12D1-9A61-33DF-BC39-E2ED2CB1D8F1
```

当然，也可以在程序运行中通过代码获取，比如：(代码来源于[http://stackoverflow.com/a/10121277/2978270](http://stackoverflow.com/a/10121277/2978270))

```c
#import <mach-o/ldsyms.h>

NSString *executableUUID()
{
    const uint8_t *command = (const uint8_t *)(&_mh_execute_header + 1);
    for (uint32_t idx = 0; idx < _mh_execute_header.ncmds; ++idx) {
        if (((const struct load_command *)command)->cmd == LC_UUID) {
            command += sizeof(struct load_command);
            return [NSString stringWithFormat:@"%02X%02X%02X%02X-%02X%02X-%02X%02X-%02X%02X-%02X%02X%02X%02X%02X%02X",
                    command[0], command[1], command[2], command[3],
                    command[4], command[5],
                    command[6], command[7],
                    command[8], command[9],
                    command[10], command[11], command[12], command[13], command[14], command[15]];
        } else {
            command += ((const struct load_command *)command)->cmdsize;
        }
    }
    return nil;
}
```

## 更新

根据 Apple 员工写的一篇文章《[Apple's "Lazy" DWARF Scheme](http://wiki.dwarfstd.org/index.php?title=Apple's_%22Lazy%22_DWARF_Scheme)》来看，链接时，会调用一个叫 **dsymutil** 的工具，把 .o 文件里的调试信息提取出到 dSYM 文件里，并且把 dSYM 文件的 UUID 设置成跟编译结果的 Mach-O 文件一致，方便查找。

也可以手工生成 dSYM 文件：

```shell
$dsymutil YourAPP -o YourAPP.dSYM 
```

当然，前提是 YourAPP 中有调试符号。

## 最后

写了一个符号化崩溃日志的 Mac App - [SYM](https://github.com/zqqf16/SYM)，欢迎使用～

## 参考链接

1. [atos and dwarfdump won't symbolicate my address](http://stackoverflow.com/a/12464678/2978270)
2. [Understanding and Analyzing iOS Application Crash Reports](https://developer.apple.com/library/ios/technotes/tn2151/_index.html#//apple_ref/doc/uid/DTS40008184-CH1-ANALYZING_CRASH_REPORTS-EXCEPTION_CODES)
3. [KSCrash](https://github.com/kstenerud/KSCrash)
4. [手动解析CrashLog之----原理篇](http://foggry.com/blog/2015/08/10/ru-he-shou-dong-jie-xi-crashlogzhi-yuan-li-pian/)