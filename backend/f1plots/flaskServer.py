from flask import Flask, send_file
from plotGenerator import generate_plots

app = Flask(__name__)

@app.route('/plot1.png')
def serve_plot1():
    buf1, _ = generate_plots()
    return send_file(buf1, mimetype='image/png')

@app.route('/plot2.png')
def serve_plot2():
    _, buf2 = generate_plots()
    return send_file(buf2, mimetype='image/png')

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
