#!/usr/bin/env node

var express = require('express');
var tty = require('tty.js');

var app = tty.createServer({
  shell: 'bash',
  users: {
    //foo: 'bar'
  },
  "io": {
  	"log": true,
  	"resource": "/secret42"
  },
  "debug": true,
  "static": __dirname,
  port: 8080
});

app.get('/foo', function(req, res, next) {
  res.send('bar');
});

//app.use(express.static(__dirname));

app.setAuth(function(req, res, next) {
	next();
});

app.listen();
