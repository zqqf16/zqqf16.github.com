---
layout: post
title: 写了一个简单的Web剪切板-Clipboard
date: 2013-12-19
tags:
    - Clipboard
    - tornado
---


平时由于工作的关系需要用到多台电脑，Mac和Windows来回切换。有时候想把一些信息复制到另一台电脑上，只能打开文件共享，然后把内容保存到文件里，再到另一台电脑里打开。时间一长，就积累了很多垃圾文件。于是乎就花了点时间，写了个简单的基于Web的内容共享程序，我叫它Clipboard。

源码在此：[github](https://github.com/zqqf16/clipboard)

我是把它当作一个练手项目来写的，尝试了很多新东西，也学到了很多。

**数据库**

一开始我把所有内容以JSON格式存储到文件里，为此写了一个简单的JSON-DB以及相应的ORM。（[View History](https://github.com/zqqf16/clipboard/blob/0eceea61e3d2e49fdafc73b88b5b42722a8ab192/clipboard/model.py)）在这个过程中充分的学习了Meta class以及Descriptor的相关知识。

后来考虑到以后可能会有更多功能，自己维护一套类似数据库有点不现实，所以就转向了Sqlite，并采用了一个比较小巧的ORM - Peewee。也就有了当前的版本。

**Unit Test**

从写JSON-DB的时候就仔仔细细的写了Unit Test，虽然最后还是发现了一些纰漏，但是还算成功。后来又加了Web层的Unit Test，学会了用Tornado的HTTPClient来测试，也算收获不小。

```python
class TestModel(unittest.TestCase):
    def setUp(self):
        application = app.App()
        http_server = tornado.httpserver.HTTPServer(application)
        http_server.listen(8888)

    def handle_request(self, response):
        self.response = response
        tornado.ioloop.IOLoop.instance().stop()

    def test_get(self):
        http_client = tornado.httpclient.AsyncHTTPClient()
        http_client.fetch('http://0.0.0.0:8888', self.handle_request)
        tornado.ioloop.IOLoop.instance().start()

        print self.response.body
```

**XMLHTTPRequest**

尝试了一把RESTful，但由于原生的HTML Form不支持DELETE方法，我又不想引入JQuery这样的牛刀。经过一番搜索，找着了XMLHTTPRequest。就照着网上的例子画了个瓢~

```Javascript
function delete_entry(id) {
        var form = new FormData();
        form.append("id", id);

        var xhr = new XMLHttpRequest();
        xhr.open("DELETE", "/c/"+id, true);
        xhr.responseType = "json";
        xhr.onload = function(e) {
                if (this.status == 200) {
                        var data = JSON.parse(this.response);
                        if (data.status == 'success'){
                                window.location.reload();
                        } else {
                                alert(data.status);
                        }
                } else {
                        alert('Connection error!');
                }
        };

        xhr.send(form);
};
```

**Others**

为了使开发的过程更加规范，我强制自己用了Github的issue功能，成功的解决了仅有的两个issue~

用了Yahoo的CSS框架 - Pure。Bootstrap太大了，而且默认的界面看疲劳了。所以就尝试了这个小清新的Pure。抄了不少官网的代码。最后的界面还凑合，不难看。

最后，上一张效果图~

![Clipboard](https://z_blog.oss-cn-hangzhou.aliyuncs.com/blog/clipboard.png?x-oss-process=style/jpg)