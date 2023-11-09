var express = require('express'),
    async = require('async'),
    { Pool } = require('pg'),
    cookieParser = require('cookie-parser'),
    app = express(),
    server = require('http').Server(app),
    io = require('socket.io')(server);

var path = require('path');  // Añadir esta línea para utilizar 'path'

var port = process.env.PORT || 4000;

io.on('connection', function (socket) {
  socket.emit('message', { text : 'Welcome!' });

  socket.on('subscribe', function (data) {
    socket.join(data.channel);
  });
});

var pool = new Pool({
  connectionString: 'postgres://postgres:postgres@db/postgres'
});

async.retry(
  {times: 1000, interval: 1000},
  function(callback) {
    pool.connect(function(err, client, done) {
      if (err) {
        console.error("Waiting for db");
      }
      callback(err, client);
    });
  },
  function(err, client) {
    if (err) {
      return console.error("Giving up");
    }
    console.log("Connected to db");
    getVotes(client);
  }
);

function getVotes(client) {
  client.query('SELECT distancia_manhattan, distancia_pearson FROM votes LIMIT 1', [], function(err, result) {
    if (err) {
      console.error("Error performing query: " + err);
    } else {
      var distances = collectDistancesFromResult(result);
      io.sockets.emit("updateDistances", distances);
    }

    setTimeout(function() {getVotes(client) }, 1000);
  });
}

function collectDistancesFromResult(result) {
  if (result.rows.length > 0) {
    var row = result.rows[0];
    return {
      distancia_manhattan: row.distancia_manhattan,
      distancia_pearson: row.distancia_pearson
    };
  } else {
    return {
      distancia_manhattan: 0,
      distancia_pearson: 0
    };
  }
}

app.use(cookieParser());
app.use(express.urlencoded());
app.use(express.static(path.join(__dirname, '/views')));  // Utilizar 'path'

app.get('/', function (req, res) {
  res.sendFile(path.resolve(__dirname + '/views/index.html'));
});

server.listen(port, function () {
  console.log('App running on port ' + port);
});
