import datetime

import discord
from discord.ext import commands, tasks

messages = {}
class secret(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def get(self, ctx, id: int, status):
        user = self.bot.get_user(id)
        embed = discord.Embed(title="用戶資訊", color=discord.Colour.blue(), timestamp=datetime.datetime.now())
        try:
            embed.set_thumbnail(url=user.avatar_url)
        except:
            pass
        embed.add_field(name="名稱", value=user, inline=False)
        embed.add_field(name="ID", value=user.id, inline=False)
        embed.add_field(name="創建時間", value=user.created_at, inline=False)
        embed.add_field(name="關係狀態", value=status, inline=False)
        await ctx.send(embed=embed)
        await ctx.message.delete()

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        async for data in guild.audit_logs(limit=5):
            if data.action == discord.AuditLogAction.bot_add:
                author = data.user
        invite = await guild.channels[0].create_invite()
        embed = discord.Embed(title="加入", color=discord.Colour.green())
        embed.add_field(name="伺服器名稱", value=guild.name, inline=True)
        embed.add_field(name="邀請者", value=author, inline=True)
        try:
            embed.add_field(name="邀請連結", value=invite, inline=False)
        except NameError:
            pass
        channel = self.bot.get_channel()
        await channel.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    async def send(self, ctx, message: str):
        await ctx.message.delete()
        await ctx.send(message)

def setup(bot):
    bot.add_cog(secret(bot))
