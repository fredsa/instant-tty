tty.on('connect', function() {
  new tty.Window();
  document.body.className += " connected";
})
