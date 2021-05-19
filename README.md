# RedmineNotificationDiscord
Redmineの情報をDiscordに通知するボット

# 環境変数
DISCORD_TOKEN　= DiscordBotのトークン\
REDMINE_TOKEN　= Redmineのトークン

# config.ini
[discord]\
not_ordered_channel_id = 未受注通知チャンネルID\
review_channel_id = レビュー待ち通知チャンネルID\
final_review_channel_id = 最終レビュー待ち通知チャンネルID\
interval_minutes = 実行間隔(分単位)
\
[redmine]\
tickets_url = プロジェクトのチケット一覧ページ.json?\
ticket_url = チケット詳細のURL\
not_ordered = 未受注を表示するカスタムクエリの番号\
review = レビュー待ちを表示するカスタムクエリの番号\
final_review = 最終レビュー待ちを表示するカスタムクエリの番号\