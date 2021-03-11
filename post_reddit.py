#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import plain_db
import cached_url
from telegram_util import isCN
from reddit_2_album import reddit
from telepost import getPost, getImages, exitTelethon, getText
from praw.models import InlineImage, InlineVideo
from telegram_util import matchKey
import copy

reddit.validate_on_submit = True
subreddit = reddit.subreddit('cn_talk')
channel = 'twitter_translate'
existing = plain_db.load('existing')

def getCore(soup):
    soup = copy.copy(soup)
    for item in soup.find_all('a'):
        item.decompose()
    for item in soup.find_all('br'):
        item.replace_with('\n')
    lines = soup.text.split('\n')
    lines = [line for line in lines if line.strip() and not 
        matchKey(line, ['http', '译者', 'translated by'])]
    result = '　'.join(lines)
    for char in '。！？，':
        result = result.replace(char + '　', char)
    return result

def splitText(text):
    lines = text.split('\n')
    return lines[0], '\n'.join(lines[1:]).strip()

def postAsGallery(core, fns, key): 
    if len(fns) == 1:
        return subreddit.submit_image(core, fns[0])
    images = [{"image_path": fn, "outbound_url": key} for fn in fns]
    return subreddit.submit_gallery(core, images)

def postAsText(post_text):
    title, content = splitText(post_text)
    return subreddit.submit(title, selftext=content)

def postInline(post_text, fns):
    media = {}
    count = 0
    text = ''
    for fn in fns:
        count += 1
        image_key = 'image' + str(count)
        media[image_key] = InlineImage(fn)
        text += '{%s}' % image_key
    title, content = splitText(post_text)
    content += text
    return subreddit.submit(title, selftext=content, inline_media=media)

def postVideo(post_text, video):
    cached_url.get(video, mode='b', force_cache=True)
    title, content = splitText(post_text)
    content += '{video}'
    return subreddit.submit(title, selftext=content, inline_media={
        "video": InlineVideo(cached_url.getFilePath(video))})
    
async def postImp(post, key):
    post_text = getText(post.text)
    img_number = post.getImgNumber()
    if post.getVideo():
        return postVideo(post_text, post.getVideo())
    if not img_number:
        # see if I need to deal with the link case separately
        return postAsText(post_text)
    fns = await getImages(channel, post.post_id, img_number)
    core = getCore(post.text)
    if len(core) < 180:
        return postAsGallery(core, fns, key)
    return postInline(post_text, fns)

async def runImp():
    post = getPost(channel, existing, min_time=1)
    if not post:
        return
    key = 'https://t.me/' + post.getKey()
    if not isCN(post.text.text):
        existing.update(key, -1)
        return
    result = await postImp(post, key)
    print('https://www.reddit.com/r/cn_talk/comments/' + str(result))
    existing.update(key, 1)

async def run():
    await runImp()
    await exitTelethon()
        
if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    r = loop.run_until_complete(run())
    loop.close()