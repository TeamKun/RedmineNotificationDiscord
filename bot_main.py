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
issues_url = config.get('redmine', 'issue_url')
not_ordered_channel_id = config.getint('discord', 'not_ordered_channel_id')
review_channel_id = config.getint('discord', 'review_channel_id')
final_review__channel_id = config.getint('discord', 'final_review_channel_id')
query_ids = {'not_ordered': config.get('redmine', 'not_ordered'),
             'review': config.get('redmine', 'review'),
             'final_review': config.get('redmine', 'final_review')}


class BotClient(discord.Client):
    channels = {}

    async def on_ready(self):
        print("Botが起動しました")
        BotClient.channels = {
            'not_ordered': BotClient.get_channel(self, not_ordered_channel_id),
            'review': BotClient.get_channel(self, review_channel_id),
            'final': BotClient.get_channel(self, final_review__channel_id)
        }
        BotClient.check_tickets.start(BotClient)

    # 1分ごとにデータ取得
    @tasks.loop(minutes=1)
    async def check_tickets(self):
        not_ordered_json = await self.get_json(self, query_ids.get('not_ordered'))
        review_json = await self.get_json(self, query_ids.get('review'))
        final_review_json = await self.get_json(self, query_ids.get('final_review'))
        not_ordered_tickets = await self.get_tickets(self, not_ordered_json)
        review_tickets = await self.get_tickets(self, review_json)
        final_review_tickets = await self.get_tickets(self, final_review_json)
        await self.send_message(self, not_ordered_tickets, 'not_ordered')
        await self.send_message(self, review_tickets, 'review')
        await self.send_message(self, final_review_tickets, 'final')

    # 通信する
    async def get_json(self, filter_id):
        header = {'X-Redmine-API-Key': redmine_token}
        url = issues_url + 'query_id=' + filter_id
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=header) as r:
                if r.status == 200:
                    return await r.json()

    # チケット情報取り出す
    async def get_tickets(self, ticket_json):
        tickets = []
        for ticket in ticket_json['issues']:
            tickets.append({
                'id': ticket['id'],
                'subject': ticket['subject']
            })
        return tickets

    # 各チャンネルに投稿
    async def send_message(self, tickets, status):
        issue_url = 'https://redmine.lab.kunmc.net/redmine/issues/'
        for ticket in tickets:
            await BotClient.channels[status].send(ticket['subject'] + '\n' +
                                                  issue_url + str(ticket['id']))


client = BotClient()
client.run(discord_token)
