---
layout: post
title: Dispatch Queue 与线程
date: 2015-12-07
tags:
    - GCD
    - iOS
    - libdispatch
image:
    feature: /static/img/gcd-queues@2x-82965db9.png
excerpt: 阅读了一下 libdispatch 的代码，发现了以前对于 GCD 的很多理解都是错误的。
---


> 背景图片来自[Concurrent Programming: APIs and Challenges](https://www.objc.io/issues/2-concurrency/concurrency-apis-and-pitfalls/)

前几天 Apple 开源了 Swift，顺带也开源了 [swift-corelibs-libdispatch](https://github.com/apple/swift-corelibs-libdispatch)，其实也就是个跨平台的 [libdispatch](https://opensource.apple.com/tarballs/libdispatch/)。之前对 GCD 的理解很多都是死记硬背下来的（而且基本上都是去面试前准备的……）。正好趁这个机会研究一下，当然，最主要的原因是看不懂 Swift 代码😂

认真看过代码之后才发现，以前对很多概念的理解都是错误的，比如 Queue，线程池等。

### Queue

在之前的理解中，我以为每次创建的 queue 都是一个独立的 queue 实体，管理着它自己的线程池。

然而并不是这样。

先来看一下创建 queue 的函数 `dispatch_queue_create` 代码：

``` c
dispatch_queue_t
dispatch_queue_create(const char *label, dispatch_queue_attr_t attr)
{
    return dispatch_queue_create_with_target(label, attr,
            DISPATCH_TARGET_QUEUE_DEFAULT);
    // #define DISPATCH_TARGET_QUEUE_DEFAULT NULL
}
```

`dispatch_queue_create_with_target` 函数定义如下（省略部分代码)：

``` c
dispatch_queue_t
dispatch_queue_create_with_target(const char *label, dispatch_queue_attr_t dqa,
        dispatch_queue_t tq)
{
    // ...
    if (!tq) {
        // ...
        tq = _dispatch_get_root_queue(qos, overcommit == 
                _dispatch_queue_attr_overcommit_enabled);
        if (slowpath(!tq)) {
            DISPATCH_CLIENT_CRASH("Invalid queue attribute");
        }
    }
    // ...
    _dispatch_queue_set_override_priority(dq);
    dq->do_targetq = tq;
    _dispatch_object_debug(dq, "%s", __func__);
    return _dispatch_introspection_queue_create(dq);
}
```

可以发现，其实创建自定义 queue 的时候，只不过是从 root queue 列表里找一个相应优先级的 root queue，把它设置成新 queue 的 target queue 而已。在自定义 queue 中执行 block 时实际是在它的 target queue 中执行的。

自定义 queue 更像是一个 root queue 的 “代理”。

代码里的 “root queue”，其实就是 GCD 概念里的 **Global Queue**。在初始化的时候，会创建 15 个 global queue，分别是：
<!--
| 序号   | 名称                                       |
| ---- | ---------------------------------------- |
| 1    | com.apple.main-thread                    |
| 2    | com.apple.libdispatch-manager            |
| 3    | com.apple.root.libdispatch-manager       |
| 4    | com.apple.root.maintenance-qos           |
| 5    | com.apple.root.maintenance-qos.overcommit |
| 6    | com.apple.root.background-qos            |
| 7    | com.apple.root.background-qos.overcommit |
| 8    | com.apple.root.utility-qos               |
| 9    | com.apple.root.utility-qos.overcommit    |
| 10   | com.apple.root.default-qos               |
| 11   | com.apple.root.default-qos.overcommit    |
| 12   | com.apple.root.user-initiated-qos        |
| 13   | com.apple.root.user-initiated-qos.overcommit |
| 14   | com.apple.root.user-interactive-qos      |
| 15   | com.apple.root.user-interactive-qos.overcommit |
-->
<table>
<thead>
<tr>
<th>序号</th>
<th>名称</th>
</tr>
</thead>
<tbody>
<tr>
<td>1</td>
<td>com.apple.main-thread</td>
</tr>
<tr>
<td>2</td>
<td>com.apple.libdispatch-manager</td>
</tr>
<tr>
<td>3</td>
<td>com.apple.root.libdispatch-manager</td>
</tr>
<tr>
<td>4</td>
<td>com.apple.root.maintenance-qos</td>
</tr>
<tr>
<td>5</td>
<td>com.apple.root.maintenance-qos.overcommit</td>
</tr>
<tr>
<td>6</td>
<td>com.apple.root.background-qos</td>
</tr>
<tr>
<td>7</td>
<td>com.apple.root.background-qos.overcommit</td>
</tr>
<tr>
<td>8</td>
<td>com.apple.root.utility-qos</td>
</tr>
<tr>
<td>9</td>
<td>com.apple.root.utility-qos.overcommit</td>
</tr>
<tr>
<td>10</td>
<td>com.apple.root.default-qos</td>
</tr>
<tr>
<td>11</td>
<td>com.apple.root.default-qos.overcommit</td>
</tr>
<tr>
<td>12</td>
<td>com.apple.root.user-initiated-qos</td>
</tr>
<tr>
<td>13</td>
<td>com.apple.root.user-initiated-qos.overcommit</td>
</tr>
<tr>
<td>14</td>
<td>com.apple.root.user-interactive-qos</td>
</tr>
<tr>
<td>15</td>
<td>com.apple.root.user-interactive-qos.overcommit</td>
</tr></tbody></table>

其中：

1. ＃0 没有使用。
2. ＃1 与主线程关联，定义在 init.c 文件。
3. ＃2－3 是内部管理 queue 用的，定义在 queue.c 文件。
4. ＃4－15 queue 定义在 queue.c 文件的 `_dispatch_root_queues` 数组里。

带 overcommit 参数的表示该 queue 在执行 block 时，无论系统多忙都会新开一个线程。在调用 ｀`dispatch_get_global_queue(long identifier, unsigned long flags)` 方法时，指定 flags 为 `DISPATCH_QUEUE_OVERCOMMIT` 即可获取此类 Queue。

关于优先级，在早期版本中比较简单，有以下这些：

- DISPATCH_QUEUE_PRIORITY_HIGH 
- DISPATCH_QUEUE_PRIORITY_DEFAULT 
- DISPATCH_QUEUE_PRIORITY_LOW 
- DISPATCH_QUEUE_PRIORITY_BACKGROUND

在支持了 [Quality of Service（QoS）](https://developer.apple.com/library/prerelease/ios/documentation/Performance/Conceptual/EnergyGuide-iOS/PrioritizeWorkWithQoS.html)之后复杂了一些：

- QOS_CLASS_USER_INTERACTIVE
- QOS_CLASS_USER_INITIATED （DISPATCH_QUEUE_PRIORITY_HIGH）
- QOS_CLASS_DEFAULT （DISPATCH_QUEUE_PRIORITY_DEFAULT）
- QOS_CLASS_UTILITY （DISPATCH_QUEUE_PRIORITY_LOW）
- QOS_CLASS_BACKGROUND （DISPATCH_QUEUE_PRIORITY_BACKGROUND）

为了支持 QoS，root queue 也从 11 个增加到了 15 个。

objc.io 的这幅图很形象地描述了各种 queue 的关系：

![queue](/static/img/gcd-queues@2x-82965db9.png)

### Queue 与线程

之前我以为每个 queue 都管理着它自己的线程池，concurrent queue 的线程池里有多个线程，而 serial queue 的只有一个。

然而并不是。

所有 queue 的线程池都是统一管理的，在 Mac OS 中，是靠 pthread workqueue 实现的。（pthread workqueue 没找到详细信息，可以参考 [FreeBSD 手册](https://people.freebsd.org/~sson/thrworkq/pthread_workqueue.3.txt)。*PS：可以用 `sysctl kern.wq_max_threads` 查看 workqueue 中支持的最大线程数*）。这需要 Libc 标准库与 Kernel 的支持。

所以即使对于 serial queue 来说，它所面对的也是所有的线程池。所以任务是否是并发执行的决定权在 queue 本身。

来看一下 queue 结构体的定义（不同平台可能有差异，大致如下）：

``` c
struct dispatch_queue_s {
    DISPATCH_STRUCT_HEADER(queue);

    /* DISPATCH_QUEUE_HEADER */
    uint32_t volatile dq_running;
    struct dispatch_object_s *volatile dq_items_head;
    /* LP64 global queue cacheline boundary */
    struct dispatch_object_s *volatile dq_items_tail;
    dispatch_queue_t dq_specific_q;
    uint16_t dq_width;
    uint16_t dq_is_thread_bound:1;
    uint32_t volatile dq_override;
    pthread_priority_t dq_priority;
    mach_port_t dq_thread;
    mach_port_t volatile dq_tqthread;
    voucher_t dq_override_voucher;
    unsigned long dq_serialnum;
    const char *dq_label;

    DISPATCH_QUEUE_CACHELINE_PADDING; // for static queues only
};
```

其中 **dq_width** 属性的值就是能够并发执行的最大任务数，concurrent queue 的值为 `DISPATCH_QUEUE_WIDTH_MAX` （`#define DISPATCH_QUEUE_WIDTH_MAX UINT16_MAX`），serial queue 的值为 1。

Queue 会根据自身 dq_width 值的大小来安排任务的执行。

--待续--

### 参考链接

- [GCD Internals](http://newosxbook.com/articles/GCD.html)
- [Concurrent Programming: APIs and Challenges](https://www.objc.io/issues/2-concurrency/concurrency-apis-and-pitfalls/)
- [Low-Level Concurrency APIs](https://www.objc.io/issues/2-concurrency/low-level-concurrency-apis/)