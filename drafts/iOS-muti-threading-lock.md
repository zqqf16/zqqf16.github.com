title: iOS 中的各种锁
date: 2015-8-3
tag: iOS
tag: 锁

## 互斥锁（Mutex）
互斥锁是最常用的，它是阻塞的，当一个线程无法获取互斥锁时，它将会被挂起，让出 CPU，直到该锁被释放。

### POSIX

```c
pthread_mutex_t mutex;

void MyInitFunction()
{
    // Initialize a mutex
    pthread_mutex_init(&mutex, NULL);
}

void MyLockingFunction()
{
    // Lock
    pthread_mutex_lock(&mutex);

    // Do work
    // ...

    // Unlock
    pthread_mutex_unlock(&mutex);
}
```

### @synchronized

```objective-c
- (void)myMethod:(id)anObj
{
    @synchronized(anObj)
    {
        // Everything between the braces is protected by the @synchronized directive.
    }
}
```

### NSLock

```objective-c
BOOL moreToDo = YES;
NSLock *theLock = [[NSLock alloc] init];
// ...
while (moreToDo) {
    // Do another increment of calculation
    // until there’s no more to do.
    if ([theLock tryLock]) {
        // Update display used by all threads.
        [theLock unlock];
    }
}
```

递归锁（Recursive lock）
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


读写锁（Read-write lock）
读写锁把访问对象划分为读者和写者，当读写锁在*读加锁*状态时，所有的试图以读加锁方式对其进行加锁时，都会获得访问权限。
所有的试图以写加锁方式对其加锁的线程都将阻塞，直到所有的读锁释放。
当在*写加锁*状态时，所有试图对其加锁的线程都将阻塞。
读写锁适合读操作远大于写操作的情况。

分布锁（Distributed lock）
分布锁通常是进程级别的，它不像互斥锁，并不阻塞线程。只是告知一下，该锁被占用。具体该怎么处理由进程自己决定。

自旋锁（Spin lock）
自旋锁是非阻塞的，当一个线程无法获取自旋锁时，会自旋，直到该锁被释放。
它的优点是效率高，不用进行线程切换。缺点是如果一个线程霸占锁的时间过长，自旋会消耗 CPU 资源。

## 条件变量（Condition）

### NSConditionLock

```objective-c
id condLock = [[NSConditionLock alloc] initWithCondition:NO_DATA];

while(true)
{
    [condLock lock];
    // Add data to the queue.
    [condLock unlockWithCondition:HAS_DATA];
}

// 消费者
while (true)
{
    [condLock lockWhenCondition:HAS_DATA];
    // Remove data from the queue.
    [condLock unlockWithCondition:(isEmpty ? NO_DATA : HAS_DATA)];

    // Process the data locally.
}
```

信号量（Semaphore）
