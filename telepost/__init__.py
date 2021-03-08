import yaml
import webgram
import time

with open('credential') as f:
	credential = yaml.load(f, Loader=yaml.FullLoader)

Day = 24 * 60 * 60

def getPosts(channel, min_time = None, max_time = None):
	if not min_time:
		min_time = time.time() - 2 * Day
	if not max_time:
		max_time = time.time() - Day
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

def getPost(channel, existing_file, min_time = None, max_time = None):
	for post in getPosts(channel, min_time, max_time):
		key = 'https://t.me/' + post.getKey()
		if existing_file.get(key):
			continue
		return post

client_cache = {}
async def getTelethonClient():
    if 'client' in client_cache:
        return client_cache['client']
    client = TelegramClient('session_file', credential['telegram_api_id'], credential['telegram_api_hash'])
    await client.start(password=credential['telegram_user_password'])
    client_cache['client'] = client   
    return client_cache['client']

async def getImages(channel, post_id, post_size):
    client = await getTelethonClient()
    entity = await getChannel(client, channel)
    posts = await client.get_messages(entity, min_id=post_id - 1, max_id = post_id + post_size + 1)
    result = []
    for post in posts:
    	fn = await post.download_media('tmp/')
    	result.append(fn)
    return result
