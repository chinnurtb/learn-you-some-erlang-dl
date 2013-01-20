#!/usr/bin/env python2.7

import os
import hashlib
import urllib2
import re
from pprint import pprint as pp
from sys import exit

BASEURL = 'http://learnyousomeerlang.com/'
CWD = os.path.dirname(os.path.abspath(__file__))
CACHEDIR = os.path.join(CWD, '.cache')
BUILDDIR = os.path.join(CWD, 'build')

if not os.path.exists(CACHEDIR):
    os.mkdir(CACHEDIR)

if os.path.exists(BUILDDIR):
    print 'build dir exists, but should not'
    exit(1)

os.mkdir(BUILDDIR)
os.mkdir(os.path.join(BUILDDIR, 'img'))

def hsh(s):
    return hashlib.sha1(s).hexdigest() + hashlib.md5(s).hexdigest()

def fetch_url(url):
    cfn = hsh(url)
    full_cfn = os.path.join(CACHEDIR, cfn)

    if not os.path.exists(full_cfn):
        f = urllib2.urlopen(url)
        data = f.read()
        f.close()

        fp = open(full_cfn, 'w')
        fp.write(data)
        fp.close()

    data = open(full_cfn).read()
    return data


noscript_re = re.compile('<div class="noscript"><noscript>.+?</noscript></div>', 
    re.MULTILINE+re.DOTALL)
def cleanup_html(h):
    return noscript_re.sub('', h)

total_inner = ''

# first download toc
toc = fetch_url(BASEURL+'contents')

# find print css
print_css_re = re.compile('<link rel="stylesheet" type="text/css" href="(.+?)" media="print" />')
for pcss in print_css_re.findall(toc):
    break
else:
    print 'no print css'
    exit(1)

css = fetch_url(pcss)
open('print.css', 'w').write(css)

toc_section_re = re.compile('<h3><a class="local chapter" href="([^"]+?)">(.+?)</a></h3>')
img_re = re.compile('<img.+?src="(.+?)".+?(?:title="(.+?)")?.+?>')
aname_re = re.compile('<a.+?name="(.+?)">')
alink_re = re.compile(BASEURL.replace('.', '\\.')+'(.+?)#(.+?)"')
res = toc_section_re.findall(toc)

for link, title in res:
    section_name = os.path.basename(link)
    section = fetch_url(link)
    # find section begin and end positions
    start = section.find('<div id="content">')
    end = section.find('<ul class="navigation">')

    html = cleanup_html(section[start:end])

    # find and download pictures
    images = img_re.findall(section)
    for img_url, img_title in images:
        img_data = fetch_url(img_url)
        img_filename = os.path.basename(img_url)
        open(os.path.join(BUILDDIR, 'img', img_filename), 'wb').write(img_data)

        html = html.replace(img_url, 'img/'+img_filename)

    # correct internal links
    html = aname_re.sub(lambda mo: mo.group(0).replace('name="{}"'.format(mo.group(1)), 'name="{}---{}"'.format(section_name, mo.group(1))), html)
    html = alink_re.sub(lambda mo: '#'+mo.group(1)+'---'+mo.group(2)+'"', html)

    total_inner += html

res = '''<html><head>
<link rel="stylesheet" type="text/css" href="print.css">
</head><body>''' +\
    total_inner +\
'''</body></html>'''

open(os.path.join(BUILDDIR, 'index.html'), 'w').write(res)