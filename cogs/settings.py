import discord
from discord.ext import commands
import pymongo
import random
from disputils import BotEmbedPaginator, BotConfirmation, BotMultipleChoice
import asyncio

client = pymongo.MongoClient("")
verify_db = client.main.verify
client = pymongo.MongoClient("")
voice_db = client.main.voice
client = pymongo.MongoClient("")
ticket_db = client.main.ticket

client = pymongo.MongoClient("")
abot_db = client.security.anti_bot

class settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        data = voice_db.find_one({"id": member.guild.id})

        if data == None:
            return ''
        else:
            try:
                if before.channel.name.endswith(' 的頻道') and len(before.channel.members) == 0:
                    await before.channel.delete()
            except AttributeError:
                pass
            try:
                if after.channel.id == data['channel']:
                    channel = await after.channel.category.create_voice_channel(name=f"[{len(after.channel.category.channels)}] {member.name} 的頻道")
                    await member.move_to(channel)
            except AttributeError:
                pass

    
    @commands.group()
    async def vc(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(title="動態語音頻道", description="`setup` 初始化動態語音頻道\n`lock` 鎖住當前頻道\n`unlock` 解鎖當前頻道")
            await ctx.send(embed=embed)
            

    @vc.command()
    async def lock(self, ctx):
        data = voice_db.find_one({"id": ctx.guild.id})
        channel = self.bot.get_channel(data['channel'])
        if data is None:
            await ctx.send("此伺服器尚未設置動態語音頻道!")
            return ''
        if not ctx.author.voice.channel.category.id == channel.category.id:
            await ctx.send(":x: 你不在一個動態語音裡面!")
        await ctx.author.voice.channel.set_permissions(ctx.guild.default_role, connect=False)
        embed = discord.Embed(title='鎖定頻道', description="成功將此頻道鎖定!", color=discord.Colour.green())
        await ctx.send(embed=embed)
    @vc.command()
    async def unlock(self, ctx):
        data = voice_db.find_one({"id": ctx.guild.id})
        channel = self.bot.get_channel(data['channel'])
        if data is None:
            await ctx.send("此伺服器尚未設置動態語音頻道!")
            return ''
        if not ctx.author.voice.channel.category.id == channel.category.id:
            await ctx.send(":x: 你不在一個動態語音裡面!")
        await ctx.author.voice.channel.set_permissions(ctx.guild.default_role, connect=True)
        embed = discord.Embed(title='鎖定頻道', description="成功將此頻道解鎖!", color=discord.Colour.green())
        await ctx.send(embed=embed)

    @vc.command(name="setup")
    @commands.has_permissions(manage_guild=True)
    async def setup_(self, ctx):
        embed = discord.Embed(title="動態語音", description="動態語音可以讓伺服器不需要為了分門別類創建一堆語音頻道\n輸入 `continue` 繼續",
                              color=discord.Colour.green())
        embed.set_image(url="https://media.discordapp.net/attachments/738984608061849635/746669114818428988/DVC.gif")
        await ctx.send(embed=embed)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content == 'continue'

        await self.bot.wait_for('message', check=check)
        data = voice_db.find_one({"id": ctx.guild.id})
        if data == None:
            category = await ctx.guild.create_category(name="動態語音頻道", position=1)
            channel = await category.create_voice_channel(name="創建新頻道", user_limit=1)
            voice_db.insert({"id": ctx.guild.id, "channel": channel.id})
        else:
            category = await ctx.guild.create_category(name="動態語音頻道", position=1)
            channel = await category.create_voice_channel(name="創建新頻道", user_limit=1)
            voice_db.remove({"id": ctx.guild.id})
            voice_db.insert({"id": ctx.guild.id, "channel": channel.id})
        embed = discord.Embed(title="完成", color=discord.Colour.green())
        await ctx.send(embed=embed)
        
        
    @commands.command()
    @commands.has_permissions(manage_roles=True, manage_channels=True)
    async def verifysetup(self, ctx):
        while True:
            embed = discord.Embed(title="驗證初始化", colour=discord.Colour.green()).set_footer(text="請選擇驗證頻道")
            embed.description = ""
            times = 0
            channels = {}
            for channel in ctx.guild.text_channels:
                times += 1
                channels[str(times)] = channel
            for channel in channels:
                embed.description += f"[{channel}] {channels[channel].name}\n"


            await ctx.send(ctx.author.mention, embed=embed)
            def check(m):
                return m.channel == ctx.channel and m.author == ctx.author
            
            msg = await self.bot.wait_for('message', check=check)
            try:
                VerifyChannel = channels[str(msg.content)]
                break
            except KeyError:
                embed=discord.Embed(title="驗證初始化", description="未知的頻道，請重新輸入!", colour=discord.Colour.red())
                await ctx.send(embed=embed)
                continue
        while True:
            embed=discord.Embed(title="驗證初始化", colour=discord.Colour.green()).set_footer(text="請選擇已驗證身分組")
            embed.description = ""
            times = 0
            roles = {}
            raw_roles = ctx.guild.roles
            raw_roles.remove(ctx.guild.default_role)
            for role in raw_roles:
                times += 1
                roles[str(times)] = role
            for role in roles:
                embed.description += f"[{role}] {roles[role].mention}\n"
            await ctx.send(ctx.author.mention, embed=embed)
            def check(m):
                return m.channel == ctx.channel and m.author == ctx.author
            
            msg = await self.bot.wait_for('message', check=check)
            try:
                VerifyRole = roles[msg.content]
                break
            except KeyError:
                embed=discord.Embed(title="驗證初始化", description="未知的身分組，請重新輸入!", colour=discord.Colour.red())
                await ctx.send(embed=embed)
                continue
        old = verify_db.find_one({"id": str(ctx.guild.id)})
        if old == None:
            data = {
                "id": str(ctx.guild.id),
                "channel": str(VerifyChannel.id),
                "role": str(VerifyRole.id)
            }
            verify_db.insert(data)
        else:
            verify_db.delete_one({"id": str(ctx.guild.id)})
            data = {
                "id": str(ctx.guild.id),
                "channel": str(VerifyChannel.id),
                "role": str(VerifyRole.id)
            }
            verify_db.insert_one(data)
        embed=discord.Embed(title="驗證初始化", description=f"完成, 現在在{VerifyChannel.mention}使用`verify`指令即可執行驗證!", colour=discord.Colour.green())
        await ctx.send(embed=embed)
        
        
    @commands.command()
    async def verify(self, ctx):
        data = verify_db.find_one({"id": str(ctx.guild.id)})
        if data == None:
            await ctx.send("此伺服器尚未設置驗證系統!")
        else:
            if str(ctx.channel.id) == data['channel']:
                code = str(random.randint(111111, 999999))
                message = await ctx.send(f"請在30秒內輸入`{code}`")
                def check(m):
                    return m.author == ctx.author and m.channel == ctx.channel and m.content == code
                try:
                    await self.bot.wait_for('message', check=check, timeout=30)
                    await ctx.send(":white_check_mark: 驗證成功!")
                    role = ctx.guild.get_role(int(data['role']))
                    try:
                        await ctx.author.add_roles(role, reason="驗證成功", atomic=True)
                    except:
                        await ctx.send(":x: 在新增身分組時發生錯誤!")
                except asyncio.TimeoutError:
                    await message.delete()
                    await ctx.message.delete()

            else:
                await ctx.send("這裡不是驗證頻道!")

    @commands.command()
    @commands.has_permissions(manage_roles=True, manage_channels=True)
    async def verifyremove(self, ctx):
        verify_db.remove({"id": str(ctx.guild.id)})
        await ctx.send("完成! 已將此伺服器d的驗證系統關閉!")
        
    @commands.group()
    async def ticket(self, ctx):
        if ctx.invoked_subcommand is None:
            data = ticket_db.find_one({"guild": ctx.guild.id})
            if data == None:
                await ctx.send(":x: 此伺服器還沒有設置Ticket")
                return ''
            try:
                category = self.bot.get_channel(data['category'])
            except:
                await ctx.send(":x: 此伺服器還沒有設置Ticket")
                return ''
            for channel in category.text_channels:
                if channel.topic == str(ctx.author.id):
                    embed = discord.Embed(title="Ticket", description="你已經創建了你的Ticket!", color=discord.Colour.red())
                    await ctx.send(embed=embed)
                    return ''
                
            for roleid in data['roles']:
                try:
                    role = ctx.guild.get_role(roleid)
                except:
                    continue
            channel = await category.create_text_channel(name=f'ticket-{ctx.author.name}', topic=str(ctx.author.id))
            await channel.set_permissions(ctx.guild.default_role, read_messages=False)
            await channel.set_permissions(ctx.author, read_messages=True, send_messages=True)
            for roleid in data['roles']:
                try:
                    role = ctx.guild.get_role(roleid)
                except:
                    continue
                await channel.set_permissions(role, read_messages=True, send_messages=True)
            
            
            embed=discord.Embed(title="Ticket", description="輸入`ticket close`指令來關閉此頻道", color=discord.Colour.green())
            await channel.send(ctx.author.mention, embed=embed)
            embed=discord.Embed(title="Ticket", description=f"創建成功! {channel.mention}")
            await ctx.send(embed=embed)
            return ''

    @ticket.command()
    @commands.cooldown(1, 20)
    @commands.has_permissions(manage_channels=True)
    async def setup(self, ctx):
        permissions = ctx.author.guild_permissions
        data = ticket_db.find_one({"guild": ctx.guild.id})
        if data != None:
            ticket_db.delete_one({"guild": data['guild']})
        category = await ctx.guild.create_category(name="Ticket")
        
        def check(m):
            return m.author.id == ctx.author.id and m.channel == ctx.channel
        
        embed = discord.Embed(title="Ticket", description="請輸入客服身分組的ID，以`,`隔開", color=discord.Colour.green())
        await ctx.send(embed=embed)
        msg = await self.bot.wait_for('message', check=check)
        roles = []
        for roleid in msg.content.split(","):
            try:
                role = ctx.guild.get_role(int(roleid))
                roles.append(role.id)
            except:
                await ctx.send(":x: 未知的身分組")
                return ''
        data = {
            "guild": ctx.guild.id,
            "category": category.id,
            "roles": roles
        }
        ticket_db.insert(data)
        embed = discord.Embed(title="Ticket", description="完成", color=discord.Colour.green())
        await ctx.send(embed=embed)
        return ''
    @ticket.command()
    async def create(self, ctx):
        data = ticket_db.find_one({"guild": ctx.guild.id})
        if data == None:
            await ctx.send(":x: 此伺服器還沒有設置Ticket")
            return ''
        try:
            category = self.bot.get_channel(data['category'])
        except:
            await ctx.send(":x: 此伺服器還沒有設置Ticket")
            return ''
        for channel in category.text_channels:
            if channel.topic == str(ctx.author.id):
                embed = discord.Embed(title="Ticket", description="你已經創建了你的Ticket!", color=discord.Colour.red())
                await ctx.send(embed=embed)
                return ''
            
        for roleid in data['roles']:
            try:
                role = ctx.guild.get_role(roleid)
            except:
                continue
            permissions = {
                role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
        channel = await category.create_text_channel(name=f'ticket-{ctx.author.name}', topic=str(ctx.author.id))
        await channel.set_permissions(ctx.guild.default_role, read_messages=False)
        await channel.set_permissions(ctx.author, read_messages=True, send_messages=True)
        for roleid in data['roles']:
            try:
                role = ctx.guild.get_role(roleid)
            except:
                continue
            await channel.set_permissions(role, read_messages=True, send_messages=True)
        
        
        embed=discord.Embed(title="Ticket", description="輸入`ticket close`指令來關閉此頻道", color=discord.Colour.green())
        await channel.send(ctx.author.mention, embed=embed)
        embed=discord.Embed(title="Ticket", description=f"創建成功! {channel.mention}")
        await ctx.send(embed=embed)
        return ''
    
    @ticket.command()
    async def close(self, ctx):
        data = ticket_db.find_one({"guild": ctx.guild.id})
        if data == None:
            await ctx.send(":x: 此伺服器還沒有設置Ticket")
            return ''
        if ctx.channel.category.id == data['category']:
            confirm = BotConfirmation(ctx, discord.Colour.green())
            await confirm.confirm(f"關閉此Ticket?")
            if confirm.confirmed:
                await confirm.quit()
                await ctx.channel.delete()
                return ''
            else:
                await confirm.quit("已取消") 
                return ''
    @ticket.command()
    async def help(self, ctx):
        embed = discord.Embed(title="Ticket", description="`setup` 設置Ticket系統\n`create` 創建Ticket頻道\n`close` 關閉Ticket頻道", color=discord.Colour.green())
        await ctx.send(embed=embed)
        return ''

    @commands.group()
    async def security(self, ctx):
        if not ctx.invoked_subcommand:
            embed = discord.Embed(title="安全", description="`bot` 防止機器人進入")
            await ctx.send(embed=embed)
            return ''

    @security.command()
    @commands.has_permissions(administrator=True)
    async def bot(self, ctx):
        if ctx.author.top_role > ctx.guild.get_member(ctx.bot.user.id).top_role or ctx.guild.owner.id == ctx.author.id:
            pass
        else:
            await ctx.send(":x: 你沒有足夠的權限!")
            return ''
        confirm = BotConfirmation(ctx=ctx, color=discord.Colour.green())
        await confirm.confirm("確定?")
        await confirm.quit()
        if confirm.confirmed:
            data = abot_db.find_one({"id": ctx.guild.id})
            if data == None:
                abot_db.insert({"id": ctx.guild.id, "enabled": True})
                await ctx.send(embed=discord.Embed(title="Anti Bot✅", color=discord.Colour.green()))
                return ''
            else:
                if data['enabled']:
                    abot_db.update({"id": ctx.guild.id}, {"$set": {"enabled": False}})
                    await ctx.send(embed=discord.Embed(title="Anti Bot❌", color=discord.Colour.red()))
                    return ''
                else:
                    abot_db.update({"id": ctx.guild.id}, {"$set": {"enabled": False}})
                    await ctx.send(embed=discord.Embed(title="Anti Bot✅", color=discord.Colour.green()))
                    return ''
        else:
            await ctx.send(embed=discord.Embed(title="已取消", color=discord.Colour.red()))
    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot:
            data = abot_db.find_one({"id": member.guild.id})
            if data == None:
                return ''
            if data['enabled']:
                await member.kick()

    
    
def setup(bot):
    bot.add_cog(settings(bot))