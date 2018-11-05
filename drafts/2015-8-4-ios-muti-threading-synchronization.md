---
layout: post
title: iOS 的多线程同步
date: 2015-8-4
tags:
    - iOS
    - 多线程
---


> 我的上一家公司有个引以为豪的技术：多核无锁，不仅避免了各种由锁带来的问题，还极大的提高了性能，所以产品性能能够在业界数一数二。
> 在这样的氛围影响下，我在开发的时候也很少用锁，能不用就不用。
> 后来去面试 iOS 开发的时候，面试官总是喜欢问有关于锁的问题，最近趁有时间就整理了一下，算是补充一下技能树吧。

## 1. 互斥锁（Mutex）

互斥锁是比较常用的一种锁，当一个线程试图获取被另一个线程占用的锁时，它将会被挂起，让出 CPU，直到该锁被释放。

在 iOS 中，互斥锁有多种实现方式：

### 1.1 POSIX Api

POSIX 方式的优点是比较通用，对那些需要跨平台的 library 来说再合适不过了。

POSIX 中与互斥锁有关的主要有 5 个函数：

- `pthread_mutex_init` 初始化锁
- `pthread_mutex_lock` 加锁
- `pthread_mutex_tylock` 加锁，当锁被占用时，返回 busy，不挂起线程。
- `pthread_mutex_unlock` 释放锁
- `pthread_mutex_destroy` 销毁锁

例子：

```objective-c

#include <pthread.h>

pthread_mutex_t mutex;
pthread_mutex_init(&mutex, NULL);

void mutiThreadMethod()
{
    pthread_mutex_lock(&mutex);

    // Do something

    pthread_mutex_unlock(&mutex);
}

void destroyLock()
{
    pthread_mutex_destroy(&mutex);
}
```

### 1.2 @synchronized

@synchronized 应该是用起来最简单的方式了，例如：

```objective-c
- (void)mutiThreadMethod2
{
    @synchronized(self) {
        // Do something
    }
}
```

用 clang 改写一下就可以发现，其实编译器为这个语法糖做了很多工作，大致如下：

```c
//...

objc_sync_enter
objc_exception_try_enter
setjmp
objc_exception_extract

// Do something

objc_exception_try_exit
objc_sync_exit
// ...
objc_exception_throw
// ...
```

可以看到做了很多与锁有关的操作，其性能不如 POSIX 方式，尽管后者难看些。

### 1.3 NSLock

```objective-c
NSLock *lock = [[NSLock alloc] init];

// ...

- (void)mutiThreadMethod3
{
    if ([lock tryLock]) {
        // Do something
        // ...
        [lock unlock];
    }
}
```

## 2. 递归锁（Recursive Lock）

递归锁是互斥锁的变体，它允许一个线程在释放它之前多次获取它，并且只有在释放相同次数之后其它线程才能获取它。

```objective-c
NSRecursiveLock *theLock = [[NSRecursiveLock alloc] init];

void MyRecursiveFunction(int value)
{
    [theLock lock];
    if (value != 0)
    {
        --value;
        MyRecursiveFunction(value);
    }
    [theLock unlock];
}

MyRecursiveFunction(5);
```


## 3. 读写锁（Read-write Lock）

读写锁把访问对象划分为**读者**和**写者**，当读写锁在**读加锁**状态时，所有的试图以读加锁方式对其进行加锁时，都会获得访问权限。
所有的试图以写加锁方式对其加锁的线程都将阻塞，直到所有的读锁释放。
当在**写加锁**状态时，所有试图对其加锁的线程都将阻塞。

读写锁适合读操作远大于写操作的情况。

在 iOS 上，读写锁得用 POSIX 方式实现。POSIX 提供的相关函数如下：

- `pthread_rwlock_init` 初始化读写锁
- `pthread_rwlock_rdlock` 读加锁
- `pthread_rwlock_wrlock` 写加锁
- `pthread_rwlock_unlock` 释放锁
- `pthread_rwlock_destroy` 销毁锁

例子：

```c
#include <pthread.h>

pthread_rwlock_t rwlock;
pthread_rwlock_init(&rwlock, NULL);

void mutiThreadWritting()
{
    pthread_rwlock_wrlock(&rwlock);
    // write
    pthread_rwlock_unlock(&rwlock);
}

void mutiThreadReadding()
{
    pthread_rwlock_rdlock(&rwlock);
    // read
    pthread_rwlock_unlock(&rwlock);
}
```

## 4. 自旋锁（Spin Lock）

自旋锁与互斥锁不同的地方在于，自旋锁是非阻塞的，当一个线程无法获取自旋锁时，会自旋，直到该锁被释放，等待的过程中线程并不会挂起。

它的优点是效率高，不用进行线程切换。缺点是如果一个线程霸占锁的时间过长，自旋会消耗 CPU 资源。

```objective-c
#import <libkern/OSAtomic.h>

static OSSpinLock lock = OS_SPINLOCK_INIT;

void mutiThreadMethod4
{
    OSSpinLockLock(&lock);
    // Do something
    OSSpinLockUnlock(&lock);
}
```

## 5. 分布锁（Distributed Lock）

严格来说，分布锁是进程间同步的工具，有点像 Unix 下的各种 lock 文件，比如 apt-get 的 “/var/lib/apt/lists/lock”。

它并不强制进程休眠，只是起到告知的作用。具体如何处理资源被占，完全由进程自己决定。

iOS 上几本用不上分布锁，在 OS X 中，可以用 **NSDistributedLock** 实现：

```objective-c
NSDistributedLock *lock = [NSDistributedLock lockWithPath:path];

// ...

if ([lock tryLock]) {
    // Do something
    [lock unlock];
}
```

或者，可以直接通过写 lock 文件的方式来实现。

## 6. 条件变量（Condition Variable）

如果一个线程需要等待某一条件才能继续执行，而这个条件是由别的线程产生的，这时候只用锁就有点捉襟见肘了。要么不停的轮询，消耗资源，要么每隔一段时间查询一次，丧失了及时性。
条件变量就是为了满足这种场景而生的，它可以让一个线程等待某一条件，当条件满足时，会收到通知。
在获取条件变量并等待条件发生的过程中，也会产生多线程的竞争，所以条件变量通常会和互斥锁一起工作。

iOS 中，条件变量有两种实现方式：

### 6.1 POSIX

POSIX 提供的相关函数如下：

- `pthread_cond_init` 初始化
- `pthread_cond_wait` 等待条件
- `pthread_cond_broadcast` 发送广播，唤醒所有正在等待的线程
- `pthread_cond_signal` 发送信号，唤醒第一个线程
- `pthread_cond_destroy` 销毁

例子：

```c
#include <pthread.h>

static pthread_mutex_t mutex;
static pthread_cond_t condition;

// ...

pthread_mutex_init(&mutex, NULL);
pthread_cond_init(&condition, NULL);

// ...

void waitCondition()
{
    pthread_mutex_lock(&mutex);
    while (value == 0) {
        pthread_cond_wait(&condition, &mutex);
    }
    pthread_mutex_unlock(&mutex);
}

void triggerCondition()
{
    pthread_mutex_lock(&mutex);

    value = 1;

    pthread_mutex_unlock(&mutex);
    pthread_cond_broadcast(&condition);
}

// ...

pthread_mutex_destroy(&mutex);
pthread_cond_destroy(&condition);
```

### 6.2 NSCondition

例子摘自 [Threading Programming Guide](https://developer.apple.com/library/mac/documentation/Cocoa/Conceptual/Multithreading/ThreadSafety/ThreadSafety.html)

```objective-c
[cocoaCondition lock];
while (timeToDoWork <= 0)
    [cocoaCondition wait];

timeToDoWork--;

// Do real work here.

[cocoaCondition unlock];
```

发送信号：

```objective-c
[cocoaCondition lock];
timeToDoWork++;
[cocoaCondition signal];
[cocoaCondition unlock];
```

## 7. NSConditionLock

NSConditionLock 跟 NSCondition 类似，但是实现机制是不一样的，所以单独列了出来。

例子：

生产者

```objective-c
id condLock = [[NSConditionLock alloc] initWithCondition:NO_DATA];

while(true)
{
    [condLock lock];
    // Add data to the queue.
    [condLock unlockWithCondition:HAS_DATA];
}
```

消费者

```objective-c
while (true)
{
    [condLock lockWhenCondition:HAS_DATA];
    // Remove data from the queue.
    [condLock unlockWithCondition:(isEmpty ? NO_DATA : HAS_DATA)];

    // Process the data locally.
}
```

## 8. 信号量（Semaphore）

信号量可以看成是一种特殊的互斥锁，不同的是，它可以不只有两个状态，它可以是资源的计数器。还记得《操作系统》中学过的 PV 操作么？

iOS 中，信号量有两种实现方式：

### 8.1 POSIX

POSIX 提供的相关函数如下：

- `sem_init` 初始化
- `sem_post` 给信号量的值加一（V 操作）
- `sem_wait` 给信号量的值减一（P 操作）
- `sem_getvalue` 返回信号量的值
- `sem_destroy` 销毁

### 8.2 GCD 信号量

GCD 提供的函数如下：

- `dispatch_semaphore_create` 创建信号量
- `dispatch_semaphore_signal` 发送信号（信号量加一，V 操作）
- `dispatch_semaphore_wait`等待信号（信号量减一，P 操作）

例子：

```objective-c
dispatch_semaphore_t semaphore = dispatch_semaphore_create(10);

// ...

dispatch_semaphore_wait(semaphore, DISPATCH_TIME_FOREVER);
// Do something
dispatch_semaphore_signal(semaphore);
```

## 9. 栅栏／屏障（Barrier）

如果一个线程需要等待另一个线程的某些操作之后才能继续执行，可以用上面所说的条件变量来实现，还有一种优雅的实现方式 —— Barrier。
形象点说，就是把线程挡在同一个 Barrier 之前，所有的线程都达到 Barrier 之后，统一放行。

同样，iOS 中有两种实现方式：

### 9.1 POSIX

相关函数如下：
- `pthread_barrier_init` 创建 barrier
- `pthread_barrier_wait` 告知当前线程已经到达 barrier，等所有线程都告知后，会继续往下执行
- `pthread_barrier_destroy` 销毁

### 9.2 Dispatch Barrier

Dispatch Barrier 的概念跟 POSIX 类似，不同的是它是针对于 GCD 异步任务的。它可以让在它之前提交的异步任务都执行完成之后再执行。

例子：

```objective-c
dispatch_async(async_queue, block1);
dispatch_async(async_queue, block2);
// block3 会在 block1 和 block2 执行完成之后再执行
dispatch_barrier_async(async_queue, block3);
// block4 和 block5 会在 block3 之后执行
dispatch_async(async_queue, block4);
dispatch_async(async_queue, block5);
```

## 后记

**锁** 这个东西可谓 “小用怡情，滥用伤身”，用的时候一不小心就会有各种各样的问题，比如死锁，我曾经就这样写过：

```objective-c
void func()
{
    LOCK;

    //...

    if (someCondition) {
        return;
    }

    UNLOCK;
}
```

在 iOS 中，很多时候都可以用 GCD 的串行队列来避免使用锁：

```objective-c
dispatch_async(serialQueue, block);
```

因为串行队列中的任务一次只能执行一个，所以就不存在资源的竞争，还能有效的避免死锁问题。

-----更新-----

最近发现很多同事，以及各种博客都在测试各种加锁方式的性能，比如连续加解锁几千次取总时间等。想通过这种比较来选取一种所谓*高效率*的锁。

还有，面试的时候，有些自认为懂得多的面试官总是想让你说一下常用的线程同步方式。要是回答 @synchronized，就会各种受鄙视。

🤷‍♀️🤷‍♀️🤷‍♀️🤷‍♀️🤷‍♀️🤷‍♀️🤷‍♀️🤷‍♀️🤷‍♀️🤷‍♀️🤷‍♀️🤷‍♀️

iOS，或者各平台的客户端，都不是一个高并发的环境，用锁的时候通常是为了解决两个线程偶尔发生的同步性问题。一种锁自身的性能再好，也不会对整个应用带来多大的性能提升，临界区的大小才是关键。

比如，A 线程，加锁用了 1ms，然后在临界区内呆了 100ms，解锁（1ms），总共用了 102ms。

在 A 处于临界区时，B 线程试图加锁，发生竞争，等待 A 结束，需要等待 0~102ms。

及时用了超级 NB 的锁，加解锁只需 0.0000000001ms，对于 B 来说也无济于事。

我曾见过一个横跨了几百行代码的锁，类似于这样：

```c
LOCK

// 中间省略几百行

x = y; // 真正需要加锁的代码

// 又省略几百行

UNLOCK
```

写代码的同学还特意用了信号量，感觉能提高效率……

所以，就 iOS 开发而言，能用 `@synchronized` 就用吧，简单、支持嵌套，还能避免各种死锁问题，何乐而不为。