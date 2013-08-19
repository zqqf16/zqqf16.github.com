#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os
from mako.lookup import TemplateLookup
from datetime import datetime
# from markdown2 import markdown
# Use python-markdown to relpace markdown2
import markdown

CONFIG = {
    'domain': 'zqqf16.info',
    'title': u'穷折腾',
    'description': u'des',
}

PATH = {
    'draft':    'drafts',
    'post':     'posts',
    'page':     'pages',
    'tag':      'tags',
}

def get_url(type, name):
    return PATH[type]+'/'+name+'.html'

class Tag(object):
    def __init__(self, name):
        self.name = name
        self.posts = []
        self.url = get_url('tag', self.name)

class Post(object):
    def __init__(self, title, content, slug, date=None, tags=[]):
        self.title = title
        self.content = content
        self.slug = slug
        if date:
            self.date = date
        else:
            self.date = datetime.now()

        self.tags = []
        for tag in tags:
            tag.posts.append(self)
            self.tags.append(tag)

        self.url = get_url('post', self.slug)

class Page(object):
    def __init__(self, title, content, slug, date=None):
        self.title = title
        self.content = content
        self.slug = slug
        if date:
            self.date = date
        else:
            self.date = datetime.now()

        self.url = get_url('page', self.slug)

class Draft(object):
    file_name_re = re.compile(r'([^/]+)\.(md|markdown)')
    _instance = None

    def __new__(cls, *args, **kwargs):
        #singleton
        if not isinstance(cls._instance, Draft):
            cls._instance = super(Draft, cls).__new__(cls, *args, **kwargs)
        return cls._instance
        
    def __init__(self, directory = PATH['draft']):
        self.directory = directory
        self._data = {
            'posts': [],
            'pages': [],
            'tags':  {},
        }

    # metadata handlers
    _META_HANDLERS = {
        'tag':      lambda x: x if x else [],
        'title':    lambda x: x[0] if x else '',
        'date':     lambda x: datetime.strptime(x[0], '%Y-%m-%d') if x else datetime.now(),
        'category': lambda x: x[0] if x else None,
        'type':     lambda x: x[0] if x else 'post',
    }

    def __parse_metadata(self, meta):
        res = {}
        for name, handler in self._META_HANDLERS.items():
            value = handler(meta.get(name, None))
            res[name] = value

        return res

    def __get_tags(self, name_list):
        ''' If tag name exists in self._data['tags'], return it.
            Else create a new tag and return it.
        '''
        tags = []
        for name in name_list:
            tag = self._data['tags'].get(name)
            if tag:
                tags.append(tag)
            else:
                tag = Tag(name)
                self._data['tags'][name] = tag
                tags.append(tag)
        return tags

    def load(self):
        ''' Parse draft files to generate posts, pages and tags.
            Draft file should be named as 'xxx.md' or 'xxx.markdown'.
        '''
        md = markdown.Markdown(extensions=['fenced_code', 'codehilite', 'meta'])
        for f in os.listdir(self.directory):
            m = self.file_name_re.search(f)
            if not m: 
                continue
            slug = m.group(1)

            filepath = os.path.join(self.directory, f)
            with open(filepath, 'r') as f:
                content = f.read().decode('utf-8')
                html = md.reset().convert(content.strip(' \n'))
                if not md.Meta:
                    #No need to convert this draft
                    continue

                meta = self.__parse_metadata(md.Meta)
                tags = self.__get_tags(meta['tag'])

                if meta['type'] == 'post':
                    post = Post(meta['title'], html, slug,
                                meta['date'], tags)
                    self._data['posts'].append(post)
                elif meta['type'] == 'page':
                    page = Page(meta['title'], html, slug,
                                meta['date'])
                    self._data['pages'].append(page)

        self._sort_posts_by_date()
    
    def _sort_posts_by_date(self):
        self._data['posts'].sort(lambda x, y: cmp(x.date, y.date), reverse=True)

    @property
    def posts(self):
        return self._data['posts']

    @property
    def pages(self):
        return self._data['pages']

    @property
    def tags(self):
        return [value for name,value in self._data['tags'].items()]

_TEMPLATES = TemplateLookup(
    directories=['templates'], 
    input_encoding='utf-8',
    output_encoding='utf-8', 
    encoding_errors='replace'
)

def generate_file(template, path, **namespace):
    with open(path, 'w') as f: 
        html = template.render(**namespace)
        f.write(html)

def peanut():
    drafts = Draft()
    drafts.load()
    tags = drafts.tags
    posts = drafts.posts
    pages = drafts.pages

    post_temp = _TEMPLATES.get_template('post.html')
    page_temp = _TEMPLATES.get_template('page.html')
    tag_temp =  _TEMPLATES.get_template('tag.html')
    index_temp = _TEMPLATES.get_template('index.html')
    rss_temp = _TEMPLATES.get_template('rss.xml')
    sitemap_temp = _TEMPLATES.get_template('sitemap.xml')
    
    namespace = {
        'tags': tags,
        'posts': posts,
        'pages': pages,
    }

    namespace.update(CONFIG)

    for tag in tags:
        generate_file(tag_temp, tag.url, tag=tag, **namespace)
    for post in posts:
        generate_file(post_temp, post.url, post=post, **namespace)
    for page in pages:
        generate_file(page_temp, page.url, page=page, **namespace)

    generate_file(index_temp, 'index.html', **namespace)
    generate_file(rss_temp, 'rss.xml', **namespace)
    generate_file(sitemap_temp, 'sitemap.xml', **namespace)

if __name__ == '__main__':
    peanut()
