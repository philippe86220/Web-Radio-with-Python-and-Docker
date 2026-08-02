from flask import Flask, render_template

app = Flask(__name__)

# Liste de stations de radio (flux publics en streaming direct)
STATIONS = [
    {"name": "FIP", "url": "https://icecast.radiofrance.fr/fip-midfi.mp3"},
    {"name": "France Inter", "url": "https://icecast.radiofrance.fr/franceinter-midfi.mp3"},
    {"name": "France Info", "url": "https://icecast.radiofrance.fr/franceinfo-midfi.mp3"},
    {"name": "France Musique", "url": "https://icecast.radiofrance.fr/francemusique-midfi.mp3"},
    {"name": "Nova", "url": "https://novazz.ice.infomaniak.ch/novazz-128.mp3"},
    {"name": "Nostalgie", "url": "https://streaming.nrjaudio.fm/oug7girb92oc?origine=fluxradios"},
    {"name": "mradio", "url": "http://mfmwr-007.ice.infomaniak.ch/mfmwr-007.mp3"},
    {"name": "Jazz-Radio", "url": "http://jazzradio.ice.infomaniak.ch/jazzradio-high.mp3"},
    {"name": "radio-classique", "url": "http://radioclassique.ice.infomaniak.ch/radioclassique-high.mp3"},
    {"name": "alouette-Vienne", "url": "http://alouette-poitiers.ice.infomaniak.ch/alouette-poitiers-128.mp3"},
    {"name": "alouette-Gironde", "url": "http://alouette-larochelle.ice.infomaniak.ch/alouette-larochelle-128.mp3"},
    {"name": "RTL", "url": "http://icecast.rtl.fr/rtl-1-44-128?listen=webCwsBCggNCQgLDQUGBAcGBg"}
]

 
 
@app.route("/")
def index():
    return render_template("index.html", stations=STATIONS)


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
