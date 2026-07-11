/* Rhody — landing interactions. Flat, no dependencies. */
(function () {
  "use strict";

  // Current year in footer
  var yearEl = document.getElementById("year");
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  // Reveal-on-scroll: tag most content blocks, animate as they enter view.
  var revealTargets = document.querySelectorAll(
    ".thesis__card, .step, .feat, .features__soon, .role, .plan, .section-head"
  );
  revealTargets.forEach(function (el) { el.classList.add("reveal"); });

  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-in");
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
    );
    revealTargets.forEach(function (el) { io.observe(el); });
  } else {
    // No IO support: just show everything.
    revealTargets.forEach(function (el) { el.classList.add("is-in"); });
  }

  // Waitlist form — client-side only (no backend on a flat site).
  // Stores signups in localStorage so nothing is lost, and gives friendly feedback.
  var form = document.getElementById("waitlistForm");
  var msg = document.getElementById("waitlistMsg");

  function isEmail(v) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);
  }

  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var band = form.band.value.trim();
      var email = form.email.value.trim();

      if (!band) { setMsg("Add your band name so we know who's in.", false); form.band.focus(); return; }
      if (!isEmail(email)) { setMsg("That email looks off — mind checking it?", false); form.email.focus(); return; }

      try {
        var key = "rhody_waitlist";
        var list = JSON.parse(localStorage.getItem(key) || "[]");
        list.push({ band: band, email: email, at: new Date().toISOString() });
        localStorage.setItem(key, JSON.stringify(list));
      } catch (err) { /* localStorage may be blocked; not fatal */ }

      form.reset();
      setMsg("You're on the list, " + band + ". We'll be in touch before your next run. 🎸", true);
    });
  }

  function setMsg(text, ok) {
    if (!msg) return;
    msg.textContent = text;
    msg.style.color = ok ? "#ffffff" : "#ffe0c2";
  }
})();
