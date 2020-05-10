import pip._vendor.requests as req
from datetime import datetime 
import time
import os
import random
import string

from flask_sqlalchemy import SQLAlchemy
from flask import Flask,render_template,request,redirect,Markup
from flask_socketio import SocketIO, send,join_room,leave_room,emit,rooms
from bs4 import BeautifulSoup
from utils.file_helper import read


app = Flask(__name__,static_url_path='/static')
app.config['SECRET_KEY'] = os.environ.get('SECRET')


app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://tbcptjvkoiotvd:95b2637180a39cd15a8755567b00631ef441a48bd7f1f491fb2a76591ed38979@ec2-54-75-246-118.eu-west-1.compute.amazonaws.com:5432/d8ntst072imlh7'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
socketio = SocketIO(app)
movie_rooms = []
eng_url = "https://bmoviesfree.page/"
url = "https://hindimovies.to/"

class Bmovies(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(220))
    image = db.Column(db.String(220))
    link = db.Column(db.String(220))

    def __init__(self, title,image,link):
        self.title = title
        self.image = image
        self.link = link
@socketio.on('join_room',namespace='/event')
def handle_join_room_event(data):
    join_room(data['room'])

@socketio.on('leave_room',namespace='/event')
def handle_leave_room_event(data):
    leave_room(data['room'])

@socketio.on('event_alert',namespace='/event')
def handle_send_alert_event(data):
    emit('receive_event', data, room=data['room'])

@socketio.on('send_message',namespace='/message')
def handle_send_message_event(data):
    join_room(data['room'])
    emit('receive_message', data, room=data['room'])

@socketio.on('join_chat_room',namespace='/message')
def handle_join_chat_room_event(data):
    join_room(data['room'])
    room_data =''
    for movie_room in movie_rooms:
        if(movie_room['room']==data['room']):
            room_users = movie_room['users']
            room_users.append(data['username'])
            movie_room.update(users = room_users)
            room_data = movie_room
    data.update(room_data = room_data)        
    emit('join_room_announcement',data,room=data['room'])

@socketio.on('leave_chat_room',namespace='/message')
def handle_leave_chat_room_event(data):
    leave_room(data['room'])
    room_data =''
    for movie_room in movie_rooms:
        if(movie_room['room']==data['room']):
            room_users = movie_room['users']
            room_users.remove(data['username'])
            movie_room.update(users = room_users)
            room_data = movie_room
    data.update(room_data = room_data)      
    emit('leave_room_announcement', data, room=data['room'])

def fetch(url):
    return req.get(url)

def get_random(x):
       return "".join( [random.choice(string.ascii_letters[:26]) for i in range(x)])

@app.route('/',methods = ["POST","GET"])
def search():
    list_template = '   <div class="items"><a href="[[movie_link]]"><div class="ite"><img src="[[img-src]]" class="image" alt="">[[movie_title]]</a></div></div>'
    if request.method == "POST":
        keyword = request.form['search']
        response=fetch(url+'full-search/'+ keyword)
        movie_soup = BeautifulSoup(response.text,'html.parser')
        movie_list = movie_soup.findAll('div',attrs={'class':'w3l-movie-gride-agile'})
        html = ''
        for movie in movie_list:
            list = list_template.replace('[[img-src]]',movie.find('img')['data-src'])
            list = list.replace('[[movie_link]]',movie.find('a')['href'])
            list = list.replace('[[movie_title]]',movie.find('a')['title'])
            html += list
        data = Markup(html)    
        return render_template('movie_list.html',data = data)
    else:
        return render_template('index.html')


@app.route('/movie/<string:movie_name>/')
def movie(movie_name):
    keyword = movie_name
    room = get_random(20)
    movie_rooms.append({'room':room,'movie':keyword,'users' : []})
    return  redirect('/watch/'+room+'/',)


@app.route('/watch/<string:room>/')
def room(room):
    movie = ''
    data = ['hindi' ,'in']
    for rom in movie_rooms:
       if(rom['room'] == room):
           movie = rom['movie']
    tokens = movie.split('-');
    movie_name = ''
    for token in tokens:
        if(token not in data and token.isalpha()):
            movie_name+= token + ' '

    data = {
            'username' : get_random(5),
                'room'  : room,
                'movie' : movie,
                'name'  : movie_name
    }
    return render_template('watch/movie.html',data=data)

@app.route('/embeded/<string:movie>/<string:room>/<string:username>/')
def embeded(movie,room,username):
    response=fetch(url+'movie/'+ movie)
    movie_soup = BeautifulSoup(response.text,'html.parser')
    movie_servers = movie_soup.findAll('li',attrs={'class':'mb5'})
    content =''
    for server in movie_servers:
        iframe_source = fetch(url+'embed-src/?url='+server.find('a')['data-id']+'&t=0')
        iframe_text = iframe_source.text
        if(iframe_text.find('Clappr') != -1):
            iframe_inner = iframe_text
            js = read('static/js/player.js')
            js = js.replace('[[username]]',username)
            js = js.replace('[[room]]',room)
            iframe_inner = iframe_inner.replace('</html>','<script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/1.4.8/socket.io.min.js"></script><script>'+js+'</script>')
            content = Markup(iframe_inner)
            break
        else:
            content = Markup('<h1>Movie not Found</h1>')
    return render_template('watch/embeded/movie_embeded.html',content=content)

@app.route('/eng/search',methods = ["POST","GET"])
def bmovies_search():
    if request.method == "POST":
        keyword = request.form['search']
        list_template = '<div class="items"><a href="[[movie_link]]"><div class="ite"><img src="[[img-src]]" class="image" alt="">[[movie_title]]</a></div></div>'
        movies = db.session.execute("select * from public.bmovies where title ilike '%"+keyword+"%'")
        html = ''
        for movie in movies:
            content = list_template.replace('[[movie_link]]',movie['link'].replace(eng_url,'/eng/'))
            content = content.replace('[[img-src]]',movie['image'])
            content = content.replace('[[movie_title]]',movie['title'])
            html+=content
        data = Markup(html)
        return render_template('movie_list.html',data = data)
    else:
        return render_template('index.html')  

@app.route('/eng/movie/<string:movie_name>/')
def eng_movie(movie_name):
    keyword = movie_name
    room = get_random(20)
    movie_rooms.append({'room':room,'movie':'eng/'+keyword,'users' : []})
    return  redirect('/watch/'+room+'/',)

@app.route('/embeded/eng/<string:movie>/<string:room>/<string:username>/')
def eng_embeded(movie,room,username):
    response=fetch(eng_url+'movie/'+ movie+'/watching/?server_id=6')
    movie_soup = BeautifulSoup(response.text,'html.parser')
    token = movie_soup.find('div',attrs={'id':'iframes'})['data-onlystream']
    content =''
    iframe_source = fetch('https://vidoo.streamango.to/e/'+token)
    iframe_text = iframe_source.text
    iframe_inner = iframe_text
    js = read('static/js/player_jw.js')
    js = js.replace('[[username]]',username)
    js = js.replace('[[room]]',room)
    iframe_inner = iframe_inner.replace('</HTML>','<script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/1.4.8/socket.io.min.js"></script><script>'+js+'</script>')
    content = Markup(iframe_inner)
    return render_template('watch/embeded/movie_embeded.html',content=content)  

@app.route('/eng/update')
def update_bmovies_list():
    i = 1
    while(True):
        response=fetch('https://bmoviesfree.page/movies/page/'+str(i)+'/')
        movie_soup = BeautifulSoup(response.text,'html.parser')
        movie_list = movie_soup.findAll('div',attrs={'class':'item'})
        if(len(movie_list) == 0):
            break;
        for movie in movie_list:
            movie_link = movie.find('a',attrs={'class':'name'})['href']
            movie_image = movie.find('img',attrs={'class':'lazy'})['src']
            movie_name = movie.find('a',attrs={'class':'name'}).text
            db.session.add(Bmovies(movie_name,movie_image,movie_link))
            db.session.commit()
        i+=1
    data = Markup('<h1>Done</h1>')    
    return render_template('movie_list.html',data=data)

if __name__=='__main__':
    db.create_all()
    socketio.run()