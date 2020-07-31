from datetime import datetime
from pytz import timezone
import discord
from TlxContest import TlxContest


ONE = 'NzM1NzEyNTY1NDU1MzU1OTA2'
TWO = 'XxkPuA'
THREE = 'sG1fHqxuYsQ2ENSyyRMJ1TAcaPE'
TOKEN = ONE + '.' + TWO + '.' + THREE


COLOR = {
    'danger': 0xDC3545,
    'info': 0x17A2B8,
    'warning': 0xFFC107,
    'success': 0x28A745
}

bot = discord.ext.commands.Bot(command_prefix=';')

bot.tlx_contests = dict()
bot.auto_increment = 1

def generate_contest_embed(contest, sender):
    problem_value = '-------'
    durasi_value = '------'

    if len(contest.problems) > 0:
        if sender is contest.admin or contest.start is not None:
            problem_value = '\n'.join('- [{}](https://tlx.toki.id/problems/{})'.format(contest.problems[p]['name'], p) for p in contest.problems)
        else:
            problem_value = '- ?????\n' * (len(contest.problems) - 1) + '- ?????'

    if contest.duration > 0:
        durasi_value = '{} menit'.format(contest.duration)
        if contest.start is not None:
            durasi_value += '\n ({} - {})'.format(datetime.fromtimestamp(contest.start, timezone('Asia/Jakarta')).strftime('%d %B %Y %H:%M'), datetime.fromtimestamp(contest.end, timezone('Asia/Jakarta')).strftime('%d %B %Y %H:%M'))

    embed = discord.Embed(title=' ', description='Author: {} | Contest ID: {}'.format(contest.admin.mention, contest.ID), color=COLOR['info'])
    embed.set_author(name=contest.name)

    embed.add_field(name='Problem', value=problem_value, inline=True)
    embed.add_field(name='Durasi', value=durasi_value, inline=True)
    if contest.start is None:
        embed.set_footer(text='Kontes belum dimulai')
    elif contest.is_over():
        embed.set_footer(text='Kontes sudah selesai')
    else:
        embed.set_footer(text='Kontes akan selesai dalam {} menit, happy coding!'.format((contest.end - int(datetime.timestamp(datetime.now(timezone('Asia/Jakarta'))))) // 60))
    # embed.timestamp = datetime.now(timezone('Asia/Jakarta'))

    return embed

def generate_scoreboard_embed(contest):
    rank_value = ''
    score_value = ''

    sort_orders = sorted(contest.scoreboard.items(), key=lambda x: (x[1]['totalScore'], -x[1]['totalTime']), reverse=True)
    for index, item in enumerate(sort_orders, start=1):
        for user in contest.players:
            if contest.players[user] == item[0]:
                rank_value += '`{}` {} ({})\n'.format(index, user.mention, item[0])
                score_value += '`{}`  `{}`\n'.format(item[1]['totalScore'], item[1]['totalTime'] // 60)
                break

    embed = discord.Embed(title=' ', description='Author: {} | Contest ID: {}'.format(contest.admin.mention, contest.ID), color=COLOR['info'])
    embed.set_author(name='Scoreboard {}'.format(contest.name))
    embed.add_field(name='Rank', value=rank_value, inline=True)
    embed.add_field(name='Score', value=score_value, inline=True)
    if contest.is_over():
        embed.set_footer(text='Kontes sudah selesai')
    else:
        embed.set_footer(text='Kontes akan selesai dalam {} menit, happy coding!'.format((contest.end - int(datetime.timestamp(datetime.now(timezone('Asia/Jakarta'))))) // 60))
    # embed.timestamp = datetime.now(timezone('Asia/Jakarta'))

    return embed

async def embed_message(ctx, message, level):
    return await ctx.send(embed=discord.Embed(description='{} {}'.format(message, ctx.message.author.mention), color=COLOR[level]))

@bot.event
async def on_ready():
    app_info = await bot.application_info()
    await app_info.owner.send('{} has connected to Discord!'.format(bot.user.name))

@bot.event
async def on_error(event, *args, **kwargs):
    with open('error.log', 'a') as log_file:
        log_file.writelines('Event:', event)
        log_file.writelines('Unhandled message:', args)
        log_file.writelines('Kwargs:', kwargs)

@bot.command(name='tlx_contest', help='Menampilkan kontes TLX')
async def tlx_contest_show(ctx, contest_id: int):
    if contest_id not in bot.tlx_contests:
        await embed_message(ctx, 'Kontes tidak ditemukan', 'warning')
        return

    contest = bot.tlx_contests[contest_id]
    await ctx.send(embed=generate_contest_embed(contest, ctx.author))

@bot.command(name='tlx_contest+', help='Membuat kontes TLX')
async def tlx_contest_create(ctx, *, name: str):
    contest = TlxContest(bot.auto_increment, name, ctx.message.author)
    bot.auto_increment += 1
    bot.tlx_contests[contest.ID] = contest

    await ctx.send(embed=generate_contest_embed(contest, ctx.author))

@bot.command(name='tlx_contest-', help='Menghapus kontes TLX')
async def tlx_contest_delete(ctx, contest_id: int):
    if contest_id not in bot.tlx_contests:
        await embed_message(ctx, 'Kontes tidak ditemukan', 'warning')
        return

    contest = bot.tlx_contests[contest_id]

    if contest.admin != ctx.message.author:
        await embed_message(ctx, 'Perintah ditolak, Anda tidak memiliki akses', 'danger')
        return

    del bot.tlx_contests[contest_id]

    await embed_message(ctx, 'Kontes berhasil dihapus', 'success')

@bot.command(name='tlx_problem+', help='Menambahkan problem ke kontes TLX')
async def tlx_problem_add(ctx, contest_id: int, slug: str):
    if contest_id not in bot.tlx_contests:
        await embed_message(ctx, 'Kontes tidak ditemukan', 'warning')
        return

    contest = bot.tlx_contests[contest_id]

    if contest.admin != ctx.message.author:
        await embed_message(ctx, 'Perintah ditolak, Anda tidak memiliki akses', 'danger')
        return

    response = contest.add_problem(slug)
    if response != 'OK':
        await embed_message(ctx, response, 'warning')
        return

    await embed_message(ctx, 'Problem berhasil ditambahkan', 'success')

@bot.command(name='tlx_problem-', help='Menghapus problem dari kontes TLX')
async def tlx_problem_delete(ctx, contest_id: int, slug: str):
    if contest_id not in bot.tlx_contests:
        await embed_message(ctx, 'Kontes tidak ditemukan', 'warning')
        return

    contest = bot.tlx_contests[contest_id]

    if contest.admin != ctx.message.author:
        await embed_message(ctx, 'Perintah ditolak, Anda tidak memiliki akses', 'danger')
        return

    response = contest.del_problem(slug)
    if response != 'OK':
        await embed_message(ctx, response, 'warning')
        return

    await embed_message(ctx, 'Problem berhasil dihapus', 'success')

@bot.command(name='tlx_duration', help='Mengatur durasi(menit) kontes TLX')
async def tlx_duration_set(ctx, contest_id: int, duration: int):
    if contest_id not in bot.tlx_contests:
        await embed_message(ctx, 'Kontes tidak ditemukan', 'warning')
        return

    contest = bot.tlx_contests[contest_id]

    if contest.admin != ctx.message.author:
        await embed_message(ctx, 'Perintah ditolak, Anda tidak memiliki akses', 'danger')
        return

    response = contest.set_duration(duration)
    if response != 'OK':
        await embed_message(ctx, response, 'warning')
        return

    await embed_message(ctx, 'Durasi kontes berhasil diatur', 'success')

@bot.command(name='tlx_player+', help='Mendaftarkan diri ke kontes TLX')
async def tlx_player_add(ctx, contest_id: int, tlx_username: str):
    if contest_id not in bot.tlx_contests:
        await embed_message(ctx, 'Kontes tidak ditemukan', 'warning')
        return

    contest = bot.tlx_contests[contest_id]

    response = contest.add_player(ctx.message.author, tlx_username)
    if response != 'OK':
        await embed_message(ctx, response, 'warning')
        return

    await embed_message(ctx, 'Berhasil mendaftar', 'success')

@bot.command(name='tlx_player-', help='Mengundurkan diri dari kontes TLX')
async def tlx_player_del(ctx, contest_id: int):
    if contest_id not in bot.tlx_contests:
        await embed_message(ctx, 'Kontes tidak ditemukan', 'warning')
        return

    contest = bot.tlx_contests[contest_id]

    response = contest.del_player(ctx.message.author)
    if response != 'OK':
        await embed_message(ctx, response, 'warning')
        return

    await embed_message(ctx, 'Berhasil mengundurkan diri', 'success')

@bot.command(name='tlx_start', help='Memulai kontes TLX')
async def tlx_start(ctx, contest_id: int):
    if contest_id not in bot.tlx_contests:
        await embed_message(ctx, 'Kontes tidak ditemukan', 'warning')
        return

    contest = bot.tlx_contests[contest_id]

    if contest.admin != ctx.message.author:
        await embed_message(ctx, 'Perintah ditolak, Anda tidak memiliki akses', 'danger')
        return

    wait_message = await embed_message(ctx, 'Mohon tunggu, sedang menyiapkan kontes...', 'info')
    response = contest.start_contest()
    await wait_message.delete()
    if response != 'OK':
        await embed_message(ctx, response, 'warning')
        return

    message = ''
    message += '`{} dimulai!`\n'.format(contest.name)
    message += ' '.join('{}'.format(p.mention) for p in contest.players)
    await ctx.send(embed=generate_contest_embed(contest, ctx.author))
    if len(contest.players) > 0:
        await ctx.send(embed=generate_scoreboard_embed(contest))

    await ctx.send(message)

@bot.command(name='tlx_scoreboard', help='Menampilkan scoreboard kontes TLX')
async def tlx_scoreboard(ctx, contest_id: int):
    if contest_id not in bot.tlx_contests:
        await embed_message(ctx, 'Kontes tidak ditemukan', 'warning')
        return

    contest = bot.tlx_contests[contest_id]

    if contest.start is None:
        await embed_message(ctx, 'Kontes belum dimulai', 'warning')
        return

    if len(contest.players) == 0:
        await embed_message(ctx, 'Peserta kontes tidak ada, tidak bisa menampilkan scoreboard', 'warning')
        return

    wait_message = await embed_message(ctx, 'Mohon tunggu, sedang menyiapkan scoreboard...', 'info')

    response = contest.update_scoreboard()
    await wait_message.delete()
    if response != 'OK':
        await embed_message(ctx, response, 'warning')
        return

    await ctx.send(embed=generate_scoreboard_embed(contest))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, discord.ext.commands.CheckFailure):
        await embed_message(ctx, 'You do not have the correct role for this command.', 'danger')
    elif isinstance(error, discord.ext.commands.CommandInvokeError):
        await embed_message(ctx, 'Internal Error', 'danger')
        print(type(error))
        print(error.original)
        embed = discord.Embed(title='ComBot Command Error', color=COLOR['danger'])
        embed.add_field(name='Guild', value=ctx.guild, inline=True)
        embed.add_field(name='Channel', value=ctx.channel, inline=True)
        embed.add_field(name='User', value=ctx.author, inline=True)
        embed.add_field(name='Message', value=ctx.message.clean_content, inline=False)
        embed.add_field(name='Error', value=error, inline=False)
        # embed.timestamp = datetime.now(timezone('Asia/Jakarta'))
        try:
            app_info = await bot.application_info()
            await app_info.owner.send(embed=embed)
        except: # pylint: disable=bare-except
            pass

bot.run(TOKEN)
