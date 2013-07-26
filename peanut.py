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

if __name__ == '__main__':
    p = Peanut('.')
    p.load()
    p.gen_all()
