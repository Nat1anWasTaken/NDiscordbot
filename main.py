import os

import discord
import pymongo
import requests
from discord.ext import commands, tasks

client = pymongo.MongoClient("")
prefix_db = client.main.prefix

def PREFIX(bot, message):
    setting = prefix_db.find_one({"id": str(message.guild.id)})

    if setting == None:
        return commands.when_mentioned_or('!!')(bot, message)
    else:
        return commands.when_mentioned_or(setting['prefix'])(bot, message)

intents = discord.Intents.all()

bot = commands.Bot(command_prefix=PREFIX, owner_id=731146912975159427, intents=intents)

bot.remove_command('help')

@bot.command()
@commands.has_permissions(manage_guild=True)
async def prefix(ctx, *, prefix):
    CLIENT = ctx.guild.get_member(701294182500925490)
    await CLIENT.edit(nick=f"[{prefix}] 奈豆")
        
    old = prefix_db.find({"id": str(ctx.guild.id)})
    if old == None:
        data = {
            "id": str(ctx.guild.id),
            "prefix": prefix
        }
        prefix_db.insert_one(data)
    else:
        prefix_db.delete_one({"id": str(ctx.guild.id)})
        data = {
            "id": str(ctx.guild.id),
            "prefix": prefix
        }
        prefix_db.insert_one(data)
    await ctx.send(f"已將前綴設成 `{prefix}`")

@bot.command()
async def load(ctx, extension):
    embed=discord.Embed(title="Load")
    try:
        bot.load_extension(f'cogs.{extension}')
        embed.color = discord.Colour.green()
        embed.description = f'Loaded: {extension}'
        print(f"[檔案] 讀取 {extension}")
    except Exception as error:
        embed.color = discord.Colour.red()
        embed.description = f'Error:\n```{error}```'
        print(f"[檔案] 讀取 {extension} 時發生錯誤: \n{error}")
    await ctx.send(embed=embed)

@bot.command()
async def reload(ctx, extension):
    embed=discord.Embed(title="Reload")
    try:
        bot.reload_extension(f'cogs.{extension}')
        embed.color = discord.Colour.green()
        embed.description = f'Reloaded: {extension}'
        print(f"[檔案] 重新讀取 {extension}")
    except Exception as error:
        embed.color = discord.Colour.red()
        embed.description = f'Error:\n```{error}```'
        print(f"[檔案] 重新讀取 {extension} 時發生錯誤: \n{error}")
    await ctx.send(embed=embed)

@bot.command()
async def unload(ctx, extension):
    embed=discord.Embed(title="Unload")
    try:
        bot.unload_extension(f'cogs.{extension}')
        embed.color = discord.Colour.green()
        embed.description = f'Unloaded: {extension}'
        print(f"[檔案] 卸載 {extension}")
    except Exception as error:
        embed.color = discord.Colour.red()
        embed.description = f'Error:\n```{error}```'
        print(f"[檔案] 卸載 {extension} 時發生錯誤: \n{error}")
    await ctx.send(embed=embed)
      

            
async def delete():
    for filename in os.listdir('./downloads'):
        try:
            path = f'./downloads/{filename}'
            os.remove(path)
        except:
            pass

@bot.event
async def on_ready():
    ping.start()
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="!!help"))
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            bot.load_extension(F'cogs.{filename[:-3]}')
            print(f"[啟動] 讀取檔案: {filename}")
    print(F"[啟動] 完成! {bot.user}")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.send(':x:錯誤的指令參數')

    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(':x:缺少必須的指令參數')

    elif isinstance(error, commands.ArgumentParsingError):
        await ctx.send(':x:無法解讀指令參數')

    elif isinstance(error, commands.MissingPermissions):
        await ctx.send(':x:你沒有足夠的權限')

    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send(':x:機器人沒有足夠的權限')

    elif isinstance(error, commands.NotOwner):
        await ctx.send(":x:你不是機器人擁有者")

    elif isinstance(error, commands.CommandNotFound):
        pass

    else:
        await ctx.send(f"```{str(error)}```")
        print(f'[錯誤] {str(error)}')

    embed=discord.Embed(title="發生錯誤", description=f"在{ctx.channel.mention}發生錯誤\n```css\n[錯誤] {error}```", color=discord.Colour.red())
    channel = bot.get_channel()
    await channel.send(embed=embed)


if __name__ == "__main__":
    bot.run("")