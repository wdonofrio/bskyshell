import os
from time import sleep

import typer
from atproto import Client, models
from dotenv import load_dotenv
from getch import getch
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

load_dotenv()

app = typer.Typer()
console = Console()


class BlueskyClient:
    """A client for the Bluesky API."""

    def __init__(self, username: str, password: str):
        self.client = Client()
        self.client.login(username, password)

    def login(self, username: str, password: str):
        return self.client.login(username, password)

    def get_feed(self, cursor=None, limit=20):
        response = self.client.get_timeline(
            algorithm="reverse-chronological", cursor=cursor, limit=10
        )
        return response

    def send_post(self, content: str):
        self.client.send_post(content)

    def reply_to_post(self, post, content: str):
        post_id = post.cid
        root_post_ref = models.create_strong_ref(post_id)
        self.client.send_post(
            text=content,
            reply_to=models.AppBskyFeedPost.ReplyRef(
                parent=root_post_ref, root=root_post_ref
            ),
        )

    def like_post(self, post):
        self.client.like(post.uri, post.cid)


def get_client():
    return BlueskyClient(os.getenv("BLUESKY_HANDLE"), os.getenv("BLUESKY_PASSWORD"))


def fetch_posts(client: BlueskyClient, limit: int = 20):
    cursor = None
    while True:
        response = client.get_feed(cursor=cursor, limit=limit)
        feed = response.feed
        for postview in feed:
            yield postview
        cursor = response.cursor
        if not cursor:
            break


def display_feed(client: BlueskyClient):
    post_generator = fetch_posts(client)
    current_post = next(post_generator, None)

    while current_post:
        if current_post.post.record.reply is not None:
            current_post = next(post_generator, None)
            continue
        os.system("clear")
        author = current_post.post.author.handle
        content = current_post.post.record.text
        timestamp = current_post.post.record.created_at
        likes = current_post.post.like_count
        replies = current_post.post.reply_count
        reposts = current_post.post.repost_count

        post_text = Text()
        post_text.append(f"{author}\n", style="bold blue")
        post_text.append(f"{timestamp}\n", style="dim")
        post_text.append(f"{content}\n\n")
        post_text.append(f"{replies} 💬 | {reposts} 🔃 | {likes} 👍", style="dim")

        console.print(Panel(post_text, border_style="blue"))
        console.print(
            "Commands: [bold]q[/bold]uit, [bold]n[/bold]ext, [bold]p[/bold]ost, [bold]r[/bold]eply, [bold]l[/bold]ike, [bold]h[/bold]elp"
        )
        user_input = getch().lower()
        if user_input == "q":
            exit(0)
        elif user_input == "n":
            current_post = next(post_generator, None)
        elif user_input == "h":
            os.system("clear")
            console.print(
                "Commands:\n"
                "[bold]q[/bold]: Quit the program.\n"
                "[bold]n[/bold]: Load the next post.\n"
                "[bold]p[/bold]: Create a new post.\n"
                "[bold]r[/bold]: Reply to the current post.\n"
                "[bold]l[/bold]: Like the current post.\n"
                "[bold]h[/bold]: Show this help message."
            )
            user_input = getch().lower()
        elif user_input == "p":
            post_with_client(client)
        elif user_input == "r":
            reply(client, current_post.post)
        elif user_input == "l":
            like(client, current_post.post)
            sleep(1)


def post_with_client(client: BlueskyClient):
    if client is None:
        client = get_client()
    content = Prompt.ask("Enter your post content")
    client.send_post(content)
    console.print("[bold green]Post created successfully![/bold green]")


@app.command()
def post():
    client = get_client()
    post_with_client(client)


def reply(client, post):
    if client is None:
        client = get_client()
    content = Prompt.ask("Enter your reply content")
    client.reply_to_post(post, content)
    console.print("[bold green]Reply posted successfully![/bold green]")


def like(client, post):
    if client is None:
        client = get_client()
    client.like_post(post)
    console.print("[bold green]Post liked successfully![/bold green]")


@app.command()
def main():
    client = get_client()
    while True:
        display_feed(client)


if __name__ == "__main__":
    app()
