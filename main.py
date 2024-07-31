import discord
from discord import app_commands
from discord.ext import commands
from discord.ext import tasks
from discord.ext.commands import has_permissions
from datetime import datetime, timedelta
import random
import sqlite3
import os

token = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

con = sqlite3.connect('databases/database-discord.db')
cur = con.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS reminders(username TEXT, remind_at TIMESTAMP, subject TEXT, reminded BOOLEAN, channelID TEXT, guildID TEXT)')
cur.execute('CREATE TABLE IF NOT EXISTS flashcards(topic TEXT, question TEXT, answer TEXT, userID TEXT, guildID TEXT, channelID TEXT)')
cur.execute('CREATE TABLE IF NOT EXISTS notes(topic TEXT, note TEXT, userID TEXT, guildID TEXT, channelID TEXT)')

@tasks.loop(minutes=1)
async def check_reminders():
    # print("Checking reminders...")
    date_time_format = "%Y-%m-%d %H:%M"
    reminders = cur.execute('SELECT rowid, *  FROM reminders WHERE remind_at <= ? AND reminded = ?', (datetime.now().strftime(date_time_format), False)).fetchall()
    for reminder in reminders:
        print(reminder)
        guild_id = int(reminder[-1])
        guild = bot.get_guild(guild_id)

        # print(guild)
        # print(int(reminder[1]))
        # print(guild.get_member(int(reminder[6])))
        
        user_id = int(reminder[1])
        user = guild.get_member(user_id)
        subject = reminder[3].capitalize()

        embed = discord.Embed(
            title=f'⏰ Reminder for studying {subject}!', 
            description=f'Hey {user.mention}, its time to get back to studying {subject}!',
            color=discord.Color.red()
        )
        embed.set_footer(text='Reminder by Study Buddy')

        channel_id = int(reminder[5])
        channel = bot.get_channel(channel_id)
        await channel.send(embed=embed)
        
        try:
            await user.send(embed=embed)

        except Exception as e:
            try:
                print(e)
                newEmbed = discord.Embed(
                    title=f"Error Sending Reminder via DM!",
                    description=f"Hey {user.mention}, I tried to send you a reminder but I couldn't.\n\
                    Please take a look at your DM settings, to receive reminders in future!",
                    color=discord.Color.red()
                )
                await channel.send(embed=newEmbed)
            
            except Exception as e:
                print(e)

        
        cur.execute('UPDATE reminders SET reminded = ? WHERE rowid = ?', (True, reminder[0]))
        con.commit()

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(e)
    if not check_reminders.is_running():
        check_reminders.start()

@bot.command(name="sync")
async def sync(ctx):
    syncing = await ctx.bot.tree.sync()
    await ctx.send(f"Synced {len(syncing)} command(s)!")
    return

@bot.tree.command(name='clear', description='Clears the given number of messages')
async def clear(interaction: discord.Interaction, amount: int = 5):

    if amount > 100:
        await interaction.response.send_message("You can't delete more than 100 messages at a time!", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    try:
        deleted = await interaction.channel.purge(limit=amount, check=lambda msg: not msg.pinned)
        await interaction.followup.send(f"Successfully deleted {len(deleted)} messages.")
    except discord.HTTPException as e:
        await interaction.followup.send(f"Error deleting messages: {e}")

    
@bot.tree.command(name='remindme', description='Remindign students to study the subject at the given time!')
async def remindme(interaction: discord.Interaction, time:str, subject:str):

    await interaction.response.defer()

    date_time_format = "%Y-%m-%d %H:%M"
    time_format = "%H:%M"
    
    try:
        remind_at = datetime.strptime(time, date_time_format)
        if remind_at < datetime.now():
            await interaction.followup.send("***How tf am I supposed to do time travel to remind you?\n***Provide a valid time, of future!", ephemeral=True)
            return
        time_difference = remind_at - datetime.now()
        print(time_difference)
        hours_diff = time_difference.total_seconds() / 3600

        embed = discord.Embed(
            title=f'Reminder for {subject}', 
            description=f'Reminder set for {remind_at}, I will remind you in {hours_diff:.2f} hours\nCC: {interaction.user.mention}',
            color=discord.Color.blue()
        )
        embed.set_footer(text='Study Buddy')
        
        cur.execute('INSERT INTO reminders VALUES (?, ?, ?, ?, ?, ?)', (interaction.user.id, remind_at.strftime(date_time_format), subject, False, interaction.channel.id, interaction.guild.id))
        con.commit()

        await interaction.followup.send(embed=embed)
        return

    except Exception as e:
        try:
            remind_at = datetime.strptime(time, time_format)
            remind_at = datetime.now().replace(hour=remind_at.hour, minute=remind_at.minute, second=0, microsecond=0)

            if remind_at < datetime.now():
                remind_at += timedelta(days=1)
            time_difference = remind_at - datetime.now()
            hours_diff = time_difference.seconds / 3600

            embed = discord.Embed(
                title=f'Reminder for {subject}', 
                description=f'Reminder set for {remind_at}, I will remind you in {hours_diff:.2f} hours.\nCC: {interaction.user.mention}',
                color=discord.Color.blue()
            )
            embed.set_footer(text='Study Buddy')
            
            cur.execute('INSERT INTO reminders VALUES (?, ?, ?, ?, ?, ?)', (interaction.user.id, remind_at.strftime(date_time_format), subject, False, interaction.channel.id, interaction.guild.id))
            con.commit()

            await interaction.followup.send(embed=embed)
            return
        except Exception as e:
            print(e)
            embed = discord.Embed(title="Invalid time format", description="Please use 'YYYY-MM-DD HH:MM' or 'HH:MM'")
            await interaction.followup.send(embed=embed)
            return

@bot.tree.command(name='flashcards', description='Add, Store and Manage Flashcards')
@app_commands.describe(
    command="The command to execute (required)",
    topic="The topic of the flashcard (required for add command, optional for list command)",
    question="The question that you want to add (required only for add command)",
    answer="The answer to the question (required only for add command)",
    page="If you want to fetch a specific page. Each page has 5 flash cards (optional, default 1)",
    id="Id of the flash card (required for delete command)"
)
@app_commands.choices(
    command=[
        app_commands.Choice(name="add", value="add"),
        app_commands.Choice(name="list", value="list"),
        app_commands.Choice(name="delete", value="delete"),
    ],
)
async def flashcards(interaction: discord.Interaction, command: app_commands.Choice[str], topic: str = None, question: str = None, answer: str = None, page: int = 1, id: int = -1):
    
    await interaction.response.defer(ephemeral=False)

    if command == "add":
        if topic is None or question is None or answer is None:
            await interaction.followup.send(
                "One or more arguments are missing!\nCommand usage: ***/flashcards add <topic> <question> <answer>***", 
                ephemeral=False
            )
            return

        try:
            
            cur.execute('INSERT INTO flashcards (topic, question, answer, userID, guildID, channelID) VALUES (?, ?, ?, ?, ?, ?)',(topic, question, answer, interaction.user.id, interaction.guild.id, interaction.channel.id))
            con.commit()

            embed = discord.Embed(
                title="Flash Card Added!",
                description=f"Question added by {interaction.user.mention} for {topic}",
                color=discord.Color.green()
            )
            embed.add_field(name="Question", value=question, inline=False)
            embed.add_field(name="Answer", value=answer, inline=False)
            embed.set_footer(text="Study Buddy")

            await interaction.followup.send(embed=embed, ephemeral=False)

        except Exception as e:
            await interaction.followup.send(f"An error occurred while adding the flashcard: {e}", ephemeral=False)

    elif command == "list":
        
        if topic is None:
            flashcards = cur.execute('SELECT rowid, * FROM flashcards WHERE guildID = ?', (interaction.guild.id,)).fetchall()
        else:
            flashcards = cur.execute('SELECT rowid, * FROM flashcards WHERE guildID = ? AND topic = ?', (interaction.guild.id, topic)).fetchall()
        
        if len(flashcards) == 0:
            embed = discord.Embed(
                title="No Flash Cards Found!",
                description=f"Add a flash card with */flashcard add <topic> <question> <answer>*",
                color=discord.Color.red()
            )
            embed.set_footer(text="Study Buddy")
            await interaction.followup.send(embed=embed, ephemeral=False)
            return
    
        if len(flashcards) > 5:
            flashcards = flashcards[(page-1)*5:page*5]
        else:
            flashcards = flashcards[(page-1)*5:]
        
        if len(flashcards) == 0:
            embed = discord.Embed(
                title="There are no more flash cards!",
                description="You have reached the end of the list.\nThere is no flashcard on this page",
                color=discord.Color.red()
            )
            embed.set_footer(text="Study Buddy")
            await interaction.followup.send(embed=embed, ephemeral=False)
            return
    
        
        for flashcard in flashcards:

            rowid, topic, question, answer, userID, guildID, channelID = flashcard

            guild = bot.get_guild(int(guildID))
            user = guild.get_member(int(userID))

            embed = discord.Embed(
                title=f"Flash Card -- Topic: {topic} -- ID: {rowid}",
                description=f"This flash card was added by {user.mention}",
                color=discord.Color.blue()
            ) 

            embed.add_field(name="Question", value=question, inline=False)
            embed.add_field(name="Answer", value=f"|| {answer} ||", inline=False)
            embed.set_footer(text="Try to answer the question before revealing the answer -- Study Buddy")

            await interaction.followup.send(embed=embed, ephemeral=True)

        total_pages = len(flashcards)//5   
        if len(flashcards) % 5 != 0:
            total_pages += 1
        
        await interaction.followup.send(f"Page {page} of {total_pages}", ephemeral=True)
    
    elif command == "delete":
        if id == -1:
            await interaction.followup.send("Please specify the flashcard ID", ephemeral=False)
            return
        
        delete_row = cur.execute('SELECT * FROM flashcards WHERE guildID = ? AND rowid = ?', (interaction.guild.id, id)).fetchone()
        
        if interaction.user.guild_permissions.administrator or interaction.user.id == int(delete_row[3]):

            cur.execute('DELETE FROM flashcards WHERE guildID = ? AND rowid = ?', (interaction.guild.id, id))
            con.commit()

            embed = discord.Embed(
                title="Flash Card Deleted!",
                description=f"Flash card with ID {id} deleted by {interaction.user.mention}",
                color=discord.Color.red()
            )

            embed.add_field(name="Question", value=delete_row[1], inline=False)
            embed.add_field(name="Answer", value=delete_row[2], inline=False)
            embed.set_footer(text="Study Buddy")

            await interaction.followup.send(embed=embed, ephemeral=False)
    else:
        await interaction.followup.send("Invalid Command",ephemeral=True)


@bot.tree.command(name='notes', description='Add, Store and Manage Notes')
async def notes(interaction: discord.Interaction,command: str, topic: str = None, note: str = None):

    """
        Notes are supposed to be different from flashcards
        While the whole group can access flash cards and view their content, notes can
        only be seen, added and deleted by the user who created them.
        Notes are also supposed to be more simplistic
    """

    await interaction.response.defer()

    if command == "add":

        if topic is None or note is None:
            await interaction.followup.send("Please specify a topic and a note", ephemeral=True)
            return

        cur.execute('INSERT INTO notes VALUES (?, ?, ?, ?)', (interaction.user.id, interaction.guild.id, topic, note))
        con.commit()
        rowid = cur.lastrowid
        
        message = f"Note for {topic} added by {interaction.user.mention}\n**{rowid}**: {note}"
        await interaction.followup.send(message, ephemeral=True)
    
    elif command == "list":
        
        if topic is None:
            notes = cur.execute('SELECT rowid, * FROM notes WHERE guildID = ?', (interaction.guild.id,)).fetchall()
        else:
            notes = cur.execute('SELECT rowid, * FROM notes WHERE guildID = ? AND topic = ?', (interaction.guild.id, topic)).fetchall()

        if len(notes) == 0:
            message = "No notes found!"
            await interaction.followup.send(message, ephemeral=True)
            return
        
        message = "***Notes:***\n\n"
        for note in notes:

            rowid, userID, guildID, topic, note = note
            message += f"**{rowid}**: {note}\n"

        await interaction.followup.send(message, ephemeral=True)
    
    else:

        await interaction.followup.send("Invalid Command",ephemeral=True)

        

bot.run(token)