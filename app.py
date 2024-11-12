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
from lxml import etree


def create_xrechnung_xml(data):
    # Hauptknoten für das XRechnung-Dokument
    root = etree.Element("CrossIndustryInvoice", nsmap={
        None: "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100",
        "rsm": "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100",
        "udt": "urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100",
        "qdt": "urn:un:unece:uncefact:data:standard:QualifiedDataType:100",
        "ram": "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100",
        "xs": "http://www.w3.org/2001/XMLSchema-instance"
    })

    # Kopfzeileninformationen (z.B. Rechnungsnummer, Datum)
    header = etree.SubElement(root, "ExchangedDocument")
    invoice_number = etree.SubElement(header, "ID")
    invoice_number.text = data.get("invoice_number", "Unbekannt")

    issue_date = etree.SubElement(header, "IssueDateTime")
    date_time = etree.SubElement(issue_date, "DateTimeString", format="102")
    date_time.text = data.get("invoice_date", "20230101")  # Beispiel: Datum im Format JJJJMMTT

    # Informationen über den Verkäufer (SellerTradeParty)
    seller = etree.SubElement(root, "SupplyChainTradeTransaction")
    seller_party = etree.SubElement(seller, "ApplicableHeaderTradeAgreement")
    seller_trade_party = etree.SubElement(seller_party, "SellerTradeParty")

    seller_name = etree.SubElement(seller_trade_party, "Name")
    seller_name.text = data.get("seller_name", "Beispiel GmbH")

    seller_id = etree.SubElement(seller_trade_party, "ID")
    seller_id.text = data.get("seller_vat_id", "DE123456789")  # Beispielhafte Umsatzsteuer-ID

    seller_address = etree.SubElement(seller_trade_party, "PostalTradeAddress")
    street_name = etree.SubElement(seller_address, "StreetName")
    street_name.text = data.get("seller_street", "Musterstraße 1")

    postal_code = etree.SubElement(seller_address, "PostcodeCode")
    postal_code.text = data.get("seller_postal_code", "12345")

    city_name = etree.SubElement(seller_address, "CityName")
    city_name.text = data.get("seller_city", "Musterstadt")

    country_id = etree.SubElement(seller_address, "CountryID")
    country_id.text = data.get("seller_country", "DE")

    # Informationen über den Käufer (BuyerTradeParty)
    buyer_party = etree.SubElement(seller_party, "BuyerTradeParty")

    buyer_name = etree.SubElement(buyer_party, "Name")
    buyer_name.text = data.get("buyer_name", "Kunden AG")

    buyer_id = etree.SubElement(buyer_party, "ID")
    buyer_id.text = data.get("buyer_vat_id", "DE987654321")

    buyer_address = etree.SubElement(buyer_party, "PostalTradeAddress")
    buyer_street_name = etree.SubElement(buyer_address, "StreetName")
    buyer_street_name.text = data.get("buyer_street", "Kundenstraße 5")

    buyer_postal_code = etree.SubElement(buyer_address, "PostcodeCode")
    buyer_postal_code.text = data.get("buyer_postal_code", "54321")

    buyer_city_name = etree.SubElement(buyer_address, "CityName")
    buyer_city_name.text = data.get("buyer_city", "Kundenstadt")

    buyer_country_id = etree.SubElement(buyer_address, "CountryID")
    buyer_country_id.text = data.get("buyer_country", "DE")

    # Zahlungsinformationen (SpecifiedTradeSettlement)
    trade_settlement = etree.SubElement(seller, "ApplicableHeaderTradeSettlement")
    invoice_currency = etree.SubElement(trade_settlement, "InvoiceCurrencyCode")
    invoice_currency.text = data.get("currency", "EUR")

    total_amount = etree.SubElement(trade_settlement, "GrandTotalAmount")
    total_amount.text = data.get("total_amount", "1000.00")

    # Steuerinformationen (SpecifiedTradeSettlementMonetarySummation)
    tax_total = etree.SubElement(trade_settlement, "TaxTotalAmount")
    tax_total.text = data.get("tax_total", "190.00")  # Beispielsteuerbetrag

    # Rechnungspositionen (LineTrade)
    trade_line_items = data.get("line_items", [
        {"item_name": "Produkt A", "quantity": "2", "price": "500.00"},
        {"item_name": "Produkt B", "quantity": "1", "price": "500.00"}
    ])

    for item in trade_line_items:
        line_item = etree.SubElement(seller, "IncludedSupplyChainTradeLineItem")
        item_id = etree.SubElement(line_item, "AssociatedDocumentLineDocument")
        line_id = etree.SubElement(item_id, "LineID")
        line_id.text = item.get("item_id", "1")

        quantity = etree.SubElement(line_item, "SpecifiedTradeProduct",
                                    nsmap={'udt': 'urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100'})
        quantity.text = item.get("quantity", "1")

        price_amount = etree.SubElement(line_item, "SpecifiedLineTradeAgreement")
        price = etree.SubElement(price_amount, "NetPriceProductTradePrice")
        price.text = item.get("price", "100.00")

        item_name = etree.SubElement(line_item, "Name")
        item_name.text = item.get("item_name", "Unbenanntes Produkt")

    # XML-Datei speichern
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
