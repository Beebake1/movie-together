$(function() {
    room = "{{ data.room }}";
    username = "{{ data.username }}";
    $("iframe").attr("src", "/embeded/" + room + "/" + username);

    var message_socket = io.connect('http://192.168.1.101:9000/message');

    message_socket.on('receive_message', function(data) {
        console.log(data.username + ' says ' + data.message);
    });
    message_socket.on('join_room_announcement', function(data) {
        console.log(data.username + ' joined');
        $('.user-row').append('<div class="col-md-3 user">User-' + (data.username).toUpperCase() + '</div>');
    });

    message_socket.on('leave_room_announcement', function(data) {
        console.log(data.username + ' left');
    });
    message_socket.on('connect', function() {
        message_socket.emit('join_chat_room', {
            username: username,
            room: room,
        });
    });

    window.onbeforeunload = function() {
        message_socket.emit('leave_chat_room', {
            username: username,
            room: room
        })
    };

    message_socket.emit('send_message', {
        username: username,
        room: room,
        message: 'hello test'
    });
});