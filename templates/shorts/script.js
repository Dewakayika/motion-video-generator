// Content of the short. Edit this file only; short.html is the engine.
//
// Timing: give each scene `seg: n` (starts with spoken line n from segments.js),
// `seg: [n, m]` (lines n..m), or explicit seconds `t: 3.2, end: 6`.
// A scene runs until the next scene in its lane starts. Captions (`cap`/`title`) are one lane,
// visuals (everything else) the other, so a caption and a visual can be on screen together.
// Any visual can carry its own caption: { type:'bignum', ..., cap:{ lead:'...', key:'...' } }.
//
// Scene types
//   cap     { lead, key, hl, pos }      small lead line + big bold keyword(s); hl = orange box; pos = 'top' | 'mid'
//   title   { lead, key, hl }           same as cap, centred (hooks)
//   bignum  { value, unit, kicker, badges:[..] }   counts up when value is a number
//   stat    { value, label }            dark card, big orange number
//   compare { items:[{ icon, name, value, sub }] } 2-3 cards side by side
//   pills   { title, items:[..], ok }   "NOT RECOMMENDED FOR" style list (ok:true = green ticks)
//   badges  { items:[{ value, label }] } round recap badges
//   list    { title, items:[..], icons:[..], gap }  numbered steps appearing one by one
//   doc     { img, marks:[y,..] }       document / notice B-roll; marks = highlighter bars (px from top of page)
//   broll   { src }                     full-screen image or video
//   hero    { icon }                    big emoji
//   cta     { icon, text, sub }         closing call to action
window.SCRIPT = {
  brand: '@yourhandle',
  look: 'warm',            // 'warm' (beige studio) | 'dark'
  audio: 'voice.mp3',      // voiceover; length sets the video length
  presenter: null,         // 'presenter.mp4' for a version with a person on camera
  presenterOffset: 0,      // seconds to skip at the start of presenter.mp4
  scenes: [
    { t: 0.0,  type: 'title', lead: 'Want videos like this', key: 'IN MINUTES?', hl: false },
    { t: 0.0,  type: 'hero', icon: '🎬' },
    { t: 3.0,  type: 'cap', lead: 'Every line becomes a', key: 'BOLD CAPTION', hl: true },
    { t: 6.0,  type: 'bignum', value: '400', unit: 'mg / day', kicker: 'Big numbers', badges: ['Source A', 'Source B'],
               cap: { lead: 'Numbers', key: 'COUNT UP' } },
    { t: 10.0, type: 'stat', value: '17', label: 'Stat cards for one key fact' },
    { t: 13.0, type: 'compare', items: [{ icon: '🥤', name: 'Option A', value: '32 / 100' }, { icon: '🧃', name: 'Option B', value: '30 / 100' }],
               cap: { lead: 'Side-by-side', key: 'COMPARISONS' } },
    { t: 17.0, type: 'doc', marks: [300, 420], cap: { lead: 'Show the', key: 'SOURCE', hl: true } },
    { t: 21.0, type: 'pills', title: 'Not for', items: ['Children', 'Pregnant women', 'Diabetics'] },
    { t: 25.0, type: 'badges', items: [{ value: '400', label: 'per day' }, { value: '100', label: 'per can' }, { value: '2', label: 'max' }],
               cap: { lead: 'Just remember', key: '3 NUMBERS' } },
    { t: 29.0, type: 'cta', icon: '👇', text: 'Comment your number', sub: 'Follow for more' },
    { t: 32.5, end: 33, type: 'hero', icon: '✨' },
  ],
};
