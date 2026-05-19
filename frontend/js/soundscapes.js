// Web Audio API ambient soundscape engine — no external API needed

const SoundscapePlayer = (() => {
  let _ctx = null;
  let _master = null;
  let _nodes = [];
  let _playing = false;
  let _current = null;

  function getCtx() {
    if (!_ctx) _ctx = new (window.AudioContext || window.webkitAudioContext)();
    if (_ctx.state === 'suspended') _ctx.resume();
    return _ctx;
  }

  function brownBuf(ac, secs = 6) {
    const n = ac.sampleRate * secs;
    const buf = ac.createBuffer(2, n, ac.sampleRate);
    for (let ch = 0; ch < 2; ch++) {
      const d = buf.getChannelData(ch);
      let last = 0;
      for (let i = 0; i < n; i++) {
        const w = Math.random() * 2 - 1;
        d[i] = (last + 0.02 * w) / 1.02;
        last = d[i];
        d[i] *= 3.5;
      }
    }
    return buf;
  }

  function whiteBuf(ac, secs = 6) {
    const n = ac.sampleRate * secs;
    const buf = ac.createBuffer(2, n, ac.sampleRate);
    for (let ch = 0; ch < 2; ch++) {
      const d = buf.getChannelData(ch);
      for (let i = 0; i < n; i++) d[i] = Math.random() * 2 - 1;
    }
    return buf;
  }

  function pinkBuf(ac, secs = 6) {
    const n = ac.sampleRate * secs;
    const buf = ac.createBuffer(2, n, ac.sampleRate);
    for (let ch = 0; ch < 2; ch++) {
      const d = buf.getChannelData(ch);
      let b0=0,b1=0,b2=0,b3=0,b4=0,b5=0,b6=0;
      for (let i = 0; i < n; i++) {
        const w = Math.random() * 2 - 1;
        b0=0.99886*b0+w*0.0555179; b1=0.99332*b1+w*0.0750759;
        b2=0.96900*b2+w*0.1538520; b3=0.86650*b3+w*0.3104856;
        b4=0.55000*b4+w*0.5329522; b5=-0.7616*b5-w*0.0168980;
        d[i] = (b0+b1+b2+b3+b4+b5+b6+w*0.5362)*0.11;
        b6 = w*0.115926;
      }
    }
    return buf;
  }

  function mkSrc(ac, buf) {
    const s = ac.createBufferSource();
    s.buffer = buf; s.loop = true; return s;
  }

  function mkFilter(ac, type, freq, q = 1) {
    const f = ac.createBiquadFilter();
    f.type = type; f.frequency.value = freq; f.Q.value = q; return f;
  }

  function mkGain(ac, v) {
    const g = ac.createGain(); g.gain.value = v; return g;
  }

  function mkLFO(ac, freq, depth) {
    const osc = ac.createOscillator();
    osc.type = 'sine'; osc.frequency.value = freq;
    const g = mkGain(ac, depth);
    osc.connect(g);
    return { osc, gain: g };
  }

  function pipe(nodes, dest) {
    for (let i = 0; i < nodes.length - 1; i++) nodes[i].connect(nodes[i+1]);
    nodes[nodes.length-1].connect(dest);
    return nodes;
  }

  const GENERATORS = {
    rain(ac, dest, p = {}) {
      const s = mkSrc(ac, brownBuf(ac));
      const hp = mkFilter(ac, 'highpass', p.filter_freq || 600);
      const lp = mkFilter(ac, 'lowpass', 10000);
      const g = mkGain(ac, p.gain || 0.55);
      const wave = mkLFO(ac, p.lfo_rate || 0.05, p.lfo_depth || 0.08);
      wave.gain.connect(g.gain);
      pipe([s, hp, lp, g], dest);
      s.start(); wave.osc.start();
      return [s, hp, lp, g, wave.osc, wave.gain];
    },

    ocean(ac, dest, p = {}) {
      const s = mkSrc(ac, pinkBuf(ac));
      const lp = mkFilter(ac, 'lowpass', p.filter_freq || 700);
      const g = mkGain(ac, p.gain || 0.5);
      const wave = mkLFO(ac, p.lfo_rate || 0.07, p.lfo_depth || 0.22);
      wave.gain.connect(g.gain);
      pipe([s, lp, g], dest);
      s.start(); wave.osc.start();
      return [s, lp, g, wave.osc, wave.gain];
    },

    forest(ac, dest, p = {}) {
      const s = mkSrc(ac, whiteBuf(ac));
      const bp = mkFilter(ac, 'bandpass', p.filter_freq || 1800, 0.6);
      const lp = mkFilter(ac, 'lowpass', 5000);
      const g = mkGain(ac, p.gain || 0.28);
      const wind = mkLFO(ac, p.lfo_rate || 0.12, p.lfo_depth || 0.1);
      wind.gain.connect(g.gain);
      pipe([s, bp, lp, g], dest);
      s.start(); wind.osc.start();
      return [s, bp, lp, g, wind.osc, wind.gain];
    },

    fire(ac, dest, p = {}) {
      const s = mkSrc(ac, brownBuf(ac));
      const hp = mkFilter(ac, 'highpass', 60);
      const lp = mkFilter(ac, 'lowpass', p.filter_freq || 500);
      const g = mkGain(ac, p.gain || 0.65);
      const flicker = mkLFO(ac, p.lfo_rate || 0.25, p.lfo_depth || 0.12);
      flicker.gain.connect(g.gain);
      pipe([s, hp, lp, g], dest);
      s.start(); flicker.osc.start();
      return [s, hp, lp, g, flicker.osc, flicker.gain];
    },

    space(ac, dest, p = {}) {
      const base = p.filter_freq ? p.filter_freq / 2 : 55;
      const freqs = [base, base*1.5, base*2, base*1.007, base*1.507];
      const g = mkGain(ac, p.gain || 0.13);
      const oscs = freqs.map(f => {
        const o = ac.createOscillator();
        o.type = 'sine'; o.frequency.value = f;
        o.connect(g); o.start(); return o;
      });
      g.connect(dest);
      const ns = mkSrc(ac, whiteBuf(ac));
      const nlp = mkFilter(ac, 'lowpass', 180);
      const ng = mkGain(ac, 0.04);
      pipe([ns, nlp, ng], dest);
      ns.start();
      return [...oscs, g, ns, nlp, ng];
    },

    storm(ac, dest, p = {}) {
      const s1 = mkSrc(ac, brownBuf(ac));
      const s2 = mkSrc(ac, brownBuf(ac));
      const lp = mkFilter(ac, 'lowpass', p.filter_freq || 300);
      const g1 = mkGain(ac, p.gain || 0.75);
      const g2 = mkGain(ac, (p.gain || 0.75) * 0.6);
      const surge = mkLFO(ac, p.lfo_rate || 0.04, p.lfo_depth || 0.28);
      surge.gain.connect(g1.gain);
      pipe([s1, g1], dest);
      pipe([s2, lp, g2], dest);
      s1.start(); s2.start(); surge.osc.start();
      return [s1, s2, lp, g1, g2, surge.osc, surge.gain];
    },

    cafe(ac, dest, p = {}) {
      const s = mkSrc(ac, whiteBuf(ac));
      const bp1 = mkFilter(ac, 'bandpass', p.filter_freq || 500, 0.4);
      const bp2 = mkFilter(ac, 'bandpass', (p.filter_freq || 500) * 2.8, 0.6);
      const g = mkGain(ac, p.gain || 0.18);
      const murmur = mkLFO(ac, p.lfo_rate || 0.35, p.lfo_depth || 0.06);
      murmur.gain.connect(g.gain);
      s.connect(bp1); s.connect(bp2);
      bp1.connect(g); bp2.connect(g); g.connect(dest);
      s.start(); murmur.osc.start();
      return [s, bp1, bp2, g, murmur.osc, murmur.gain];
    },
  };

  const EMOTION_MOOD_MAP = {
    rain:   ['sadness','grief','peaceful','anxiety','relief'],
    ocean:  ['longing','hope','excitement','joy','wonder'],
    forest: ['tenderness','hope','relief','peaceful','nostalgia'],
    fire:   ['dread','fear','restlessness','pride','anger'],
    space:  ['awe','wonder','confusion','nostalgia','longing'],
    storm:  ['anxiety','restlessness','fear','frustration','dread'],
    cafe:   ['nostalgia','tenderness','joy','longing','warmth'],
  };

  return {
    current: null,

    play(mood, params = {}) {
      this.stop();
      const ac = getCtx();
      _master = mkGain(ac, 0);
      _master.connect(ac.destination);
      _master.gain.setTargetAtTime(1, ac.currentTime, 0.8);
      _nodes = (GENERATORS[mood] || GENERATORS.rain)(ac, _master, params);
      _playing = true;
      _current = mood;
      this.current = mood;
    },

    pause() {
      if (!_master) return;
      _master.gain.setTargetAtTime(0, getCtx().currentTime, 0.4);
      _playing = false;
    },

    resume() {
      if (!_master) return;
      const ac = getCtx();
      _master.gain.setTargetAtTime(1, ac.currentTime, 0.4);
      _playing = true;
    },

    stop() {
      if (!_master) return;
      const ac = getCtx();
      const m = _master;
      const ns = _nodes;
      m.gain.setTargetAtTime(0, ac.currentTime, 0.3);
      setTimeout(() => {
        ns.forEach(n => { try { n.stop?.(); n.disconnect?.(); } catch(e){} });
        try { m.disconnect(); } catch(e) {}
      }, 1200);
      _master = null; _nodes = []; _playing = false; _current = null;
      this.current = null;
    },

    isPlaying() { return _playing; },

    emotionsToMood(emotions = []) {
      const lower = emotions.map(e => e.toLowerCase());
      const scores = {};
      for (const [mood, list] of Object.entries(EMOTION_MOOD_MAP)) {
        scores[mood] = lower.filter(e => list.includes(e)).length;
      }
      const best = Object.entries(scores).sort((a, b) => b[1] - a[1])[0];
      return best[1] > 0 ? best[0] : 'space';
    },
  };
})();
