import discord
from discord.ext import commands
from disputils import BotEmbedPaginator
import pymongo

client = pymongo.MongoClient("")
marry_db = client.Testdb.marries

client = pymongo.MongoClient("")
pets_db = client.main.pets

ticket_db = client.main.ticket
voice_db = client.main.voice
prefix_db = client.main.prefix
verify_db = client.main.verify

client = pymongo.MongoClient("")
abot_db = client.main.anti_bot

snipe_dict = {}


class info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    @commands.command(name="commands")
    async def commands__(self, ctx):
        await ctx.message.add_reaction('✅')
        embeds = [
            discord.Embed(title="指令列表|:notepad_spiral:提示", description="`{}`表示必選，`[]`表示可選", color=0x0080c0),
            discord.Embed(title="指令列表|:bell:普通類", description="`ping`顯示機器人延遲\n`help`顯示此訊息\n`userinfo [成員]`顯示用戶資訊\n`invite` 顯示機器人邀請連結", color=0x0080c0),
            discord.Embed(title="指令列表|:hammer_pick:管理類", description="`clear {數量}` 刪除一定數量的訊息\n`kick {成員} [原因]` 踢出某位成員\n`ban {成員} [原因]` 封鎖某位成員\n`vote {問題}` 舉行一個投票\n`nick {暱稱}` 更改你的暱稱\n`nsfw` 設置所在頻道的限制級模式\n`slowmode {秒數}` 設置所在頻道的慢速模式", color=0x0080c0),
            discord.Embed(title="指令列表|:tada:遊戲類", description="`dice` 擲骰子\n`ask {問題}` 問一個問題\n`rps` 猜拳小遊戲\n`marry {成員}` 向某個人求婚\n`divorce` 離婚", color=0x0080c0),
            discord.Embed(title="指令列表|:gear:設定類", description="`prefix {前綴}` 設定伺服器前綴\n`vc` 動態語音頻道\n`verifysetup` 初始化驗證系統\n`verfiyremove` 移除此伺服器的驗證系統\n`ticket` Ticket系統主指令\n`security` 保護你的群組", color=0x0080c0),
            discord.Embed(title="指令列表|:notes:音樂類", description="`join [頻道]` 讓機器人連接至語音頻道\n`np` 顯示現正播放曲目\n`pause` 暫停音樂\n`play {URL/關鍵字}` 播放某首歌曲\n`queue` 顯示播放序列\n`resume` 繼續音樂\n`search {關鍵字}` 搜尋音樂\n`skip` 跳過音樂\n`stop` 停止音樂\n`volume {音量}` 改變播放音量`", color=0x0080c0)
        ]
        
        # paginator = BotEmbedPaginator(ctx, embeds)
        # await paginator.run()
        helpm = discord.Embed(title="指令列表", color=discord.Colour.blue(), description="`{}`表示必選，`[]`表示可選")
        for embed in embeds:
            helpm.add_field(name=embed.title.replace("指令列表|", ""), value=embed.description)
        await ctx.send(embed=helpm)

    @commands.command()
    async def help(self, ctx):
        raw_prefix = prefix_db.find_one({"id": str(ctx.guild.id)})
        if raw_prefix == None:
            prefix = "!!"
        else:
            prefix = raw_prefix['prefix']
        embed = discord.Embed(color=discord.Colour.red())
        embed.set_author(name="奈豆", icon_url="https://cdn.discordapp.com/avatars/701294182500925490/868bc2a69db212f1572d8cdaf662c5f0.png", url="https://ndiscordbot.tk")
        embed.description = f"歡迎使用奈豆機器人!\n我可以提供音樂、結婚、寵物、動態語音、Ticket等服務!\n\n你可以使用`!!commands`指令來在Discord中查看所有指令\n也可以前往[點我開啟](https://ndiscordbot.tk/commands?prefix={prefix})查看網頁版的指令列表!"
        await ctx.send(embed=embed)

        
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if not message.author.bot:
            snipe_dict[str(message.channel.id)] = message
        
    @commands.command()
    async def snipe(self, ctx):
        try:
            message = snipe_dict[str(ctx.channel.id)]
            embed = discord.Embed(description=message.content, color=message.author.top_role.color, timestamp=message.created_at)
            if len(message.attachments) > 0:
                links = []
                for attachment in message.attachments:
                    links.append(f"[{attachment.filename}]({attachment.url.replace('cdn.discordapp.com', 'media.discordapp.net')})")
                embed.add_field(name="🔗附件", value=", ".join(links))

                embed.set_image(url=message.attachments[0].url.replace('cdn.discordapp.com', 'media.discordapp.net'))
            embed.set_author(name=message.author, icon_url=message.author.avatar_url)
            await ctx.send(embed=embed)
        except KeyError:
            embed = discord.Embed(title=":x: | 無法找到最後刪除的訊息")
            await ctx.send(embed=embed)

    @commands.command()
    async def ping(self, ctx):
        await ctx.send(F'Pong!\n機器人延遲: {round(self.bot.latency * 1000)} ms')

    @commands.command(aliases=['ui', 'uinfo'])
    @commands.cooldown(1, 5, discord.ext.commands.BucketType.default)
    async def userinfo(self, ctx, member: discord.Member = None):
        await ctx.channel.trigger_typing()
        if member is None:
            member = ctx.author
        embed = discord.Embed(title=f"{member}", description=f'ID: {member.id}', color=member.top_role.color)
        if member.bot:
            embed.title = f"{member}<:bot:764287332848762900>"
        if ctx.guild.owner_id == member.id:
            embed.title = f"{member}<:owner:764287851650220053>"
        if member.id == 731146912975159427:
            embed.title=f"{member}<:bot_owner:764288266664149012>"

        if member.status == discord.Status.online:
            status = '<:online:742189840686252032>線上'
        elif member.status == discord.Status.idle:
            status = '<:idle:742189840631857152>閒置'
        elif member.status == discord.Status.do_not_disturb:
            status = '<:dnd:742189840115826831>請勿打擾'
        elif member.status == discord.Status.offline:
            status = '<:offline:742189840648634483>離線/隱形'
        
        try:
            if member.activity.type == discord.ActivityType.playing:
                doing = '正在玩'
                activity = f'🎮{member.activity.name}'
            elif member.activity.type == discord.ActivityType.listening:
                if member.activity.name == 'Spotify':
                    doing = '正在聽'
                    activity = f'<:spotify:742208812622020709>{member.activity.title}'
                else:
                    doing = "正在聽"
                    activity = f":headphones{member.activity.title}"
            elif member.activity.type == discord.ActivityType.streaming:
                doing = '正在直播'
                activity = f':red_circle:[{member.activity.title}]({member.activity.url})'
            elif member.activity.type == discord.ActivityType.custom:
                doing = '自訂狀態'
                activity = f'{member.activity.name}'
            else:
                doing = '動作'
                activity = f"N/A"
        except AttributeError:
            doing = None
        except UnboundLocalError:
            pass

        roles = []
        for role in member.roles:
            roles.append(f"<@&{role.id}>")
        roles.pop(0)
        roles.reverse()
        member_roles = ", ".join(roles)

        petData = pets_db.find({"user": str(member.id)})
        if pets_db.count_documents({"user": str(member.id)}) == 0:
            pet = None
        else:
            pets = []
            for data in petData:
                pets.append(f"<@{data['pet']}>")
            pet = ", ".join(pets)
            
        masterData = pets_db.find({"pet": str(member.id)})
        if pets_db.count_documents({"pet": str(member.id)}) == 0:
            master = None
        else:
            masters = []
            for data in masterData:
                masters.append(f"<@{data['user']}>")
            master = ", ".join(masters)

        love = marry_db.find_one({"discordid1": str(member.id)})
        if love == None:
            love = marry_db.find_one({"discordid2": str(member.id)})
            if love == None:
                loveStatus = '單身'
            else:
                mate = love['discordid1']
                loveStatus = f"已婚 - <@{mate}>"
        else:
            mate = love['discordid2']
            loveStatus = f"已婚 - <@{mate}>"

        try:
            invites = 0
            for invite in await ctx.guild.invites():
                if invite.inviter.id == member:
                    invites += invite.uses
        except:
            invites = 0
            
        

        
        embed.add_field(name="創建時間", value=member.created_at.strftime("%Y/%m/%d\n%H時%M分%S秒"), inline=True)
        embed.add_field(name="狀態", value=status, inline=True)
        if doing != None:
            embed.add_field(name=doing, value=activity, inline=True)
        embed.add_field(name="暱稱", value=member.display_name, inline=True)
        embed.add_field(name="身分組", value=f'{member_roles}, @everyone', inline=True)
        embed.add_field(name="邀請人數", value=invites, inline=True)
        if pet != None:
            embed.add_field(name="寵物", value=f"{pet}", inline=True)
        if master != None:
            embed.add_field(name="主人", value=f"{master}", inline=True)
        embed.add_field(name="感情狀態", value=loveStatus, inline=False)
        embed.set_thumbnail(url=member.avatar_url)
        await ctx.send(embed=embed)


    @commands.command(aliases=['gi', 'ginfo'])
    async def guildinfo(self, ctx):
        await ctx.message.add_reaction('✅')
        await ctx.channel.trigger_typing()
        nl = '\n'
        owner = discord.Embed(title=f"{ctx.guild.name}|擁有者資訊", description=f"**擁有者名稱:**\n{self.bot.get_user(ctx.guild.owner_id)}\n\n**擁有者暱稱:**\n{ctx.guild.get_member(ctx.guild.owner.id).nick}", color=discord.Colour.red())
        server = discord.Embed(title=f"{ctx.guild.name}|伺服器資訊", description=f"**伺服器ID:**\n{ctx.guild.id}\n\n**伺服器位置:**\n{ctx.guild.region}", color=discord.Colour.red())
        # MEMBERS
        online = []
        idle = []
        dnd = []
        offline = []
        for user in ctx.guild.members:
            if user.status == discord.Status.online:
                online.append(user)
            if user.status == discord.Status.idle:
                idle.append(user)
            if user.status == discord.Status.dnd:
                dnd.append(user)
            if user.status == discord.Status.offline:
                offline.append(user)
        users = []
        bots = []
        for user in ctx.guild.members:
            if user.bot:
                bots.append(user)
            else:
                users.append(user)
        member = discord.Embed(title=f"{ctx.guild.name}|人員資訊", description=f"**伺服器人數:**\n總人數: {len(ctx.guild.members)}\n成員: {len(users)}\n機器人: {len(bots)}\n\n**各狀態人數:**\n<:online:742189840686252032>線上人數: {len(online)}{nl}<:idle:742189840631857152>閒置總人數: {len(idle)}{nl}<:dnd:742189840115826831>請勿打擾總人數: {len(dnd)}{nl}<:offline:742189840648634483>離線總人數: {len(offline)}", color=discord.Color.red())
        # CHANNELS
        text = []
        voice = []
        category = []
        nsfw = []
        news = []
        for channel in ctx.guild.channels:
            if channel.type == discord.ChannelType.text:
                text.append(channel)
            if channel.type == discord.ChannelType.voice:
                voice.append(channel)
            if channel.type == discord.ChannelType.category:
                category.append(channel)
            if channel.type != discord.ChannelType.voice:
                if channel.is_nsfw():
                    nsfw.append(channel)
            if channel.type == discord.ChannelType.news:
                news.append(channel)
        channel = discord.Embed(title=f"{ctx.guild.name}|頻道資訊", description=f"文字頻道數: {len(text)}\n語音頻道數: {len(voice)}\n類別總數: {len(category)}\n限制級頻道數: {len(nsfw)}\n公告頻道數: {len(news)}", color=discord.Colour.red())
        # MORE INFORMATION
        png = []
        gif = []
        for emoji in ctx.guild.emojis:
            if emoji.animated:
                gif.append(emoji)
            else:
                png.append(emoji)
        more = discord.Embed(title=f"{ctx.guild.name}|其他資訊", description=f"**加乘狀態:**\n<:server_level:771995828771880991>等級: {ctx.guild.premium_tier}{nl}<:server_boost:771995838368972811>加成數: {ctx.guild.premium_subscription_count}\n\n**自訂表情資訊:**\n總數: {len(ctx.guild.emojis)}\n靜態表情符號: {len(png)}\n動態表情符號: {len(gif)}", color=discord.Colour.red())
        # ICON
        icon = discord.Embed(title=f"{ctx.guild.name}|伺服器圖片", color=discord.Colour.red())
        icon.set_image(url=ctx.guild.icon_url)
        # SETTINGS
        settings = discord.Embed(title=f"{ctx.guild.name}|伺服器設定", color=discord.Colour.red())
        prefix = prefix_db.find_one({"id": str(ctx.guild.id)})
        if prefix == None:
            pass
        else:
            settings.add_field(name="自訂前綴", value=prefix['prefix'])
        ticket = ticket_db.find_one({"guild": ctx.guild.id})
        if ticket == None:
            pass
        else:
            roles = []
            for role in ticket['roles']:
                try:
                    roles.append(ctx.guild.get_role(role).mention)
                except:
                    pass
            try:
                settings.add_field(name="Ticket系統", value=f"類別:　{self.bot.get_channel(ticket['category']).name}\n客服身分組: {', '.join(roles)}", inline=False)
            except:
                pass
        voice = voice_db.find_one({"id": ctx.guild.id})
        if voice == None:
            pass
        else:
            try:
                settings.add_field(name="動態語音", value=f"頻道: {self.bot.get_channel(voice['channel']).name}", inline=False)
            except:
                pass
        verify = verify_db.find_one({"id": str(ctx.guild.id)})
        if verify == None:
            pass
        else:
            try:
                settings.add_field(name="驗證系統", value=f"驗證頻道: {self.bot.get_channel(int(verify['channel'])).mention}\n已驗證身分組: {ctx.guild.get_role(int(verify['role'])).mention}", inline=False)
            except Exception as e:
                print(e)
                pass
        abot = abot_db.find_one({"id": ctx.guild.id})
        if abot == None:
            settings.add_field(name="反機器人", value="<:no:747794608947462221>", inline=False)
        else:
            if abot['enabled']:
                settings.add_field(name="反機器人", value="<:yes:747794599099105281>", inline=False)
            else:
                settings.add_field(name="反機器人", value="<:no:747794608947462221>", inline=False)
        embeds = [
            owner,
            server,
            icon,
            member,
            channel,
            settings,
            more
        ]
        paginator = BotEmbedPaginator(ctx, embeds)
        try:
            await paginator.run()
        except:
            await ctx.send(":x: 發生錯誤!")
            pass
        
    @commands.command(aliases=['bi'])
    @commands.is_owner()
    async def botinfo(self, ctx):
        embed=discord.Embed(title='機器人資訊', color=discord.Colour.red())
        embed.add_field(name="伺服器總數", value=len(self.bot.guilds))
        await ctx.send(embed=embed)

        
def setup(bot):
    bot.add_cog(info(bot))