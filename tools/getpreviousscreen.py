#!/usr/bin/env python3
#from ransomlook import ransomlook
import importlib
from os.path import dirname, basename, isfile, join
import json
import glob
import sys

from datetime import datetime
from datetime import timedelta

import collections

import redis

from ransomlook.default.config import get_config, get_socket_path

from ransomlook.sharedutils import dbglog, stdlog, errlog, statsgroup, run_data_viz

def posttemplate(victim, description, link, timestamp):
    '''
    assuming we have a new post - form the template we will use for the new entry in posts.json
    '''
    schema = {
        'post_title': victim,
        'discovered': timestamp,
        'description' : description,
        'link' : link,
        'screen' : None
    }
    stdlog('new post: ' + victim)
    dbglog(schema)
    return schema

def appender(entry, group_name):
    '''
    append a new post to posts.json
    '''
    if type(entry) is str :
       post_title = entry
       description = ''
       link = ''
    else :
       post_title=entry['title']
       description = entry['description']
       if 'link' in entry: 
           link = entry['link']
       else:
           link = ''
    if len(post_title) == 0:
        errlog('post_title is empty')
        return
    # limit length of post_title to 90 chars
    if len(post_title) > 90:
        post_title = post_title[:90]
    if link != '':
        red = redis.Redis(unix_socket_path=get_socket_path('cache'), db=2)
        posts = json.loads(red.get(group_name.encode()))
        for post in posts:
            if post['post_title'] == post_title:
                 if 'screen' in post and post['screen'] is not None:
                      return
        screenred = redis.Redis(unix_socket_path=get_socket_path('cache'), db=1)
        if 'toscan'.encode() not in screenred.keys():
           toscan=[]
        else: 
           toscan = json.loads(screenred.get('toscan')) # type: ignore
        toscan.append({'group': group_name, 'title': entry['title'], 'slug': entry['slug'], 'link': entry['link']})
        screenred.set('toscan', json.dumps(toscan))
    # Notification zone

def main():
    if len(sys.argv) != 2:
        modules = glob.glob(join(dirname('ransomlook/parsers/'), "*.py"))
        __all__ = [ basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]
    else:
        __all__ = [sys.argv[1]]
    for parser in __all__:
        module = importlib.import_module(f'ransomlook.parsers.{parser}')
        print('\nParser : '+parser)

        try:
            for entry in module.main():
                appender(entry, parser)
        except Exception as e:
            print("Error with : " + parser)
            print(e)
            pass

if __name__ == '__main__':
    main()

