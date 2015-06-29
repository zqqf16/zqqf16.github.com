#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os
import markdown
import six

from datetime import datetime
from mako.template import Template
from mako.lookup import TemplateLookup

CONFIG = {
    'domain': 'blog.zorro.im',
    'title': u'穷折腾',
    'description': u'zqqf16 的个人博客',
    'author': 'zqqf16',
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
#    ('tags.html', 'tags/index.html', os.path.join('tags', 'index.html')),
#    ('rss.xml', 'rss.xml', 'rss.xml'),
)

# Model

class BaseModel(object):
    '''Base MOdel'''

    _object_pool = {}

    def __init__(self, mid):
        self.mid = mid

    @classmethod
    def get(cls, mid):
        '''Get instance'''
        return cls._object_pool.get(mid)

    @classmethod
    def add(cls, instance):
        '''Add instance'''
        cls._object_pool[instance.mid] = instance

    @classmethod
    def all(cls):
        '''Get all instances'''
        return cls._object_pool.values()


class HTMLPage(BaseModel):
    '''HTML Page'''

    def __init__(self, title, url, html_path):
        super(HTMLPage, self).__init__(title)
        self.title = title
        self.url = url
        self.html_path = html_path


class Tag(HTMLPage):
    '''Tag'''

    def __init__(self, title):
        url = 'tags/' + title + '.html'
        path = os.path.join('tags', title+'.html')
        super(Tag, self).__init__(title, url, path)

        self._post_ids = set()

    @property
    def posts(self):
        '''Get all posts that has this tag'''
        return [Post.get(p) for p in self._post_ids]

    def add_post(self, post):
        self._post_ids.add(post.mid)


class Category(Tag):
    '''Category'''

    def __init__(self, title):
        super(Category, self).__init(title)
        self.url = 'categories/' + title + '.html'
        self.file_path = os.path.join('categories', title+'.html')


class Post(HTMLPage):
    '''Post'''

    def __init__(self, title, content, slug,
            date=None,top=False, publish=True):

        url = 'posts/' + slug + '.html'
        path = os.path.join('posts', slug+'.html')
        super(Post, self).__init__(title, url, path)

        self.top = top
        self.publish = publish
        self.content = content
        self.date = date if date else datetime.now()

        self._tag_ids = set()
        self._category_id = None

    def add_tag(self, tag):
        self._tag_ids.add(tag.mid)
        tag.add_post(self)

    @property
    def tags(self):
        return [Tag.get(t) for t in self._tag_ids]

    @property
    def category(self):
        return Category.get(self._category_id)

    @category.setter
    def category(self, c):
        self._category_id = c.mid
        c.add_post(self)


class Writer(object):
    '''HTML file writer'''

    _TEMPLATE = TemplateLookup(
        directories=['theme'],
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

    def __init__(self):

        # Markdown extensions
        extensions = ['fenced_code', 'codehilite', 'meta', 'footnotes', 'tables', 'toc'],
        # Extension configurations
        configs = {'codehilite': [ ('guess_lang', False) ]}
        #self.md = markdown.Markdown(extensions=extensions,
        #                            extension_configs=configs)
        self.md = markdown.Markdown(extensions=['fenced_code', 'codehilite', 'meta', 'footnotes', 'tables', 'toc'], extension_configs={'codehilite': [ ('guess_lang', False) ]})

    def get_slug(self, file_name):
        m = self.regex.match(file_name)
        if not m:
            return None
        return m.group(1)

    # metadata handlers
    meta_handlers = {
        'tag':      lambda x: x if x else [],
        'title':    lambda x: x[0] if x else '',
        'category': lambda x: x[0] if x else None,
        'date':     lambda x: datetime.strptime(x[0], '%Y-%m-%d') if x else datetime.now(),
        'top':      lambda x: True if x and x[0]=='yes' else False,
        'publish':  lambda x: False if x and x[0]=='no' else True,
    }

    def parse_metadata(self, meta):
        res = {}
        for name, handler in self.meta_handlers.items():
            value = handler(meta.get(name))
            res[name] = value
        # Tag
        tag_titles = res.get('tag')
        if tag_titles:
            tags = set()
            for t in tag_titles:
                tag = Tag.get(t)
                if not tag:
                    tag = Tag(t)
                    Tag.add(tag)
                tags.add(tag)
            res.pop('tag')
        # Category
        category_title = res.get('category')
        if category_title:
            category = Category.get(category_title)
            if not category:
                category = Category(category_title)
                Category.add(category)
            res['category'] = category

        return res

    def read(self, file_name, slug=None):
        '''Read markdown file'''

        if not slug:
            slug = self.get_slug(file_name)

        if not slug:
            return None

        with open(file_name, 'r') as f:
            content = f.read()
            if six.PY2:
                content = content.decode('utf-8')

            html = self.md.reset().convert(content.strip(' \n'))
            if not self.md.Meta:
                return None

            meta = self.parse_metadata(self.md.Meta)
            post = Post(content=html, slug=slug, title=meta.get('title'),
                    top = meta.get('top'), publish = meta.get('publish'))

            tags = meta.get('tags')
            if tags:
                for t in tags:
                    post.add_tag(t)

            category = meta.get('category')
            if category:
                post.category = category

            return post

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
    posts = filter(lambda x: x.publish, posts)

    tags = Tag.all()
    tops = filter(lambda x: x.top, posts)

    namespace = {
        'posts': posts,
        'tags': tags,
        'tops': tops,
    }
    namespace.update(CONFIG)

    writer = Writer(namespace)

    #map(writer.write, tags)
    map(writer.write, posts)

    singles = []
    for layout, url, dest in SINGLE_FILES:
        singles.append(HTMLPage('', url, layout, dest))

    map(writer.write, singles)



if __name__ == '__main__':
    peanut()
