import dotenv
import argparse
import hashlib
import httpx
import asyncio
from datetime import datetime

from textual.app import App
from textual import events
from textual.widgets import Header, RichLog, Input

VERSION = "0.1.1"

parser = argparse.ArgumentParser(prog="WebBot Client")
parser.add_argument("config", help="Path to config file")

server_address: str
password: str
password_hash: str


class Client(App):
    last_received_id = 0
    last_received_date = (0, 0, 0)

    def compose(self):
        yield Header()
        self.richlog = RichLog(markup=True)
        yield self.richlog
        self.input = Input(placeholder="Write a message...")
        yield self.input

    def on_mount(self):
        self.title = "WebBot Client"
        self.input.focus()  # Required to run over SSH
        self.richlog.styles.padding = (1, 3, 1, 3)
        self.run_worker(self.message_update_worker())

    async def on_key(self, event: events.Key):
        if event.key != "enter" or self.input.value.strip() == "":
            return

        async with httpx.AsyncClient() as client:
            await client.post(server_address + "/user/message", headers={
                "Authorization": password_hash
            }, json={
                "content": self.input.value.strip()
            })
            self.input.value = ""

    async def get_new_messages(self):
        async with httpx.AsyncClient() as client:
            res = await client.get(server_address + "/user/messages", params={
                "last_received_id": self.last_received_id
            }, headers={
                "Authorization": password_hash
            })
            res.raise_for_status()

            if not res.json():
                return

            self.last_received_id = res.json()[-1]["id"]
            for message in res.json():
                self.add_new_message(message["content"], message["by_bot"], message["sent_at"])

    async def message_update_worker(self):
        while True:
            try:
                await self.get_new_messages()
            except Exception as e:
                self.richlog.write(f"[red]Exception occured: {e}[/red]")

            await asyncio.sleep(1)

    def add_new_message(self, content: str, by_bot: bool, sent_at: int):
        # TODO: Add timestamps
        date = datetime.fromtimestamp(sent_at)
        hour = date.time().hour if date.time().hour >= 10 else "0" + str(date.time().hour)
        minute = date.time().minute if date.time().minute >= 10 else "0" + str(date.time().minute)

        day = date.date().day
        month = date.date().month
        year = date.date().year

        if year > self.last_received_date[2]:
            self.print_date(day, month, year)
        elif month > self.last_received_date[1]:
            self.print_date(day, month, year)
        elif day > self.last_received_date[0]:
            self.print_date(day, month, year)

        self.last_received_date = (day, month, year)

        date_prefix = f"{hour}:{minute}"
        color = "green" if by_bot else "cyan"
        sender = "Bot" if by_bot else "You"
        self.richlog.write(f"[[green]{date_prefix}[/green]] [[{color}]{sender}[/{color}]] [white]{content}[/white]")

    def print_date(self, day, month, year):
        day = str(day) if day >= 10 else "0" + str(day)
        month = str(month) if month >= 10 else "0" + str(month)
        year = str(year)
        self.richlog.write(f"\n[gray][bold]{day}.{month}.{year}[/bold][/gray]\n")

if __name__ == "__main__":
    args = parser.parse_args()
    if not args.config:
        print("Config file not provided. Check help for more info\n")
        server_address = input("Server address: ")
        password = input("Password: ")
    else:
        server_address = dotenv.get_key(args.config, "SERVER_ADDRESS")
        password = dotenv.get_key(args.config, "PASSWORD")

    if not server_address:
        print("Key SERVER_ADDRESS not set")
        exit(-1)
    if not password:
        print("Key PASSWORD not set")
        exit(-1)

    password_hash = hashlib.sha256(password.encode()).hexdigest()

    print("Connecting to the server...")
    try:
        with httpx.Client(timeout=10) as client:
            res = client.get(server_address + "/version")
            res.raise_for_status()

            client = VERSION.split(".")
            api = res.json().split(".")

            if api[0] > client[0]:
                print(f"Client is too outdated. Update client to version {res.json()} and try again")
                exit(-1)
            elif api[0] < client[0]:
                print(f"API version is too outdated. Update API and run again")
                exit(-1)
            elif api[1] > client[1]:
                print(f"Client version is outdated. Some features may not be available. Update it and run again")
            elif api[2] > client[2]:
                print(f"Client version is outdated. Some bugfix may not be available. Update it and run again")
    except httpx.ConnectTimeout:
        print("Can't connect to the server: Timeout")
        exit(-1)
    except Exception:
        print("Can't connect to the server: Connection refused")
        exit(-1)

    try:
        with httpx.Client(timeout=10) as client:
            res = client.get(server_address + "/auth/validate-user-password", params={
                "password_hash": password_hash
            })
            res.raise_for_status()

            if not res.json()["valid"]:
                print("Password check failed")
                exit(0)
    except httpx.ConnectTimeout:
        print("Can't connect to the server: Timeout")
        exit(-1)
    except Exception:
        print("Can't connect to the server: Connection refused")
        exit(-1)

    app = Client()
    app.run()
