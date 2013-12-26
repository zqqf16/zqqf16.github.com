#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os
import markdown

from datetime import datetime
from mako.template import Template
from mako.lookup import TemplateLookup

CONFIG = {
    'domain': 'zqqf16.info',
    'title': u'穷折腾',
    'description': u'Zqqf16的个人BLog，记录我的生活、学习、以及心情。',
}

PATH = {
    'draft':    'drafts',
    'post':     'posts',
    'page':     'pages',
    'tag':      'tags',
}

TEMPLATES = TemplateLookup(
    directories=['templates'], 
    input_encoding='utf-8',
    output_encoding='utf-8', 
    encoding_errors='replace'
)

SINGLE_FILES = (
    #(template, path)
    ('index.html', 'index.html'),
    ('sitemap.xml', 'sitemap.xml'),
    ('tags.html', 'tags/index.html'),
    ('rss.xml', 'rss.xml'),
)

class Entry(object):
    template = None
    type = ''

    def __init__(self, **kargs):
        self.title = kargs.get('title', '')
        self.slug = kargs.get('slug', '')
        self.static_url = kargs.get('url', '')
        template_file = kargs.get('template', '')
        if template_file:
            self.template = TEMPLATES.get_template(template_file)

    @property
    def url(self):
        if self.static_url:
            return self.static_url
        return PATH[self.type]+'/'+self.slug+'.html'

    def generate(self, **kwargv):
        if not isinstance(self.template, Template):
            return

        kwargv[self.type] = self

        with open(self.url, 'w') as f: 
            html = self.template.render(**kwargv)
            f.write(html)

class Pool(type):
    '''Meta class to implement a simple "object pool".
    '''
    def __new__(self, name, bases, attrs):
        '''Add an attribute "_pool" and a classmethod "all".
        '''

        def all(cls):
            return cls._pool.values()

        attrs['_pool'] = {}
        attrs['all'] = classmethod(all)

        return super(Pool, self).__new__(self, name, bases, attrs)

    def __call__(cls, *args, **kwargs):
        identity = tuple(*args, **kwargs)
        if identity in cls._pool:
            #Get from pool
            return cls._pool[identity]

        #Generate a new one
        instance = super(Pool, cls).__call__(*args, **kwargs)
        cls._pool[identity] = instance

        return instance

class Tag(Entry):
    template = TEMPLATES.get_template('tag.html')
    type = 'tag'

    __metaclass__ = Pool

    def __init__(self, title):
        super(Tag, self).__init__(title=title, slug=title)
        self.posts = []

    def generate(self, **kwargv):
        self.posts.sort(lambda x, y: cmp(x.date, y.date), reverse=True)
        kwargv['posts'] = self.posts

        super(Tag, self).generate(**kwargv)

class Page(Entry):
    template = TEMPLATES.get_template('page.html')
    type = 'page'

    def __init__(self, title, content, slug, date=None, publish='yes'):
        super(Page, self).__init__(title=title, slug=slug)

        self.content = content

        if not date:
            date = datetime.now()
        self.date = date

        if publish.lower() == 'yes':
            self.publish = True
        else:
            self.publish = False

    def generate(self, **kwargv):
        if not self.publish:
            return
        super(Page, self).generate(**kwargv)

class Post(Page):
    template = TEMPLATES.get_template('post.html')
    type = 'post'

    def __init__(self, title, content, slug, date=None, publish='yes', tags=[]):
        super(Post, self).__init__(title, content, slug, date=date, publish=publish)

        self.tags = []
        for t in tags:
            tag = Tag(t)
            tag.posts.append(self)
            self.tags.append(tag)

class Draft(object):
    regex = re.compile(r'([^/]+)\.(md|markdown)')

    def __init__(self, path, slug):
        self.path = path
        self.slug = slug

    # metadata handlers
    meta_handlers = {
        'tag':      lambda x: x if x else [],
        'title':    lambda x: x[0] if x else '',
        'date':     lambda x: datetime.strptime(x[0], '%Y-%m-%d') if x else datetime.now(),
        'category': lambda x: x[0] if x else None,
        'type':     lambda x: x[0] if x else 'post',
        'publish':  lambda x: x[0] if x else 'yes',
    }

    def parse_metadata(self, meta):
        res = {}
        for name, handler in self.meta_handlers.items():
            value = handler(meta.get(name, None))
            res[name] = value

        return res

    md = markdown.Markdown(extensions=['fenced_code', 'codehilite', 'meta'],
                           extension_configs={
                               'codehilite': [
                                   ('guess_lang', False),
                               ]
                           })
    def convert(self):
        '''Parse draft files to generate posts, pages and tags.
           Draft file should be named as 'xxx.md' or 'xxx.markdown'.
        '''
        entry = None
        with open(self.path, 'r') as f:
            content = f.read().decode('utf-8')
            html = self.md.reset().convert(content.strip(' \n'))
            if not self.md.Meta:
                #No need to convert this draft
                return None

            meta = self.parse_metadata(self.md.Meta)

            if meta['type'] == 'post':
                entry = Post(meta['title'], html, self.slug,
                             date=meta['date'], tags=meta['tag'], 
                             publish=meta['publish'])
            elif meta['type'] == 'page':
                entry = Page(meta['title'], html, self.slug,
                             date=meta['date'],
                             publish=meta['publish'])

        return entry

def get_drafts(path):
    drafts = []
    for f in os.listdir(path):
        m = Draft.regex.match(f)
        if not m:
            continue

        slug = m.group(1)
        draft = Draft(os.path.join(path, f), slug)
        drafts.append(draft)

    return drafts

def peanut():
    drafts = get_drafts(PATH['draft'])

    posts = []
    pages = []

    for d in drafts:
        p = d.convert()
        if p.type == 'post':
            posts.append(p)
        elif p.type == 'page':
            pages.append(p)

    posts.sort(lambda x, y: cmp(x.date, y.date), reverse=True)
    pages.sort(lambda x, y: cmp(x.date, y.date), reverse=True)

    tags = Tag.all()

    namespace = {
        'posts': posts,
        'pages': pages,
        'tags': tags,
    }
    namespace.update(CONFIG)

    for tag in tags:
        tag.generate(**namespace)
    for post in posts:
        post.generate(**namespace)
    for page in pages:
        page.generate(**namespace)

    for f in SINGLE_FILES:
        e = Entry(url=f[1], template=f[0])
        e.generate(**namespace)

if __name__ == '__main__':
    peanut()
