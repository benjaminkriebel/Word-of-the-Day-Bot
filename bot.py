# Word of the Day Bot
# A Reddit bot that replies to comments using a word of the day.

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


def run_bot():
    """
    Main driver function.
    """
    reddit = bot_login()

    while True:
        run_bot(reddit)
        time.sleep(60)


def bot_login():
    """
    Log into Reddit and return the newly created Reddit instance.
    """
    
    print("Logging in...")

    reddit = praw.Reddit(
        username=config.username,
        password=config.password,
        client_id=config.client_id,
        client_secret=config.client_secret,
        user_agent="WORD OF THE DAY BOT")

    print("Successfully logged in.")

    return reddit


def run_bot(reddit):
    """
    Get the word of the day and then monitor comments coming from r/all.
    """
    
    [word, main_attr, syllables, defs] = get_word()

    comments_replied_to = get_saved_comments()

    subreddit = reddit.subreddit("all")

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


def get_word():
    """
    Get the word of the day and other information from merriam-webster.com.
    """
    
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


def get_saved_comments():
    """
    Retrieve the list of saved comments.
    """
    
    if not os.path.isfile("comments.txt"):
        id_list = []
    else:
        with open("comments.txt", "r") as f:
            id_list = f.read()
            id_list = id_list.split("\n")

    return id_list


def save_comment(comment, comments_replied_to):
    """
    Save a comment to a list of comments previously replied to.
    """
    
    comments_replied_to.append(comment.id)
    with open("comments.txt", "a") as f:
        f.write(comment.id + "\n")


def build_reply(word, main_attr, syllables, defs):
    """
    Construct the reply message that the bot will send.
    """
    
    reply_message = []
    reply_message.append(REPLY_HEADER)
    reply_message.append(BLANK_LINE)
    reply_message.append(REPLY_WORD % word)
    reply_message.append(REPLY_ATTRIBUTES % (main_attr, syllables))
    for definition in defs:
        reply_message.append(REPLY_DEFINITIONS % definition)
    reply_message.append(REPLY_LINK)

    return ("".join(reply_message))


if __name___ == "__main__":
    run_bot()
