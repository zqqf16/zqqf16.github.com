---
title: 重拾C语言之strncpy
date: 2013-5-24
tags: c, strncpy
---

> 前一段时间Python用惯了，冷不丁地切换回C，发现很多基础东西都有点模糊了。从今天起，我将把一些平时碰到的知识点整理起来，起名为“重拾C语言”系列。纯粹的基础知识，老鸟绕行~

```c
char *strncpy(char *dest, const char *src, size_t n);
```
虽然加了个n，当时这个函数一点也不靠谱。它并不能保证dest的末尾一定是`'\0'`。来看看这个函数的简单实现（来自man手册）:

```c
char *
strncpy(char *dest, const char *src, size_t n)
{
	size_t i;

	for (i = 0; i < n && src[i] != '\0'; i++)
		dest[i] = src[i]; 

	for ( ; i < n; i++) 
		dest[i] = '\0'; 

	return dest; 
}
```

只有当n大于src的长度才会在dest的末尾填“\0”。
