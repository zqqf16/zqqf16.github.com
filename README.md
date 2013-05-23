我的个人blog，欢迎fork

**Feature**

- 轻量级
- 基于Markdown  
- 支持代码高亮
- 支持标签 

**依赖**

- markdown2 将markdown文本转换成HTML
- mako    	模板引擎
- pygments	代码着色工具
 
**步骤**

1. 在`blog`目录下新建文件：`example.md`
2. 编辑`example.md`，在文件开头插入：

	\----------  
	title: 标题  
	date: 2013-5-7  
	tags: 标签(可选)  
	category: 分类(可选)  
	\----------

3. `python peanut.py`生成相关文件
4. `python -m SimpleHTTPServer`，访问"0.0.0.0:8000"即可预览

**TODO**

- 支持分类（比较简单，只是目前没想好有啥用） 
- 没想好  
- 没想好  
- ……
