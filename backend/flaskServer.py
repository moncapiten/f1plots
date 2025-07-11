import os
import time
from flask import Flask, send_file, request
from plotGenerator import generate_plots
from datetime import datetime

app = Flask(__name__)
CACHE_TIMEOUT = 3600  # 1 hour

def get_plot_paths(year):
    return f'static/plot1_{year}.png', f'static/plot2_{year}.png'

def plots_expired(year):
    current_year = str(datetime.now().year)
    plot1_path, plot2_path = get_plot_paths(year)
    
    if not os.path.exists(plot1_path) or not os.path.exists(plot2_path):
        return True
    
    # Only check expiration for current year
    if year == current_year:
        last_modified = min(os.path.getmtime(plot1_path), os.path.getmtime(plot2_path))
        return (time.time() - last_modified) > CACHE_TIMEOUT
    
    # Historical years never expire
    return False

@app.route('/plot1.png')
def serve_plot1():
    year = request.args.get('year', str(datetime.now().year))
    plot1_path, plot2_path = get_plot_paths(year)
    
    if plots_expired(year):
        generate_plots_to_disk(year)
    
    return send_file(plot1_path, mimetype='image/png')

@app.route('/plot2.png')
def serve_plot2():
    year = request.args.get('year', str(datetime.now().year))
    plot1_path, plot2_path = get_plot_paths(year)
    
    if plots_expired(year):
        generate_plots_to_disk(year)
    
    return send_file(plot2_path, mimetype='image/png')

def generate_plots_to_disk(year):
    plot1_path, plot2_path = get_plot_paths(year)
    
    # Make sure static directory exists
    os.makedirs('static', exist_ok=True)
    
    # Generate plots with year parameter
    buf1, buf2 = generate_plots(year)
    
    buf1.seek(0)
    buf2.seek(0)
    
    with open(plot1_path, 'wb') as f:
        f.write(buf1.read())
    with open(plot2_path, 'wb') as f:
        f.write(buf2.read())

@app.route('/')
def index():
    current_year = datetime.now().year
    return f'''
    <html>
        <head>
            <title>F1 Season Plots</title>
        </head>
        <body>
            <h1>F1 Season Analysis</h1>
            
            <div style="margin-bottom: 20px;">
                <label for="yearSelector">Select Year:</label>
                <select id="yearSelector" onchange="updatePlots()">
                    <!-- Options will be populated by JavaScript -->
                </select>
            </div>
            
            <h2>Season Points Distribution</h2>
            <img id="plot1" src="/plot1.png" alt="Plot 1" style="max-width: 100%;">
            
            <h2>Points History</h2>
            <img id="plot2" src="/plot2.png" alt="Plot 2" style="max-width: 100%;">
            
            <script>
                function populateYearSelector() {{
                    const selector = document.getElementById('yearSelector');
                    const currentYear = {current_year};
                    
                    // Clear existing options
                    selector.innerHTML = '';
                    
                    // Add years from current year back to 2020 (adjust as needed)
                    for (let year = currentYear; year >= 2020; year--) {{
                        const option = document.createElement('option');
                        option.value = year;
                        option.textContent = year;
                        if (year === currentYear) {{
                            option.selected = true;
                        }}
                        selector.appendChild(option);
                    }}
                }}
                
                function updatePlots() {{
                    const selectedYear = document.getElementById('yearSelector').value;
                    const plot1 = document.getElementById('plot1');
                    const plot2 = document.getElementById('plot2');
                    
                    // Add timestamp to prevent browser caching
                    const timestamp = new Date().getTime();
                    
                    plot1.src = `/plot1.png?year=${{selectedYear}}&t=${{timestamp}}`;
                    plot2.src = `/plot2.png?year=${{selectedYear}}&t=${{timestamp}}`;
                }}
                
                // Initialize on page load
                document.addEventListener('DOMContentLoaded', function() {{
                    populateYearSelector();
                }});
            </script>
        </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)