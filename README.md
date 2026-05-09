# COUNTDOWN BOT FOR DISCORD
This is a small project i've been doing to count the days from now to a specified date using Python for a discord server.
It was needed to count the days before i'd get to see my girlfriend which is actually in Japan for arround 3 months.
I've been helping myself with Claude code.

## Installation on your project

### 1. Clone the project
The arborescence should be like this :
countdown_bot/
├── .env.example
├── bot.py
├── README.md
└── requirements.txt

### 2. Add the venv folder
```cmd
python3 -m venv venv
source venv/bin/activate
```

### 3. Install the requierements
```cmd
pip install -r requirements.txt
```

### 4. prepare your .env
Copy the .env.example and rename it ".env".
You can now go to the next part

## installation on discord

I use a .env to store the discord token to use it
if you want to do the same create a discord bot with the following instructions :
- Copy the token given to access the bot and past it in your .env file
- Go to OAuth2 and in URL generator add the following application field : `bot` + `applications.commands`
- In bot permissions select : `Send Messages` + `Read Message History` + `Embed Links`
- Copy the generated url and paste in yout browser to add the bot on your discord server

## Test it locally
After adding the bot in your discord server, you can type in the terminal in your project :
```cmd
python bot.py
```
And try to do in your discord server the "/countdown"

If everything works, it means you have followed well the instructions. If not, maybe watch again to ensure you've not missed anything

If you want the bot to working without have to launch your project locally, try adding the project to a server