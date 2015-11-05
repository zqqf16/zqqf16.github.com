---
title: Python中关于__new__和__init__的坑
date: 2014-1-6
tags: python
---

前几天在重构Peanut的时候，想实现一个扩展的单实例模式。即每个同名的Tag在内存中只有一份，这样方便Tag与Post的关联。然后想起了之前在网上看的Python单实例方法，重写了`__new__`:

```python
class Tag(object):
	_pool = {}

	def __new__(cls, *args, **kwargs):
		identity = tuple(*args, **kwargs)
		if identity in cls._pool:
			return cls._pool[identity]

		instance = super(Tag, self).__new__(*args, **kwargs)
		cls._pool[identity] = instance
		return instance

	def __init__(self, title):
		self.title = title
		self.posts = []
```

当我高兴地以为问题解决了的时候，发现程序运行的结果不太对。在有多个Post对应着同一个Tag的时候，`tag.posts`里面的内容只有最后一个Post。

后来一顿Google后发现了问题所在，在调用`Tag('title')`的时候，总是会先执行`__new__`，然后再执行`__init__`。所以每次posts都会被初始化为空。

想要改变`Tag()`的行为，单纯地重写本类的`__new__`已经满足不了需求了，需要引入元类，重写元类的`__call__`方法：

```python
class Pool(type):
    '''Meta class to implement a simple "object pool".
    '''
    def __new__(self, name, bases, attrs):
        '''Add an attribute "_pool" and a classmethod "all".
        '''
        def all(cls):
            return cls._pool.values()

        def get(cls, id):
            return cls._pool.get(id)

        attrs['_pool'] = {}
        attrs['all'] = classmethod(all)
        attrs['get'] = classmethod(get)

        return super(Pool, self).__new__(self, name, bases, attrs)

    def __call__(cls, *args, **kwargs):
        identity = tuple(*args, **kwargs)
        if identity in cls._pool:
            #Get from pool
            return cls._pool[identity]

        #Generate a new one
        instance = super(Pool, cls).__call__(*args, **kwargs)
        cls._pool[identity] = instance
        setattr(instance, 'id', identity)

        return instance

```

在定义Tag的时候需要指定元类：

```python
class Tag(HTMLPage):
    __metaclass__ = Pool
```

在执行`Tag('title')`的时候，先执行了元类中的`__call__`方法。

至此，问题圆满解决~

另外，为了研究元类中的`__new__`、`__init__`、`__call__`，我写了一个小脚本：

> 2015-7-23 更新：
> Python 3 中，object 的 `__new__`、`__init__` 方法接受的参数有变，在此做了兼容

```python
#!/usr/bin/env python

from __future__ import print_function

from six import with_metaclass


class Meta(type):
	'''Meta class'''

    def __new__(self, name, bases, attrs):
        print('Meta: __new__: {} | {} | {} | {}'.format(self, name, bases, attrs))
        return super(Meta, self).__new__(self, name, bases, attrs)

    def __init__(cls, name, bases, attrs):
        print('Meta: __init__: {} | {} | {} | {}'.format(cls, name, bases, attrs))
        super(Meta, cls).__init__(name, bases, attrs)

    def __call__(cls, *args, **kwargs):
        print('Meta: __call__: {}'.format(cls))
        return super(Meta, cls).__call__(*args, **kwargs)


class Tmp(with_metaclass(Meta, object)):

    def __new__(cls, *args, **kwargs):
        print('Tmp: __new__: {} | {} | {}'.format(cls, args, kwargs))
        return super(Tmp, cls).__new__(cls)

    def __init__(self, *args, **kwargs):
        print('Tmp: __init__: {} | {} | {}'.format(self, args, kwargs))
        super(Tmp, self).__init__()

    def __call__(self, *args, **kwargs):
        print('Tmp: __call__: {} | {} | {}'.format(self, args, kwargs))
        super(Tmp, self).__call__(*args, **kwargs)


Tmp('Hello world')
```

上面的脚本执行后，打印结果如下：

```shell
$ python3 meta.py
Meta: __new__: <class '__main__.Meta'> | Tmp | (<class 'object'>,) | {'__module__': '__main__', '__init__': <function Tmp.__init__ at 0x10e6b1598>, '__qualname__': 'Tmp', '__new__': <function Tmp.__new__ at 0x10e6b1488>, '__call__': <function Tmp.__call__ at 0x10e6b1620>}
Meta: __init__: <class '__main__.Tmp'> | Tmp | (<class 'object'>,) | {'__module__': '__main__', '__init__': <function Tmp.__init__ at 0x10e6b1598>, '__qualname__': 'Tmp', '__new__': <function Tmp.__new__ at 0x10e6b1488>, '__call__': <function Tmp.__call__ at 0x10e6b1620>}
Meta: __call__: <class '__main__.Tmp'>
Tmp: __new__: <class '__main__.Tmp'> | ('Hello world',) | {}
Tmp: __init__: <__main__.Tmp object at 0x10e642438> | ('Hello world',) | {}
```

*PS: 由于引入了 six 的缘故，在 Python 2 下执行的结果会有些不同，可以改为 `__metaclass__ = Meta` 的方式来查看正确结果*

通过这个，可以很清楚的了解元类的流程。

完
