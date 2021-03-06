import configparser
import os

import aiohttp
import discord
from discord.ext import tasks

config = configparser.ConfigParser()
config.read('config.ini', 'UTF-8')
discord_token = os.environ.get('DISCORD_TOKEN')
redmine_token = os.environ.get('REDMINE_TOKEN')
interval = config.getint('discord', 'interval_minutes')
tickets_url = config.get('redmine', 'tickets_url')  # チケットの一覧URL
ticket_url = config.get('redmine', 'ticket_url')  # チケットの詳細URL
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
        BotClient.check_task.start(BotClient)

    # 1分ごとに処理実行
    @tasks.loop(minutes=interval)
    async def check_task(self):
        # データを取得する処理
        not_ordered_json = await self.get_json(self, query_ids.get('not_ordered'))
        review_json = await self.get_json(self, query_ids.get('review'))
        final_review_json = await self.get_json(self, query_ids.get('final_review'))
        # JSONをパースする(たぶん)
        not_ordered_tickets = await self.get_tickets(self, not_ordered_json)
        review_tickets = await self.get_tickets(self, review_json)
        final_review_tickets = await self.get_tickets(self, final_review_json)
        # 各チャンネルの投稿をチェックしたりしなかったりする
        await self.check_ticket(self, not_ordered_tickets, 'not_ordered')
        await self.check_ticket(self, review_tickets, 'review')
        await self.check_ticket(self, final_review_tickets, 'final')

    # RedmineのAPIからJSONを取得する
    async def get_json(self, filter_id):
        header = {'X-Redmine-API-Key': redmine_token}
        url = tickets_url + 'query_id=' + filter_id
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=header) as r:
                if r.status == 200:
                    return await r.json()

    # チケット情報をJSONから取り出す
    async def get_tickets(self, ticket_json):
        tickets = []
        for ticket in ticket_json['issues']:
            tickets.append({
                'id': ticket['id'],
                'priority': ticket['priority']['name'],
                'category': ticket['project']['name'],
                'subject': ticket['subject']
            })
        return tickets

    # 各チャンネルに投稿
    async def send_message(self, ticket, status):
        await BotClient.channels[status].send('No：' + str(ticket['id']) + '\n' +
                                              '優先度：' + ticket['priority'] + '\n' +
                                              'カテゴリ：' + ticket['category'] + '\n' +
                                              '題名：' + ticket['subject'] + '\n' +
                                              ticket_url + str(ticket['id']))

    # 各チャンネルの投稿をチェック
    # 各チケットごとにメッセージの中に含まれているかチェックして、
    # 含まれている場合はedit or そのまま
    # 含まれていない場合はチケット情報を送信する
    async def check_ticket(self, tickets, status):
        messages = await BotClient.channels[status].history().flatten()  # 履歴を全取得してリスト化
        unsent_tickets = []
        # チケットとDiscordメッセージの照合をする
        for ticket in tickets:
            ticket_no = 'No：' + str(ticket['id']) + '\n'
            exist = False
            for message in messages:
                if ticket_no not in message.content:
                    continue
                exist = True
                subject = '題名：' + ticket['subject'] + '\n'
                # タイトルが変更されているか判定、含まれていない場合は変更
                if subject not in message.content:
                    await message.edit(content='No：' + str(ticket['id']) + '\n' +
                                               '優先度：' + ticket['priority'] + '\n' +
                                               'カテゴリ：' + ticket['category'] + '\n' +
                                               '題名：' + ticket['subject'] + '\n' +
                                               ticket_url + str(ticket['id']))
                break
            # 未送信のチケットを配列に保存
            if not exist:
                unsent_tickets.append(ticket)
        # ステータスが変更されたチケットを削除する
        for message in messages:
            exist = False
            for ticket in tickets:
                ticket_no = 'No：' + str(ticket['id']) + '\n'
                if ticket_no in message.content:
                    exist = True
                    break
            if not exist:
                await message.delete()
        # 未送信のチケットを送信
        for unsent in unsent_tickets:
            await self.send_message(self, unsent, status)


client = BotClient()
client.run(discord_token)
