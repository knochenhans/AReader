window.addEventListener("load", function () {
  new QWebChannel(qt.webChannelTransport, function (channel) {
    var x = 0
    document.bridge = channel.objects.bridge;
  });
});

var beep_snd;

window.addEventListener('load', (event) => {
  beep_snd = new Audio('../beep.mp3')
});

function beep() {
  beep_snd.play();
  var color = document.body.style.backgroundColor;
  setTimeout(function () {
    document.body.style.backgroundColor = '#5078A0';
  }, 100);
  setTimeout(function () {
    document.body.style.backgroundColor = color;
  }, 200);
}

function setStyle(elementName, string) {
  for (i = 0; i < document.getElementsByTagName(elementName).length; i++) {
    document.getElementsByTagName(elementName)[i].style.cssText = string
  }
}

// function alert_box() {
//   alert('bla');
//   document.getElementsByTagName('a')[0].style.backgroundColor = 'red';
// }