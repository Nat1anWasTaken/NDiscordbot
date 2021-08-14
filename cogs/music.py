import discord
from discord.ext import commands
import asyncio
import itertools
import sys
import traceback
import os
from async_timeout import timeout
from functools import partial
from youtube_dl import YoutubeDL
from youtubesearchpython import SearchVideos

ytdlopts = {
    'format': 'bestaudio/best',
    'outtmpl': 'downloads/%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # ipv6 addresses cause issues sometimes
}

ffmpegopts = {
    'before_options': '-nostdin',
    'options': '-vn'
}

ytdl = YoutubeDL(ytdlopts)


def delete():
    for filename in os.listdir('./downloads'):
        try:
            path = f'./downloads/{filename}'
            os.remove(path)
            print(f"[音樂] 刪除了{filename}")
        except:
            print(f"[音樂] 無法刪除{filename}")
    return ''


class VoiceConnectionError(commands.CommandError):
    """Custom Exception class for connection errors."""


class InvalidVoiceChannel(VoiceConnectionError):
    """Exception for cases of invalid Voice Channels."""


class YTDLSource(discord.PCMVolumeTransformer):

    def __init__(self, source, *, data, requester, filename, url):
        super().__init__(source)
        self.requester = requester

        self.title = data.get('title')
        self.web_url = data.get('webpage_url')
        self.path = filename
        self.url = url

        # YTDL info dicts (data) have other useful information you might want
        # https://github.com/rg3/youtube-dl/blob/master/README.md

    def __getitem__(self, item: str):
        """Allows us to access attributes similar to a dict.
        This is only useful when you are NOT downloading.
        """
        return self.__getattribute__(item)

    @classmethod
    async def create_source(cls, ctx, search: str, *, loop, download=True):
        loop = loop or asyncio.get_event_loop()

        to_run = partial(ytdl.extract_info, url=search, download=download)
        data = await loop.run_in_executor(None, to_run)

        if data['duration'] >= 600:
            await ctx.send(":x: 音樂過長 無法播放")
            return ''
        if 'entries' in data:
            data = data['entries'][0]

        await ctx.send(f"已將 `{data['title']}` 加入至序列!")

        if download:
            source = ytdl.prepare_filename(data)
        else:
            return {'webpage_url': data['webpage_url'], 'requester': ctx.author, 'title': data['title']}

        return cls(discord.FFmpegPCMAudio(source), data=data, requester=ctx.author, filename=source, url=f"https://www.youtube.com/watch?v={data['id']}")

    @classmethod
    async def regather_stream(cls, data, *, loop):
        """Used for preparing a stream, instead of downloading.
        Since Youtube Streaming links expire."""
        loop = loop or asyncio.get_event_loop()
        requester = data['requester']

        to_run = partial(ytdl.extract_info, url=data['webpage_url'], download=False)
        data = await loop.run_in_executor(None, to_run)
        print("Downloaded")
        return cls(discord.FFmpegPCMAudio(data['url']), data=data, requester=requester)


class MusicPlayer:
    __slots__ = ('bot', '_guild', '_channel', '_cog', 'queue', 'next', 'current', 'np', 'volume')

    def __init__(self, ctx):
        self.bot = ctx.bot
        self._guild = ctx.guild
        self._channel = ctx.channel
        self._cog = ctx.cog

        self.queue = asyncio.Queue()
        self.next = asyncio.Event()

        self.np = None  # Now playing message
        self.volume = .5
        self.current = None

        ctx.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        """Our main player loop."""
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.next.clear()

            try:
                # Wait for the next song. If we timeout cancel the player and disconnect...
                async with timeout(300):  # 5 minutes...
                    source = await self.queue.get()
            except asyncio.TimeoutError:
                return self.destroy(self._guild)

            if not isinstance(source, YTDLSource):
                # Source was probably a stream (not downloaded)
                # So we should regather to prevent stream expiration
                try:
                    source = await YTDLSource.regather_stream(source, loop=self.bot.loop)
                    print("is YTDLSource!")
                except Exception as e:
                    await self._channel.send(f'處理你的歌曲時發生錯誤!\n'
                                             f'```css\n[{e}]\n```')
                    continue

            source.volume = self.volume
            self.current = source

            self._guild.voice_client.play(source, after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))
            self.np = await self._channel.send(f"正在播放 `{source.title}`，使用`{get_prefix(self._guild)}np`來獲得詳細資訊!")
            await self.next.wait()
            os.remove(f"./{source.path}")
            try:
                # We are no longer playing this song...
                await self.np.delete()
            except discord.HTTPException:
                pass
            # Make sure the FFmpeg process is cleaned up.
            source.cleanup()
            self.current = None

    def destroy(self, guild):
        """Disconnect and cleanup the player."""
        return self.bot.loop.create_task(self._cog.cleanup(guild))


class Music(commands.Cog):
    """Music related commands."""

    __slots__ = ('bot', 'players')

    def __init__(self, bot):
        self.bot = bot
        self.players = {}

    async def cleanup(self, guild):
        try:
            await guild.voice_client.disconnect()
        except AttributeError:
            pass

        try:
            del self.players[guild.id]
        except KeyError:
            pass

    async def __local_check(self, ctx):
        """A local check which applies to all commands in this cog."""
        if not ctx.guild:
            raise commands.NoPrivateMessage
        return True

    async def __error(self, ctx, error):
        """A local error handler for all errors arising from commands in this cog."""
        if isinstance(error, commands.NoPrivateMessage):
            try:
                return await ctx.send('這個指令不能在私訊中使用!')
            except discord.HTTPException:
                pass
        elif isinstance(error, InvalidVoiceChannel):
            await ctx.send('無法連接至語音頻道!')

        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    def get_player(self, ctx):
        """Retrieve the guild player, or generate one."""
        try:
            player = self.players[ctx.guild.id]
        except KeyError:
            player = MusicPlayer(ctx)
            self.players[ctx.guild.id] = player

        return player

    @commands.command(name='connect', aliases=['join'])
    async def connect_(self, ctx, *, channel: discord.VoiceChannel = None):
        """Connect to voice.
        Parameters
        ------------
        channel: discord.VoiceChannel [Optional]
            The channel to connect to. If a channel is not specified, an attempt to join the voice channel you are in
            will be made.
        This command also handles moving the bot to different channels.
        """
        if not channel:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                raise InvalidVoiceChannel('無法加入語音頻道!')

        vc = ctx.voice_client

        if vc:
            if vc.channel.id == channel.id:
                return
            try:
                await vc.move_to(channel)
            except asyncio.TimeoutError:
                raise VoiceConnectionError(f'無法加入語音頻道!')
        else:
            try:
                await channel.connect()
            except asyncio.TimeoutError:
                raise VoiceConnectionError(f'無法加入語音頻道!')

        await ctx.send(f'連接至: **{channel}**')

    @commands.command(name='play', aliases=['p', 'pl'])
    async def play_(self, ctx, *, search: str):
        await ctx.trigger_typing()

        vc = ctx.voice_client

        if not vc:
            try:
                await ctx.invoke(self.connect_, channel=ctx.author.voice.channel)
            except:
                raise VoiceConnectionError(f'無法加入語音頻道!')
        # else:
        #     source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop, download=True)
        player = self.get_player(ctx)
        try:
            source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop, download=True)
        except:
            try:
                track = sp.track(search.replace("https://open.spotify.com/embed/track/", "https://open.spotify.com/track/"))
                artists = []
                for artist in track['artists']:
                    artists.append(artist['name'])
                keyword = f"{' x '.join(artists)} - {track['name']}"
                raw_result = SearchVideos(keyword, offset=1, mode="json", max_results=1).result()
                result = eval(raw_result)
                print(type(result))
                s_source = result['search_result'][0]['link']
                o_source = await YTDLSource.create_source(ctx, s_source, loop=self.bot.loop, download=True)
                await player.queue.put(o_source)
                return ''
            except:
                await ctx.send(":x: 無法處理你的歌曲")
        await player.queue.put(source)

    @commands.command(name='pause')
    async def pause_(self, ctx):
        """Pause the currently playing song."""
        vc = ctx.voice_client

        if not vc or not vc.is_playing():
            return await ctx.send('沒有歌曲正在播放!')
        elif vc.is_paused():
            return

        vc.pause()
        await ctx.send(f'**`{ctx.author}`**: 暫停了音樂!')

    @commands.command(name='resume')
    async def resume_(self, ctx):
        """Resume the currently paused song."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send('沒有歌曲正在播放!')
        elif not vc.is_paused():
            return

        vc.resume()
        await ctx.send(f'**`{ctx.author}`**: 繼續了音樂!')

    @commands.command(name='skip')
    async def skip_(self, ctx):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send('沒有歌曲正在播放!')

        if vc.is_paused():
            pass
        elif not vc.is_playing():
            return

        vc.stop()
        await ctx.send(f'**`{ctx.author}`**: 跳過了音樂!')

    @commands.command(name='queue', aliases=['q', 'playlist'])
    async def queue(self, ctx):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send('沒有歌曲在序列中!')

        player = self.get_player(ctx)
        if player.queue.empty():
            return await ctx.send('沒有歌曲在序列中!')

        # Grab up to 5 entries from the queue...
        upcoming = list(itertools.islice(player.queue._queue, 0, 5))

        fmt = '\n'.join(f'**`{_["title"]}`**' for _ in upcoming)
        embed = discord.Embed(title=f'接下來還有 {len(upcoming)} 首歌曲!', description=fmt)

        await ctx.send(embed=embed)

    @commands.command(name='now_playing', aliases=['np', 'current', 'currentsong', 'playing'])
    async def nowplaying(self, ctx):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send('沒有歌曲正在播放!')

        player = self.get_player(ctx)
        if not player.current:
            return await ctx.send('沒有歌曲正在播放!')
        try:
            await player.np.delete()
        except:
            pass
        try:
            raw_result = SearchVideos(vc.source.url, offset=1, mode="json", max_results=1)
            video = eval(raw_result.result())['search_result'][0]

            embed = discord.Embed(title=video['title'], color=discord.Colour.blue(), url=video['link'])
            embed.set_author(name=video['channel'])
            embed.set_thumbnail(url=video['thumbnails'][0])
            embed.add_field(name="長度", value=video['duration'])
            embed.add_field(name="點播者", value=f"{vc.source.requester.mention}({vc.source.requester})")

        except AttributeError:
            await ctx.send("沒有歌曲正在播放!")
            return None

        player.np = await ctx.send(embed=embed)
        await player.np.add_reaction('▶')
        await player.np.add_reaction('⏸')
        await player.np.add_reaction('⏹')
        await player.np.add_reaction("⏭")
        await player.np.add_reaction("➕")
        await player.np.add_reaction("🔎")
        while True:
            def check(reaction, user):
                return user.id == ctx.author.id and str(reaction.emoji) in ['▶', '⏸', '⏹', '⏭', '➕', '🔎'] and reaction.message.id == player.np.id

            reaction, user = await self.bot.wait_for('reaction_add', check=check)
            if str(reaction.emoji) == '▶':
                try:
                    await reaction.remove(user)
                except:
                    await ctx.author.send("看來機器人無法移除你的反應，請手動移除你的反應，這可能是因為機器人缺少`manage_messages(管理訊息)`的權限造成的。")
                    pass
                await self.resume_(ctx=ctx)
            elif str(reaction.emoji) == '⏸':
                try:
                    await reaction.remove(user)
                except:
                    await ctx.author.send("看來機器人無法移除你的反應，請手動移除你的反應，這可能是因為機器人缺少`manage_messages(管理訊息)`的權限造成的。")
                    pass
                vc.pause()
                await ctx.send(f'**`{ctx.author}`**: 暫停了音樂!')
            elif str(reaction.emoji) == '⏹':
                try:
                    await reaction.remove(user)
                except:
                    await ctx.author.send("看來機器人無法移除你的反應，請手動移除你的反應，這可能是因為機器人缺少`manage_messages(管理訊息)`的權限造成的。")
                    pass
                await self.stop_(ctx=ctx)
            elif str(reaction.emoji) == '⏭':
                try:
                    await reaction.remove(user)
                except:
                    await ctx.author.send("看來機器人無法移除你的反應，請手動移除你的反應，這可能是因為機器人缺少`manage_messages(管理訊息)`的權限造成的。")
                    pass
                await self.skip_(ctx=ctx)
            elif str(reaction.emoji) == '➕':
                try:
                    await reaction.remove(user)
                except:
                    pass

                def m_check(m):
                    return m.author == ctx.author and m.channel.id == ctx.channel.id

                try:
                    sended_1 = await ctx.send("請在30秒內輸入要新增到序列的歌曲: ")
                    msg = await self.bot.wait_for('message', check=m_check, timeout=30)
                    if msg.content == "cancel":
                        try:
                            await msg.delete()
                        except:
                            await ctx.author.send("看來機器人無法移除你的訊息，請手動移除你的訊息，這可能是因為機器人缺少`manage_messages(管理訊息)`的權限造成的。")
                            pass
                        await sended_1.delete()
                        continue
                    else:
                        try:
                            await msg.delete()
                        except:
                            await ctx.author.send("看來機器人無法移除你的訊息，請手動移除你的訊息，這可能是因為機器人缺少`manage_messages(管理訊息)`的權限造成的。")
                            pass
                        await sended_1.delete()
                        await ctx.invoke(self.play_, search=msg.content)
                        continue
                except asyncio.TimeoutError:
                    await sended_1.delete()
            elif str(reaction.emoji) == "🔎":
                await reaction.remove(user)

                def m_check(m):
                    return m.author == ctx.author and m.channel.id == ctx.channel.id

                try:
                    sended_1 = await ctx.send("請在30秒內輸入要搜尋的關鍵字: ")
                    msg = await self.bot.wait_for('message', check=m_check, timeout=30)
                    if msg.content == "cancel":
                        try:
                            await msg.delete()
                        except:
                            await ctx.author.send("看來機器人無法移除你的訊息，請手動移除你的訊息，這可能是因為機器人缺少`manage_messages(管理訊息)`的權限造成的。")
                            pass
                        await sended_1.delete()
                        continue
                    else:
                        try:
                            await msg.delete()
                        except:
                            await ctx.author.send("看來機器人無法移除你的訊息，請手動移除你的訊息，這可能是因為機器人缺少`manage_messages(管理訊息)`的權限造成的。")
                            pass
                        await sended_1.delete()
                        await self.search_(ctx=ctx, keyword=msg.content)
                        continue
                except asyncio.TimeoutError:
                    await sended_1.delete()

    @commands.command(name='volume', aliases=['vol'])
    async def volume(self, ctx, *, vol: float):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send('沒有歌曲正在播放!')

        if not 0 < vol < 101:
            return await ctx.send('請輸入一個在`1`至`100`間的數值!')

        player = self.get_player(ctx)

        if vc.source:
            vc.source.volume = vol / 100

        player.volume = vol / 100
        await ctx.send(f'**`{ctx.author}`**: 將音量設置成 **{vol}%**')

    @commands.command(name='stop')
    async def stop_(self, ctx):
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send('沒有歌曲正在播放!')

        await self.cleanup(ctx.guild)

    @commands.command(name='search')
    async def search_(self, ctx, *, keyword: str):
        await ctx.trigger_typing()

        vc = ctx.voice_client

        if not vc:
            await ctx.invoke(self.connect_)

        result = SearchVideos(keyword, offset=1, mode="json", max_results=10)
        result_json = eval(result.result())
        message = ""
        for video in result_json['search_result']:
            message = f"{message}[{video['index'] + 1}] [{video['title']}]({video['link']}) `{video['duration']}`\n"
        embed = discord.Embed(title="搜尋結果", description=message, color=discord.Colour.blue()).set_footer(
            text="請在30秒內輸入要播放的曲目編號，輸入`cancel`取消")
        sended = await ctx.send(embed=embed)

        def check(m):
            return m.content in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'cancel']

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30)
            if msg.content == 'cancel':
                await sended.edit(embed=discord.Embed(title="已取消", color=discord.Colour.red()))
                return ''
            await sended.delete()
            try:
                await msg.delete()
            except:
                await ctx.author.send("看來機器人無法移除你的訊息，請手動移除你的訊息，這可能是因為機器人缺少`manage_messages(管理訊息)`的權限造成的。")
                pass
            choose = result_json['search_result'][int(msg.content) - 1]
        except asyncio.TimeoutError:
            await sended.edit(embed=discord.Embed(title="已取消", color=discord.Colour.red()))

        player = self.get_player(ctx)
        source = await YTDLSource.create_source(ctx, choose['link'], loop=self.bot.loop, download=True)
        await player.queue.put(source)


def setup(bot):
    bot.add_cog(Music(bot))