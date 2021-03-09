#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telethon import TelegramClient
import asyncio
import tweepy
import yaml
import time
import plain_db
import webgram
import post_2_album
from bs4 import BeautifulSoup
import cached_url
import os
import export_to_telegraph
from telegram_util import isCN
from reddit_2_album import reddit
from telepost import getPost, getImages, exitTelethon

subreddit = reddit.subreddit('cn_talk')

from praw.models import InlineGif, InlineImage, InlineVideo


existing = plain_db.load('existing')

with open('credential') as f:
    credential = yaml.load(f, Loader=yaml.FullLoader)

Day = 24 * 60 * 60

def getPosts(channel):
    start = time.time()
    result = []
    posts = webgram.getPosts(channel)[1:]
    result += posts
    while posts and posts[0].time > (time.time() - 
            credential['channels'][channel]['back_days'] * Day):
        pivot = posts[0].post_id
        posts = webgram.getPosts(channel, posts[0].post_id, 
            direction='before', force_cache=True)[1:]
        result += posts
    for post in result:
        if post.time > time.time() - Day:
            continue
        try:
            yield post_2_album.get('https://t.me/' + post.getKey()), post
        except Exception as e:
            print('post_2_album failed', post.getKey(), str(e))

def getLinkReplace(url, album):
    if 'telegra.ph' in url and 'douban.com/note/' in album.cap_html:
        return ''
    if 'telegra.ph' in url:
        soup = BeautifulSoup(cached_url.get(url, force_cache=True), 'html.parser')
        title = export_to_telegraph.getTitle(url)
        try:
            return '\n\n【%s】 %s' % (title, soup.find('address').find('a')['href'])
        except:
            return ''
    return '\n\n' + url

def getText(album, post):
    soup = BeautifulSoup(album.cap_html, 'html.parser')
    for item in soup.find_all('a'):
        if item.get('href'):
            item.replace_with(getLinkReplace(item.get('href'), album))
    for item in soup.find_all('br'):
        item.replace_with('\n')
    text = soup.text.strip()
    if post.file:
        text += '\n\n' + album.url
    return text

async def getMediaSingle(api, post):
    fn = await post.download_media('tmp/')
    if not fn:
        return
    if os.stat(fn).st_size >= 4883 * 1024: # twitter limit
        return
    try:
        return api.media_upload(fn).media_id
    except Exception as e:
        print('media upload failed:', str(e))

async def getMedia(api, posts):
    # tweepy does not support video yet.  https://github.com/tweepy/tweepy/pull/1486
    result = []
    for post in posts:
        media = await getMediaSingle(api, post)
        if media:
            result.append(media)
        if len(result) >= 4:
            return result
    return result

def matchLanguage(channel, status_text):
    if not credential['channels'][channel].get('chinese_only'):
        return True
    return isCN(status_text)

def getGroupedPosts(posts):
    grouped_id = None
    result = []
    for post in posts[::-1]:
        if not grouped_id and not post.grouped_id:
            return [post]
        if not grouped_id:
            grouped_id = post.grouped_id
        if post.grouped_id == grouped_id:
            result.append(post)
    return result

async def getMediaIds(api, channel, post, album):
    if not album.imgs:
        return []
    client = await getTelethonClient()
    entity = await getChannel(client, channel)
    posts = await client.get_messages(entity, min_id=post.post_id - 1, max_id = post.post_id + 9)
    media_ids = await getMedia(api, getGroupedPosts(posts))
    return list(media_ids)
 
async def runImp():
    channel = 'twitter_translate'
    post = getPost(channel, existing)
    key = 'https://t.me/' + post.getKey()
    post_size = post.getPostSize()
    fns = await getImages(channel, post.post_id, post_size)
    media = {}
    for fn in fns:
        media[fn] = InlineImage(fn)
    print(post.text)

async def run():
    await runImp()
    await exitTelethon()
    # print(len(post.soup.find_all('a', 'tgme_widget_message_photo_wrap')))
    # gif = InlineGif("path/to/image.gif", "optional caption")
    # image = InlineImage("path/to/image.jpg", "optional caption")
    # video = InlineVideo("path/to/video.mp4", "optional caption")
    # selftext = "Text with a gif {gif1} an image {image1} and a video {video1} inline"
    # media = {"gif1": gif, "image1": image, "video1": video}
    # reddit.subreddit("redditdev").submit("title", selftext=selftext, inline_media=media)

        
if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    r = loop.run_until_complete(run())
    loop.close()