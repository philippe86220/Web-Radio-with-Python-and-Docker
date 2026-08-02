# 🎧 Web Radio - Projet Docker (Python 3)

Petite application Flask qui propose un lecteur de web radio dans le navigateur,
avec plusieurs stations sélectionnables. Le projet est conteneurisé avec une
image **Python slim** pour rester léger.

## Environnement utilisé

Ce projet a été conçu et testé sous **Linux (Debian 13)**.

Il fonctionne également sous **macOS** et **Windows** avec Docker Desktop, mais les procédures d’installation de Docker peuvent différer selon le système d’exploitation.

Une fois Docker et Docker Compose installés, les commandes utilisées dans ce README restent les mêmes.

## Structure du projet

```
webradio/
├── app.py                 # Application Flask
├── requirements.txt       # Dépendances Python
├── Dockerfile             # Image Docker (python:3.13-slim + Gunicorn)
├── docker-compose.yml     # Lancement simplifié
├── templates/
│   └── index.html         # Page avec le lecteur audio
└── static/
    └── style.css           # Style de la page
```

## Lancer le projet

### Avec Docker Compose (recommandé)

```bash
cd webradio
docker compose up -d --build
```

Puis il faut ouvrir le navigateur sur : http://localhost:5000

### Avec Docker seul

```bash
docker build -t webradio .
docker run -p 5000:5000 webradio
```

### Arrêter le conteneur

```bash
docker compose down
```

## Comment ça marche

- `app.py` définit une liste de stations (nom + URL du flux MP3 direct).
- La page HTML affiche un bouton par station ; un clic charge l'URL du flux
  dans une balise `<audio>` HTML5, qui se charge de la lecture (le navigateur
  fait le streaming, pas le serveur Flask).
- En production, Gunicorn sert l'application au lieu du serveur de
  développement Flask (plus stable, plus performant).
- L'image `python:3.13-slim` est utilisée à la place de l'image standard pour
  réduire la taille finale de l'image (pas d'outils de compilation ni de
  paquets inutiles).

## Comprendre le code Flask ligne par ligne

### La route principale

```python
@app.route("/")
def index():
    return render_template("index.html", stations=STATIONS)
```

- **`@app.route("/")`** : c'est un *décorateur* Python. Il enregistre la
  fonction juste en dessous auprès de Flask comme gestionnaire de la route
  `/` (la page d'accueil). Autrement dit : "quand quelqu'un visite
  `http://.../`, exécute cette fonction".
- **`def index():`** : une fonction Python classique, appelée *vue* (view
  function) en Flask. Son nom n'a pas d'importance particulière pour Flask,
  mais elle doit obligatoirement retourner quelque chose que Flask peut
  transformer en réponse HTTP (texte, HTML, JSON...).
- **`render_template("index.html", stations=STATIONS)`** :
  - `render_template()` va chercher `index.html` dans le dossier
    `templates/` et le transforme en HTML final (via le moteur de templates
    Jinja2).
  - `stations=STATIONS` transmet la liste Python `STATIONS` au template sous
    le nom `stations`, ce qui permet d'écrire dans `index.html` :
    ```jinja
    {% for station in stations %}
            <button
                class="station-btn"
                onclick='playStation({{ station.url | tojson }}, {{ station.name | tojson }})'>
                {{ station.name }}
            </button>
            {% endfor %}
    ```
    Sans ce paramètre, le template n'aurait aucun accès à cette liste — un
    template ne voit que ce qu'on lui passe explicitement.

### La route `/health`

```python
@app.route("/health")
def health():
    return {"status": "ok"}
```

Même principe : cette route répond aux requêtes sur `/health` en renvoyant
un petit JSON `{"status": "ok"}` (Flask convertit automatiquement un
dictionnaire Python retourné par une vue en réponse JSON).

Elle ne sert pas à un humain qui navigue sur le site, mais à un système de
supervision : c'est un **endpoint de healthcheck**, une convention très
répandue en conteneurisation. Un healthcheck peut interroger régulièrement cette route afin de déterminer si l’application est opérationnelle. Docker peut alors marquer le conteneur comme `healthy` ou `unhealthy`. Certains orchestrateurs ou outils de supervision peuvent ensuite agir selon cet état.

## Comment les stations arrivent dans la page HTML (serveur vs navigateur)

C'est le point le plus important à comprendre pour un débutant : 
Dans ce projet, **il existe deux mondes bien séparés**. Flask et Jinja2 construisent la page côté serveur ; le JavaScript prend ensuite en charge les interactions dans le navigateur.

### 1. Le monde "serveur" (Python / Flask) — s'exécute UNE SEULE FOIS

Quand le navigateur charge `http://localhost:5000/`, voici ce qui se passe
côté serveur, dans `app.py` :

```python
STATIONS = [
    {"name": "FIP", "url": "https://icecast.radiofrance.fr/fip-midfi.mp3"},
    ...
]

@app.route("/")
def index():
    return render_template("index.html", stations=STATIONS)
```

`STATIONS` est une simple liste Python, qui n'existe que côté serveur, en
mémoire. Le navigateur ne la connaît pas et n'y a jamais accès directement.

`render_template()` va lire le fichier `templates/index.html`, qui contient
du code **Jinja2** (le moteur de templates de Flask) mélangé à du HTML :

```jinja
{% for station in stations %}
<button
    class="station-btn"
    onclick='playStation({{ station.url | tojson }}, {{ station.name | tojson }})'>
    {{ station.name }}
</button>
{% endfor %}
```

Jinja2 **remplace** ce code par du HTML pur, en bouclant sur la liste
`STATIONS` reçue en paramètre. Concrètement, pour 2 stations, ça donne
quelque chose comme :

```html
<button
    class="station-btn"
    onclick='playStation("https://icecast.radiofrance.fr/fip-midfi.mp3", "FIP")'>
    FIP
</button>

<button
    class="station-btn"
    onclick='playStation("https://icecast.radiofrance.fr/franceinter-midfi.mp3", "France Inter")'>
    France Inter
</button>
```

Ce texte HTML final (sans plus aucune trace de `{% %}` ni `{{ }}`) est ce que
`index()` retourne, et c'est ce que Flask envoie au navigateur dans la
réponse HTTP.

**Point clé** : ce mécanisme (Python + Jinja2) tourne **côté serveur**, une
seule fois par chargement de page. Une fois le HTML envoyé, Python n'a plus aucun rôle dans les interactions
avec les boutons de cette page. Le serveur reste toutefois actif et attend
les prochaines requêtes HTTP.

### 2. Le monde "navigateur" (HTML / JavaScript) — s'exécute à CHAQUE clic

Une fois que le navigateur a reçu le HTML ci-dessus, il ne sait plus qu'il
vient d'une liste Python : pour lui, ce ne sont que des boutons ordinaires
avec des URLs écrites en dur dans l'attribut `onclick`.

```javascript
function playStation(url, name) {
    const player = document.getElementById("audio-player");
    const nowPlaying = document.getElementById("now-playing");
    player.src = url;
    player.play()
        .then(() => {
            nowPlaying.textContent = "▶️ En écoute : " + name;
        })
        .catch((error) => {
            console.error("Erreur de lecture :", error);
            nowPlaying.textContent = "❌ Impossible de lire : " + name;
        });
}
```

Quand on clique sur un bouton, cette fonction JavaScript s'exécute
**entièrement dans le navigateur**, sans jamais recontacter Flask. Elle
prend l'URL déjà stockée dans le bouton et l'assigne au lecteur `<audio>`,
qui se connecte alors directement au flux radio (ex:
`icecast.radiofrance.fr`).

### Pourquoi cette séparation est importante

| | Templating Python/Jinja2 | JavaScript dans le navigateur |
|---|---|---|
| Où ça s'exécute | Sur le serveur (dans le conteneur Docker) | Dans le navigateur de l'utilisateur |
| Quand | Une fois, à la génération de la page | À chaque interaction (clic, etc.) |
| Accès à `STATIONS` | Oui (variable Python) | Non — seulement aux URLs déjà écrites en HTML |
| Visible en "Voir le code source" | Non (déjà transformé) | Oui, c'est exactement ce qui est envoyé |

Pour le vérifier soi-même : faire un clic droit sur la page →
**"Afficher le code source de la page"** (pas les outils de développement).
On voit les URLs des stations déjà écrites en clair dans les boutons —
aucune trace de Python, Flask ou Jinja2, seulement du HTML et du JavaScript
prêts à l'emploi. C'est la preuve que le templating s'est bien produit côté
serveur, avant l'envoi.

## Le rôle de Docker dans tout ça

Après avoir vu Flask, Jinja2 et le JavaScript, une question légitime se pose :
et Docker dans tout ça, il sert à quoi exactement ?

**Réponse courte : Docker n'a aucun rôle dans la logique de l'application.**
Il ne sait pas ce qu'est une route Flask, une station de radio ou un
template Jinja2. Il se situe à un niveau complètement différent : celui de
**l'environnement d'exécution**.

### Ce que Docker fait concrètement ici

1. **Il empaquette l'environnement** nécessaire pour faire tourner
   l'application : Python 3.13, Flask, Jinja2, Gunicorn, et un système de
   fichiers minimal (`python:3.13-slim`) — le tout dans une image figée et
   portable, décrite dans le `Dockerfile`.

2. **Il isole l'exécution** dans un conteneur, séparé du système hôte
   (ici Debian 13). Pas de conflit possible avec d'autres versions de
   Python ou d'autres projets installés sur la machine.

3. **Il améliore la reproductibilité** : sur une architecture compatible, la même image fournit les mêmes versions de Python, des bibliothèques et des fichiers applicatifs, indépendamment des logiciels déjà installés sur la machine hôte.

4. **Il gère le réseau** : la ligne `ports: - "5000:5000"` dans
   `docker-compose.yml` redirige le port 5000 de la machine hôte vers le
   port 5000 à l'intérieur du conteneur, là où Gunicorn écoute.

### Du serveur jusqu’au navigateur
```
Côté serveur
Docker
└─ Gunicorn
   └─ Flask
      └─ Jinja2
         └─ génère le HTML dynamique dans `index()`

                 ↓ réponse HTTP

Côté navigateur
HTML
└─ JavaScript
   └─ gère les clics et la lecture des stations
```

### Pour vérifier par soi-même

Si on supprimait complètement `Dockerfile` et `docker-compose.yml`,
l'application fonctionnerait exactement pareil en local avec juste
`python3 app.py`. Docker n'ajoute **aucune fonctionnalité** à
l'application — il ajoute une couche de **portabilité et d'isolation**
autour de code qui, sans lui, existerait et fonctionnerait déjà.

## Le rôle de Gunicorn dans tout ça

### Le problème que Gunicorn résout

Flask possède son propre serveur intégré, qu'on lance avec
`app.run(host="0.0.0.0", port=5000)` (visible dans le `if __name__ ==
"__main__":` de `app.py`). C'est très pratique pour développer, mais ce
serveur n'est **pas conçu pour la production** :

- Le serveur intégré de Flask est destiné au développement. Il facilite les tests et le débogage, mais il n’est pas conçu pour offrir la robustesse, la gestion des processus et les garanties attendues d’un serveur de production.
- il n'est pas optimisé pour encaisser une charge importante
- Flask lui-même affiche un avertissement dans les logs si on l'utilise
  tel quel en prod

### Ce que fait Gunicorn

**Gunicorn** (*Green Unicorn*) est un serveur d'application Python conçu
spécifiquement pour la production. Il ne remplace pas Flask — il se place
**devant** Flask et se charge de :

- **Recevoir les requêtes HTTP** venant du réseau (ici, du port 5000 exposé
  par Docker)
- **Gérer plusieurs workers** (processus) en parallèle, pour traiter
  plusieurs requêtes simultanément au lieu d'une seule à la fois
- **Transmettre chaque requête à l'application Flask**, qui fait ensuite
  tout le travail vu précédemment (routing, Jinja2, etc.)
- **Redémarrer automatiquement un worker qui plante**, pour éviter qu'une
  erreur ne fasse tomber tout le serveur

### Où on le voit dans le projet

Dans le `Dockerfile` :

CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]

- `-w 2` : lance 2 *workers* (2 processus qui peuvent traiter des requêtes
  en parallèle)
- `-b 0.0.0.0:5000` : écoute sur le port 5000, sur toutes les interfaces
  réseau du conteneur
- `app:app` : va chercher, dans le fichier `app.py`, la variable `app`
  (l'instance Flask créée par `Flask(__name__)`) — c'est elle qui sera
  exécutée pour chaque requête reçue

### La hiérarchie complète, avec Gunicorn à sa juste place
```
Docker
└─ fournit un espace utilisateur Linux isolé avec Python et les dépendances,
   tout en partageant le noyau de la machine hôte
   └─ Gunicorn
      └─ reçoit les requêtes HTTP et les répartit entre plusieurs workers
         └─ Flask
            └─ route chaque requête vers la bonne fonction Python
               (`index()` ou `health()`)
               └─ Jinja2
                  └─ génère le HTML dynamique dans `index()`

Navigateur
└─ JavaScript
   └─ gère les clics et la lecture des stations,
      hors de Docker et hors du serveur
```

### Pour vérifier par soi-même

```bash
docker top webradio
```

On voit plusieurs processus Gunicorn tourner en parallèle dans le conteneur :
le processus maître et les deux workers. Cela confirme que l’option `-w 2`
lance bien deux processus workers.

## Synthèse : quand y a-t-il vraiment contact avec le serveur ?

En résumé, le chargement de la page provoque plusieurs requêtes vers Flask : notamment une pour le document HTML et une pour la feuille de style CSS. Ensuite, cliquer sur une station ne déclenche aucune nouvelle requête vers Flask. Le navigateur se connecte directement au serveur de streaming de la radio sélectionnée. Il se débrouille seul avec le HTML et le JavaScript déjà reçus,
pour tout ce qui concerne l'affichage et la lecture des stations.

Un nouveau contact avec le serveur n'a lieu que dans des cas précis, où le
navigateur envoie explicitement une nouvelle requête HTTP :

- au premier chargement de la page (`http://localhost:5000/`)
- à un rafraîchissement (**F5** ou bouton "Recharger")
- si on retape l'adresse dans la barre du navigateur
- si on visite une autre route existante, comme `/health`

En dehors de ces cas, cliquer sur une station ne génère aucune nouvelle
requête vers le serveur Flask. Le navigateur contacte directement le serveur
de streaming de la radio sélectionnée.

### Le rôle de chaque brique dans ce contact

Quand ce contact a lieu, voici ce qui se passe, de la brique la plus
extérieure à la plus intérieure :

- **Docker** héberge le serveur de façon autonome et isolée, dans un
  conteneur qui tourne en continu, indépendamment de ce qui se passe dans
  le navigateur
- **Gunicorn**, à l'intérieur du conteneur, reçoit la requête HTTP et la
  distribue à l'un de ses workers
- **Flask** route la requête vers la bonne fonction Python (`index()` ou
  `health()`)
- Le résultat (HTML ou JSON) est renvoyé au navigateur, qui reprend alors
  la main de façon totalement autonome jusqu'au prochain contact

## Remerciements
README relu et amélioré avec l’aide de ChatGPT.
