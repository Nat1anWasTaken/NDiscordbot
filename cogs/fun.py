import discord
from discord.ext import commands
import random
import asyncio
from disputils import BotEmbedPaginator, BotConfirmation, BotMultipleChoice
import requests
import pymongo
import time


def convert(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60

    return f"{hour}時 {minutes}分 {seconds}秒"

async def add_reactions(message: discord.Message, reactions: list):
    for reaction in reactions:
        await message.add_reaction(reaction)
    return message

client = pymongo.MongoClient("")
marry_db = client.Testdb.marries
client = pymongo.MongoClient("")
pets_db = client.main.pets
owner = [731146912975159427, 498505540612259840, 716166764051824640]

class fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def osu(self, ctx, user: str):
        res = requests.get(f"https://osu.ppy.sh/api/get_user?k=ad9f5859ff6bdcb753b357d8c45112333a35d4a6&u={user}").json()[0]
        embed = discord.Embed(title=f"{reaction.emoji}{res['username']} | {res['user_id']}", color=0xf562a6)
        embed.description = f"<:osu_SSH:772010519829676032>{res['count_rank_ssh']} | <:osu_SS:772010519832821800>{res['count_rank_ss']} | <:osu_SH:772010519816962088>{res['count_rank_sh']} | <:osu_S:772010520542707722>{res['count_rank_s']} | <:osu_A:772010519853793300>{res['count_rank_a']}"
        embed.add_field(name="國家", value=res['country'], inline=True)
        embed.add_field(name="遊玩次數", value=res['playcount'], inline=True)
        embed.add_field(name="遊玩時數", value=convert(int(res['total_seconds_played'])), inline=True)
        embed.add_field(name="Ranked分數 | 所有分數", value=f"{res['ranked_score']} | {res['total_score']}", inline=True)
        embed.add_field(name="等級", value=round(float(res['level'])), inline=True)
        embed.add_field(name="準確度", value=f"{round(float(res['accuracy']))}%\n<:osu_300:772014757346934804>{res['count300']}\n<:osu_100:772014757233557505>{res['count100']}\n<:osu_50:772014757401591838>{res['count300']}", inline=True)
        embed.add_field(name="加入日期", value=res['join_date'], inline=True)
        embed.add_field(name="PP", value=res['pp_rank'])
        embed.set_image(url=f"http://lemmmy.pw/osusig/sig.php?colour=hexff66aa&uname={res['username']}&pp=1&countryrank&flagshadow&onlineindicator=undefined&xpbar&xpbarhex&mode={mode}")
        embed.set_thumbnail(url=f"https://a.ppy.sh/{res['user_id']}")
        await ctx.send(embed=embed)
        
    @commands.command()
    async def ask(self, ctx, *,Q):
        A = random.choice(['否', '是', '嗯?'])
        if Q.endswith('好不好'):
            A = random.choice(['好', '不好'])
        if Q.endswith('的機率'):
            A = f"{random.randint(1,100)}%"
        embed=discord.Embed(title="EGG!", color=0x0080ff)
        embed.add_field(name="問題", value=Q, inline=False)
        embed.add_field(name="答案:", value=A, inline=False)
        await ctx.send(ctx.author.mention, embed=embed)

    @commands.command()
    async def rps(self, ctx):
        PlayerScore = 0
        BotScore = 0
        while True:
            player = BotMultipleChoice(ctx, ['剪刀', '石頭', '布'], "請出拳")
            await player.run()
            await player.quit()
            bot = random.choice(['剪刀', '石頭', '布'])
            if player.choice == '剪刀':
                if bot == '剪刀':
                    status = '平手'
                if bot == '石頭':
                    status = '失敗'
                if bot == '布':
                    status = '勝利'
            elif player.choice == '石頭':
                if bot == '剪刀':
                    status = '勝利'
                if bot == '石頭':
                    status = '平手'
                if bot == '布':
                    status = '失敗'
            elif player.choice == '布':
                if bot == '剪刀':
                    status = '失敗'
                if bot == '石頭':
                    status = '勝利'
                if bot == '布':
                    status = '平手'
            else:
                embed=discord.Embed(title="已取消", color=discord.Colour.red())
                await ctx.send(embed=embed)
                break

            if status == '失敗':
                BotScore += 1
                color = discord.Colour.red()
            if status == '勝利':
                PlayerScore += 1
                color = discord.Colour.green()
            if status == '平手':
                color = discord.Colour.orange()
            
            confirm = BotConfirmation(ctx, color)
            await confirm.confirm(f"__**{status}**__\n{player.choice} vs {bot}\n{PlayerScore} | {BotScore}\n繼續?")

            if confirm.confirmed:
                await confirm.quit()
                continue
            else:
                break
            
    @commands.command()
    async def marry(self, ctx, user: discord.Member):
        love1 = marry_db.find_one({"discordid1": str(ctx.author.id)})
        if love1 == None:
            love1 = marry_db.find_one({"discordid2": str(ctx.author.id)})
            if love1 != None:
                await ctx.send(":x: 你居然想要同時跟兩個人結婚?!")
                return ''
        else:
            await ctx.send(":x: 你居然想要同時跟兩個人結婚?!")
            return ''
        love2 = marry_db.find_one({"discordid1": str(user.id)})
        if love2 == None:
            love2 = marry_db.find_one({"discordid2": str(user.id)})
            if love2 != None:
                await ctx.send(":x: 他已經結過婚了啦")
                return ''
        else:
            await ctx.send(":x: 他已經結過婚了啦")
            return ''
        if user.bot:
            await ctx.send(":x: 你居然邊緣到只能跟機器人結婚?!")
            return ''
        if ctx.author.id == user.id:
            await ctx.send(":x: 自己跟自己結婚...是不是有點怪怪的?")
            return ''
        embed = discord.Embed(title="求婚", description="輸入`yes`同意\n輸入`no`拒絕", colour=discord.Colour.green())
        msg = await ctx.send(user.mention, embed=embed)
        
        def check(m):
            return m.author.id == user.id and m.channel == ctx.channel and m.content in ['yes', 'no']
            
        message = await self.bot.wait_for('message', check=check)
        if message.content == 'yes':
            data = {
                "discordid1": str(ctx.author.id),
                "discordid2": str(user.id),
                "time": time.time(),
                "__v": 0
            }
            marry_db.insert(data)
            embed.title = "結婚"
            embed.description = f"{ctx.author.mention} :heart: {user.mention}"
            await msg.edit(embed=embed, content="")
            return ''
        elif message.content == 'no':
            embed.title = "結婚"
            embed.description = "看來他拒絕了"
            embed.colour = discord.Colour.red()
            await msg.edit(content="", embed=embed)
            return ''
        
            
    @commands.command()
    async def divorce(self, ctx):
        love = marry_db.find_one({"discordid1": str(ctx.author.id)})
        if love == None:
            love = marry_db.find_one({"discordid2": str(ctx.author.id)})
            if love == None:
                await ctx.send(":x: 你還沒有結過婚!")
                return ''
        embed = discord.Embed(title="你確定?", description="輸入`yes`確認\n輸入`no`取消", color=discord.Colour.green())
        msg = await ctx.send(embed=embed)
        def check(m):
            return m.author.id == ctx.author.id and m.content in ['yes', 'no'] and m.channel == ctx.channel
            
        message = await self.bot.wait_for('message', check=check)
        if message.content == 'yes':
            marry_db.delete_one({'_id': love['_id']})
            embed.title = '離婚'
            embed.description = f"離婚成功"
            await msg.edit(embed=embed)
            return ''
        elif message.content == 'no':
            embed.title = '離婚'
            embed.description = '已取消'
            embed.color = discord.Colour.red()
            await msg.edit(embed=embed)
            return ''
        
        
    @commands.group()
    async def pet(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(title="寵物系統", description="`add {寵物}` 認養寵物\n`remove {寵物}` 棄養寵物\n`disconnect` 與主人斷開關係", color=discord.Colour.green())
            await ctx.send(embed=embed)

    @pet.command()
    async def add(self, ctx, pet: discord.Member):
        data_1 = pets_db.find_one({"user": str(ctx.author.id), "pet": str(pet.id)})
        data_2 = pets_db.find_one({"user": str(pet.id), "pet": str(ctx.author.id)})
        if not data_1 is None and not data_2 is None:
            await ctx.send(":x:你不能夠認養這隻寵物!")
            return ''
        embed = discord.Embed(title="寵物", description="輸入`yes`以同意\n輸入`no`以拒絕", color=discord.Colour.green())
        message = await ctx.send(pet.mention, embed=embed)
        
        def check(m):
            return m.author.id == pet.id and m.channel == ctx.channel and m.content in ['yes', 'no']
        
        msg = await self.bot.wait_for('message', check=check)
        if msg.content == 'yes':
            data = {
                "user": str(ctx.author.id),
                "pet": str(pet.id)
            }
            pets_db.insert(data)
            embed.description = f"現在{pet.mention}是{ctx.author.mention}的寵物了!"
            await message.edit(embed=embed)
        elif msg.content == 'no':
            embed.description = "取消"
            embed.color = discord.Colour.red()
            await message.edit(embed=embed)
        else:
            pass
    
    @pet.command()
    async def remove(self, ctx, pet: discord.Member):
        data = pets_db.find_one({"user": str(ctx.author.id), "pet": str(pet.id)})
        if data == None:
            await ctx.send(":x: 他並不是你的寵物!")
            return ''
        confirm = BotConfirmation(ctx, discord.Colour.green())
        await confirm.confirm(f"你要確定欸")
        if confirm.confirmed:
            await confirm.quit()
        else:
            await ctx.message.delete()
            await confirm.quit()
            return ''
        pets_db.delete_one({"user": str(ctx.author.id), "pet": str(pet.id)})
        embed = discord.Embed(title="寵物", description=f"現在{pet.mention}不再是{ctx.author.mention}的寵物了!", color=discord.Colour.red())
        await ctx.send(embed=embed)
        
    @pet.command()
    async def disconnect(self, ctx, user: discord.Member):
        data = pets_db.find_one({"user": str(user.id), "pet": str(ctx.author.id)})
        if data == None:
            await ctx.send(":x: 你並不是他的寵物!")
            return ''
        confirm = BotConfirmation(ctx, discord.Colour.green())
        await confirm.confirm(f"你要確定欸")
        if confirm.confirmed:
            await confirm.quit()
        else:
            await ctx.message.delete()
            await confirm.quit()
            return ''
        pets_db.delete_one({"user": str(user.id), "pet": str(ctx.author.id)})
        embed = discord.Embed(title="寵物", description=f"現在{user.mention}不再是{ctx.author.mention}的主人了!", color=discord.Colour.red())
        await ctx.send(embed=embed)
        
    @commands.command()
    async def ant(self, ctx, *, content):
        await ctx.send("҉".join(list(content.replace(' ', ''))))
        
    @commands.command(aliases=["bs"])
    async def bullshit(self, ctx, topic: str, minlen: int = 500):
        res = requests.post("https://api.howtobullshit.me/bullshit", json={"MinLen": minlen,"Topic": topic}).text
        embed = discord.Embed(title=topic, description=res.replace("&nbsp;", " "), color=discord.Colour.blue())
        await ctx.send(embed=embed)

    @commands.command()
    async def weather(self, ctx, location: str = "Taiwan"):
        embed = discord.Embed(title="天氣預報", color=discord.Colour.blue()).set_image(url=f"http://wttr.in/{location}.png?lang=zh-tw")
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(fun(bot))