#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os
from mako.template import Template
from mako.lookup import TemplateLookup
from datetime import datetime
import markdown

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

class Entry(object):
    template = None
    type = ''
    title = ''
    slug = ''

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

    def generate(self, **kargv):
        if not isinstance(self.template, Template):
            return

        kargv[self.type] = self

        with open(self.url, 'w') as f: 
            html = self.template.render(**kargv)
            f.write(html)

class Tag(Entry):
    template = TEMPLATES.get_template('tag.html')
    type = 'tag'

    _pool = dict()
    @classmethod
    def create(cls, title):
        t = cls._pool.get(title)
        if t:
            return t
        t = cls(title)
        cls._pool[title] = t
        return t

    @classmethod
    def all(cls):
        return cls._pool.values()
    
    def __init__(self, title):
        super(Tag, self).__init__(title=title, slug=title)
        self.posts = []

    def generate(self, **kargv):
        self.posts.sort(lambda x, y: cmp(x.date, y.date), reverse=True)
        kargv['posts'] = self.posts

        super(Tag, self).generate(**kargv)

class Page(Entry):
    template = TEMPLATES.get_template('page.html')
    type = 'page'

    def __init__(self, title, content, slug, date=None):
        super(Page, self).__init__(title=title, slug=slug)

        self.content = content

        if not date:
            date = datetime.now()

        self.date = date

class Post(Page):
    template = TEMPLATES.get_template('post.html')
    type = 'post'

    def __init__(self, title, content, slug, date=None, tags=[]):
        super(Post, self).__init__(title, content, slug, date=date)
        self.tags = []
        for t in tags:
            tag = Tag.create(t)
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
        ''' Parse draft files to generate posts, pages and tags.
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
                            date=meta['date'], tags=meta['tag'])
            elif meta['type'] == 'page':
                entry = Page(meta['title'], html, self.slug,
                            date=meta['date'])

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
    }

    namespace.update(CONFIG)

    for tag in tags:
        tag.generate(**namespace)
    for post in posts:
        post.generate(**namespace)
    for page in pages:
        page.generate(**namespace)

    static_files = ['index.html', 'rss.xml', 'sitemap.xml']
    for f in static_files:
        e = Entry(url=f, template=f)
        e.generate(**namespace)

if __name__ == '__main__':
    peanut()
