/* Jovian Labs · SEM scale & pixel-size check — runs entirely in the browser; images never leave the computer.
   Port of the calibration step of the Jovian Labs particle-size engine (data band, scale bar, Zeiss / Thermo Fisher metadata). */
(function () {
  "use strict";
  var UNIT_NM = { pm: 1e-3, nm: 1, "µm": 1e3, um: 1e3, mm: 1e6 };
  var rows = [];

  // ---------------------------------------------------------------- image decoding
  function decode(file, buf) {
    var name = file.name.toLowerCase();
    if (/\.tiff?$/.test(name)) {
      var ifds = UTIF.decode(buf);
      var ifd = ifds[0];
      UTIF.decodeImage(buf, ifd, ifds);
      var rgba = UTIF.toRGBA8(ifd);
      return { w: ifd.width, h: ifd.height, rgba: rgba, ifd: ifd };
    }
    return new Promise(function (resolve, reject) {
      var url = URL.createObjectURL(new Blob([buf]));
      var im = new Image();
      im.onload = function () {
        var c = document.createElement("canvas");
        c.width = im.naturalWidth; c.height = im.naturalHeight;
        var ctx = c.getContext("2d");
        ctx.drawImage(im, 0, 0);
        var d = ctx.getImageData(0, 0, c.width, c.height);
        URL.revokeObjectURL(url);
        resolve({ w: c.width, h: c.height, rgba: d.data, ifd: null });
      };
      im.onerror = function () { reject(new Error("unreadable image")); };
      im.src = url;
    });
  }

  function gray(img) {
    var n = img.w * img.h, g = new Float32Array(n), lo = 1e9, hi = -1e9, d = img.rgba;
    for (var i = 0; i < n; i++) {
      var v = 0.2125 * d[4 * i] + 0.7154 * d[4 * i + 1] + 0.0721 * d[4 * i + 2];
      g[i] = v; if (v < lo) lo = v; if (v > hi) hi = v;
    }
    var s = hi - lo + 1e-12;
    for (var j = 0; j < n; j++) g[j] = (g[j] - lo) / s;
    return g;
  }

  // ---------------------------------------------------------------- data band and scale bar
  function detectDatabar(g, w, h) {
    var dark = new Uint8Array(h);
    for (var r = 0; r < h; r++) {
      var c = 0;
      for (var x = 0; x < w; x++) if (g[r * w + x] < 0.05) c++;
      dark[r] = c / w > 0.5 ? 1 : 0;
    }
    var row = h - 1, gap = 0, gapMax = Math.max(4, Math.floor(h / 100));
    while (row >= 0 && !dark[row] && gap < gapMax) { row--; gap++; }
    var bh = 0;
    while (row >= 0 && dark[row]) { row--; bh++; }
    if (bh < 15 || bh > 0.25 * h) return 0;
    return h - 1 - row;
  }

  function longestRun(mask, W, r, c0, c1) {
    var best = 0, cur = 0;
    for (var c = c0; c <= c1; c++) { if (mask[r * W + c]) { cur++; if (cur > best) best = cur; } else cur = 0; }
    return best;
  }

  function detectScalebarPx(g, w, h, bh) {
    if (!bh) return 0;
    var y0 = h - bh, H = bh, W = w, bin = new Uint8Array(H * W), lab = new Int32Array(H * W), best = 0, id = 0;
    for (var r = 0; r < H; r++) for (var c = 0; c < W; c++) bin[r * W + c] = g[(y0 + r) * w + c] > 0.5 ? 1 : 0;
    var stack = new Int32Array(H * W);
    for (var p = 0; p < H * W; p++) {
      if (!bin[p] || lab[p]) continue;
      id++;
      var top = 0, rmin = H, rmax = -1, cmin = W, cmax = -1, pix = [];
      stack[top++] = p; lab[p] = id;
      while (top) {
        var q = stack[--top], qr = (q / W) | 0, qc = q - qr * W;
        pix.push(q);
        if (qr < rmin) rmin = qr; if (qr > rmax) rmax = qr; if (qc < cmin) cmin = qc; if (qc > cmax) cmax = qc;
        for (var dr = -1; dr <= 1; dr++) for (var dc = -1; dc <= 1; dc++) {
          var nr = qr + dr, nc = qc + dc;
          if (nr < 0 || nc < 0 || nr >= H || nc >= W) continue;
          var nq = nr * W + nc;
          if (bin[nq] && !lab[nq]) { lab[nq] = id; stack[top++] = nq; }
        }
      }
      if (rmin === 0 || rmax === H - 1) continue;          // touches the band edge: image remnant, not the bar
      var cw = cmax - cmin + 1;
      if (cw < 15) continue;
      var sub = new Uint8Array(H * W);
      for (var k = 0; k < pix.length; k++) sub[pix[k]] = 1;   // this component only
      var t = 0;
      for (var rr = rmin; rr <= rmax; rr++) if (longestRun(sub, W, rr, cmin, cmax) >= 0.9 * cw) t++;
      if (t === 0 || t > Math.max(3, 0.25 * cw)) continue;
      var tick = new Uint8Array(cw);
      for (var cc = 0; cc < cw; cc++) {
        var s = 0;
        for (var r2 = rmin; r2 <= rmax; r2++) s += sub[r2 * W + cmin + cc];
        tick[cc] = s > t + 2 ? 1 : 0;
      }
      var len = cw;
      if ((tick[0] || tick[1] || tick[2]) && (tick[cw - 1] || tick[cw - 2] || tick[cw - 3])) {
        var a = 0; while (a < cw && !tick[a]) a++; var lt = a; while (lt < cw && tick[lt]) lt++;
        var b = cw - 1; while (b >= 0 && !tick[b]) b--; var rt = cw - 1 - b; while (b >= 0 && tick[b]) { b--; } rt = cw - 1 - b;
        len = cw - (lt + rt) / 2;
      }
      if (len > best) best = len;
    }
    return best;
  }

  // ---------------------------------------------------------------- microscope metadata
  function tagText(v) {
    if (!v) return null;
    if (typeof v[0] === "string") return v.join("");
    var s = "";
    for (var i = 0; i < v.length; i++) s += String.fromCharCode(v[i]);
    return s;
  }

  function metadata(ifd, width) {
    if (!ifd) return null;
    var z = tagText(ifd.t34118);
    if (z) {
      var m = /AP_IMAGE_PIXEL_SIZE[\s\S]*?=\s*([\d.]+)\s*(pm|nm|µm|um|mm)/.exec(z);
      if (m) {
        var px = parseFloat(m[1]) * UNIT_NM[m[2]];
        var st = /DP_IMAGE_STORE[\s\S]*?=\s*(\d+)\s*\*\s*(\d+)/.exec(z);
        if (st) px *= parseInt(st[1], 10) / width;
        var mag = /AP_MAG[\s\S]*?=\s*([\d.]+\s*[KkX]*\s*X?)/.exec(z);
        return { px: px, src: "Zeiss SmartSEM metadata", mag: mag ? mag[1].trim() : "" };
      }
    }
    var codes = ["t34682", "t34680"];
    for (var i = 0; i < codes.length; i++) {
      var f = tagText(ifd[codes[i]]);
      if (!f) continue;
      var sec = /\[(?:Scan|EScan)\][^\[]*?PixelWidth\s*=\s*([\d.eE+\-]+)/.exec(f);
      if (sec) {
        var p2 = parseFloat(sec[1]) * 1e9;
        var rx = /\[Image\][^\[]*?ResolutionX\s*=\s*(\d+)/.exec(f);
        if (rx) p2 *= parseInt(rx[1], 10) / width;
        return { px: p2, src: "Thermo Fisher / FEI metadata", mag: "" };
      }
    }
    return null;
  }

  // ---------------------------------------------------------------- formatting
  function fmtLen(nm) {
    if (nm >= 1e6) return (nm / 1e6).toPrecision(3) + " mm";
    if (nm >= 1e3) return (nm / 1e3).toPrecision(3) + " µm";
    return nm.toPrecision(3) + " nm";
  }
  function fmtPx(nm) { return nm >= 1000 ? (nm / 1000).toPrecision(4) + " µm/px" : nm.toPrecision(4) + " nm/px"; }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }

  function barValueNm() {
    var v = parseFloat(String(document.getElementById("barValue").value).replace(",", "."));
    if (!(v > 0)) return null;
    return v * UNIT_NM[document.getElementById("barUnit").value];
  }

  function evaluate(r) {
    var bv = r.override || barValueNm();
    r.pxBar = (r.barPx && bv) ? bv / r.barPx : null;
    r.px = r.meta ? r.meta.px : r.pxBar;
    r.disc = (r.meta && r.pxBar) ? Math.abs(r.pxBar / r.meta.px - 1) : null;
    if (r.error) { r.status = "bad"; r.note = r.error; }
    else if (r.disc !== null) {
      r.status = r.disc < 0.01 ? "ok" : (r.disc < 0.03 ? "warn" : "bad");
      r.note = (r.disc < 0.01 ? "metadata and scale bar agree" : "metadata and scale bar differ by " + (100 * r.disc).toFixed(1) + " %");
    } else if (r.meta) { r.status = "ok"; r.note = r.barPx ? "metadata (type the bar length to cross-check)" : "metadata only"; }
    else if (r.pxBar) { r.status = "ok"; r.note = "scale bar only"; }
    else if (r.barPx) { r.status = "warn"; r.note = "bar found (" + r.barPx.toFixed(1) + " px): type its length above"; }
    else { r.status = "bad"; r.note = "no metadata and no scale bar found"; }
  }

  function render() {
    var tb = document.getElementById("rows"), html = "";
    var groups = {};
    rows.forEach(function (r) { evaluate(r); if (r.px) { var k = r.px.toPrecision(3); groups[k] = (groups[k] || 0) + 1; } });
    rows.forEach(function (r, i) {
      var icon = { ok: "✓", warn: "!", bad: "✗" }[r.status];
      var fov = r.px ? fmtLen(r.px * r.w) + " × " + fmtLen(r.px * (r.h - r.bh)) : "—";
      html += "<tr><td class='st " + r.status + "'>" + icon + "</td><td>" + esc(r.name) + "</td><td class='num'>" + r.w + " × " + r.h +
        "</td><td class='num'>" + (r.meta ? fmtPx(r.meta.px) : "—") + "</td><td class='num'>" + (r.barPx ? r.barPx.toFixed(1) + " px" : "—") +
        "</td><td class='num'>" + (r.pxBar ? fmtPx(r.pxBar) : "—") + "</td><td class='num'>" + fov + "</td><td>" + esc(r.note) +
        "</td><td>" + (r.px ? "<button data-i='" + i + "' class='burn'>PNG</button>" : "") + "</td></tr>";
    });
    tb.innerHTML = html;
    var n = rows.length, ok = rows.filter(function (r) { return r.status === "ok"; }).length;
    var mags = Object.keys(groups).length;
    document.getElementById("summary").textContent = n ? (n + " image(s) · " + ok + " calibrated without warning · " +
      (mags > 1 ? mags + " different pixel sizes (mixed magnifications: analyse them separately)" : (mags === 1 ? "one pixel size for all images" : ""))) : "";
    document.getElementById("csv").disabled = !n;
    Array.prototype.forEach.call(document.querySelectorAll("button.burn"), function (b) {
      b.onclick = function () { burn(rows[+b.getAttribute("data-i")]); };
    });
  }

  // ---------------------------------------------------------------- clean scale bar (PNG)
  function niceLength(target) {
    var e = Math.pow(10, Math.floor(Math.log10(target))), best = e;
    [1, 2, 5, 10].forEach(function (m) { if (m * e <= target) best = m * e; });
    return best;
  }
  function burn(r) {
    var fh = r.h - r.bh, c = document.createElement("canvas");
    c.width = r.w; c.height = fh;
    var ctx = c.getContext("2d"), id = ctx.createImageData(r.w, fh);
    id.data.set(r.rgba.subarray ? r.rgba.subarray(0, r.w * fh * 4) : r.rgba.slice(0, r.w * fh * 4));
    ctx.putImageData(id, 0, 0);
    var L = niceLength(0.2 * r.w * r.px), Lpx = L / r.px, pad = Math.round(r.w * 0.02), th = Math.max(4, Math.round(r.w / 160));
    var fs = Math.max(14, Math.round(r.w / 45)), label = fmtLen(L).replace(/\.0+ /, " ").replace(/(\.\d*?)0+ /, "$1 ");
    ctx.font = "600 " + fs + "px system-ui, sans-serif";
    var tw = ctx.measureText(label).width, bw = Math.max(Lpx, tw) + 2 * pad, bhh = th + fs + 2.6 * pad;
    ctx.fillStyle = "rgba(0,0,0,0.6)";
    ctx.fillRect(pad, fh - bhh - pad, bw, bhh);
    ctx.fillStyle = "#fff";
    ctx.fillRect(2 * pad, fh - pad - 1.2 * pad - th, Lpx, th);
    ctx.textBaseline = "bottom";
    ctx.fillText(label, 2 * pad, fh - pad - 1.8 * pad - th);
    c.toBlob(function (blob) {
      var a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = r.name.replace(/\.[^.]+$/, "") + "_scalebar.png";
      a.click();
      setTimeout(function () { URL.revokeObjectURL(a.href); }, 2000);
    });
  }

  function csv() {
    var lines = [["file", "width_px", "height_px", "metadata_pixel_nm", "metadata_source", "scale_bar_px", "scale_bar_pixel_nm",
      "difference_pct", "pixel_size_used_nm", "field_width_um", "status", "note"].join(",")];
    rows.forEach(function (r) {
      lines.push([JSON.stringify(r.name), r.w, r.h, r.meta ? r.meta.px.toPrecision(6) : "", r.meta ? JSON.stringify(r.meta.src) : "",
        r.barPx ? r.barPx.toFixed(2) : "", r.pxBar ? r.pxBar.toPrecision(6) : "", r.disc !== null ? (100 * r.disc).toFixed(2) : "",
        r.px ? r.px.toPrecision(6) : "", r.px ? (r.px * r.w / 1000).toPrecision(5) : "", r.status, JSON.stringify(r.note)].join(","));
    });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([lines.join("\n")], { type: "text/csv" }));
    a.download = "scale_check.csv";
    a.click();
  }

  // ---------------------------------------------------------------- main
  function handle(files) {
    var list = Array.prototype.slice.call(files), prog = document.getElementById("progress");
    var chain = Promise.resolve();
    list.forEach(function (f, k) {
      chain = chain.then(function () {
        prog.textContent = "Reading " + (k + 1) + " / " + list.length + ": " + f.name;
        return f.arrayBuffer().then(function (buf) { return Promise.resolve(decode(f, buf)); }).then(function (img) {
          var g = gray(img), bh = detectDatabar(g, img.w, img.h);
          rows.push({ name: f.name, w: img.w, h: img.h, bh: bh, rgba: img.rgba, meta: metadata(img.ifd, img.w),
                      barPx: detectScalebarPx(g, img.w, img.h, bh) });
        }).catch(function (e) {
          rows.push({ name: f.name, w: 0, h: 0, bh: 0, rgba: null, meta: null, barPx: 0, error: "could not read: " + e.message });
        }).then(render);
      });
    });
    chain.then(function () { prog.textContent = ""; });
  }

  window.JLScale = { detectDatabar: detectDatabar, detectScalebarPx: detectScalebarPx, metadata: metadata, rows: rows };
  document.addEventListener("DOMContentLoaded", function () {
    var inp = document.getElementById("files"), drop = document.getElementById("drop");
    inp.addEventListener("change", function () { handle(inp.files); inp.value = ""; });
    ["dragenter", "dragover"].forEach(function (t) { drop.addEventListener(t, function (e) { e.preventDefault(); drop.classList.add("over"); }); });
    ["dragleave", "drop"].forEach(function (t) { drop.addEventListener(t, function (e) { e.preventDefault(); drop.classList.remove("over"); }); });
    drop.addEventListener("drop", function (e) { handle(e.dataTransfer.files); });
    document.getElementById("barValue").addEventListener("input", render);
    document.getElementById("barUnit").addEventListener("change", render);
    document.getElementById("csv").addEventListener("click", csv);
    document.getElementById("clear").addEventListener("click", function () { rows.length = 0; render(); });
  });
})();
