/* found.js: how did this visitor find us?
 * Remembers, in this browser only, the visitor's first and latest arrival (where they came from and the page they
 * landed on). Nothing is sent anywhere until they send an enquiry, and then it goes with the enquiry so we can see
 * which search, AI assistant, advert or link brought them. No cookies, no ID, cleared after 90 days.
 * Same file on rutlanddriveways.co.uk, miltonkeynesdriveways.co.uk and dimensure.co.uk. */
(function () {
  var KEY = 'foundVia1', MAX_AGE = 90 * 864e5, MAX_LEN = 200;
  var store = {
    get: function () { try { return JSON.parse(window.localStorage.getItem(KEY) || 'null'); } catch (e) { return null; } },
    set: function (v) { try { window.localStorage.setItem(KEY, JSON.stringify(v)); } catch (e) {} }
  };
  var cut = function (s) { return String(s || '').slice(0, MAX_LEN); };
  var host = function (u) { try { return new URL(u).hostname.toLowerCase().replace(/^www\./, ''); } catch (e) { return ''; } };
  var self = location.hostname.toLowerCase().replace(/^www\./, '');

  // Turn a referrer + query string into a plain-English source.
  function channel(refHost, q) {
    var src = (q.get('utm_source') || '').toLowerCase(), med = (q.get('utm_medium') || '').toLowerCase();
    if (q.get('gclid') || q.get('gbraid') || q.get('wbraid') || (src === 'google' && /cpc|ppc|paid/.test(med))) return 'Google Ads';
    if (q.get('msclkid')) return 'Microsoft (Bing) Ads';
    if (/^L\d{3,6}$/i.test(q.get('ref') || '')) return 'Planning letter QR code';
    if (/chatgpt|openai/.test(src) || /chatgpt\.com|openai\.com/.test(refHost)) return 'ChatGPT';
    if (/perplexity/.test(src + refHost)) return 'Perplexity';
    if (/gemini/.test(src) || refHost === 'gemini.google.com') return 'Google Gemini';
    if (/copilot/.test(src + refHost)) return 'Microsoft Copilot';
    if (/claude/.test(src) || refHost === 'claude.ai') return 'Claude';
    if (/gbp|google_business|business_profile|gmb/.test(src + med)) return 'Google Business Profile';
    if (q.get('fbclid') || /facebook|^fb$/.test(src) || /(^|\.)facebook\.com$|^fb\.me$/.test(refHost)) return 'Facebook';
    if (/instagram/.test(src + refHost)) return 'Instagram';
    if (/linkedin|lnkd\.in/.test(src + refHost)) return 'LinkedIn';
    if (/nextdoor/.test(src + refHost)) return 'Nextdoor';
    if (src) return 'Campaign link: ' + src + (med ? ' / ' + med : '');
    if (/(^|\.)google\.[a-z.]+$/.test(refHost)) return refHost.indexOf('maps.') === 0 ? 'Google Maps' : 'Google search';
    if (refHost === 'bing.com' || /\.bing\.com$/.test(refHost)) return 'Bing search';
    if (/duckduckgo|yahoo|ecosia|search\.brave|startpage|yandex/.test(refHost)) return 'Search engine: ' + refHost;
    if (/checkatrade|mybuilder|trustatrade|ratedpeople|houzz|yell|bark\.com|trustpilot|scoot|cylex|freeindex|thomsonlocal|192\.com/.test(refHost)) return 'Directory or review site: ' + refHost;
    if (/rutlanddriveways|miltonkeynesdriveways|dimensure|buildbro/.test(refHost)) return 'Our other website: ' + refHost;
    if (refHost) return 'Link on another website: ' + refHost;
    return 'Direct: typed the address, a bookmark, or a link in an app, email or text';
  }

  var now = Date.now(), q, ref = document.referrer || '', refHost = host(ref);
  try { q = new URLSearchParams(location.search); } catch (e) { q = { get: function () { return null; } }; }
  var internal = refHost && refHost === self;
  var tagged = /utm_|gclid|gbraid|wbraid|msclkid|fbclid|[?&]ref=L/i.test(location.search);

  var d = store.get();
  if (!d || !d.first || now - (d.first.at || 0) > MAX_AGE) d = { first: null, last: null, pages: 0, visits: 0 };

  // A new arrival is any page view that didn't come from one of our own pages.
  if (!internal || tagged || !d.first) {
    var touch = {
      at: now,
      channel: channel(refHost, q),
      landing: cut(location.pathname),
      referrer: cut(refHost ? ref.split('?')[0] : ''),
      campaign: cut([q.get('utm_campaign'), q.get('utm_term')].filter(Boolean).join(' / '))
    };
    if (!d.first) d.first = touch;
    d.last = touch;
    d.visits = (d.visits || 0) + 1;
  }
  d.pages = (d.pages || 0) + 1;
  store.set(d);

  var when = function (t) {
    try { return new Date(t).toLocaleString('en-GB', { timeZone: 'Europe/London', day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }); }
    catch (e) { return new Date(t).toISOString(); }
  };
  var describe = function (t) {
    return t.channel + ' | landed on ' + (t.landing || '/') + (t.referrer ? ' | from ' + t.referrer : '') + (t.campaign ? ' | ' + t.campaign : '') + ' | ' + when(t.at);
  };

  // Called by the enquiry forms. Returns plain fields for the email and the hub.
  window.foundVia = function () {
    var f = d.first || {}, l = d.last || f, same = f.at === l.at;
    return {
      found_channel: f.channel || '',
      found_first: f.channel ? describe(f) : '',
      found_latest: same ? '' : describe(l),
      found_landing: f.landing || '',
      found_referrer: f.referrer || '',
      found_visits: String(d.visits || 1),
      found_pages: String(d.pages || 1)
    };
  };
})();
