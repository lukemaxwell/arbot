#!/usr/bin/env python
# -*- coding: utf-8 -*-
import praw

USER_AGENT = ("Cryptobot 0.1")
USERNAME = 'meaowletspow'
PASSWORD = 'K1ttycat'
CLIENT_ID = '0Y9u02W8vkRdCg'
CLIENT_SECRET = '6llz5TdG71m-2dyhCWIgav9mgOo'

reddit = praw.Reddit(client_id=CLIENT_ID,
                     client_secret=CLIENT_SECRET,
                     user_agent=USER_AGENT)


subreddits = reddit.subreddit('altcoin+cryptocurrency+cryptomarkets')
for comment in subreddits.stream.comments():
    print(30*'_')
    print()
    print(comment.body)

