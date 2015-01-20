title: 理解Git的暂存区
date: 2013-6-5
tag: Git
tag: 暂存区

> 虽然用了几个月的 Git，但是今天才了解了“Index（暂存区域）”这个东西，惭愧啊。。。

在公司用的是 CVS，因此用`git add`的时候就以为和`cvs add`的作用是一样的，把新文件加到代码库。后来学了一招`git commit -a`，还以为-a就是--all的意思。稀里糊涂地用到现在。。。

Git 中的暂存区类似于任务列表，当对工作区的文件做了修改之后，执行

```bash
git add filename
```

就会把修改的文件加到这个任务列表中，当执行

```bash
git commit
```

的时候，暂存区中的改动就会提交到版本库中，而在“git add”之后所做的改动就不会被提交。

比如，我现在 Readme.md 文件中增加了一行，然后执行`git add Readme.md`。然后再加一行，执行`git commit`，这样我提交的只是第一次修改的内容。

命令

```bash
git checkout filename
```

是用暂存区中的文件来替换工作区中的文件。

命令

```bash
git checkout HEAD
```

是用HEAD指向的版本库中的文件来替换暂存区和工作区的文件。

好了，先这么多了。通过这件事总结出一个道理：经验有时候会形成思维定势。
