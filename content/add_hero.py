"""Give the four documents the hero the About page has: cycling words and a
sticky note that keeps itself up to date.

The About page's hero cycles a word ("clarity / evidence / numbers ...") and
carries a ledger card that counts live. The four documents had a plain title,
so they now open the same way, each with a sticky note that shows something
true at the moment it is read rather than something written in October.
"""
import re
from bs4 import BeautifulSoup

SPEC = {
    "contact-milled-edge": dict(
        kicker="Contact · the desk",
        lead="Say", words=["hello", "namaste", "bonjour", "salaam"],
        tail="to the desk.",
        lede="A question about a page, a correction, a topic worth covering — every message is read by the "
             "person who writes the publication.",
        note_title="The desk, right now",
        note_rows=[("Publisher’s local time", "clock"), ("Reply window", "2–3 working days"),
                   ("Read by", "a person, not a robot"), ("Advice", "not given, ever")],
        foot="Both inboxes are monitored."),
    "privacy-policy-milled-edge": dict(
        kicker="Legal · privacy",
        lead="Your data,", words=["your rules.", "your call.", "your choice."],
        tail="",
        lede="What this site collects, why, and what you can do about it — with the one optional service "
             "named and the defaults stated honestly.",
        note_title="What is switched on",
        note_rows=[("Google Analytics 4", "consent"), ("Advertising network", "none"),
                   ("Newsletter", "none"), ("Data sold", "never")],
        foot="Nothing loads until you allow it."),
    "financial-disclaimer-milled-edge": dict(
        kicker="Legal · disclaimer",
        lead="The fine print, in", words=["plain sight.", "broad daylight.", "black and white."],
        tail="",
        lede="What this publication is, what it is not, and the boundary that applies to every figure on "
             "the site.",
        note_title="Today, on this page",
        note_rows=[("Education", "not advice"), ("Adviser relationship", "none created"),
                   ("Page reviewed", "date"), ("Governed by", "Indian law")],
        foot="Markets can and do lose money."),
    "terms-milled-edge": dict(
        kicker="Legal · terms",
        lead="Terms, in", words=["plain language.", "short clauses.", "clear words."],
        tail="",
        lede="The practical boundaries for reading, quoting and using this site — short enough to finish, "
             "specific enough to mean something.",
        note_title="The short version",
        note_rows=[("Reading the site", "accepts these terms"), ("Content", "education, not advice"),
                   ("Availability", "as available"), ("Cost to read", "nothing")],
        foot="Nothing to pay, nothing to sign."),
}

CSS = """
<style id="meHeroStyle">
.me-hero{position:relative;overflow:hidden;margin:8px 0 26px;padding:clamp(20px,3.2vw,38px);
 border:1px solid #EADCC8;border-radius:22px;background:linear-gradient(178deg,#FFFDF8,#F8F0E3);
 font-family:Inter,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;color:#241610}
.me-hero *{box-sizing:border-box}
.me-hero-in{display:grid;gap:clamp(18px,3vw,34px);grid-template-columns:minmax(0,1.1fr) minmax(0,.9fr);
 align-items:start;position:relative;z-index:1}
@media (max-width:860px){.me-hero-in{grid-template-columns:1fr}}
.me-kick{display:flex;align-items:center;gap:10px;margin:0 0 12px;font:700 10.5px/1.2 Inter,Arial,sans-serif;
 letter-spacing:.2em;text-transform:uppercase;color:#9C4522}
.me-kick::before{content:"";width:24px;height:1px;background:#BC5B33}
.me-h1{margin:0 0 12px;font:600 clamp(29px,4.6vw,50px)/1.06 'Playfair Display',Georgia,serif;
 letter-spacing:-.03em;color:#241610}
.me-flip{display:inline-block;position:relative;color:#9C4522;font-family:'Parisienne','ME Script',cursive;
 font-size:1.04em;line-height:.95;min-width:4.2em;vertical-align:baseline}
.me-flip b{position:absolute;left:0;top:0;white-space:nowrap;opacity:0;font-weight:400;
 animation:meFlip 12s infinite}
.me-flip b:first-child{position:relative;animation-name:meFlipFirst}
@keyframes meFlip{0%,2%{opacity:0}6%,22%{opacity:1}26%,100%{opacity:0}}
@keyframes meFlipFirst{0%{opacity:1}22%{opacity:1}26%,100%{opacity:0}}
.me-lede{margin:0 0 16px;font:400 clamp(15px,1.3vw,16.6px)/1.66 Inter,Arial,sans-serif;color:#3C2A1E;max-width:52ch}
.me-note{background:#fff;border:1px solid #EADCC8;border-radius:16px;padding:15px 16px 13px;
 box-shadow:0 24px 48px -42px rgba(36,22,16,.7);position:relative}
.me-note::before{content:"";position:absolute;left:16px;top:-7px;width:46px;height:12px;
 background:linear-gradient(180deg,rgba(240,192,132,.85),rgba(240,192,132,.25));border-radius:2px;
 transform:rotate(-2.2deg)}
.me-note-t{margin:2px 0 10px;padding-bottom:8px;border-bottom:1px solid #F1E7D8;
 font:400 20px/1.15 'Parisienne','ME Script',cursive;color:#9C4522}
.me-row{display:flex;align-items:baseline;justify-content:space-between;gap:10px;padding:7px 0;
 border-bottom:1px dashed #F1E7D8;font:400 13px/1.45 Inter,Arial,sans-serif;color:#4A3225}
.me-row:last-of-type{border-bottom:0}
.me-row b{font-weight:700;color:#241610;text-align:right}
.me-live{display:inline-flex;align-items:center;gap:6px}
.me-live::before{content:"";width:6px;height:6px;border-radius:50%;background:#BC5B33;
 box-shadow:0 0 0 0 rgba(188,91,51,.5);animation:mePulse 2s infinite}
@keyframes mePulse{70%{box-shadow:0 0 0 7px rgba(188,91,51,0)}100%{box-shadow:0 0 0 0 rgba(188,91,51,0)}}
.me-note-f{margin:9px 0 0;font:600 10.5px/1.5 Inter,Arial,sans-serif;letter-spacing:.1em;
 text-transform:uppercase;color:#8A7358}
@media (prefers-reduced-motion:reduce){
 .me-flip b{animation:none;opacity:0}.me-flip b:first-child{opacity:1}
 .me-live::before{animation:none}
}
</style>
"""

JS = """
<script>
/* the sticky note shows what is true when it is read, not what was true on the
   day the page was written */
(function(){
 function clock(){
   try{
     return new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Kolkata',hour:'2-digit',
       minute:'2-digit',hour12:false}).format(new Date())+' IST';
   }catch(e){ return 'IST'; }
 }
 var d=new Date();
 var date=new Intl.DateTimeFormat('en-GB',{day:'numeric',month:'short',year:'numeric'}).format(d);
 var consent='off until you allow it';
 try{ var v=localStorage.getItem('me.ga.consent');
      consent = v==='yes' ? 'on, by your choice' : (v==='no' ? 'declined by you' : 'off until you allow it');
 }catch(e){}
 document.querySelectorAll('[data-me-live]').forEach(function(el){
   var kind=el.getAttribute('data-me-live');
   el.textContent = kind==='clock' ? clock() : (kind==='date' ? date : (kind==='consent' ? consent : el.textContent));
 });
})();
</script>
"""


def hero_html(s):
    words = "".join("<b>%s</b>" % w for w in s["words"])
    rows = []
    for label, value in s["note_rows"]:
        if value in ("clock", "date", "consent"):
            rows.append('<div class="me-row"><span>%s</span>'
                        '<b class="me-live" data-me-live="%s">&nbsp;</b></div>' % (label, value))
        else:
            rows.append('<div class="me-row"><span>%s</span><b>%s</b></div>' % (label, value))
    tail = (" " + s["tail"]) if s["tail"] else ""
    return ('<div class="me-hero"><div class="me-hero-in"><div>'
            '<p class="me-kick">%s</p>'
            '<h1 class="me-h1">%s <span class="me-flip">%s</span>%s</h1>'
            '<p class="me-lede">%s</p>'
            '</div><div class="me-note">'
            '<p class="me-note-t">%s</p>%s'
            '<p class="me-note-f">%s</p>'
            '</div></div></div>' % (s["kicker"], s["lead"], words, tail, s["lede"],
                                    s["note_title"], "".join(rows), s["foot"]))


for slug, spec in SPEC.items():
    path = "/home/user/build/pages/%s.html" % slug
    html = open(path, encoding="utf-8").read()
    soup = BeautifulSoup(html, "html.parser")
    root = soup.find("div", class_="post-body")
    # drop the old plain title block so the hero is the only opening
    for el in root.select("h1"):
        el.decompose()
    for el in root.select(".me-hero, #meHeroStyle"):
        el.decompose()
    if soup.find("style", id="meHeroStyle"):
        soup.find("style", id="meHeroStyle").decompose()
    root.insert(0, BeautifulSoup(CSS, "html.parser"))
    main = root.find("main") or root
    first = main.find(True)
    frag = BeautifulSoup(hero_html(spec) + JS, "html.parser")
    if first:
        first.insert_before(BeautifulSoup(hero_html(spec), "html.parser"))
    else:
        main.append(BeautifulSoup(hero_html(spec), "html.parser"))
    root.append(BeautifulSoup(JS, "html.parser"))
    open(path, "w", encoding="utf-8").write(str(root))
    print("hero added:", slug, len(str(root)), "bytes")
