import aiohttp
import xml.etree.ElementTree as ET
from flask import Flask, render_template

# Which lines to filter out of results 
# Assign ids from id_map
filter_out = ['trams', 'water', 'dlr']

def get_distruptions(BranchDisruptions, namespace):

    disruptions = []

    for BranchDisruption in BranchDisruptions:
        disruption = {}
        for child in BranchDisruption:
            if child.tag == namespace + "StationTo":
                disruption['station_to'] = child.attrib['Name']
            elif child.tag == namespace + "StationFrom":
                disruption['station_from'] = child.attrib['Name']
            elif child.tag == namespace + "Status":
                disruption['status'] = child.attrib['Description']
                disruption['is_active'] = child.attrib['IsActive']
        disruptions.append(disruption)

    return disruptions

    table = PrettyTable()
    table.field_names = ['line_name', 'line_status',
                         'line_is_active', 'line_disruptions']
    for i in data:
        table.add_row([i['line_name'], i['line_status'],
                      i['line_is_active'], len(i['line_disruptions'])])
    print(table)


async def get_data():

    id_map = {
        'Bakerloo': 'bake',
        'Central': 'cent',
        'Circle': 'circ',
        'District': 'dist',
        'Hammersmith & City': 'hammer',
        'Jubilee': 'jub',
        'Metropolitan': 'metro',
        'Northern': 'north',
        'Piccadilly': 'picc',
        'Victoria': 'vic',
        'Waterloo and City': 'water',
        'Overground': 'over',
        'Elizabeth Line': 'eliz',
        'DLR': 'dlr',
        'Trams': 'trams',
    }

    async with aiohttp.ClientSession() as session:
        async with session.get("http://cloud.tfl.gov.uk/TrackerNet/LineStatus") as response:
            data = await response.read()

    # Parse XML data
    root = ET.fromstring(data)

    currentData = {'data': []}

    # Define namespace
    namespace = "{http://webservices.lul.co.uk/}"

    for lineStatus in root:

        lineData = {}

        lineData['status_details'] = lineStatus.attrib.get('StatusDetails', '')

        for child in lineStatus:
            if child.tag == f"{namespace}BranchDisruptions":
                lineData['line_disruptions'] = get_distruptions(
                    child, namespace)
            elif child.tag == f"{namespace}Line":
                lineData['line_name'] = child.attrib.get('Name', '')
                if lineData['line_name'] == 'Hammersmith and City':
                  lineData['line_name'] = 'Hammersmith & City' # Hardcoded because its easier
                lineData['line_id'] = id_map[lineData['line_name']]
            elif child.tag == f"{namespace}Status":
                lineData['line_status'] = child.attrib.get('ID', '')
                lineData['line_status_description'] = child.attrib.get(
                    'Description', '')
                lineData['line_is_active'] = child.attrib.get('IsActive', '')

        if not lineData['line_id'] in filter_out:
          currentData['data'].append(lineData)
    return currentData


app = Flask(__name__)

@app.route('/')
async def home():
    return render_template('index.html')


@app.route('/data')
async def gather_data():
    data = await get_data()
    print(len(data['data']))
    return data


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
