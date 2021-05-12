import asyncio
import os
import configparser

import aiohttp
import discord
from discord.ext import tasks


config = configparser.ConfigParser()
config.read('config.ini', 'UTF-8')
discord_token = os.environ.get('DISCORD_TOKEN')
redmine_token = os.environ.get('REDMINE_TOKEN')
issue_url = config.get('redmine', 'issue_url')
review_channel_id = config.getint('discord', 'review_channel_id')
final_review__channel_id = config.getint('discord', 'final_review_channel_id')
query_ids = {'not_ordered': config.get('redmine', 'not_ordered'),
             'review': config.get('redmine', 'review'),
             'final_review': config.get('redmine', 'final_review')}


class BotClient(discord.Client):
    review_channel = ''
    final_review_channel = ''

    async def on_ready(self):
        BotClient.review_channel = BotClient.get_channel(self, review_channel_id)
        BotClient.final_review_channel = BotClient.get_channel(self, review_channel_id)

        print("Botが起動しました")
        BotClient.check_tickets.start(BotClient)

    # 2週間経過したメッセージを消去する（1日ごとに実行）
    @tasks.loop(minutes=1)
    async def check_tickets(self):
        not_ordered = await self.get_json(self, query_ids.get('not_ordered'))
        review = await self.get_json(self, query_ids.get('review'))
        final_review = await self.get_json(self, query_ids.get('final_review'))
        print(not_ordered)

    # http通信するやーつ
    async def get_json(self, filter_id):
        header = {'X-Redmine-API-Key': redmine_token}
        url = issue_url + 'query_id=' + filter_id
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=header) as r:
                if r.status == 200:
                    return await r.json()


client = BotClient()
client.run(discord_token)
