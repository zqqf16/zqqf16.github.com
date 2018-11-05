---
layout: post
title: tornado源码之Configurable类
tags:
    - tornado
    - python
date: 2013-7-16
---


最近比较清闲，打算研究一下tornado的源码。之前很少接触过网络编程方面的东西，对Epoll只是有个概念上的了解，所以就在网上找了一个别人写的[源码分析](http://www.cnblogs.com/Bozh/archive/2012/07/22/2603976.html)来作为入门。

第一讲是说IOLoop的，也是tornado的核心。程序中主函数通常调用`tornado.ioloop.IOLoop.instance().start()`来启动IOLoop，但是看了一下IOLoop的实现，start方法是这样的：

```python
    def start(self):
        """Starts the I/O loop.

        The loop will run until one of the callbacks calls `stop()`, which
        will make the loop stop after the current event iteration completes.
        """
        raise NotImplementedError()
```

也就是说`IOLoop`是个抽象的基类，具体工作是由它的子类负责的。由于是Linux平台，所以应该用`Epoll`，对应的类是`PollIOLoop`。`PollIOLoop`的`start`方法开始了事件循环。

问题来了，`tornado.ioloop.IOLoop.instance()`是怎么返回`PollIOLoop`实例的呢？刚开始有点想不明白，后来看了一下IOLoop的代码就豁然开朗了。

`IOLoop`继承自`Configurable`，后者位于`tornado/util.py`。

>	A configurable interface is an (abstract) class whose constructor acts as a factory function for one of its implementation subclasses. The implementation subclass as well as optional keyword arguments to its initializer can be set globally at runtime with `configure`.

`Configurable`类实现了一个工厂方法，也就是设计模式中的“工厂模式”，看一下`__new__`函数的实现：

```python
    def __new__(cls, **kwargs):
        base = cls.configurable_base()
        args = {}
        if cls is base:
            impl = cls.configured_class()
            if base.__impl_kwargs:
                args.update(base.__impl_kwargs)
        else:
            impl = cls
        args.update(kwargs)
        instance = super(Configurable, cls).__new__(impl)
        # initialize vs __init__ chosen for compatiblity with AsyncHTTPClient
        # singleton magic.  If we get rid of that we can switch to __init__
        # here too.
        instance.initialize(**args)
        return instance
```

当创建一个`Configurable`类的实例的时候，其实创建的是`configurable_class()`返回的类的实例。

```python
    @classmethod
    def configured_class(cls):
        """Returns the currently configured class."""
        base = cls.configurable_base()
        if cls.__impl_class is None:
            base.__impl_class = cls.configurable_default()
        return base.__impl_class
```

最后，就是返回的`configurable_default()`。此函数在IOLoop中的实现如下：

```python
    @classmethod
    def configurable_default(cls):
        if hasattr(select, "epoll"):
            from tornado.platform.epoll import EPollIOLoop
            return EPollIOLoop
        if hasattr(select, "kqueue"):
            # Python 2.6+ on BSD or Mac
            from tornado.platform.kqueue import KQueueIOLoop
            return KQueueIOLoop
        from tornado.platform.select import SelectIOLoop
        return SelectIOLoop
```

`EPollIOLoop`是`PollIOLoop`的子类。至此，这个流程就理清楚了。

第一天看tornado的代码就收获不少，**最好的学习方式就是看别人的代码**这话一点都不假。