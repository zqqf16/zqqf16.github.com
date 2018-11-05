---
layout: post
title: 修复 Xcode 调试时卡死的脚本
date: 2017-02-27
tags: 
    - iOS
    - 开发工具
    - Xcode Tips
---

印象中从 Xcode 8 开始，真机调试的时候总是隔三差五地卡死。

代码切换分支，直接编译调试，卡死  
App 启动时触发断点，卡死  
断点事件过长，卡死  
。。。

最早的时候能发现是 lldb_rpc_server cpu 100% 导致的，干死这个进程后就好了。  
后来，随着 Xcode 越来越“稳定”，卡死的原因就找不到了……

综合网上的各种信息以及本人的摸索，写了个脚本，能在 Xcode 卡死时“回春”一下～

<script src="https://gist.github.com/zqqf16/a4ba12b26dc307c33d3bb6e6001c42a3.js"></script>

一共干了四件事：

1. 干死 Xcode
2. 删掉 xcuserdata
3. 删掉 DerivedData
4. 重新 Launch

脚本地址 [Gist](https://gist.github.com/zqqf16/a4ba12b26dc307c33d3bb6e6001c42a3)

希望对大家有所帮助，也希望 Apple 争点气，隔壁 Visual Code 已经甩开一万条街了。