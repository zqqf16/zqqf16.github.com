---
title: Python命令行参数解析工具——argparse
date: 2013-10-22
tags:
    - argparse
    - python
    - diff
---

鄙司一直用的CVS来代码管理，每次提交代码都相当的繁琐。先diff，再review，再commit。由于代码量庞大，有可能同时在修好几个bug。一不小心就会误改一些不相关的文件，所以每次diff的时候都需要仔细看一遍改过的文件。

之前用Python写了一个解析工具，可以从Diff文件中提取出修改过的文件列表，很方便的就可以找出不相关的文件，提交代码的时候也能省去很多麻烦。原理十分简单，主要是用正则表达式`^Index: (.*)$`来找出所有以“Index”开头的行。

前几天在用着个工具的时候想用一下管道，结果发现当时写的太简单了，不支持……趁着空闲就花了点时间改造了一下，让它既支持从文件中读取，又支持stdin读取。既可以返回文件列表，又可以方便CVS操作的文件名串。

刚开始打算用命令行解析的传统方法`getopt`来搞定，用了一会发现getopt有些弱，帮助啥的还得自己写。于是乎进行一番搜索，发现了argparse，一个更好的命令行参数解析工具。

使用方法很简单，以我的小工具为例：

```python
import argparse

parser = argparse.ArgumentParser(description='Get changed files from diff')

parser.add_argument('file', nargs='?', help='Diff file')
parser.add_argument('-i', dest='input', action='store_true',
                    help='Read diff string from stdin')
parser.add_argument('-l', dest="list", action='store_true',
                    help='List all files')

args = parser.parse_args()
```

它会自动生成一个很好看的帮助信息：

```bash
$getfile
usage: getfile [-h] [-i] [-l] [file]

Get changed files from diff

positional arguments:
  file        Diff file

optional arguments:
  -h, --help  show this help message and exit
  -i          Read diff string from stdin
  -l          List all files
```

完整的代码如下：

```python
#!/usr/bin/env python

import re
import sys
import argparse

FILE_RE = re.compile(r'^Index: (.*)$')

def get_files_from_diff(diff):
    res = []
    for line in diff:
        m = FILE_RE.match(line)
        if m:
            res.append(m.group(1))

    return res

def main():
    parser = argparse.ArgumentParser(description='Get changed files from diff')
    parser.add_argument('file', nargs='?', help='Diff file')
    parser.add_argument('-i', dest='input', action='store_true',
                        help='Read diff string from stdin')
    parser.add_argument('-l', dest="list", action='store_true',
                        help='List all files')


    args = parser.parse_args()

    if args.input:
        ret = get_files_from_diff(sys.stdin)
    elif args.file:
        try:
            with open(args.file, 'r') as f:
                ret = get_files_from_diff(f)
        except:
            print('\033[;31m[ERROR!] \033[0mFail to open "{0}"'.format(args.file))
            exit(-1)
    else:
        parser.print_help()
        exit(2)

    if args.list:
        for index, text in enumerate(ret):
            print('\033[;33m[{0}] \033[;32m{1}\033[0m'.format(index, text))
    else:
        print(' '.join(ret))

if __name__ == '__main__':
    main()
```

或者[Gist](https://gist.github.com/zqqf16/7094628)
