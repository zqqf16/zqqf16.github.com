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
        self.html = None
        self.type = 'post'

        self.__convert_to_html()
        self.__parse_metadata()

    def __repr__(self):
        return u'<date: %s, title: %s, slug: %s>' % (self.date, self.title, self.slug)

    def __convert_to_html(self):
        with open(self.path, 'r') as f:
            content = f.read().decode('utf-8')
            self.html = markdown(content.strip(' \n'), 
                                 extras=["fenced-code-blocks", "metadata"])

    def __parse_metadata(self):
        if not self.html:
            return

        for key, value in self.html.metadata.items():
            if key == 'tags':
                self.tags = value.split(',')
            elif key == 'title':
                self.title = value
            elif key == 'date':
                self.date = datetime.strptime(value, '%Y-%m-%d')
            elif key == 'category':
                self.category = value
            elif key == 'type':
                self.type = value

        path = cfg['post_path'] if self.type=='post' else cfg['page_path']
        self.uri = path + '/' + self.slug + '.html'

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
