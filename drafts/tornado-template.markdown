title: Tornado源码之Template
date: 2013-11-19
tag: tornado
tag: template

Tornado底层的源码分析已经有很多人写过了，他们的水平都在我之上，写的也比我好，所以我就不再重复了。打算剑走偏锋，研究一下tornado周边的东西。于是乎就打算从之前一直感兴趣的Template入手。

Template的工作流程如下：

1. 读取模板文件，解析成相应的数据结构
2. 把解析到的结构拼接成Python代码
3. 将生成的代码编译成字节码
4. 执行字节码，返回结果

这其中还会有一些编码转换、特殊字符转义等工作，本文中不做研究。

步骤1-3主要由Template类的__init__方法完成，关键代码如下：

```python
reader = _TemplateReader(name, escape.native_str(template_string))
self.file = _File(self, _parse(reader, self))
self.code = self._generate_python(loader, compress_whitespace)
```

首先创建了一个reader，用来读取模板字符串。`_TemplateReader`这个类还重载了一些诸如`__getitem__`这样的方法，可以很方便的来操作字符串。

`_parse`这个函数负责了模板的语法的解析和数据结构的生成。在这个过程中，会将`{{title}}`这样的字符串解析成`_Expression`，`{% for line in lines %}`解析成`_IntermediateControlBlock`等。这些类都继承自`_Node`，最终会返回一个由这些类为节点组成的树状结构，树的根节点是`_File`。

当字符串解析完成之后，调用Template的`_generate_python`方法，来生成Python代码。代码生成时会调用每个树节点的`generate`方法。

`_File`的`generate`代码如下：

```python
def generate(self, writer):
    writer.write_line("def _tt_execute():", self.line)
    with writer.indent():
        writer.write_line("_tt_buffer = []", self.line)
        writer.write_line("_tt_append = _tt_buffer.append", self.line)
        self.body.generate(writer)
        writer.write_line("return _tt_utf8('').join(_tt_buffer)", self.line)
```

这个方法会会生成类似这样的语句：

```python
def __tt_execute():
    _tt_buffer = []
    _tt_append = _tt_buffer.append

    #body

    return _tt_utf8('').join(_tt_buffer) 
```

也就是说，最终生成的代码都会被嵌套在一个叫`__tt_execute`的函数内，函数内所有语句生成的字符串会被塞到_tt_buffer中被返回。

在这里举个简单的例子来看一下生成的代码：

```python
from tornado.template import Template

html = '''\
<ul>
{% for l in lines %}
    <li>{{l}}</li>
{% end %}
</ul>
'''

t = Template(html)
print(t.code)
```

执行完这段代码打印结果如下：

```python
def _tt_execute():  # <string>:0
    _tt_buffer = []  # <string>:0
    _tt_append = _tt_buffer.append  # <string>:0
    _tt_append('<ul>\n')  # <string>:2
    for l in lines:  # <string>:2
        _tt_append('\n    <li>')  # <string>:3
        _tt_tmp = l  # <string>:3
        if isinstance(_tt_tmp, _tt_string_types): _tt_tmp = _tt_utf8(_tt_tmp)  # <string>:3
        else: _tt_tmp = _tt_utf8(str(_tt_tmp))  # <string>:3
        _tt_tmp = _tt_utf8(xhtml_escape(_tt_tmp))  # <string>:3
        _tt_append(_tt_tmp)  # <string>:3
        _tt_append('</li>\n')  # <string>:4
        pass  # <string>:2
    _tt_append('\n</ul>\n')  # <string>:6
    return _tt_utf8('').join(_tt_buffer)  # <string>:0
```

生成的每条语句后都会有该语句在模板文件中的行号。

代码生成之后，就调用python的`compile`函数，将代码编译成了字节码。

当执行Template的`generate`方法时，首先会把一些常用函数比如`datetime`等以及用户输入的参数放到namespace中，而这个namespace会成为执行字节码时的全局变量。

tornado实现了一个叫`exec_in`的函数