document.querySelectorAll('a').forEach(item => {
  item.addEventListener('click', event => {
    // Send JSON message to application
    window.webkit.messageHandlers.signal.postMessage(
      { "path": item.dataset.path, "line": item.dataset.line });

    // Keep href from being parsed
    return false;
  })
});

function beep() {
  new Audio('beep.mp3').play();
  var color = document.body.style.backgroundColor;
  setTimeout(function () {
    document.body.style.backgroundColor = '#5078A0';
  }, 100);
  setTimeout(function () {
    document.body.style.backgroundColor = color;
  }, 200);
}

function set_font(font, font_size) {
  document.body.style.fontFamily = font;
  document.body.style.fontSize = font_size;
}