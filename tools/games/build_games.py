"""Rubrique Jeux du site : /games/ (anglais) et /fr/jeux/ (français), une page par jeu, games/sitemap.xml.

python tools/games/build_games.py   (depuis la racine du dépôt ; aucune connexion réseau)
Les jeux eux-mêmes ne sont pas hébergés ici : chaque page renvoie vers les portails où le jeu est en ligne.
Ajouter un portail : compléter PLAY[jeu] (le premier lien est le bouton principal).
Images : assets/img/games/ (couverture 1280×720 et captures 960×540, en JPEG).
"""
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "site"))
from chrome import MAIL, SITE, esc, footer, header, hreflang_links  # noqa: E402

LANGS = ("en", "fr")
BASE = {"en": "/games/", "fr": "/fr/jeux/"}
GAMES = ("monster-steps", "counterpoise", "equipoise")
SHOTS = {"monster-steps": 3, "counterpoise": 4, "equipoise": 3}
NAMES = {"monster-steps": "Monster Steps", "counterpoise": "Counterpoise", "equipoise": "Equipoise"}
PLAY = {
    "monster-steps": [("Playgama", "https://playgama.ai/play/vky5ziuu5m3eor")],
    "counterpoise": [("Playgama", "https://playgama.ai/play/ve3y5vovpfap7n"), ("itch.io", "https://jovianlabs.itch.io/counterpoise")],
    "equipoise": [("Playgama", "https://playgama.ai/play/phiyufgxws5ylk"), ("itch.io", "https://jovianlabs.itch.io/equipoise")],
}

T = {
    "en": dict(
        title="Games · Jovian Labs", desc="Free puzzle games for the browser by Jovian Labs: Monster Steps, Counterpoise and Equipoise. Mouse or touch, no sign-in.",
        h1="Games", lede="Calm, clever puzzle games for the browser. Free to play with a mouse or a finger, nothing to install, no sign-in.",
        facts=["Every level tested to be solvable", "Mouse, touch or keyboard", "English and French"],
        play="Play on {p}", more="About the game", how_h="How to play", feat_h="Features", shots_h="Screenshots",
        where_h="Where to play", fair="Fair by design: the pieces and puzzles never change to push you toward an ad.",
        back="All games", contact="Questions or a bug? Write to {mail}.",
        games={
            "monster-steps": dict(
                k="Halloween puzzle", tag="A turn-based Halloween escape: every step you take, the monsters take theirs.",
                desc="Lead a little witch to the glowing door, one tile at a time, while a mummy, a werewolf, a vampire and Anubis close in. "
                     "After each of your steps, every monster takes its own: red claw marks show the tiles where you would be caught, "
                     "and footprints show where each monster is about to go. Think ahead, wait at the right moment, "
                     "and lure two monsters into each other to knock them out.",
                how=[("Step", "Tap a tile next to you, swipe or use the arrow keys. Tap yourself to wait a turn."),
                     ("Watch", "Red claws mark the deadly tiles. The mummy and the vampire take one step, the werewolf two; Anubis charges along his line."),
                     ("Escape", "Reach the door. Never caught, no hint and within par: three stars.")],
                feat=["33 levels over four haunted nights: graveyard, dark woods, castle and the tomb of Anubis",
                      "Four monsters with their own rules, introduced one at a time",
                      "Undo any step, even after being gobbled",
                      "Every level checked by a solver; par is the shortest way out"],
                alt="Monster Steps: a little witch with a pumpkin lantern surrounded by a mummy, a werewolf, a vampire and Anubis under a full moon"),
            "counterpoise": dict(
                k="Block puzzle", tag="A block puzzle on a balancing board: fill rows and columns, but don't tip it over.",
                desc="Drag gem blocks onto an 8×8 grid and fill a row or a column to clear it. The board rests on a golden pivot: "
                     "the farther a block sits from the centre, the more it weighs, and a move that would tip the board too far is refused. "
                     "Hold a piece over the board and it leans before you let go.",
                how=[("Place", "Drag a piece from the tray onto the board. Three pieces per hand, no rotation."),
                     ("Clear", "Fill a whole row or column to clear it. Lucky charms trapped in crystal blocks fly free."),
                     ("Balance", "Blocks far from the centre weigh more. Clear the heavy side to bring the board back to level.")],
                feat=["40 Journey levels around the moons of Jupiter, with a short playable tutorial",
                      "Classic endless mode and a Daily challenge with the same pieces for everyone",
                      "The board leans under the piece you hold, and weight marks show how heavy each column is",
                      "Fair draw: the pieces never depend on your board"],
                alt="Counterpoise: a tilted puzzle board full of gem blocks resting on a golden pivot"),
            "equipoise": dict(
                k="Logic puzzle", tag="A relaxing logic puzzle: hang the weights until every mobile balances.",
                desc="Drag numbered gem weights onto golden hooks until every bar hangs level. A bar balances when weight × distance "
                     "is the same on both sides: the numbers above each bar do the maths for you and turn green when they match.",
                how=[("Hang", "Drag a weight from the tray onto an empty hook, or tap a weight then a hook."),
                     ("Read", "Each bar shows weight × distance on both sides; green means it balances."),
                     ("Solve", "Level every bar. Solve within par and without a hint for three stars.")],
                feat=["40 levels in 4 chapters, from a single bar to deep nested mobiles with spare weights",
                      "A new Daily puzzle every day, the same for everyone",
                      "Undo, restart and hints whenever you are stuck",
                      "Calm ambient music and effects, each can be switched off"],
                alt="Equipoise: a golden hanging mobile with numbered gem weights in front of Jupiter"),
        }),
    "fr": dict(
        title="Jeux · Jovian Labs", desc="Jeux de réflexion gratuits dans le navigateur, par Jovian Labs : Monster Steps, Counterpoise et Equipoise. À la souris ou au doigt, sans inscription.",
        h1="Jeux", lede="Des jeux de réflexion calmes et malins, dans le navigateur. Gratuits, à la souris ou au doigt, rien à installer, sans inscription.",
        facts=["Chaque niveau vérifié soluble", "Souris, doigt ou clavier", "En français et en anglais"],
        play="Jouer sur {p}", more="Le jeu en détail", how_h="Comment jouer", feat_h="Ce qu'il propose", shots_h="Captures",
        where_h="Où jouer", fair="Loyal par principe : les pièces et les énigmes ne changent jamais pour vous pousser vers une pub.",
        back="Tous les jeux", contact="Une question ou un bug ? Écrivez à {mail}.",
        games={
            "monster-steps": dict(
                k="Puzzle d'Halloween", tag="Une évasion au tour par tour pour Halloween : à chaque pas que vous faites, les monstres font le leur.",
                desc="Guidez une petite sorcière jusqu'à la porte lumineuse, case par case, pendant qu'une momie, un loup-garou, un vampire "
                     "et Anubis se rapprochent. Après chacun de vos pas, chaque monstre fait le sien : des griffes rouges montrent les cases "
                     "où l'on vous attraperait, et des empreintes montrent où chaque monstre va aller. Anticipez, attendez au bon moment, "
                     "et faites se percuter deux monstres pour les assommer.",
                how=[("Avancer", "Touchez une case voisine, glissez ou utilisez les flèches. Touchez-vous pour attendre un tour."),
                     ("Observer", "Les griffes rouges marquent les cases mortelles. La momie et le vampire font un pas, le loup-garou deux ; Anubis fonce dans sa ligne."),
                     ("S'évader", "Atteignez la porte. Jamais attrapé, sans indice et dans le par : trois étoiles.")],
                feat=["33 niveaux sur quatre nuits hantées : cimetière, bois sombre, château et tombeau d'Anubis",
                      "Quatre monstres aux règles différentes, présentés un par un",
                      "Annuler n'importe quel pas, même après s'être fait croquer",
                      "Chaque niveau vérifié par un solveur ; le par est le plus court chemin"],
                alt="Monster Steps : une petite sorcière avec une lanterne citrouille, entourée d'une momie, d'un loup-garou, d'un vampire et d'Anubis sous la pleine lune"),
            "counterpoise": dict(
                k="Puzzle de blocs", tag="Un puzzle de blocs sur un plateau en équilibre : remplissez lignes et colonnes sans le faire basculer.",
                desc="Glissez des blocs « gemmes » sur une grille de 8 × 8 et remplissez une ligne ou une colonne pour l'effacer. "
                     "Le plateau repose sur un pivot doré : plus un bloc est loin du centre, plus il pèse, et une pose qui ferait trop "
                     "pencher le plateau est refusée. Tenez une pièce au-dessus du plateau : il penche avant même que vous la lâchiez.",
                how=[("Poser", "Glissez une pièce du plateau de réserve vers la grille. Trois pièces par main, sans rotation."),
                     ("Effacer", "Une ligne ou une colonne pleine s'efface. Les porte-bonheur pris dans le cristal s'envolent."),
                     ("Équilibrer", "Loin du centre, les blocs pèsent plus. Effacez le côté lourd pour remettre le plateau à niveau.")],
                feat=["40 niveaux de Voyage autour des lunes de Jupiter, avec un court tutoriel joué",
                      "Mode Classique sans fin et Défi du jour, avec les mêmes pièces pour tout le monde",
                      "Le plateau penche sous la pièce tenue, et des repères montrent le poids de chaque colonne",
                      "Tirage loyal : les pièces ne dépendent jamais de votre plateau"],
                alt="Counterpoise : un plateau de puzzle penché, rempli de blocs « gemmes », posé sur un pivot doré"),
            "equipoise": dict(
                k="Énigme de logique", tag="Une énigme de logique apaisante : accrochez les poids jusqu'à ce que chaque mobile soit à l'équilibre.",
                desc="Glissez des poids numérotés sur les crochets dorés jusqu'à ce que chaque barre soit horizontale. Une barre est à "
                     "l'équilibre quand poids × distance est le même des deux côtés : les nombres au-dessus de chaque barre font le calcul "
                     "pour vous et passent au vert quand c'est égal.",
                how=[("Accrocher", "Glissez un poids sur un crochet libre, ou touchez un poids puis un crochet."),
                     ("Lire", "Chaque barre affiche poids × distance de chaque côté ; le vert veut dire équilibre."),
                     ("Résoudre", "Mettez toutes les barres à niveau. Sans indice et dans le par : trois étoiles.")],
                feat=["40 niveaux en 4 chapitres, d'une seule barre à des mobiles profonds avec des poids en trop",
                      "Un nouveau défi chaque jour, le même pour tout le monde",
                      "Annuler, recommencer et indices quand vous bloquez",
                      "Musique d'ambiance et effets apaisants, chacun désactivable"],
                alt="Equipoise : un mobile doré suspendu avec des poids numérotés devant Jupiter"),
        }),
}


def page_path(lang, game=None):
    return BASE[lang] + (f"{game}/" if game else "")


def shell(lang, path, title, desc, body, alternates, image, jsonld=None):
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ""
    return (f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{SITE}{path}">'
            f'{hreflang_links(alternates)}<link rel="icon" href="/assets/favicon.png"><link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">'
            f'<meta property="og:type" content="website"><meta property="og:title" content="{esc(title)}">'
            f'<meta property="og:description" content="{esc(desc)}"><meta property="og:image" content="{SITE}{image}">'
            f'<meta name="twitter:card" content="summary_large_image"><link rel="stylesheet" href="/assets/style.css">'
            f'<style>.shots{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px;margin:12px 0}}'
            f'.shots img{{width:100%;height:auto;border-radius:10px;border:1px solid var(--line);display:block}}'
            f'.gamehero{{border-radius:16px;overflow:hidden;border:1px solid var(--line);margin:16px 0}}.gamehero img{{display:block;width:100%;height:auto}}</style>'
            f'{ld}</head><body>{header(lang, None, alternates)}<main>{body}</main>{footer(lang)}</body></html>')


def write(path, text):
    out = ROOT / path.strip("/") / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")


def buttons(lang, game, more=False):
    t = T[lang]
    b = "".join(f'<a class="btn{" pro" if i == 0 else " ghost"}" href="{u}" rel="noopener">{esc(t["play"].format(p=p))}</a>'
                for i, (p, u) in enumerate(PLAY[game]))
    if more:
        b += f'<a class="btn ghost" href="{page_path(lang, game)}">{esc(t["more"])}</a>'
    return f"<p>{b}</p>"


def videogame_ld(lang, game):
    g = T["en"]["games"][game]
    return {"@context": "https://schema.org", "@type": "VideoGame", "name": NAMES[game], "url": f"{SITE}{page_path(lang, game)}",
            "description": T[lang]["games"][game]["tag"], "image": f"{SITE}/assets/img/games/{game}-cover.jpg",
            "genre": ["Puzzle", g["k"]], "gamePlatform": "Web browser", "operatingSystem": "Any", "applicationCategory": "Game",
            "playMode": "SinglePlayer", "inLanguage": ["en", "fr"], "isAccessibleForFree": True,
            "author": {"@type": "Organization", "name": "Jovian Labs", "url": f"{SITE}/"},
            "publisher": {"@type": "Organization", "name": "Jovian Labs", "url": f"{SITE}/"},
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "EUR", "url": PLAY[game][0][1]}}


def index(lang):
    t = T[lang]
    sections = ""
    for i, game in enumerate(GAMES):
        g = t["games"][game]
        sections += (f'<section class="prod{" flip" if i % 2 else ""}"><div><div class="k">{esc(g["k"])}</div>'
                     f'<h2>{NAMES[game]}</h2><p>{esc(g["tag"])}</p><ul>{"".join(f"<li>{esc(x)}</li>" for x in g["feat"][:3])}</ul>'
                     f'{buttons(lang, game, more=True)}</div><div class="media"><a href="{page_path(lang, game)}">'
                     f'<img src="/assets/img/games/{game}-cover.jpg" width="1280" height="720" alt="{esc(g["alt"])}" loading="lazy"></a></div></section>')
    mail = f'<a href="mailto:{MAIL}">{MAIL}</a>'
    body = (f'<section class="hero"><h1>{esc(t["h1"])}</h1><p class="lede">{esc(t["lede"])}</p>'
            f'<ul class="facts">{"".join(f"<li>{esc(x)}</li>" for x in t["facts"])}</ul></section>{sections}'
            f'<p class="small">{esc(t["fair"])} {esc(t["contact"]).replace("{mail}", mail)}</p>')
    ld = {"@context": "https://schema.org", "@type": "ItemList", "name": t["h1"],
          "itemListElement": [{"@type": "ListItem", "position": k + 1, "url": f"{SITE}{page_path(lang, g)}"} for k, g in enumerate(GAMES)]}
    write(page_path(lang), shell(lang, page_path(lang), t["title"], t["desc"], body, {l: page_path(l) for l in LANGS},
                                 "/assets/img/games/monster-steps-cover.jpg", ld))


def game_page(lang, game):
    t, g = T[lang], T[lang]["games"][game]
    name = NAMES[game]
    how = "".join(f"<div><b>{esc(a)}</b><p>{esc(b)}</p></div>" for a, b in g["how"])
    shots = "".join(f'<img src="/assets/img/games/{game}-{i}.jpg" width="960" height="540" alt="{name} – {esc(t["shots_h"])} {i}" loading="lazy">'
                    for i in range(1, SHOTS[game] + 1))
    where = "".join(f'<li><a href="{u}" rel="noopener">{esc(p)}</a></li>' for p, u in PLAY[game])
    mail = f'<a href="mailto:{MAIL}">{MAIL}</a>'
    body = (f'<p class="small"><a href="{page_path(lang)}">← {esc(t["back"])}</a></p>'
            f'<section class="hero"><div class="k">{esc(g["k"])}</div><h1>{name}</h1><p class="lede">{esc(g["tag"])}</p>'
            f'{buttons(lang, game)}</section>'
            f'<div class="gamehero"><img src="/assets/img/games/{game}-cover.jpg" width="1280" height="720" alt="{esc(g["alt"])}"></div>'
            f'<p class="lede">{esc(g["desc"])}</p>'
            f'<h2>{esc(t["how_h"])}</h2><div class="how">{how}</div>'
            f'<h2>{esc(t["feat_h"])}</h2><ul>{"".join(f"<li>{esc(x)}</li>" for x in g["feat"])}</ul>'
            f'<h2>{esc(t["shots_h"])}</h2><div class="shots">{shots}</div>'
            f'<h2>{esc(t["where_h"])}</h2><ul>{where}</ul>'
            f'<p class="small">{esc(t["fair"])} {esc(t["contact"]).replace("{mail}", mail)}</p>')
    title = f"{name} · {g['k']} · Jovian Labs"
    write(page_path(lang, game), shell(lang, page_path(lang, game), title, g["tag"], body,
                                       {l: page_path(l, game) for l in LANGS}, f"/assets/img/games/{game}-cover.jpg",
                                       videogame_ld(lang, game)))


def sitemap(today):
    urls = [page_path(l, g) for l in LANGS for g in (None,) + GAMES]
    sm = "".join(f"<url><loc>{SITE}{u}</loc><lastmod>{today}</lastmod></url>" for u in urls)
    (ROOT / "games" / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>')
    idx = ROOT / "sitemap.xml"
    s = idx.read_text()
    if "games/sitemap.xml" not in s:
        s = s.replace("</sitemapindex>", f"<sitemap><loc>{SITE}/games/sitemap.xml</loc><lastmod>{today}</lastmod></sitemap></sitemapindex>")
        idx.write_text(s)


def main():
    for _ in range(2):   # 2 passes : les liens de langue ne visent que des pages qui existent
        for lang in LANGS:
            index(lang)
            for game in GAMES:
                game_page(lang, game)
    sitemap(dt.date.today().isoformat())
    print("games pages:", ", ".join(page_path(l, g) for l in LANGS for g in (None,) + GAMES))


if __name__ == "__main__":
    main()
