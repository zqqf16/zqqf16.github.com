---
layout: post
title: 两个 Xcode Build Script
date: 2017-06-26
tags: 
    - iOS
    - Xcode Tips
---

检查 Localizable.strings 是否有语法错误

```shell
echo "Checking Localizable.strings ..."
plutil -lint ${SRCROOT}/path/to/your/Localizable.strings

if [ $? -ne 0 ]; then
    echo "error: Localizable.strings 有语法错误，请检查错误信息"
    exit 1
fi
```

检查 Assets.car 中是否包含 P3 色域的图片，防止在 iOS 9.x 设备上出现诡异的崩溃问题。

```shell
echo "Checking Assets.car ..."
xcrun --sdk iphoneos assetutil --info ${CODESIGNING_FOLDER_PATH}/Assets.car | grep -q "DisplayGamut.*P3" ;

if [ $$? -eq 0 ]; then
    echo "error: Assets.car 中含有 P3 色域的图片，请检查错误信息"
    exit 1
fi;
```

-EOF-