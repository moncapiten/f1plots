import os
import time
from flask import Flask, send_file
from plotGenerator import generate_plots

app = Flask(__name__)
CACHE_TIMEOUT = 3600  # 1 hour
PLOT1_PATH = 'static/plot1.png'
PLOT2_PATH = 'static/plot2.png'

def plots_expired():
    if not os.path.exists(PLOT1_PATH) or not os.path.exists(PLOT2_PATH):
        return True
    last_modified = min(os.path.getmtime(PLOT1_PATH), os.path.getmtime(PLOT2_PATH))
    return (time.time() - last_modified) > CACHE_TIMEOUT

@app.route('/plot1.png')
def serve_plot1():
    if plots_expired():
        generate_plots_to_disk()
    return send_file(PLOT1_PATH, mimetype='image/png')

@app.route('/plot2.png')
def serve_plot2():
    if plots_expired():
        generate_plots_to_disk()
    return send_file(PLOT2_PATH, mimetype='image/png')

def generate_plots_to_disk():
    buf1, buf2 = generate_plots()
    with open(PLOT1_PATH, 'wb') as f:
        f.write(buf1.read())
    with open(PLOT2_PATH, 'wb') as f:
        f.write(buf2.read())


@app.route('/')
def index():
    return '''
    <html>
        <head><title>F1 Season Plots</title></head>
        <body>
            <h1>Season Points Distribution</h1>
            <img src="/plot1.png" alt="Plot 1">
            <h1>Points History</h1>
            <img src="/plot2.png" alt="Plot 2">
        </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
