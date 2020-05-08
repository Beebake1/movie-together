$(function() {
    io.connect(location.protocol + '//' + document.domain + ':' + location.port + '/event');
    const username = '[[username]]';
    const room = '[[room]]'

    socket.on('receive_event', function(data) {
        if (username != data.username) {
            if (data.event === 'play') {
                jwplayer().play();
            } else if (data.event === 'pause') {
                jwplayer().pause(true);
            } else if (data.event === 'seek') {
                player.seek(parseFloat(data.time));
            }
        }
    });

    player.on('seek', function(x) {
        if (x.offset.toFixed(2) != player.getCurrentTime().toFixed(2)) {
            socket.emit('event_alert', {
                username: username,
                room: room,
                event: 'seek',
                time: x.offset.toString()
            });
        }
    });

    player.on('play', function() {
        socket.emit('event_alert', {
            username: username,
            room: room,
            event: 'play',
            time: player.getCurrentTime().toString()
        });
    });

    player.on('pause', function() {
        socket.emit('event_alert', {
            username: username,
            room: room,
            event: 'pause',
            time: player.getCurrentTime().toString()
        });
    });

    $(document).on('click', '.pause-video', function() {
        socket.emit('event_alert', {
            username: username,
            room: room,
            event: 'pause',
            time: '0'
        });
    });
    $(document).on('click', 'btn-change', function() {
        $('#exampleModalLong').modal('show');
        if (username === '') {
            console.log('blank');
        } else {
            $('.username').val('');
            $('#exampleModalLong').modal('hide');
        }
    });

    window.onbeforeunload = function() {
        socket.emit('leave_room', {
            username: username,
            room: room
        })
    };

    socket.on('connect', function() {
        socket.emit('join_room', {
            username: username,
            room: room
        });
    });

});