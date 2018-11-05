---
layout: post
title: React Native 中那些有意思的地方（一）
date: 2015-4-13
tags:
    - iOS
    - React Native
---

> 越来越感觉自己是个井底之蛙，开发时总是喜欢反反复复重复一小撮知识点，而且这一小撮随着时间的增长会变得越来越小，到头来发现很多之前掌握的都忘记了。

个人觉得 Facebook 的开源项目的质量很高，每次看他们的代码都能收获不少，比如之前的 [Tornado](https://zorro.im/tornado-template/)。他们对知识掌握的全面、运用的灵活是很多国内开发者（至少是我）所不及的。

好了，言归正传，说说 React Native。

RN 的原理其实挺简单的，基本上就是把 Objective-C 的对象封装一下，然后塞进 JavaScriptCore 的上下文中，这样在 JS 中就可以调用了。

RN 定义了一个叫做 RCTBridgeModule 的协议，所有要暴露给 JS 的对象都需要实现此协议。在运行时 RCTBridge 会查找所有的实现了该协议的类，并且找出这些类中想要暴露的方法。

在找方法这步，他们的方法挺有意思：

首先，定义了一个宏

```c
#define RCT_EXPORT(js_name) __attribute__((used, section("__DATA,RCTExport" \
))) static const char *__rct_export_entry__[] = { __func__, #js_name }
```

如果某一个方法想暴露出去，只需要在方法体内加一句 `RCT_EXPORT();` 即可，比如：

```objective-c
- (void)multiGet:(NSArray *)keys callback:(RCTResponseSenderBlock)callback
{
  RCT_EXPORT();

  if (!callback) {
    RCTLogError(@"Called getItem without a callback.");
    return;
  }
  // ...

```

这个宏的作用是在编译时，把当前方法名和 js_name 参数保存到二进制文件的 “\_\_DATA,RCTExport” 段（具体来说，应该叫 \_\_DATA Segment, RCTExport Section, 详见[上一篇文章](https://zorro.im/posts/objective-c-runtime-3／)）里。等在运行时，再通过读取这个段来找出所需要的方法名等信息，就知道哪些方法是需要暴露的了。具体的函数如下：


```objective-c
static RCTSparseArray *RCTExportedMethodsByModuleID(void)
{
  static RCTSparseArray *methodsByModuleID;
  static dispatch_once_t onceToken;
  dispatch_once(&onceToken, ^{

    Dl_info info;
    dladdr(&RCTExportedMethodsByModuleID, &info);

#ifdef __LP64__
    typedef uint64_t RCTExportValue;
    typedef struct section_64 RCTExportSection;
#define RCTGetSectByNameFromHeader getsectbynamefromheader_64
#else
    typedef uint32_t RCTExportValue;
    typedef struct section RCTExportSection;
#define RCTGetSectByNameFromHeader getsectbynamefromheader
#endif

    const RCTExportValue mach_header = (RCTExportValue)info.dli_fbase;
    const RCTExportSection *section = RCTGetSectByNameFromHeader((void *)mach_header, "__DATA", "RCTExport");

    if (section == NULL) {
      return;
    }

    NSArray *classes = RCTBridgeModuleClassesByModuleID();
    NSMutableDictionary *methodsByModuleClassName = [NSMutableDictionary dictionaryWithCapacity:[classes count]];

    for (RCTExportValue addr = section->offset;
         addr < section->offset + section->size;
         addr += sizeof(const char **) * 2) {

      // Get data entry
      const char **entries = (const char **)(mach_header + addr);

      // Create method
      RCTModuleMethod *moduleMethod =
        [[RCTModuleMethod alloc] initWithMethodName:@(entries[0])
                                       JSMethodName:strlen(entries[1]) ? @(entries[1]) : nil];

      // Cache method
      NSArray *methods = methodsByModuleClassName[moduleMethod.moduleClassName];
      methodsByModuleClassName[moduleMethod.moduleClassName] =
        methods ? [methods arrayByAddingObject:moduleMethod] : @[moduleMethod];
    }

    methodsByModuleID = [[RCTSparseArray alloc] initWithCapacity:[classes count]];
    [classes enumerateObjectsUsingBlock:^(Class moduleClass, NSUInteger moduleID, BOOL *stop) {
      methodsByModuleID[moduleID] = methodsByModuleClassName[NSStringFromClass(moduleClass)];
    }];
  });

  return methodsByModuleID;
}
```

这个函数不用太多的解释，主要流程就是找到那个数据段，遍历解析里面的数据，然后返回结果。

代码很容易看懂，但是背后的想法却很有意思。其实这种场景在平时开发中经常遇到，比如有时候子类需要向父类注册自己，父类根据触发条件来创建某一子类的实例。通常都会有几种实现方法：

1. 在父类的某个地方集中注册，比如维护着一个字典，每当派生出一个子类就在字典里添加一项。
2. 子类以某些特定方式命名，到时候就可以根据触发事件来构造需要调用的子类名。
3. 维护一个单独的文件，保存着类似第一种方法里面的字典。
4. 改写子类的 `+load` 方法，在里面注册子类
5. ...

不能说哪种方式最好，因为应用场景不确定，但是就目前来看 RN 的这种方式无疑是最灵活的。

第1、3种方法需要维护一个大表，不利于解耦；第2种方法对类名或者方法名有要求，但是没做出限制，稍不留神就容易出问题。第4种方法在简单的需求下挺完美的，但是如果需求比较奇葩，比如 `load` 中依赖的过多，则可能会出现很多意想不到的结果。

再反观 RN 的实现，它的注册机制是松散的、灵活的，子类注册的时候不用告诉父类，而父类在找子类的时候从约定好的地方找就可以了。它其实整合了第1、3、4条的优点，同时又简化了很多。

当然，这种方式也有缺点，因为它完全是由子类的实现者定义的，很可能存储在两个子类互相冲突的问题，这就需要有额外的措施来保证。

不过，多知道一种有意思的方法总归是有益的，是吧？