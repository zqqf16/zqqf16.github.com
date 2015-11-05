---
title: 从源码看Objective-C的对象模型（二）
date: 2014-3-17
tags:
    - Objective-C
    - iOS
---

## 前言

> 最近由于工作比较忙，所以这篇文章比预期的时间来的晚了。  

这几天找时间仔细研究了一下上一篇文章里提到的Runtime代码，发现新旧版本之间有一些差别，数据结构有点对不上。另外，`Clang`这个“rewrite”也不是很靠谱，也不支持Objective-c 2.0。所以这里所说的“源码”只是个大概，并不完全准确。

这篇文章主要写一下实例变量的存储与访问。

## 一、运行时实例对象的结构

接着上一篇文章里讲的，为类FirstClass加一个方法：

```objective-c
@interface FirstClass : NSObject
{
    NSString *className;
}
@end
- (void)accessClassName;
```

`accessClassName`定义如下：

```objective-c
- (void)accessClassName
{
    NSString *a = self.className;
    NSString *b = self->className;
    NSString *c = className;

    NSLog(@"%@, %@, %@", a, b, c);
}
```

在函数内的任意位置加断点，在`main`函数里面调用它。在lldb里执行`p *self`，可以得到这样的输出：

```
(lldb) p *self
(FirstClass) $0 = {
  NSObject = {
    isa = FirstClass
  }
  className = nil
}
```

这里要注意，不要被NSObject欺骗住了，结构体本身在内存中是不占空间的。上面的输出就等价于：

```
$0 = {
    isa = FirstClass
    className = nil
}
```

可以看到在运行时self的实例变量“className”是在实例对象的结构体里的。

## 二、编译时期的声明与定义

看Clang改写过的这段代码，其中有这样的描述：

```c
struct FirstClass_IMPL {
    struct NSObject_IMPL NSObject_IVARS;
    NSString *className;
};
```

其中，NSObject_IMPL是这样声明的：

```c
struct NSObject_IMPL {
    Class isa;
};
```

正好和上面lldb输出的信息吻合。但是有一点需要说明一下，`FirstClass_IMPL`貌似只是个内部结构（几乎没起什么作用，可能只是为了标明一下FirstClass的结构？）。而且在上一篇文章里可以看到，`FirstClass`是这样被声明的：

```c
typedef struct objc_object FirstClass;
```

在声明中，FirstClass只是个`objc_object`类型（里面只有`isa`）的结构体，也就是说在它的声明里并没有提及`className`成员变量。那么最终是怎么变成Runtime里面所描述的那样的呢？

为了弄懂这个问题，需要先回顾一下类对象的结构，`_class_t`中有个`_class_ro_t`类型的成员`ro`(Runtime代码里还有个叫`_class_wo_t`的结构，“r”和“w”没有搜索到准确的意思，好像是编译期间指定了的叫“r”，Runtime能够改变的叫“w”)，它是这样声明的：

```c
struct _class_ro_t {
    unsigned int flags;
    unsigned int instanceStart;
    unsigned int instanceSize;
    unsigned int reserved;
    const unsigned char *ivarLayout;
    const char *name;
    const struct _method_list_t *baseMethods;
    const struct _objc_protocol_list *baseProtocols;
    const struct _ivar_list_t *ivars;
    const unsigned char *weakIvarLayout;
    const struct _prop_list_t *properties;
};
```

通过阅读代码可以知道，这其中名叫的`ivars`（instance vars?）就存放着实例变量的信息。也就是说，实例变量的信息存放在类对象里。

`_ivar_list_t`的声明与`FirstClass`中的`ivars`定义如下：

```c
static struct /*_ivar_list_t*/ {
    unsigned int entsize;  // sizeof(struct _prop_t)
    unsigned int count;
    struct _ivar_t ivar_list[1];
} _OBJC_$_INSTANCE_VARIABLES_FirstClass __attribute__ ((used, section ("__DATA,__objc_const"))) = {
    sizeof(_ivar_t),
    1,
    {{(unsigned long int *)&OBJC_IVAR_$_FirstClass$className, "className", "@\"NSString\"", 3, 8}}
};
```

`_ivar_t`的声明：

```c
struct _ivar_t {
    unsigned long int *offset;  // pointer to ivar offset location
    const char *name;
    const char *type;
    unsigned int alignment;
    unsigned int  size;
};
```

这里面包括了实例变量的偏移量、名称、类型等信息。（注：改写后文件里的结构体声明与runtime.h里的有一定出入，但大体结构一致。目前尚不知是Runtime版本问题，还是Clang改写的问题，或者也有可能本身就是这样实现的。在这里就暂且忽略吧- -!）

## 三、运行时实例变量的初始化

接下来再对比一下Runtime的代码，看看在`alloc`的时候，实例对象所占的内存是怎么被分配的。

`NSOjbect`的`alloc`方法会调用`_internal_class_createInstanceFromZone`函数，而后者又会调用`_class_getInstanceSize`来获取实例变量的大小。`_class_getInstanceSize`定义如下：(注：runtime这部分的代码有些乱，新旧版本里函数的实现有所差别，这里只摘取部分代码)

```c
//objc-runtime-new.m

__private_extern__ size_t
_class_getInstanceSize(Class cls)
{
    if (!cls) return 0;
    return instanceSize(newcls(cls));
}

static uint32_t
instanceSize(struct class_t *cls)
{
    assert(cls);
    assert(isRealized(cls));
    // fixme rdar://5244378
    return (uint32_t)((cls->data->ro->instanceSize + WORD_MASK) & ~WORD_MASK);
}
```

`cls->data->ro->instanceSize`这个数值在编译时就被算好了，就是（或者可以看成）`FirstClass_IMPL`的大小。

到这里就清晰了，`FirstClass`被声明为`objc_object`类型只是个障眼法，它实际的结构应该是`FirstClass_IMPL`描述的那样。

## 四、实例对象的访问

内存分配搞明白了，但是对象的声明中并没有包含实例变量的信息，那么他们是怎么被访问的呢？

再回过头来看上面提到的`accessClassName`方法，在其中故意用了“点语法”、指针和直接访问的方式来访问`className`，下面来看看这三种方法的改写结果：

```c
static void _I_FirstClass_accessClassName(FirstClass * self, SEL _cmd) {
    NSString *a = ((NSString *(*)(id, SEL))(void *)objc_msgSend)((id)self, sel_registerName("className"));
    NSString *b = (*(NSString **)((char *)self + OBJC_IVAR_$_FirstClass$className));
    NSString *c = (*(NSString **)((char *)self + OBJC_IVAR_$_FirstClass$className));

    NSLog((NSString *)&__NSConstantStringImpl__var_folders_fy_6ckx65gn39198bs5ydlgfk800000gn_T_FirstClass_c4b878_mi_0, a, b, c);
}
```

（关于方法的实现将在在下一篇文章研究，在这里只需注意一下这个函数的第一个形参：`self`，我们在实例方法里面用到的“self”其实只不过是个形参而已，当函数被调用的时候会把实例对象自身传进来。）

在这个函数里面可以看到，除了“点语法”用到了消息机制（了解KVC的都知道吧……），后面两种方法在实现上是一样的，都是通过指针+偏移量来访问的。不知道对象的结构没关系，知道了偏移量就行了~

## 总结

- 运行时实例对象的结构中包含了实例变量
- 实例变量的信息保存在类对象里，运行时类对象会根据这些信息来完成实例化
- 在方法中通过指针或者变量名访问实例变量，是通过self指针加上偏移量来实现的
