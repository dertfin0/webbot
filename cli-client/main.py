import dotenv
import argparse
import hashlib
import httpx
import asyncio

from textual.app import App
from textual import events
from textual.widgets import Header, RichLog, Input

parser = argparse.ArgumentParser(prog="WebBot Client")
parser.add_argument("config", help="Path to config file")

server_address: str
password: str
password_hash: str

class Client(App):
    last_received_id = 0

    def compose(self):
        yield Header()
        self.richlog = RichLog(markup=True)
        yield self.richlog
        self.input = Input(placeholder="Write a message...")
        yield self.input

    def on_mount(self):
        self.title = "WebBot Client"
        self.input.focus() # Required to run over SSH
        self.richlog.styles.padding = (1, 3, 1, 3)
        self.run_worker(self.message_update_worker())

    async def on_key(self, event: events.Key):
        if event.key != "enter" or self.input.value.strip() == "":
            return

        async with httpx.AsyncClient() as client:
            await client.post(server_address + "/user/message", headers={
                "Authorization": password_hash
            }, json = {
                "content": self.input.value.strip()
            })
            self.input.value = ""

    async def get_new_messages(self):
        async with httpx.AsyncClient() as client:
            res = await client.get(server_address + "/user/messages", params= {
                "last_received_id": self.last_received_id
            }, headers={
                "Authorization": password_hash
            })
            res.raise_for_status()

            if not res.json():
                return

            self.last_received_id = res.json()[-1]["id"]
            for message in res.json():
                self.add_new_message(message["content"], message["by_bot"])

    async def message_update_worker(self):
        while True:
            try:
                await self.get_new_messages()
            except Exception as e:
                self.richlog.write(f"[red]Exception occured: {e}[/red]")

            await asyncio.sleep(1)

    def add_new_message(self, content: str, by_bot: bool):
        # TODO: Add timestamps
        color = "green" if by_bot else "cyan"
        sender = "Bot" if by_bot else "You"
        self.richlog.write(f"[[{color}]{sender}[/{color}]] [white]{content}[/white]")

if __name__ == "__main__":
    args = parser.parse_args()
    if not args.config:
        print("Config file not provided. Check help for more info\n")
        server_address = input("Server address: ")
        password = input("Password: ")
    else:
        server_address = dotenv.get_key(args.config, "SERVER_ADDRESS")
        password = dotenv.get_key(args.config, "PASSWORD")
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    print("Connecting to the server...")
    try:
        with httpx.Client(timeout=10) as client:
            res = client.get(server_address + "/version")
            res.raise_for_status()
    except httpx.ConnectTimeout:
        print("Can't connect to the server: Timeout")
        exit(-1)
    except httpx.ConnectError:
        print("Can't connect to the server: Connection refused")
        exit(-1)

    app = Client()
    app.run()