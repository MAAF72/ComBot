import discord
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
    problem_value = '\n'.join('- [{}](https://tlx.toki.id/problems/{})'.format(contest.problems[p]['name'], p) for p in contest.problems.keys())
    durasi_value = '{} menit \n ({} - {})'.format(contest.duration, datetime.fromtimestamp(contest.start).strftime('%d %B %Y %H:%M'), datetime.fromtimestamp(contest.end).strftime('%d %B %Y %H:%M'))
    
    embed = discord.Embed(title=' ', color=0x1174df)
    embed.set_author(name='{} #{}'.format(contest.name, contest.id))
    embed.add_field(name='Problem', value=problem_value)
    embed.add_field(name='Durasi', value=durasi_value)
    # embed.add_field(name='Peserta', value='\n'.join('- {} ([{}](https://tlx.toki.id/profiles/{}))'.format(p.mention, contest.players[p], contest.players[p]) for p in contest.players))
    if contest.is_over():
        embed.set_footer(text='Kontes sudah selesai')
    else:
        embed.set_footer(text='Kontes akan selesai dalam {} menit, happy coding!'.format((contest.end - int(datetime.timestamp(datetime.now()))) // 60))

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
    
    embed = discord.Embed(title=' ', color=0x1174df)
    embed.set_author(name='Scoreboard {} #{}'.format(contest.name, contest.id))
    embed.add_field(name='Rank', value=rank_value)
    embed.add_field(name='Score', value=score_value)
    if contest.is_over():
        embed.set_footer(text='Kontes sudah selesai')
    else:
        embed.set_footer(text='Kontes akan selesai dalam {} menit, happy coding!'.format((contest.end - int(datetime.timestamp(datetime.now()))) // 60))

    return embed
    
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
        return await ctx.send('Kontes #{} tidak ditemukan'.format(contest_id))
    
    contest = bot.tlx_contests[contest_id]
    await ctx.send(embed=generate_contest_embed(contest))
        
@bot.command(name='tlx_contest+', help='Membuat kontes TLX')
async def tlx_contest_create(ctx, *, name: str):
    contest = TlxContest(bot.auto_increment, name, ctx.message.author)
    bot.auto_increment += 1
    bot.tlx_contests[contest.id] = contest
    await ctx.send('{} #{} berhasil dibuat'.format(contest.name, contest.id))
    
@bot.command(name='tlx_contest-', help='Menghapus kontes TLX')
async def tlx_contest_delete(ctx, contest_id: int):
    if contest_id not in bot.tlx_contests:
        return await ctx.send('Kontes #{} tidak ditemukan'.format(contest_id))
    
    contest = bot.tlx_contests[contest_id]
    contest_name = contest.name
    
    if contest.admin != ctx.message.author:
        return await ctx.send('{} tidak memiliki hak untuk menghapus #{}'.format(ctx.message.author.mention, contest.id))
    
    del bot.tlx_contests[contest_id]
    await ctx.send('{} #{} berhasil dihapus'.format(contest_name, contest_id))
    
@bot.command(name='tlx_problem+', help='Menambahkan problem ke kontes TLX')
async def tlx_problem_add(ctx, contest_id: int, slug: str):
    if contest_id not in bot.tlx_contests:
        return await ctx.send('Kontes #{} tidak ditemukan'.format(contest_id))
        
    contest = bot.tlx_contests[contest_id]
    
    if contest.admin != ctx.message.author:
        return await ctx.send('{} tidak memiliki hak untuk menambahkan problem {} #{}'.format(ctx.message.author.mention, contest.name, contest.id))

    response = contest.add_problem(slug)
    if response != 'OK':
        return await ctx.send(response)

    await ctx.send('Problem {} ({}) berhasil ditambahkan ke {} #{}'.format(contest.problems[slug]['name'], slug, contest.name, contest.id))
    
@bot.command(name='tlx_problem-', help='Menghapus problem dari kontes TLX')
async def tlx_problem_delete(ctx, contest_id: int, slug: str):
    if contest_id not in bot.tlx_contests:
        return await ctx.send('Kontes #{} tidak ditemukan'.format(contest_id))
    
    contest = bot.tlx_contests[contest_id]
    
    if contest.admin != ctx.message.author:
        return await ctx.send('{} tidak memiliki hak untuk menghapus problem {} #{}'.format(ctx.message.author.mention, contest.name, contest.id))
    
    problem_name = contest.problems[slug]['name']
    
    response = contest.del_problem(slug)
    if response != 'OK':
        return await ctx.send(response)

    await ctx.send('Problem {} ({}) berhasil dihapus dari {} #{}'.format(problem_name, slug, contest.name, contest.id))
    
@bot.command(name='tlx_duration', help='Mengatur durasi(menit) kontes TLX')
async def tlx_duration_set(ctx, contest_id: int, duration: int):
    if contest_id not in bot.tlx_contests:
        return await ctx.send('Kontes #{} tidak ditemukan'.format(contest_id))
    
    contest = bot.tlx_contests[contest_id]
    if contest.admin != ctx.message.author:
        return await ctx.send('{} tidak memiliki hak untuk mengatur durasi {} #{}'.format(ctx.message.author.mention, contest.name, contest.id))
        
    response = contest.set_duration(duration)
    if response != 'OK':
        return await ctx.send(response)

    await ctx.send('Durasi {} #{} diatur menjadi {} menit'.format(contest.name, contest.id, contest.duration))
    
@bot.command(name='tlx_player+', help='Mendaftarkan diri ke kontes TLX')
async def tlx_player_add(ctx, contest_id: int, tlx_username: str):
    if contest_id not in bot.tlx_contests:
        return await ctx.send('Kontes #{} tidak ditemukan'.format(contest_id))
        
    contest = bot.tlx_contests[contest_id]

    response = contest.add_player(ctx.message.author, tlx_username)
    if response != 'OK':
        return await ctx.send(response)

    await ctx.send('{} ({}) berhasil mendaftarkan diri ke {} #{}'.format(ctx.message.author.mention, contest.players[ctx.message.author], contest.name, contest.id))
    
@bot.command(name='tlx_player-', help='Mengundurkan diri dari kontes TLX')
async def tlx_player_del(ctx, contest_id: int):
    if contest_id not in bot.tlx_contests:
        return await ctx.send('Kontes #{} tidak ditemukan'.format(contest_id))
        
    contest = bot.tlx_contests[contest_id]
    tlx_username = None
    if ctx.message.author in contest.players:
        tlx_username = contest.players[ctx.message.author]

    response = contest.del_player(ctx.message.author)
    if response != 'OK':
        return await ctx.send(response)

    await ctx.send('{} ({}) berhasil mengundurkan diri dari {} #{}'.format(ctx.message.author.mention, tlx_username, contest.name, contest.id))

@bot.command(name='tlx_start', help='Memulai kontes TLX')
async def tlx_start(ctx, contest_id: int):
    if contest_id not in bot.tlx_contests:
        return await ctx.send('Kontes #{} tidak ditemukan'.format(contest_id))
    
    contest = bot.tlx_contests[contest_id]
    if contest.admin != ctx.message.author:
        return await ctx.send('{} tidak memiliki hak untuk memulai {} #{}'.format(ctx.message.author.mention, contest.name, contest.id))
    
    await ctx.send('Mohon tunggu, sedang menyiapkan kontes...')
    
    response = contest.start_contest()
    if response != 'OK':
        return await ctx.send(response)
    
    message = ''
    message += '{} dimulai!\n'.format(contest.name)
    message += ' '.join('{}'.format(p.mention) for p in contest.players)
    await ctx.send(embed=generate_contest_embed(contest))
    await ctx.send(message)
    
@bot.command(name='tlx_scoreboard', help='Menampilkan scoreboard kontes TLX')
async def tlx_scoreboard(ctx, contest_id: int):
    if contest_id not in bot.tlx_contests:
        return await ctx.send('Kontes #{} tidak ditemukan'.format(contest_id))
    
    contest = bot.tlx_contests[contest_id]
    
    response = contest.update_scoreboard()
    if response != 'OK':
        return await ctx.send(response)
    
    await ctx.send(embed=generate_scoreboard_embed(contest))

# @bot.event
# async def on_command_error(ctx, error):
    # if isinstance(error, commands.errors.CheckFailure):
        # await ctx.send('You do not have the correct role for this command.')

bot.run(TOKEN)