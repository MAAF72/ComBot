import discord
import requests
from requests import get
from copy import deepcopy
from datetime import datetime
from datetime import timedelta

class TlxContest:
    def __init__(self, id: int, name: str, admin: discord.member.Member):
        self.id = id
        self.name = name
        self.admin = admin
        self.problems = dict()
        self.players = dict()
        self.duration = 0
        self.start = None
        self.end = None
        self.scoreboard = dict()
        self.dummy_score = dict()
        self.procs = []
        self.is_crawling = False
    
    def is_over(self):
        if self.start != None and datetime.timestamp(datetime.now()) > self.end:
            return True
        return False
    
    def set_duration(self, duration):
        if self.start != None:
            return 'Tidak bisa mengatur durasi kontes yang sedang berlangsung'
            
        self.duration = duration
        return 'OK'
    
    def add_duration(self, duration):
        if self.is_over():
            return 'Tidak bisa memperpanjang durasi kontes yang sudah selesai'
            
        self.duration += duration
        self.end += duration * 60
        return 'OK'
        
    def add_problem(self, slug):
        if slug in self.problems:
            return 'Problem sudah ditambahkan pada kontes ini'
        if self.start != None:
            return 'Tidak bisa menambahkan problem ke kontes yang sedang berlangsung'
        if self.is_over():
            return 'Tidak bisa menambahkan problem ke kontes yang sudah selesai'

        contest_slug, problem_alias = slug.split('/')
        json_contest = get('https://jerahmeel.tlx.toki.id/api/v2/problemsets/slug/{}'.format(contest_slug)).json()
        
        if 'errorCode' in json_contest:
            return 'Problem tidak ditemukan'
        
        json_problem = get('https://jerahmeel.tlx.toki.id/api/v2/problemsets/{}/problems/{}/worksheet?language=id'.format(json_contest['jid'], problem_alias)).json()
        
        if 'errorCode' in json_problem:
            return 'Problem tidak ditemukan'
        
        self.problems[slug] = {
            'jid': json_problem['problem']['problemJid'],
            'name': json_problem['worksheet']['statement']['title'],
            'latestSubmission': -1
        }
        
        return 'OK'
        
    def del_problem(self, slug):
        if slug not in self.problems:
            return 'Problem tidak ditemukan pada kontes ini'
        if self.start != None:
            return 'Tidak bisa menghapus problem dari kontes yang sedang berlangsung'
            
        del self.problems[slug]
        return 'OK'
        
    def crawl(self, slug):
        finish = False
        page = 1
        jid = self.problems[slug]['jid']
        found_pending = False
        stack = []
        while not finish:
            url = 'https://jerahmeel.tlx.toki.id/api/v2/submissions/programming?page={}&problemJid={}'.format(page, jid)
            json_submission = get(url).json()
            if len(json_submission['data']['page']) > 0:
                for i in json_submission['data']['page']:
                    if i['id'] == self.problems[slug]['latestSubmission']:
                        finish = True
                        break
                    
                    tlx_username = json_submission['profilesMap'][i['userJid']]['username']
                    
                    if tlx_username in self.players.values():
                        stack.append({
                            'id': i['id'],
                            'verdict': i['latestGrading']['verdict']['code'],
                            'score': i['latestGrading']['score'],
                            'time': i['time'],
                            'username': tlx_username
                        })
                page += 1
                
        # Process stack
        while stack:
            curr = stack.pop()
            if curr['verdict'] == '?':
                break
            
            user_scoreboard = self.scoreboard[curr['username']]
            if curr['score'] > user_scoreboard[slug]['score']:
                user_scoreboard['totalScore'] += curr['score'] - user_scoreboard[slug]['score']
                user_scoreboard['totalTime'] += (curr['time'] // 1000) - self.start - user_scoreboard[slug]['time'] 
                user_scoreboard[slug]['score'] = curr['score']
                user_scoreboard[slug]['time'] = (curr['time'] // 1000) - self.start
                
            print('Submission {} : timestamp : {}, start : {}'.format(curr['id'], curr['time'], self.start))
            self.problems[slug]['latestSubmission'] = curr['id']
        
    def start_contest(self):
        if self.start != None:
            return 'Tidak bisa memulai kontes yang sudah berlangsung'
        if len(self.problems) == 0:
            return 'Tolong tambahkan problem terlebih dahulu sebelum memulai kontes'
        if self.duration <= 0:
            return 'Tolong atur durasi sebelum memulai kontes'
        
        # Create dummy_score
        self.dummy_score = {
            'totalScore': 0,
            'totalTime': 0,
        }
        for slug in self.problems.keys():
            self.dummy_score[slug] = {
                'score': 0,
                'time': 0,
            }

        # Register players biar bisa dicrawl
        for tlx_username in list(self.players.values()):
            self.scoreboard[tlx_username] = deepcopy(self.dummy_score)
            
        self.start = int(datetime.timestamp(datetime.now()))
        self.end = self.start + self.duration * 60
        
        #get latestSubmission for every problem  
        procs = []
        for slug in self.problems.keys():
            url = 'https://jerahmeel.tlx.toki.id/api/v2/submissions/programming?page=1&problemJid={}'.format(self.problems[slug]['jid'])
            json_submission = get(url).json()
            if len(json_submission['data']['page']) > 0:
                self.problems[slug]['latestSubmission'] = json_submission['data']['page'][0]['id']
        print('start', self.start)
        print('end', self.end)
        return 'OK'
        
    def add_player(self, user, tlx_username):
        if user in self.players:
            return '{} ({}) sudah terdaftar pada kontes {} #{}'.format(user.mention, self.players[user], self.name, self.id)
        if self.is_over():
            return 'Tidak bisa menambahkan player baru ke kontes yang sudah selesai'

        json_user = get('https://jerahmeel.tlx.toki.id/api/v2/user-stats?username={}'.format(tlx_username)).json()
        
        if 'errorCode' in json_user:
            return 'Akun TLX {} tidak dapat ditemukan {}'.format(tlx_username, user.mention)
        
        # Join di tengah2, masukkan datanya juga ke scores dan submission agar bisa kedetect pas crawling
        self.players[user] = tlx_username
        if self.start != None:
            self.scoreboard[tlx_username] = deepcopy(self.dummy_score)

        return 'OK'
    
    def del_player(self, user):
        if user not in self.players:
            return '{} tidak terdaftar pada kontes {} #{}'.format(user.mention, self.name, self.id)
        if self.start != None:
            return 'Tidak bisa mengeluarkan player dari kontes yang sedang berlangsung'
        if self.is_over():
            return 'Tidak bisa mengeluarkan player dari kontes yang sudah selesai'
        
        del self.players[user]
        return 'OK'
        
    def update_scoreboard(self):
        if self.is_crawling:
            return 'Mohon tunggu, proses sebelumnya belum selesai...'

        self.is_crawling = True
        for slug in self.problems.keys():
            print('crawling', slug)
            self.crawl(slug)
        
        print(self.scoreboard)
        self.is_crawling = False    
        return 'OK'