![Linux](https://img.shields.io/badge/Linux-supported-FCC624?logo=linux&logoColor=black)
![Debian 13](https://img.shields.io/badge/Debian-13-A81D33?logo=debian&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-required-2496ED?logo=docker&logoColor=white)

# 🎧 Web Radio - Docker Project (Python 3)

A small Flask application that provides a web radio player in the browser,
with several selectable stations. The project is containerized using a
**Python slim** image to keep it lightweight.

## Development environment

This project was developed and tested on **Linux (Debian 13)**.

It also works on **macOS** and **Windows** with Docker Desktop, but the Docker installation procedure may differ depending on the operating system.

Once Docker and Docker Compose are installed, the commands used in this README remain the same.

## Project structure

```text
webradio/
├── app.py                 # Flask application
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker image (python:3.13-slim + Gunicorn)
├── docker-compose.yml     # Simplified startup
├── templates/
│   └── index.html         # Page containing the audio player
└── static/
    └── style.css          # Page styling
```

## Running the project

### With Docker Compose (recommended)

```bash
cd webradio
docker compose up -d --build
```

Then open the browser at: http://localhost:5000

### With Docker only

```bash
docker build -t webradio .
docker run -p 5000:5000 webradio
```

### Stopping the container

```bash
docker compose down
```

## How it works

- `app.py` defines a list of stations (name + direct MP3 stream URL).
- The HTML page displays one button per station; clicking a button loads the
  stream URL into an HTML5 `<audio>` element, which handles playback (the
  browser performs the streaming, not the Flask server).
- In production, Gunicorn serves the application instead of Flask's
  development server (more stable and more efficient).
- The `python:3.13-slim` image is used instead of the standard image to reduce
  the final image size (no unnecessary build tools or packages).

## Understanding the Flask code line by line

### The main route

```python
@app.route("/")
def index():
    return render_template("index.html", stations=STATIONS)
```

- **`@app.route("/")`**: this is a Python *decorator*. It registers the
  function immediately below it with Flask as the handler for the `/` route
  (the home page). In other words: "when someone visits `http://.../`, run
  this function."
- **`def index():`**: a standard Python function, called a *view function* in
  Flask. Its name has no special importance to Flask, but it must return
  something that Flask can turn into an HTTP response (text, HTML, JSON, etc.).
- **`render_template("index.html", stations=STATIONS)`**:
  - `render_template()` looks for `index.html` in the `templates/` directory
    and transforms it into the final HTML document using the Jinja2 template
    engine.
  - `stations=STATIONS` passes the Python list `STATIONS` to the template under
    the name `stations`, which makes it possible to write the following in
    `index.html`:

    ```jinja
    {% for station in stations %}
            <button
                class="station-btn"
                onclick='playStation({{ station.url | tojson }}, {{ station.name | tojson }})'>
                {{ station.name }}
            </button>
            {% endfor %}
    ```

    Without this parameter, the template would have no access to the list—a
    template can only see the data explicitly passed to it.

### The `/health` route

```python
@app.route("/health")
def health():
    return {"status": "ok"}
```

The same principle applies: this route responds to requests sent to `/health`
by returning a small JSON object, `{"status": "ok"}`. Flask automatically
converts a Python dictionary returned by a view into a JSON response.

It is not intended for a person browsing the site, but for a monitoring
system: it is a **health-check endpoint**, a widely used convention in
containerization. A health check can query this route regularly to determine
whether the application is operational. Docker can then mark the container as
`healthy` or `unhealthy`. Some orchestrators or monitoring tools can then act
according to that status.

## How the stations reach the HTML page (server vs. browser)

This is the most important point for a beginner to understand:

In this project, **there are two clearly separated worlds**. Flask and Jinja2
build the page on the server side; JavaScript then handles interactions in the
browser.

### 1. The "server" world (Python / Flask)—runs ONCE

When the browser loads `http://localhost:5000/`, the following happens on the
server side, in `app.py`:

```python
STATIONS = [
    {"name": "FIP", "url": "https://icecast.radiofrance.fr/fip-midfi.mp3"},
    ...
]

@app.route("/")
def index():
    return render_template("index.html", stations=STATIONS)
```

`STATIONS` is a simple Python list that exists only in server memory. The
browser does not know about it and never accesses it directly.

`render_template()` reads the `templates/index.html` file, which contains
**Jinja2** code—the Flask template engine—mixed with HTML:

```jinja
{% for station in stations %}
<button
    class="station-btn"
    onclick='playStation({{ station.url | tojson }}, {{ station.name | tojson }})'>
    {{ station.name }}
</button>
{% endfor %}
```

Jinja2 **replaces** this code with pure HTML by looping through the `STATIONS`
list received as a parameter. In practice, for two stations, the result looks
something like this:

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

This final HTML text, with no remaining `{% %}` or `{{ }}` expressions, is what
`index()` returns and what Flask sends to the browser in the HTTP response.

**Key point**: this mechanism (Python + Jinja2) runs **on the server side**,
once for each page load. Once the HTML has been sent, Python no longer plays
any role in interactions with the buttons on that page. The server does,
however, remain active and waits for further HTTP requests.

### 2. The "browser" world (HTML / JavaScript)—runs on EVERY click

Once the browser has received the HTML shown above, it no longer knows that it
came from a Python list. As far as the browser is concerned, these are ordinary
buttons whose `onclick` attributes contain hard-coded URLs.

```javascript
function playStation(url, name) {
    const player = document.getElementById("audio-player");
    const nowPlaying = document.getElementById("now-playing");
    player.src = url;
    player.play()
        .then(() => {
            nowPlaying.textContent = "▶️ Now playing: " + name;
        })
        .catch((error) => {
            console.error("Playback error:", error);
            nowPlaying.textContent = "❌ Unable to play: " + name;
        });
}
```

When a button is clicked, this JavaScript function runs **entirely in the
browser**, without contacting Flask again. It takes the URL already stored in
the button and assigns it to the `<audio>` player, which then connects directly
to the radio stream, for example `icecast.radiofrance.fr`.

### Why this separation matters

| | Python/Jinja2 templating | JavaScript in the browser |
|---|---|---|
| Where it runs | On the server (inside the Docker container) | In the user's browser |
| When | Once, when the page is generated | On each interaction (click, etc.) |
| Access to `STATIONS` | Yes (Python variable) | No—only the URLs already written into the HTML |
| Visible in "View Page Source" | No (already transformed) | Yes, this is exactly what is sent |

To verify this yourself, right-click the page and select **"View Page Source"**
(not the developer tools). The station URLs can be seen already written
directly into the buttons—there is no trace of Python, Flask, or Jinja2, only
ready-to-use HTML and JavaScript. This proves that templating took place on the
server before the page was sent.

## Docker's role in all of this

After looking at Flask, Jinja2, and JavaScript, a reasonable question arises:
what exactly is Docker doing here?

**The simple answer: Docker plays no role in the application's logic.** It
does not know what a Flask route, a radio station, or a Jinja2 template is. It
operates at a completely different level: the **runtime environment**.

### What Docker does here

1. **It packages the environment** required to run the application: Python
   3.13, Flask, Jinja2, Gunicorn, and a minimal file system
   (`python:3.13-slim`)—all inside a fixed and portable image described by the
   `Dockerfile`.

2. **It isolates execution** inside a container, separate from the host system
   (Debian 13 in this case). This prevents conflicts with other Python versions
   or other projects installed on the machine.

3. **It improves reproducibility**: on a compatible architecture, the same
   image provides the same versions of Python, the libraries, and the
   application files, regardless of the software already installed on the host
   machine.

4. **It manages networking**: the `ports: - "5000:5000"` line in
   `docker-compose.yml` forwards port 5000 on the host machine to port 5000
   inside the container, where Gunicorn is listening.

### From the server to the browser

```text
Server side
Docker
└─ Gunicorn
   └─ Flask
      └─ Jinja2
         └─ generates the dynamic HTML in `index()`

                 ↓ HTTP response

Browser side
HTML
└─ JavaScript
   └─ handles clicks and station playback
```

### Verifying it yourself

If the `Dockerfile` and `docker-compose.yml` files were removed completely, the
application would work in exactly the same way locally by running:

```bash
python3 app.py
```

Docker adds **no application feature**. It adds a layer of **portability and
isolation** around code that would already exist and work without it.

## Gunicorn's role in all of this

### The problem Gunicorn solves

Flask includes its own built-in server, which is started with
`app.run(host="0.0.0.0", port=5000)` in the
`if __name__ == "__main__":` block of `app.py`. It is very convenient for
development, but this server is **not designed for production**:

- Flask's built-in server is intended for development. It makes testing and
  debugging easier, but it is not designed to provide the robustness, process
  management, and guarantees expected from a production server.
- It is not optimized to handle heavy traffic.
- Flask itself displays a warning in the logs when it is used directly in
  production.

### What Gunicorn does

**Gunicorn** (*Green Unicorn*) is a Python application server designed
specifically for production. It does not replace Flask—it sits **in front of**
Flask and is responsible for:

- **Receiving HTTP requests** from the network, here through port 5000 exposed
  by Docker.
- **Managing multiple workers**—separate processes—in parallel, so several
  requests can be processed simultaneously.
- **Passing each request to the Flask application**, which then performs all
  the work described above, including routing and Jinja2 rendering.
- **Automatically restarting a worker that crashes**, preventing one worker
  failure from bringing down the entire server.

### Where it appears in the project

In the `Dockerfile`:

```dockerfile
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]
```

- `-w 2`: starts two *workers*—two processes that can handle requests in
  parallel.
- `-b 0.0.0.0:5000`: listens on port 5000 on all network interfaces inside the
  container.
- `app:app`: looks for the `app` variable in the `app.py` file. This is the
  Flask instance created by `Flask(__name__)`, and it is executed for each
  request received.

### The complete hierarchy, with Gunicorn in its proper place

```text
Docker
└─ provides an isolated Linux user space with Python and the dependencies,
   while sharing the host machine's kernel
   └─ Gunicorn
      └─ receives HTTP requests and distributes them among several workers
         └─ Flask
            └─ routes each request to the appropriate Python function
               (`index()` or `health()`)
               └─ Jinja2
                  └─ generates the dynamic HTML in `index()`

Browser
└─ JavaScript
   └─ handles clicks and station playback,
      outside Docker and outside the server
```

### Verifying it yourself

```bash
docker top webradio
```

Several Gunicorn processes can be seen running in parallel inside the
container: the master process and the two workers. This confirms that the
`-w 2` option starts two worker processes.

## Summary: when does the browser actually contact the server?

In summary, loading the page causes several requests to Flask, including one
for the HTML document and one for the CSS stylesheet. Clicking a station then
causes no further request to Flask. The browser connects directly to the
selected radio station's streaming server. It handles the display and station
playback itself using the HTML and JavaScript it has already received.

The browser contacts the server again only in specific situations where it
explicitly sends another HTTP request:

- when the page is first loaded (`http://localhost:5000/`);
- when the page is refreshed (**F5** or the "Reload" button);
- when the address is entered again in the browser's address bar;
- when another existing route, such as `/health`, is visited.

Outside these situations, clicking a station does not generate any new request
to the Flask server. The browser contacts the selected radio station's
streaming server directly.

### The role of each component in this contact

When this contact occurs, the following happens, from the outermost component
to the innermost:

- **Docker** hosts the server independently and in isolation, inside a container
  that runs continuously regardless of what happens in the browser.
- **Gunicorn**, inside the container, receives the HTTP request and assigns it
  to one of its workers.
- **Flask** routes the request to the appropriate Python function, either
  `index()` or `health()`.
- The result—HTML or JSON—is returned to the browser, which then operates
  independently until the next contact.

## Acknowledgements

README reviewed and improved with the help of ChatGPT.
