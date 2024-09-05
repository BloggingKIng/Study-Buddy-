# SETUP Guide

1. Create an application on the discord developer page and give it the appropriate rights.
2. Invite the bot to your server and create a token.
3. Download the source code and create a .env file.
4. Store a variable in the .env file called DISCORD_TOKEN, this should store your discord bot token. `DISCORD_TOKEN=your_token`
5. Install the required dependencies.
6. Start the bot using python `python main.py`

# Commands
## 1. Reminders
Set study reminders to keep you on track with your subjects.<br/>

**Command:** /remindme <time> <subject><br/>

**Description:** Sets a reminder for a subject at the specified time.<br/>
**Time format:** You can provide the time in two formats:<br/>
**YYYY-MM-DD HH:MM** (24-hour format)<br/>
**HH:MM** (Bot will assume the time is for today, or tomorrow if the time has already passed)<br/>
**Example:**
`/remindme 2024-09-07 14:00 math`
`/remindme 14:30 chemistry<br/>`
**Error Handling:** If the provided time is in the past or in the wrong format, the bot will notify you to enter a valid time.

## 2. Clear Messages
Clear unwanted messages from a channel.

**Command:** /clear <amount>
**Description:** Deletes a specified number of messages (up to 100).
**Example:** /clear 20
## 3. Flashcards
Manage flashcards for different study topics.

**Command:** /flashcards <command> [options]
**SubCommands:**
**Add:**Adds a flashcard to the specified topic.<br/>
**Command:**/flashcards add <topic> <question> <answer><br/>
**Example:**/flashcards add math "What is 2+2?" "4"<br/>
**List:** Lists flashcards, either for all topics or for a specific one.<br/>
**Command:**/flashcards list [topic] [page]<br/>
**Example:**/flashcards list math (lists flashcards for the math topic)<br/>
**Delete:** Deletes a flashcard by its ID.<br/>
**Command:**/flashcards delete <id><br/>
**Example:**/flashcards delete 5<br/>
## 4. Notes
Store personal study notes.<br/>

**Command:** /notes <command> [options]<br/>
**Subcommands:** <br/>
**Add:** Adds a note to a specified topic.<br/>
**Command:**/notes add <topic> <note><br/>
**Example:**/notes add physics "Newton's 3rd Law"<br/>
**List:** Lists all notes, or notes from a specific topic.<br/>
**Command:** /notes list [topic]<br/>
**Example:**/notes list physics<br/>
**Delete:** Deletes a note by its ID.<br/>
**Command:**/notes delete <id><br/>
**Example:** /notes delete 2<br/>
## 5. Quiz
Start a quiz based on flashcards.<br/>

**Command:** /quiz [topic]<br/>
Description: Begins a quiz with flashcards from a specific topic (or all topics if none is specified).<br/>
Example: /quiz math<br/>
How it works: The bot will ask a question, and you need to answer in the chat. It will keep track of your correct answers and give a score at the end.<br/>
## 6. Sync Commands
Forces the bot to synchronize its commands with the server.<br/>

**Command:** !sync
Description: Forces the bot to sync its application commands with Discord.<br/>
Example: !sync<br/>
