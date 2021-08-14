import asyncio

import discord
from discord.ext import commands
from disputils import BotEmbedPaginator, BotConfirmation, BotMultipleChoice


class mod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        await member.kick(reason=reason)
        await ctx.send(F"踢出了{member.mention}")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        await member.ban(reason=reason)
        await ctx.send(F"封鎖了{member.mention}")

    @commands.command()
    @commands.has_permissions()
    async def vote(self, ctx, *,content):
        main_embed = discord.Embed(title="建立投票", description="請選擇投票選項\n[1] <:yes:747794599099105281> <:no:747794608947462221>\n[2] <:yes:747794599099105281> <:none:747794617780666398> <:no:747794608947462221>\n[3] 自訂\n[4] 取消")
        message = await ctx.send(embed=main_embed)
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content in ['1', '2', '3', '4']
        
        option_type = await self.bot.wait_for('message', check=check)
        await option_type.delete()
        yes = self.bot.get_emoji(747794599099105281)
        none = self.bot.get_emoji(747794617780666398)
        no = self.bot.get_emoji(747794608947462221)
        numbers = {
            '1': '1️⃣',
            '2': '2️⃣',
            '3': '3️⃣',
            '4': '4️⃣',
            '5': '5️⃣',
            '6': '6️⃣',
            '7': '7️⃣',
            '8': '8️⃣',
            '9': '9️⃣',
            '10': '🔟'
        }
        if option_type.content == '1':
            embed = discord.Embed(title="投票", description=content, color=discord.Colour.blue())
            msg = await ctx.send(embed=embed)
            await msg.add_reaction(yes)
            await msg.add_reaction(no)
            await ctx.message.delete()
            await message.delete()
            return ''
        elif option_type.content == '2':
            embed = discord.Embed(title="投票", description=content, color=discord.Colour.blue())
            msg = await ctx.send(embed=embed)
            await msg.add_reaction(yes)
            await msg.add_reaction(none)
            await msg.add_reaction(no)
            await ctx.message.delete()
            await message.delete()
            return ''
        elif option_type.content == '3':
            embed = discord.Embed(title="建立投票", description="請輸入選項，以`,`隔開", color=discord.Colour.green())
            msg = await ctx.send(embed=embed)
            
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel
            
            message = await self.bot.wait_for('message', check=check)
            options = message.content.split(',')
            if len(options) > 10:
                error = discord.Embed(title="建立投票", description="最高僅只有10個選項", color=discord.Colour.red())
                await ctx.send(embed=error)
                await ctx.message.delete()
                await message.delete()
                await msg.delete()
                return ''
            vote_embed = discord.Embed(title="投票", description=content, color=discord.Colour.blue())
            times = 0
            for option in options:
                times += 1
                vote_embed.add_field(name=times, value=option, inline=True)
            vote_message = await ctx.send(embed=vote_embed)
            for i in range(1, len(options)+1):
                await vote_message.add_reaction(numbers[str(i)])
            await message.delete()
            await msg.delete()
            await ctx.message.delete()
        else:
            await message.delete()
            await ctx.message.delete()
            return ''
            
        
        
        
        

    @commands.command()
    @commands.has_permissions(change_nickname=True)
    async def nick(self, ctx, nick):
        user = ctx.author
        await user.edit(reason=None, nick=nick)
        await ctx.send(f"{user.mention}以變更你的暱稱為`{nick}`!")

    @commands.command()
    @commands.has_permissions(mention_everyone=True)
    async def shout(self, ctx, *, shout):
        await ctx.message.delete()
        embed = discord.Embed(title="公告", color=0x0080c0, description=f"{shout}")
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
        msg = await ctx.send("||@everyone||", embed=embed)
        await msg.add_reaction('👌')

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, num: int):
        await ctx.channel.purge(limit=num + 1)
        msg = await ctx.send(f"我刪除了{num}則訊息! (此訊息將在`3`秒後刪除)")
        await asyncio.sleep(1)
        await msg.edit(content=f"我刪除了{num}則訊息! (此訊息將在`2`秒後刪除)")
        await asyncio.sleep(1)
        await msg.edit(content=f"我刪除了{num}則訊息! (此訊息將在`1`秒後刪除)")
        await asyncio.sleep(1)
        await msg.delete()

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, delay: int):
        await ctx.channel.edit(slowmode_delay=delay)
        await ctx.send(f'好的! 已將{ctx.channel.mention}的慢速模式設為`{delay}`秒!')

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def nsfw(self, ctx):
        if ctx.channel.is_nsfw():
            await ctx.channel.edit(nsfw=False)
            await ctx.send(f'好的! 已將{ctx.channel.mention}的NSFW模式設為`是`!')
        else:
            await ctx.channel.edit(nsfw=True)
            await ctx.send(f'好的! 已將{ctx.channel.mention}的NSFW模式設為`否`!')


def setup(bot):
    bot.add_cog(mod(bot))
