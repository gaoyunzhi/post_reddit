#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import plain_db
from telegram_util import isCN
from reddit_2_album import reddit
from telepost import getPost, getImages, exitTelethon, getText
from praw.models import InlineImage, InlineVideo

reddit.validate_on_submit = True
subreddit = reddit.subreddit('cn_talk')

existing = plain_db.load('existing')

async def runImp():
    channel = 'twitter_translate'
    post = getPost(channel, existing)
    if not isCN(post.text.text):
        return
    key = 'https://t.me/' + post.getKey()
    post_size = post.getPostSize()
    fns = await getImages(channel, post.post_id, post_size)
    media = {}
    count = 0
    text = ''
    for fn in fns:
        count += 1
        image_key = 'image' + str(count)
        media[image_key] = InlineImage(fn)
        text += '{%s}' % image_key
    post_text = getText(post.text)
    title = post_text.split('http')[0]
    text += post_text
    # 似乎inline就没有preview了
    result = subreddit.submit(title, selftext=text, inline_media=media)
    existing.update(key, 1)

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