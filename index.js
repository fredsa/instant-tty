var express = require('express');
var tty = require('tty.js');

var app = tty.createServer({
  shell: 'bash',
  users: {
    //foo: 'bar'
  },
  "io": { "log": true },
  "debug": true,
  port: 80
});

app.get('/foo', function(req, res, next) {
  res.send('bar');
});

app.use(express.static(__dirname));

app.listen();
