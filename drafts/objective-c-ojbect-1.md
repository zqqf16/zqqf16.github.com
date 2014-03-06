title: 从源码来看Objective-C的对象模型——初探
tag: Objective-C
date: 2014-3-5

##前言
刚接触Objective-C的时候，曾被一个bug折磨得很痛苦，后来才发现是我对Category理解错了，不知道它对所有该类的实例都会起作用。当时就决定要好好研究一下Objective-C的对象模型。正好最近手头的活忙完了，可以有时间做个总结。

本文所参照的代码是clang rewrite之后的C++代码，以及Apple开源的Runtime代码，地址[在这](http://www.opensource.apple.com/source/objc4/)。Apple官方貌似没有提供一个打包下载的地址，我在Github上fork了一份别人整理过的437.1版本的，可以到[这里](https://github.com/zqqf16/OBJC4-437.1-Runtime)查看。

##基本概念
对于Objective-C有关对象、类、元类的基本概念，我就不细说了，和Python很像。这里有三篇文章，对我当时研究的启发很大，大家可以参考一下。

* [Objective-C对象之类对象和元类对象（一）](http://blog.csdn.net/wzzvictory/article/details/8592492)
* [Objective-C对象模型及应用](http://blog.devtang.com/blog/2013/10/15/objective-c-object-model/)
* [深入浅出Cocoa之类与对象](http://www.cnblogs.com/kesalin/archive/2012/01/19/objc_class_object.html)

这里只做个总结：

1. 所有对象都是一个结构体，它的第一个成员是一个指向`objc_class`类型的指针——`isa`。或者说所有第一个成员是`objc_class`指针类型的结构体都是对象。
2. 实例对象的`isa`指向它的类对象，类对象的`isa`指向元类，元类的`isa`指向根元类，根元类的指向它自己。

##实例、类、元类初探

新建一个NSObject的子类，如下：

```objective-c
/* FirstClass.h */
#import <Foundation/Foundation.h>

@interface FirstClass : NSObject
{
    NSString *className;
}
@end

/* FirstClass.m */
#import "FirstClass.h"

@implementation FirstClass

@end
```

然后执行`clang -rewrite-objc FirstClass.m`，这样就会在当前目录生成一个名叫`FirstClass.cpp`的文件，打开文件（注意，因为包含了`Foundation.h`，所以生成的cpp文件巨大，可以忽略前1W行）可以看到，FirstClass被改写成了这样：
```c
typedef struct objc_object FirstClass;
```
成了`objc_object`类型的结构体。`objc_object`的声明如下：

```c
struct objc_object {
    Class isa ;
};
```

也就是说，当我们用`FirstClass *fc;`这样的形式去声明一个变量的时候，其实这个变量就是一个指向`objc_object`类型的指针，也就是上面我总结的，他指向的是一个对象。

接着往下看，会发现以下这样的代码：

```c
extern "C" __declspec(dllimport) struct _class_t OBJC_METACLASS_$_NSObject;

extern "C" __declspec(dllexport) struct _class_t OBJC_METACLASS_$_FirstClass __attribute__ ((used, section ("__DATA,__objc_data"))) = {
    0, // &OBJC_METACLASS_$_NSObject,
    0, // &OBJC_METACLASS_$_NSObject,
    0, // (void *)&_objc_empty_cache,
    0, // unused, was (void *)&_objc_empty_vtable,
    &_OBJC_METACLASS_RO_$_FirstClass,
};

extern "C" __declspec(dllimport) struct _class_t OBJC_CLASS_$_NSObject;

extern "C" __declspec(dllexport) struct _class_t OBJC_CLASS_$_FirstClass __attribute__ ((used, section ("__DATA,__objc_data"))) = {
    0, // &OBJC_METACLASS_$_FirstClass,
    0, // &OBJC_CLASS_$_NSObject,
    0, // (void *)&_objc_empty_cache,
    0, // unused, was (void *)&_objc_empty_vtable,
    &_OBJC_CLASS_RO_$_FirstClass,
};
```

根据字面意思就可以看明白了，分别定义了两个变量，`OBJC_METACLASS_$_FirstClass`和`OBJC_CLASS_$_FirstClass`，前者是元类，后者是类。他们都是`_class_t`类型的，都是对象。因为是自动改写的，所以变量名都有些奇怪，但并不影响阅读。

这里简单介绍一下`__declspec(dllimport)`、`__declspec(dllexport)` 以及 `__attribute__ ((used, section ("__DATA,__objc_data")))`。前两个分别声明导入和导出函数，一般用于动态链接库，后面的是一个GNU C的扩展，`used`告诉编译器即使后面没有引用也要编译这段代码，`section ("__DATA,__objc_data")`是说把这段代码编译到`__DATA,__objc_data`段，而不是默认的代码段。至于为啥要这样，我也不太明白，有待进一步研究。

`_class_t`的声明如下：

```c
struct _class_t {
    struct _class_t *isa;
    struct _class_t *superclass;
    void *cache;
    void *vtable;
    struct _class_ro_t *ro;
};
```

基本可以当成`runtime.h`中的`objc_class`类型。

后面还有一段代码，定义了一个初始化函数：

```c
static void OBJC_CLASS_SETUP_$_FirstClass(void ) {
    OBJC_METACLASS_$_FirstClass.isa = &OBJC_METACLASS_$_NSObject;
    OBJC_METACLASS_$_FirstClass.superclass = &OBJC_METACLASS_$_NSObject;
    OBJC_METACLASS_$_FirstClass.cache = &_objc_empty_cache;
    OBJC_CLASS_$_FirstClass.isa = &OBJC_METACLASS_$_FirstClass;
    OBJC_CLASS_$_FirstClass.superclass = &OBJC_CLASS_$_NSObject;
    OBJC_CLASS_$_FirstClass.cache = &_objc_empty_cache;
}
```
可以看到元类的`isa`、`superclass`都指向了NSOBject，而类的`isa`指向了元类、`superclass`指向了NSObject。

看到这就明白了，类对象以及元类对象是编译时就会创建好的。那么实例对象是怎么创建的，实例变量是怎么保存的呢？且看下一篇分解~

--未完待续--
