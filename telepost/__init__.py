import yaml
import webgram

with open('credential') as f:
	credential = yaml.load(f, Loader=yaml.FullLoader)

Day = 24 * 60 * 60

def getPosts(channel, min_time = None, max_time = None):
	if not min_time:
		min_time = time.time() - 2 * Day
	if not max_time:
		min_time = time.time() - Day
	posts = webgram.getPosts(channel)[1:]
	for post in posts:
		if post.time < max_time:
			yield post
	while posts and posts[0].time > min_time:
		pivot = posts[0].post_id
		posts = webgram.getPosts(channel, posts[0].post_id, 
			direction='before', force_cache=True)[1:]
		for post in posts:
			if post.time < max_time:
				yield post

