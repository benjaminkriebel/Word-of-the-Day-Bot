# Word of the Day Bot
# A simple Reddit bot that replies to comments using a word of the day.
#
# Benjamin Kriebel (https://github.com/benjaminkriebel)

import praw
import config
import os
import requests
import bs4
import time

# Constants
URL = "https://www.merriam-webster.com/word-of-the-day"
BLANK_LINE = "\n\n&nbsp;\n\n"
REPLY_HEADER = "You said the word of the day!"
REPLY_WORD = "**%s**\n\n"
REPLY_ATTRIBUTES = "*%s* | *%s*\n\n"
REPLY_DEFINITIONS = "%s\n\n"
REPLY_LINK = "Read more at [merriam-webster.com](https://www.merriam-webster.com/word-of-the-day)."


# This function gets the reddit instance and then runs the bot.
def main():
    reddit = bot_login()

    while True:
        run_bot(reddit)


# This function logs into reddit using credentials from config.py,
# and then returns the newly created reddit instance.
def bot_login():
    print("Logging in...")

    reddit = praw.Reddit(
        username=config.username,
        password=config.password,
        client_id=config.client_id,
        client_secret=config.client_secret,
        user_agent="WORD OF THE DAY BOT")

    print("Successfully logged in.")

    return reddit


# This function gets the word of the day and then monitors comments coming
# from r/all. If the comment meets certain conditions, the bot replies to
# the comment.
def run_bot(reddit):
    [word, main_attr, syllables, defs] = get_word()

    comments_replied_to = get_saved_comments()

    subreddit = reddit.subreddit("test")

    # Grab comments 25 at a time.
    for comment in subreddit.comments(limit=25):
        # Check if the comment contains the word, if the comment has already
        # been replied to, and if it was a reply left by the bot previously.
        if (word in comment.body and
            comment.id not in comments_replied_to and
                comment.author != config.username):

            print("Comment found with id %s" % comment.id)

            reply_message = build_reply(word, main_attr, syllables, defs)
            comment.reply(reply_message)

            # Save the comment so it won't be replied to later.
            save_comment(comment, comments_replied_to)

            print("Replied to comment with id %s" % comment.id)

    # Sleep after each iteration to avoid spamming.
    time.sleep(10)


# This function scrapes merriam-webster.com to retrieve the word of the day.
# It collects the word, its main attribute, its syllables, and its definitions,
# which it then returns as a list.
def get_word():
    page = requests.get(URL)
    soup = bs4.BeautifulSoup(page.content, "html.parser")

    # Get the word.
    word_container = soup.find("div", class_="word-header")
    word = word_container.h1.text.strip()

    # Get the main attribute and syllables.
    attributes_container = soup.find("div", class_="word-attributes")
    main_attr = attributes_container.find(class_="main-attr").text.strip()
    syllables = attributes_container.find(class_="word-syllables").text.strip()

    # Get the definitions.
    def_container = soup.find("div", class_="wod-definition-container")
    formatted_defs = def_container.findChildren("p", recursive=False)
    defs = []
    for definition in formatted_defs:
        defs.append(definition.text.strip())

    return [word, main_attr, syllables, defs]


# This function retrieves the list of comment ids from comments.txt
# and returns them as a list.
def get_saved_comments():
    if not os.path.isfile("comments.txt"):
        id_list = []
    else:
        with open("comments.txt", "r") as f:
            id_list = f.read()
            id_list = id_list.split("\n")

    return id_list


# This function saves a comment to the list of comments replied to,
# and writes its id to comments.txt.
def save_comments(comment, comments_replied_to):
    comments_replied_to.append(comment.id)
    with open("comments.txt", "a") as f:
        f.write(comment.id + "\n")


# This function constructs the reply message that will be sent.
def build_reply(word, main_attr, syllables, defs):
    reply_message = []
    reply_message.append(REPLY_HEADER)
    reply_message.append(BLANK_LINE)
    reply_message.append(REPLY_WORD % word)
    reply_message.append(REPLY_ATTRIBUTES % (main_attr, syllables))
    for definition in defs:
        reply_message.append(REPLY_DEFINITIONS % definition)
    reply_message.append(REPLY_LINK)

    return ("".join(reply_message))


# Call main to initiate the bot.
main()
