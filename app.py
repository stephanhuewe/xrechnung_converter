import os
from flask import Flask, request, render_template, send_file, jsonify
import pdfplumber
from lxml import etree

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Funktion zur Extraktion von Rechnungsdaten aus PDF
def extract_pdf_data(pdf_path):
    data = {}
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            # Hier eine einfache Extraktion der Rechnungsnummer als Beispiel
            if "Rechnungsnummer" in text:
                data["invoice_number"] = text.split("Rechnungsnummer")[-1].strip()
            # Weitere Felder wie Datum und Beträge können hier extrahiert werden
    return data

# Funktion zur Erstellung von XRechnung-XML
def create_xrechnung_xml(data):
    root = etree.Element("Invoice")
    
    invoice_number = etree.SubElement(root, "InvoiceNumber")
    invoice_number.text = data.get("invoice_number", "Unbekannt")
    
    # Weitere XRechnung-Elemente hinzufügen
    
    xml_file_path = "xrechnung_output.xml"
    tree = etree.ElementTree(root)
    tree.write(xml_file_path, pretty_print=True, xml_declaration=True, encoding="UTF-8")
    return xml_file_path

# Routen für die Web-Anwendung
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "Keine Datei hochgeladen"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Dateiname fehlt"}), 400
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)
    
    # Daten aus PDF extrahieren
    data = extract_pdf_data(file_path)
    
    # XML-Datei erstellen
    xml_file_path = create_xrechnung_xml(data)
    
    return send_file(xml_file_path, as_attachment=True)

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
