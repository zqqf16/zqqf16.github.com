#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os
import weakref
import markdown

from datetime import datetime
from mako.template import Template
from mako.lookup import TemplateLookup

CONFIG = {
    'domain': 'blog.zorro.im',
    'title': u'穷折腾',
    'description': u'Zqqf16的个人BLog，记录我的生活、学习、以及心情。',
}

PATH = {
    'draft':    'drafts',
    'post':     'posts',
    'page':     'pages',
    'tag':      'tags',
}

SINGLE_FILES = (
    #layout, url, dest
    ('index.html', 'index.html', 'index.html'),
    ('sitemap.xml', 'sitemap.xml', 'sitemap.xml'),
    ('tags.html', 'tags/index.html', os.path.join('tags', 'index.html')),
    ('rss.xml', 'rss.xml', 'rss.xml'),
)

class Pool(type):
    '''Meta class to implement a simple "object pool".
    '''
    def __new__(self, name, bases, attrs):
        '''Add an attribute "_pool" and a classmethod "all".
        '''
        def all(cls):
            return cls._pool.values()

        def get(cls, id):
            return cls._pool.get(id)

        attrs['_pool'] = {}
        attrs['all'] = classmethod(all)
        attrs['get'] = classmethod(get)

        return super(Pool, self).__new__(self, name, bases, attrs)

    def __call__(cls, *args, **kwargs):
        identity = tuple(*args, **kwargs)
        if identity in cls._pool:
            #Get from pool
            return cls._pool[identity]

        #Generate a new one
        instance = super(Pool, cls).__call__(*args, **kwargs)
        cls._pool[identity] = instance
        setattr(instance, 'id', identity)

        return instance

class HTMLPage(object):
    '''Base class for HTML Page'''

    def __init__(self, title, url, layout, dest):
        self.title = title
        self.url = url
        self.layout = layout
        self.dest = dest

class Post(HTMLPage):
    def __init__(self, title, content, slug, date, layout='post.html', top=False, publish=True, tag=[]):
        url = 'posts/'+slug+'.html' 
        dest = os.path.join('posts', slug+'.html')

        super(Post, self).__init__(title, url, layout, dest)

        self.top = top
        self.publish = publish
        self.content = content
        self.date = date

        self.tags = tag
        for t in tag:
            t.add_post(self)
 
class Tag(HTMLPage):
    __metaclass__ = Pool

    def __init__(self, title):
        url = 'tags/'+title+'.html'
        dest = os.path.join('tags', title+'.html')

        super(Tag, self).__init__(title, url, 'tag.html', dest)

        self._posts = {}

    def add_post(self, post):
        self._posts[post.title] = weakref.ref(post)

    @property
    def posts(self):
        return filter(None, [p() for p in self._posts.values()])

class Writer(object):
    '''HTML file writer'''

    _TEMPLATE = TemplateLookup(
        directories=['templates'], 
        input_encoding='utf-8',
        output_encoding='utf-8', 
        encoding_errors='replace'
    )    

    def __init__(self, namespace={}):
        self.namespace = namespace

    def write(self, page):
        '''Write entry to files'''
        temp = self._TEMPLATE.get_template(page.layout)

        with open(page.url, 'w') as f:
            p = temp.render(this=page, **self.namespace)
            f.write(p)

class Reader(object):
    '''Markdown reader'''

    regex = re.compile(r'([^/]+)\.(md|markdown)')

    # metadata handlers
    meta_handlers = {
        'tag':      lambda x: [Tag(t) for t in x] if x else [],
        'title':    lambda x: x[0] if x else '',
        'date':     lambda x: datetime.strptime(x[0], '%Y-%m-%d') if x else datetime.now(),
        'top':      lambda x: True if x and x[0]=='yes' else False,
        'publish':  lambda x: False if x and x[0]=='no' else True,
    }

    def parse_metadata(self, meta):
        res = {}
        for name, handler in self.meta_handlers.items():
            value = handler(meta.get(name, None))
            res[name] = value

        return res

    def __init__(self):
        self.md = markdown.Markdown(extensions=['fenced_code', 'codehilite', 'meta'], 
                                    extension_configs={'codehilite': [ ('guess_lang', False) ]})
 
    def get_slug(self, file_name):
        m = self.regex.match(file_name)
        if not m:
            return None
        return m.group(1)

    def read(self, file_name, slug=None):
        '''Read markdown file and get the HTML and META data.'''

        if not slug:
            slug = self.get_slug(file_name)

        if not slug:
            return None

        with open(file_name, 'r') as f:
            content = f.read().decode('utf-8')
            html = self.md.reset().convert(content.strip(' \n'))
            if not self.md.Meta:
                return None

            meta = self.parse_metadata(self.md.Meta)
            return Post(content=html, slug=slug, **meta)

    def read_all(self, directory):
        '''Read all markdown files in the directory'''

        posts = []
        for f in os.listdir(directory):
            slug = self.get_slug(f)
            p = self.read(os.path.join(directory, f), slug)

            if p:
                posts.append(p)

        return posts

def peanut():
    reader = Reader()

    posts = reader.read_all(PATH['draft'])
    posts.sort(lambda x, y: cmp(x.date, y.date), reverse=True)
    tags = Tag.all()
    tops = filter(lambda x: x.top, posts)

    namespace = {
        'posts': posts,
        'tags': tags,
        'tops': tops,
    }
    namespace.update(CONFIG)

    writer = Writer(namespace)

    map(writer.write, tags)
    map(writer.write, posts)

    singles = []
    for layout, url, dest in SINGLE_FILES:
        singles.append(HTMLPage('', url, layout, dest))

    map(writer.write, singles)



if __name__ == '__main__':
    peanut()
