import discord
from discord.ext import commands
from datetime import datetime, timedelta
from discord.ext import tasks
from discord.ext.commands import has_permissions
import sqlite3
import os

token = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='/', intents=intents)

con = sqlite3.connect('databases/database-discord.db')
cur = con.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS reminders(username TEXT, remind_at TIMESTAMP, subject TEXT, reminded BOOLEAN, channelID TEXT, guildID TEXT)')

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
    if not check_reminders.is_running():
        check_reminders.start()
    
@bot.command(name='clear', help='Clears the given number of messages')
@has_permissions(administrator=True)
async def clear(ctx, amount=5):

    amount = int(amount)
    if amount > 100:
        await ctx.send("You can't delete more than 100 messages at a time!")
        return
    
    try:
        deleted = await ctx.channel.purge(limit=amount, check=lambda msg: not msg.pinned)
        await ctx.send(f"Successfully deleted {len(deleted)} messages.")
    except discord.HTTPException as e:
        await ctx.send(f"Error deleting messages: {e}")
    
@bot.command(name='remindme', help='Remindign students to study the subject at the given time!')
async def remindme(ctx, time, subject):
    print(ctx.message.author.id)
    try:
        await ctx.message.delete()
    except Exception as e:
        print(e)

    date_time_format = "%Y-%m-%d %H:%M"
    time_format = "%H:%M"
    
    try:
        remind_at = datetime.strptime(time, date_time_format)
        if remind_at < datetime.now():
            await ctx.send("***How tf am I supposed to do time travel to remind you?\n***Provide a valid time, of future!")
            return
        time_difference = remind_at - datetime.now()
        print(time_difference)
        hours_diff = time_difference.total_seconds() / 3600

        embed = discord.Embed(
            title=f'Reminder for {subject}', 
            description=f'Reminder set for {remind_at}, I will remind you in {hours_diff:.2f} hours\nCC: {ctx.message.author.mention}',
            color=discord.Color.blue()
        )
        embed.set_footer(text='Study Buddy')
        
        cur.execute('INSERT INTO reminders VALUES (?, ?, ?, ?, ?, ?)', (ctx.message.author.id, remind_at.strftime(date_time_format), subject, False, ctx.channel.id, ctx.guild.id))
        con.commit()

        await ctx.send(embed=embed)

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
                description=f'Reminder set for {remind_at}, I will remind you in {hours_diff:.2f} hours.\nCC: {ctx.message.author.mention}',
                color=discord.Color.blue()
            )
            embed.set_footer(text='Study Buddy')
            
            cur.execute('INSERT INTO reminders VALUES (?, ?, ?, ?, ?, ?)', (ctx.message.author.id, remind_at.strftime(date_time_format), subject, False, ctx.channel.id, ctx.guild.id))
            con.commit()

            await ctx.send(embed=embed)
        except Exception as e:
            print(e)
            embed = discord.Embed(title="Invalid time format", description="Please use 'YYYY-MM-DD HH:MM' or 'HH:MM'")
            await ctx.send(embed=embed)



bot.run(token)