#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os
from mako.lookup import TemplateLookup
from datetime import datetime
from markdown2 import markdown

BLOG_PATH = 'blogs'

cfg = {
    'post_path': 'posts',
    'page_path': 'pages',
}

templates = TemplateLookup(
        directories=['templates'], 
        input_encoding='utf-8',
        output_encoding='utf-8', 
        encoding_errors='replace'
)

post_template = templates.get_template('post.html')
page_template = templates.get_template('page.html')
index_template = templates.get_template('index.html')

class Blog():
    def __init__(self, path, slug):
        self.path = path
        self.slug = slug
        self.title = None
        self.date = None
        self.tags = None
        self.category = None
        self.content_raw = None
        self.type = 'post'
        self.__content = None

        self.__parse_attr()

    def __repr__(self):
        return u'<date: %s, title: %s, slug: %s>' % (self.date, self.title, self.slug)

    def __parse_attr(self):
        '''
        ---
        title: Hello World
        date: 2012-03-23
        tags: tag1, tag2
        ---
        '''
        flag_re = re.compile(r'^---$')
        attr_re = re.compile(r'^(title|type|date|tags|category)\s*:\s*(.*)$')
        _file = open(self.path, 'r')

        attr_start = False
        while True:
            line = _file.readline().decode('utf-8')
            if not line:
                break;

            if attr_start == False:
                if flag_re.match(line):
                    # attribute start flag
                    attr_start = True
                else:
                    continue
            else:
                m = attr_re.match(line)
                if m:
                    # match
                    key = m.group(1)
                    val = m.group(2)
                    if key == 'title':
                        self.title = val
                    elif key == 'date':
                        self.date = datetime.strptime(val, '%Y-%m-%d')
                    elif key == 'tags':
                        self.tags = [t.strip(' \n') for t in val.split(',')]
                    elif key == 'category':
                        self.category = val
                    elif key == 'type':
                        self.type = val

                elif flag_re.match(line):
                    # attribute end flag
                    break

        self.content_raw = _file.read().lstrip('\n')
        _file.close()

    @property
    def content(self):
        if not self.__content:
            self.__content = markdown(self.content_raw)

        return self.__content

    @property
    def uri(self):
        path = cfg['post_path'] if self.type=='post' else cfg['page_path']
        return path+'/'+self.slug+'.html'

def get_all_thing(path):
    file_name_re = re.compile(r'(.*).md')

    posts = []
    pages = []
    tags = {}

    for f in os.listdir(path):
        m = file_name_re.match(f)
        if m:
            blog = Blog(path+'/'+f, m.group(1))
            if blog.type == 'post':
                posts.append(blog)
            elif blog.type == 'page':
                pages.append(blog)

            try:
                for tag in blog.tags:
                    if tags.get(tag):
                        tags[tag].append(blog)
                    else:
                        tags[tag] = [blog]
            except:
                pass

    return posts, pages, tags

def gen_post_html(pages, post):
    with open(post.uri, 'w') as f:
        html = post_template.render(pages=pages, post=post)
        f.write(html)
        f.close()

def gen_page_html(pages, page):
    with open(page.uri, 'w') as f:
        html = page_template.render(pages=pages, page=page)
        f.write(html)
        f.close()

def gen_index_html(posts, pages):
    with open('index.html', 'w') as f:
        html = index_template.render(posts=posts, pages=pages)
        f.write(html)
        f.close
        
def sort_blogs_by_date(blogs):
    blogs.sort(lambda x, y: cmp(x.date, y.date), reverse=True)
    
if __name__ == '__main__':
    posts, pages, tags  = get_all_thing(BLOG_PATH)
    for page in pages:
        gen_page_html(pages, page)

    sort_blogs_by_date(posts)

    for post in posts:
        gen_post_html(pages, post)

    gen_index_html(posts, pages)
