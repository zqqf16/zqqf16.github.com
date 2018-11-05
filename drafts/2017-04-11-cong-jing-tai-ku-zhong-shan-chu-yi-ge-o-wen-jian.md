---
layout: post
title: 从静态库中删除一个 .o 文件
date: 2017-04-11
tags: 
    - iOS
    - 开发工具
---

[开发一个合格的 iOS SDK](https://blog.zorro.im/how_to_create_a_static_library/)里写过，有些 SDK 开发得不够规范，把一些第三方的库打包到自己的库里。比如见过很多把 OpenSSL 包进去的，SDK A 包一个 OpenSSL，SDK B 也包一个 OpenSSL，链接的时候就发现符号冲突了。

这时不得不对这些库“动手术”，把冲突的内容删掉。于是也就有了这个脚本，还加了对 Fat file 的判断。

```shell
#!/bin/sh

# Remove an object from a static library.


LIB_SRC=${1}
OBJ=${2}


if [ -z ${OBJ} ]; then
	echo "Usage: $0 source.a target.o"
	exit 0
fi

if [ ! -f ${LIB_SRC} ]; then
	echo "File ${LIB_SRC} not found"
	exit 1
fi

EXTRACT_FAT(){
	SUBS=""
	for ARCH in `echo $LIB_INFO | sed -n -e 's/Architectures in the fat file:.*are: \(.*\)/\1/p'`; do
		SUB=${1}_${ARCH}.a
		lipo -thin ${ARCH} ${1} -output ${SUB}
		EXTRACT ${SUB} ${2}
		SUBS="${SUBS} ${SUB}"
	done

	lipo -create ${SUBS} -output ${1}
	rm ${SUBS}
}

EXTRACT(){
	ar -d ${1} ${2}
}

LIB_INFO=`lipo -info ${LIB_SRC}`
if [ `echo $LIB_INFO | grep -c "Architectures in the fat file" ` -gt 0 ]; then
  	EXTRACT_FAT ${LIB_SRC} ${OBJ}
else
  	EXTRACT ${LIB_SRC} ${OBJ}
fi
```

或者，移步 Gist：[https://gist.github.com/zqqf16/1eb6649a68aeb1ee27fabd8a05ea8f1d](https://gist.github.com/zqqf16/1eb6649a68aeb1ee27fabd8a05ea8f1d)