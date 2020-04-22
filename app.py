import pip._vendor.requests as req
from datetime import datetime 
import time
import os
import random
import string

from flask import Flask,render_template,request,redirect,Markup
from flask_socketio import SocketIO, send,join_room,leave_room,emit,rooms
from bs4 import BeautifulSoup
from utils.file_helper import read


app = Flask(__name__,static_url_path='/static')
app.config['SECRET_KEY'] = os.environ.get('SECRET')

socketio = SocketIO(app)

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
    emit('join_room_announcement',data,room=data['room'])

@socketio.on('leave_chat_room',namespace='/message')
def handle_leave_chat_room_event(data):
    leave_room(data['room'])
    emit('leave_room_announcement', data, room=data['room'])
url = "https://hindimovies.to/"

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
movie_rooms = []
@app.route('/movie/<string:movie_name>/')
def movie(movie_name):
    keyword = movie_name
    
    room = get_random(12)
    movie_rooms.append({'room':room,'movie':keyword})
    return  redirect('/watch/'+room+'/',)


@app.route('/watch/<string:room>/')
def room(room):
    
    for rim in movie_rooms:
        if(rim['room'] == (room)):
            data = {
                'username' : get_random(5),
                 'room'  : room,
                 'movie' : rim['movie']
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
        else:
            content = Markup('<h1>Movie not Found</h1>')
    return render_template('watch/embeded/movie_embeded.html',content='szdxfcgvhb')

if __name__=='__main__':
    socketio.run()