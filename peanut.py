#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os
from mako.lookup import TemplateLookup
from datetime import datetime
from markdown2 import markdown

config = {
    'title': u'穷折腾',
    'path': {
        'draft': 'drafts/',
        'post': 'posts/',
        'page': 'pages/',
        'tag': 'tags/',
        'rss': 'rss.xml',
        'sitemap': 'sitemap.xml',
    },
    'domain': 'zqqf16.info',
}

_DRAFT_PATH = config['path']['draft']

templates = TemplateLookup(
    directories=['templates'], 
    input_encoding='utf-8',
    output_encoding='utf-8', 
    encoding_errors='replace'
)

class Tag():
    template = templates.get_template('tag.html')

    def __init__(self, name):
        self.name = name
        self.posts = []
        self.path = config['path']['tag'] + self.name

    def generate(self, info):
        ''' Generate html file '''

        if not os.path.exists(self.path):
            os.mkdir(self.path)

        filepath = os.path.join(self.path, 'index.html')
        with open(filepath, 'w') as f: 
            self.posts.sort(lambda x, y: cmp(x.date, y.date), reverse=True)
            html = self.template.render(info=info, tag=self, posts=self.posts)
            f.write(html)

class Blog():
    template = templates.get_template('post.html')

    def __init__(self):
        self.__slug = ''
        self.tags = []
        self.title = ''
        self.date = ''
        self.category = None
        self.type = 'post'

    def __get_meta_handler(self, meta):
        handlers = {
            'tags':     lambda x: [Tag(t.strip(' \n')) for t in x.split(',')],
            'title':    lambda x: x,
            'date':     lambda x: datetime.strptime(x, '%Y-%m-%d'),
            'category': lambda x: x,
            'type':     lambda x: x,
        }
        try:
            return handlers[meta]
        except:
            return lambda x: x

    def __parse_metadata(self):
        self.tags = []
        self.title = ''
        self.date = datetime.now()
        self.category = None
        self.type = 'post'

        for key, value in self.__meta.items():
            self.__dict__[key] = self.__get_meta_handler(key)(value)

        path = config['path']['post'] if self.type=='post' else config['path']['page']
        self.path = path + self.__slug + '.html'

    def read(self, filepath):
        ''' Read blog content and metadata from file'''

        file_name_re = re.compile(r'([^/]+)\.(md|markdown)')
        m = file_name_re.search(filepath)
        if not m: 
            return

        self.__slug = m.group(1)

        with open(filepath, 'r') as f:
            content = f.read().decode('utf-8')
            self.content = markdown(content.strip(' \n'), 
                                 extras=["fenced-code-blocks", "metadata"])
            self.__meta = self.content.metadata
            self.__parse_metadata()

    def generate(self, info):
        ''' Generate html file '''

        with open(self.path, 'w') as f: 
            html = self.template.render(info=info, post=self)
            f.write(html)

class Peanut():
    def __init__(self, path):
        self.path = path
        self.info = {
            'posts': [],
            'pages': [],
            'tags': [],
            'domain': config['domain'],
            'title': config['title'],
        }

    def load(self, draft_path=_DRAFT_PATH):
        '''Load blogs from files'''

        posts = []
        pages = []
        tags = {}

        path = self.path+'/'+draft_path
        for f in os.listdir(path):
            blog = Blog()
            blog.read(path+'/'+f)

            if blog.type == 'post':
                posts.append(blog)
            elif blog.type == 'page':
                pages.append(blog)
                continue

            try:
                for tag in blog.tags:
                    name = tag.name
                    if tags.get(name):
                        tags[name].posts.append(blog)
                    else:
                        t = Tag(name)
                        t.posts.append(blog)
                        tags[name] = t
            except:
                pass

        posts.sort(lambda x, y: cmp(x.date, y.date), reverse=True)
        self.info['posts'] = posts
        self.info['pages'] = pages
        self.info['tags'] = tags

    def gen_html_posts(self):
        for p in self.info['posts']:
            p.generate(self.info)

    def gen_html_pages(self):
        for p in self.info['pages']:
            p.generate(self.info)

    def gen_html_tags(self):
        for n, t in self.info['tags'].items():
            t.generate(self.info)

    def gen_html_index(self):
        template = templates.get_template('index.html')
        with open('index.html', 'w') as f: 
            html = template.render(info=self.info, posts=self.info['posts'])
            f.write(html)

    def gen_xml_sitemap(self):
        template = templates.get_template('sitemap.xml')
        with open('sitemap.xml', 'w') as f:
            xml = template.render(info=self.info, pages=self.info['pages'], posts=self.info['posts'])
            f.write(xml)

    def gen_xml_rss(self):
        template = templates.get_template('rss.xml')
        with open('rss.xml', 'w') as f:
            xml = template.render(info=self.info, posts=self.info['posts'][:5])
            f.write(xml)

    def gen_all(self):
        self.gen_html_posts()
        self.gen_html_pages()
        self.gen_html_tags()
        self.gen_html_index()
        self.gen_xml_sitemap()
        self.gen_xml_rss()

#MVC start

'''
    M -- post/tag/page
    V -- template
    C -- peanut

    Usage:
    posts = Post.find_all()
    tags = Tag.find_all()
    pages = Page.find_all()

    for tag in post.tags:
        pass
    for post in tag.posts:
        pass
'''
_DRAFT_DIR = 'draft'

class Tag(object):
    def __init__(self, name):
        self.name = name
        self.posts = []
        self.url = 'tag_url'

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

class Page(object):
    def __init__(self, title, content, slug, date=None):
        self.title = title
        self.content = content
        self.slug = slug
        if date:
            self.date = date
        else:
            self.date = datetime.now()

class Database(object):
    #TODO must singleton
    file_name_re = re.compile(r'([^/]+)\.(md|markdown)')

    def __init__(self, directory = _DRAFT_DIR):
        self.directory = directory
        self.posts = []
        self.pages = []
        self.tags = {}

    _META_HANDLER = {
        'tags':     lambda x: [t.strip(' \n') for t in x.split(',')] if x else [],
        'title':    lambda x: x if x else '',
        'date':     lambda x: datetime.strptime(x, '%Y-%m-%d') if x else datetime.now(),
        'category': lambda x: x if x else None,
        'type':     lambda x: x if x else 'post',
    }

    def __parse_metadata(self, meta):
        res = {}
        for name, handler in self._META_HANDLER.items():
            value = handler(meta.get(name))
            res[name] = value

        return res

    def get_tags(self, name_list):
        tags = []
        for name in name_list:
            if self.tags.get(name):
                tags.append(self.tags[name])
            else:
                tag = Tag(name)
                self.tags[name] = tag
                tags.append(tag)
        return tags

    def load(self):
        for f in os.listdir(self.directory):
            m = self.file_name_re.search(f)
            if not m: 
                continue
            slug = m.group(1)

            filepath = os.path.join(self.directory, f)
            with open(filepath, 'r') as f:
                content = f.read().decode('utf-8')
                html = markdown(content.strip(' \n'), 
                                extras=["fenced-code-blocks", "metadata"])
                if not hasattr(html, 'metadata'):
                    #No need to convert this draft
                    continue
                meta = self.__parse_metadata(html.metadata)
                tags = self.get_tags(meta['tags'])

                if meta['type'] == 'post':
                    post = Post(meta['title'], html, slug,
                                meta['date'], tags)
                    self.posts.append(post)
                elif meta['type'] == 'page':
                    page = Page(meta['title'], html, slug,
                                meta['date'])
                    self.pages.append(page)
        
        self.posts.sort(lambda x, y: cmp(x.date, y.date), reverse=True)

if __name__ == '__main__':
    p = Peanut('.')
    p.load()
    p.gen_all()
