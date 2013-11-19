title: Tornado源码之Template
date: 2013-11-19
tag: tornado
tag: template

Tornado底层的源码分析已经有很多人写过了，他们的水平都在我之上，写的也比我好，所以我就不再重复了。打算剑走偏锋，研究一下tornado周边的东西。这次就从Template入手。

Tornado的模版系统用起来很顺手，小巧精悍，基本上可以满足我所有的功能。语法啥的我就不细说了，比较简单，一看就会。这里只描述一下它的工作过程。

首先，看一下Template类的`__init__`函数：

```python
def __init__(self, template_string, name="<string>", loader=None,
                 compress_whitespace=None, autoescape=_UNSET):
        self.name = name
        if compress_whitespace is None:
            compress_whitespace = name.endswith(".html") or \
                name.endswith(".js")
        if autoescape is not _UNSET:
            self.autoescape = autoescape
        elif loader:
            self.autoescape = loader.autoescape
        else:
            self.autoescape = _DEFAULT_AUTOESCAPE
        self.namespace = loader.namespace if loader else {}
        reader = _TemplateReader(name, escape.native_str(template_string))
        self.file = _File(self, _parse(reader, self))
        self.code = self._generate_python(loader, compress_whitespace)
        self.loader = loader
        try:
            # Under python2.5, the fake filename used here must match
            # the module name used in __name__ below.
            # The dont_inherit flag prevents template.py's future imports
            # from being applied to the generated code.
            self.compiled = compile(
                escape.to_unicode(self.code),
                "%s.generated.py" % self.name.replace('.', '_'),
                "exec", dont_inherit=True)
        except Exception:
            formatted_code = _format_code(self.code).rstrip()
            app_log.error("%s code:\n%s", self.name, formatted_code)
            raise
```

先忽略autoescape，loader等部分，这些对研究工作流程没有影响。终点在于这几句：

```python
reader = _TemplateReader(name, escape.native_str(template_string))
self.file = _File(self, _parse(reader, self))
self.code = self._generate_python(loader, compress_whitespace)
```

首先，创建了一个reader，用来负责一行一行读取模版字符串。这个reader里面用到了slice()，这玩意以前从来没接触过。。。困惑了好久。。。

_parse这个函数干了十分重要的工作，它负责从reader中读取字符并按照语法规则进行解析，生成相应的数据结构。语法解析就不细说了，主要看生成的数据结构。


