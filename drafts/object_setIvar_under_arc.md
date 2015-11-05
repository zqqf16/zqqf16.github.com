---
title: 在 ARC 下使用 object_setIvar 的问题
tags:
    - Objective-C
    - Runtime
    - object_setIvar
date: 2015-9-11
---

## 背景

前几天有同事遇到了一个问题，在 ARC 下，通过 Runtime 动态创建的类（`objc_allocateClassPair`），
在调用 `object_setIvar` 给 Ivar 赋值时，发现并不能自动增加被赋值对象的引用计数。
当被赋值的对象被干掉之后，调用 `object_getIvar` 会返回野指针。

由于没 Google 到相似的，所以就自己花时间研究了一下。

## 原理

首先，看一下 `object_setIvar` 函数的定义，在 Runtime 源码里的 [objc-class.m](http://www.opensource.apple.com/source/objc4/objc4-493.9/runtime/objc-class.m) 文件，如下：

```Objective-C
void object_setIvar(id obj, Ivar ivar, id value)
{
    if (obj  &&  ivar  &&  !obj->isTaggedPointer()) {
        Class cls = _ivar_getClass(obj->ISA(), ivar);
        ptrdiff_t ivar_offset = ivar_getOffset(ivar);
        id *location = (id *)((char *)obj + ivar_offset);
        // if this ivar is a member of an ARR compiled class, then issue the correct barrier according to the layout.
        if (_class_usesAutomaticRetainRelease(cls)) {
            // for ARR, layout strings are relative to the instance start.
            uint32_t instanceStart = _class_getInstanceStart(cls);
            const uint8_t *weak_layout = class_getWeakIvarLayout(cls);
            if (weak_layout && is_scanned_offset(ivar_offset - instanceStart, weak_layout)) {
                // use the weak system to write to this variable.
                objc_storeWeak(location, value);
                return;
            }
            const uint8_t *strong_layout = class_getIvarLayout(cls);
            if (strong_layout && is_scanned_offset(ivar_offset - instanceStart, strong_layout)) {
                objc_storeStrong(location, value);
                return;
            }
        }
#if SUPPORT_GC
        // Never go here.
#else
        *location = value;
#endif
    }
}
```

在调试的时候发现 `class_getWeakIvarLayout` 以及 `class_getIvarLayout` 返回值都是`""`。

首先可以排除掉 `objc_storeStrong(location, value);`，因为这个函数会增加引用计数。
由 `object_getIvar` 函数返回野指针可以知道，Ivar 内部并不是 Weak 引用的，
进而可以排除掉 `objc_storeWeak(location, value);`。

所以，这个函数最终会执行到 `*location = value;`，直接对指针赋值，整个过程并没有涉及到内存管理。

至于为什么会这样的关键就在 `_class_usesAutomaticRetainRelease` 这个函数了，看一下它的定义：

```Objective-C
/***********************************************************************
 * _class_usesAutomaticRetainRelease
 * Returns YES if class was compiled with -fobjc-arc
 **********************************************************************/
BOOL _class_usesAutomaticRetainRelease(Class cls)
{
    return (cls->data()->ro->flags & RO_IS_ARR) ? YES : NO;
}
```

其中 `RO_IS_ARR` 宏定义如下：

```Objective-C
// class compiled with -fobjc-arc (automatic retain/release)
#define RO_IS_ARR             (1<<7)   // 0x80
```

从函数的注释可以看出来此函数是用来判断这个类是否是在开启 ARC 的情况下编译的。

而且我搜索了 `objc_allocateClassPair` 函数定义以及整个 Runtime 代码，发现没有一个地方设置了这个 flag。
也就是说在运行时创建的类肯定没有这个 flag。

为了进一步验证，得找到设置这个 flag 的地方，因此我又去翻了一下 clang 的源码（还顺便复习了当年 Vim＋Ctags＋Cscope 的各种用法￣▽￣" ），
在 CGObjCMac.cpp 这个文件中发现了这么一段：

```Objective-C
llvm::GlobalVariable * CGObjCNonFragileABIMac::BuildClassRoTInitializer(
  unsigned flags,
  unsigned InstanceStart,
  unsigned InstanceSize,
  const ObjCImplementationDecl *ID) {
  std::string ClassName = ID->getObjCRuntimeNameAsString();
  llvm::Constant *Values[10]; // 11 for 64bit targets!

  if (CGM.getLangOpts().ObjCAutoRefCount)
    flags |= NonFragileABI_Class_CompiledByARC;
```

*注：当开启 `-fobjc-arc` 选项时，`CGM.getLangOpts().ObjCAutoRefCount` 返回的是 true，而且 `NonFragileABI_Class_CompiledByARC` 的值就是 0x80。*

也就是说当 ARC 开启的时候，clang 会给类设上 0x80 这个 flag。

到这，就可以分析出来为什么 `object_getIvar` 不会增加对象的引用计数了。

**动态创建类的时候，Runtime 并不知道当前代码是否是在 ARC 下编译的，所以进行 Ivar 操作时，
它并不会对 Ivar 里的对象进行自动的内存管理，而是让调用者自己进行。**

进而也可以知道 **ARC 是需要编译器与 Runtime 共同参与的**。


## 解决方法

如果非要解决 `object_getIvar` 不能进行内存管理这个问题，可以采取以下几种方法：

1. 用 MRC

	这个简单粗暴有效。

2. 用 `objc_retain`、`objc_release` 方法手动管理 Ivar 引用计数

	这两个方法应该是私有的 API，可以用 `dlsym` 来搞定。
