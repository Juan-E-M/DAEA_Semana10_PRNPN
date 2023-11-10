var express = require('express'),
    async = require('async'),
    { Pool } = require('pg'),
    cookieParser = require('cookie-parser'),
    app = express(),
    server = require('http').Server(app),
    io = require('socket.io')(server);

var port = process.env.PORT || 4000;

io.on('connection', function (socket) {
  socket.emit('message', { text: 'Welcome!' });
  socket.on('subscribe', function (data) {
    socket.join(data.channel);
  });
});

var pool = new Pool({
  connectionString: 'postgres://postgres:postgres@db/postgres'
});

// Mantener un estado de la última ID procesada
var lastProcessedId = 0;

// Configurar notificación de PostgreSQL LISTEN/NOTIFY
pool.connect(function (err, client, done) {
  if (err) {
    console.error("Error connecting to db: " + err);
    return;
  }
  client.query('LISTEN vote_change');

  client.on('notification', function (msg) {
    // Actualizar el estado solo si la ID es mayor a la última procesada
    var newId = parseInt(msg.payload);
    if (newId > lastProcessedId) {
      lastProcessedId = newId;
      getDistances(client);
    }
  });
});

function getDistances(client) {
  client.query('SELECT id, distancia_manhattan, distancia_pearson FROM votes ORDER BY id DESC LIMIT 1', [], function (err, result) {
    if (err) {
      console.error("Error performing query: " + err);
    } else {
      var distances = result.rows[0] || { id: 0, distancia_manhattan: 0, distancia_pearson: 0 };
      io.sockets.emit("distances", JSON.stringify(distances));
    }
  });
}

app.use(cookieParser());
app.use(express.urlencoded());
app.use(express.static(__dirname + '/views'));

app.get('/', function (req, res) {
  res.sendFile(path.resolve(__dirname + '/views/index.html'));
});

server.listen(port, function () {
  var port = server.address().port;
  console.log('App running on port ' + port);
});
