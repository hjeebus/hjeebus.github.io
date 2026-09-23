// Graye Market static PoC — progressive enhancement only.
(function () {
  'use strict';

  // Mobile nav
  document.querySelectorAll('.nav-burger').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var nav = btn.closest('.nav');
      var open = nav.classList.toggle('open');
      btn.setAttribute('aria-expanded', String(open));
    });
  });

  // Mobile filters bottom sheet (browse)
  var sheetBtn = document.getElementById('filtersBtn');
  if (sheetBtn) {
    var sheet = document.getElementById('filtersSheet');
    var scrim = document.getElementById('sheetScrim');
    var closeBtn = document.getElementById('filtersClose');
    var setOpen = function (open) {
      sheet.classList.toggle('open', open);
      scrim.classList.toggle('open', open);
      document.body.style.overflow = open ? 'hidden' : '';
    };
    sheetBtn.addEventListener('click', function () { setOpen(true); });
    closeBtn.addEventListener('click', function () { setOpen(false); });
    scrim.addEventListener('click', function () { setOpen(false); });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') setOpen(false);
    });
  }

  // Photo thumbnails (listing detail)
  var thumbs = document.querySelectorAll('.thumb');
  thumbs.forEach(function (t) {
    t.addEventListener('click', function () {
      thumbs.forEach(function (x) { x.classList.remove('sel'); });
      t.classList.add('sel');
    });
  });

  // Copy seller details (unlocked)
  var copyBtn = document.getElementById('copyDetails');
  if (copyBtn) {
    copyBtn.addEventListener('click', function () {
      var keys = document.querySelectorAll('.cb-k');
      var vals = document.querySelectorAll('.cb-v');
      var text = [];
      for (var i = 0; i < keys.length; i++) {
        text.push(keys[i].textContent.trim() + ': ' + vals[i].textContent.trim());
      }
      navigator.clipboard.writeText(text.join('\n')).then(function () {
        var label = copyBtn.querySelector('span') || copyBtn;
        var prev = label.textContent;
        label.textContent = 'Copied';
        setTimeout(function () { label.textContent = prev; }, 1600);
      }).catch(function () {});
    });
  }
})();