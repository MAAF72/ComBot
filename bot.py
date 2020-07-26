import discord
from pytz import timezone
from TlxContest import TlxContest
from discord.ext import commands
from datetime import datetime

one = 'NzM1NzEyNTY1NDU1MzU1OTA2'
two = 'XxkPuA'
three = 'sG1fHqxuYsQ2ENSyyRMJ1TAcaPE'
TOKEN = one + '.' + two + '.' + three

bot = commands.Bot(command_prefix=';')

bot.tlx_contests = dict()
bot.auto_increment = 1

def generate_contest_embed(contest):
    problem_value = '-------'
    durasi_value = '------'
    
    if len(contest.problems) > 0:
        problem_value = '\n'.join('- [{}](https://tlx.toki.id/problems/{})'.format(contest.problems[p]['name'], p) for p in contest.problems.keys())
        
    if contest.duration > 0:
        durasi_value = '{} menit'.format(contest.duration)
        if contest.start != None:
            durasi_value += '\n ({} - {})'.format(datetime.fromtimestamp(contest.start, timezone('Asia/Jakarta')).strftime('%d %B %Y %H:%M'), datetime.fromtimestamp(contest.end, timezone('Asia/Jakarta')).strftime('%d %B %Y %H:%M'))
    
    embed = discord.Embed(title=' ', description='Author: {} | Contest ID: {}'.format(contest.admin.mention, contest.id), color=0x1174df)
    embed.set_author(name=contest.name)
    
    embed.add_field(name='Problem', value=problem_value, inline=True)
    embed.add_field(name='Durasi', value=durasi_value, inline=True)
    if contest.start == None:
        embed.set_footer(text='Kontes belum dimulai')
    elif contest.is_over():
        embed.set_footer(text='Kontes sudah selesai')
    else:
        embed.set_footer(text='Kontes akan selesai dalam {} menit, happy coding!'.format((contest.end - int(datetime.timestamp(datetime.now(timezone('Asia/Jakarta'))))) // 60))

    return embed

def generate_scoreboard_embed(contest):
    rank_value = ''
    score_value = ''
    
    sort_orders = sorted(contest.scoreboard.items(), key=lambda x: (x[1]['totalScore'], -x[1]['totalTime']), reverse=True)
    for index, item in enumerate(sort_orders, start=1):
        for user in contest.players.keys():
            if contest.players[user] == item[0]:
                rank_value += '`{}` {} ({})\n'.format(index, user.mention, item[0])
                score_value += '`{}`  `{}`\n'.format(item[1]['totalScore'], item[1]['totalTime'] // 60)
                break
    
    embed = discord.Embed(title=' ', description='Author: {} | Contest ID: {}'.format(contest.admin.mention, contest.id), color=0x1174df)
    embed.set_author(name='Scoreboard {}'.format(contest.name))
    embed.add_field(name='Rank', value=rank_value, inline=True)
    embed.add_field(name='Score', value=score_value, inline=True)
    if contest.is_over():
        embed.set_footer(text='Kontes sudah selesai')
    else:
        embed.set_footer(text='Kontes akan selesai dalam {} menit, happy coding!'.format((contest.end - int(datetime.timestamp(datetime.now(timezone('Asia/Jakarta'))))) // 60))

    return embed

async def embed_message(ctx, message):
    await ctx.send(embed=discord.Embed(description='{} {}'.format(message, ctx.message.author.mention)))
    
@bot.event
async def on_ready():
    print('{} has connected to Discord!'.format(bot.user.name))
    
@bot.event
async def on_error(event, *args, **kwargs):
    with open('error.log', 'a') as f:
        f.writelines('Unhandled message: {}'.format(args[0]))
        
@bot.command(name='tlx_contest', help='Menampilkan kontes TLX')
async def tlx_contest_show(ctx, contest_id: int):
    if contest_id not in bot.tlx_contests:
        await embed_message(ctx, 'Kontes tidak ditemukan')
        return
    
    contest = bot.tlx_contests[contest_id]
    await ctx.send(embed=generate_contest_embed(contest))
        
@bot.command(name='tlx_contest+', help='Membuat kontes TLX')
async def tlx_contest_create(ctx, *, name: str):
    contest = TlxContest(bot.auto_increment, name, ctx.message.author)
    bot.auto_increment += 1
    bot.tlx_contests[contest.id] = contest
    
    await ctx.send(embed=generate_contest_embed(contest))
    
@bot.command(name='tlx_contest-', help='Menghapus kontes TLX')
async def tlx_contest_delete(ctx, contest_id: int):
    if contest_id not in bot.tlx_contests:
        await embed_message(ctx, 'Kontes tidak ditemukan')
        return
    
    contest = bot.tlx_contests[contest_id]
    
    if contest.admin != ctx.message.author:
        await embed_message(ctx, 'Perintah ditolak, Anda tidak memiliki akses')
        return
    
    del bot.tlx_contests[contest_id]
    
    await embed_message(ctx, 'Kontes berhasil dihapus')
    
@bot.command(name='tlx_problem+', help='Menambahkan problem ke kontes TLX')
async def tlx_problem_add(ctx, contest_id: int, slug: str):
    if contest_id not in bot.tlx_contests:
        await embed_message(ctx, 'Kontes tidak ditemukan')
        return
        
    contest = bot.tlx_contests[contest_id]
    
    if contest.admin != ctx.message.author:
        await embed_message(ctx, 'Perintah ditolak, Anda tidak memiliki akses')
        return

    response = contest.add_problem(slug)
    if response != 'OK':
        await embed_message(ctx, response)
        return

    await embed_message(ctx, 'Problem berhasil ditambahkan')
    
@bot.command(name='tlx_problem-', help='Menghapus problem dari kontes TLX')
async def tlx_problem_delete(ctx, contest_id: int, slug: str):
    if contest_id not in bot.tlx_contests:
        await embed_message(ctx, 'Kontes tidak ditemukan')
        return
    
    contest = bot.tlx_contests[contest_id]
    
    if contest.admin != ctx.message.author:
        await embed_message(ctx, 'Perintah ditolak, Anda tidak memiliki akses')
        return
    
    response = contest.del_problem(slug)
    if response != 'OK':
        await embed_message(ctx, response)
        return

    await embed_message(ctx, 'Problem berhasil dihapus')
    
@bot.command(name='tlx_duration', help='Mengatur durasi(menit) kontes TLX')
async def tlx_duration_set(ctx, contest_id: int, duration: int):
    if contest_id not in bot.tlx_contests:
        await embed_message(ctx, 'Kontes tidak ditemukan')
        return
    
    contest = bot.tlx_contests[contest_id]
    
    if contest.admin != ctx.message.author:
        await embed_message(ctx, 'Perintah ditolak, Anda tidak memiliki akses')
        return
        
    response = contest.set_duration(duration)
    if response != 'OK':
        await embed_message(ctx, response)
        return

    await embed_message(ctx, 'Durasi kontes berhasil diatur')
    
@bot.command(name='tlx_player+', help='Mendaftarkan diri ke kontes TLX')
async def tlx_player_add(ctx, contest_id: int, tlx_username: str):
    if contest_id not in bot.tlx_contests:
        await embed_message(ctx, 'Kontes tidak ditemukan')
        return
        
    contest = bot.tlx_contests[contest_id]

    response = contest.add_player(ctx.message.author, tlx_username)
    if response != 'OK':
        await embed_message(ctx, response)
        return

    await embed_message(ctx, 'Berhasil mendaftar')
    
@bot.command(name='tlx_player-', help='Mengundurkan diri dari kontes TLX')
async def tlx_player_del(ctx, contest_id: int):
    if contest_id not in bot.tlx_contests:
        await embed_message(ctx, 'Kontes tidak ditemukan')
        return
        
    contest = bot.tlx_contests[contest_id]

    response = contest.del_player(ctx.message.author)
    if response != 'OK':
        await embed_message(ctx, response)
        return

    await embed_message(ctx, 'Berhasil mengundurkan diri')

@bot.command(name='tlx_start', help='Memulai kontes TLX')
async def tlx_start(ctx, contest_id: int):
    if contest_id not in bot.tlx_contests:
        await embed_message(ctx, 'Kontes tidak ditemukan')
        return
    
    contest = bot.tlx_contests[contest_id]
    
    if contest.admin != ctx.message.author:
        await embed_message(ctx, 'Perintah ditolak, Anda tidak memiliki akses')
        return
    
    response = contest.start_contest()
    if response != 'OK':
        await embed_message(ctx, response)
        return
    
    message = ''
    message += '`{} dimulai!`\n'.format(contest.name)
    message += ' '.join('{}'.format(p.mention) for p in contest.players)
    await ctx.send(embed=generate_contest_embed(contest))
    if len(contest.players) > 0:
        await ctx.send(embed=generate_scoreboard_embed(contest))

    await ctx.send(message)
    
@bot.command(name='tlx_scoreboard', help='Menampilkan scoreboard kontes TLX')
async def tlx_scoreboard(ctx, contest_id: int):
    if contest_id not in bot.tlx_contests:
        await embed_message(ctx, 'Kontes tidak ditemukan')
        return
    
    contest = bot.tlx_contests[contest_id]
    
    if contest.start == None:
        await embed_message(ctx, 'Kontes belum dimulai')
        return
    
    if len(contest.players) == 0:
        await embed_message(ctx, 'Peserta kontes tidak ada, tidak bisa menampilkan scoreboard')
        return
        
    response = contest.update_scoreboard()
    if response != 'OK':
        await embed_message(ctx, response)
        return
    
    await ctx.send(embed=generate_scoreboard_embed(contest))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await embed_message(ctx, 'You do not have the correct role for this command.')
    elif isinstance(error, commands.CommandInvokeError):
        await embed_message(ctx, 'Internal Error')
        print(error.original)
        embed = discord.Embed(title='ComBot Command Error', colour=0x992d22)
        embed.add_field(name='Error', value=error)
        embed.add_field(name='Guild', value=ctx.guild)
        embed.add_field(name='Channel', value=ctx.channel)
        embed.add_field(name='User', value=ctx.author)
        embed.add_field(name='Message', value=ctx.message.clean_content)
        embed.timestamp = datetime.now(timezone('Asia/Jakarta'))
        try:
            await bot.AppInfo.owner.send(embed=embed)
        except:
            pass

bot.run(TOKEN)