from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
import os
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for flashing messages

@app.route('/')
@app.route('/calculator', methods=['GET', 'POST'])
def bill_calculator():
    if request.method == 'POST':
        try:
            previous_reading = float(request.form['previous_reading'])
            current_reading = float(request.form['current_reading'])
            cost_per_unit = float(request.form['cost_per_unit'])
            
            if previous_reading < 0 or current_reading < 0 or cost_per_unit < 0:
                flash('Please enter positive values for all fields.')
                return redirect(url_for('bill_calculator'))
            
            if current_reading < previous_reading:
                flash('Current reading must be greater than previous reading.')
                return redirect(url_for('bill_calculator'))
            
            units_consumed = current_reading - previous_reading
            total_amount = units_consumed * cost_per_unit
            
            # Store values in session
            session['previous_reading'] = previous_reading
            session['current_reading'] = current_reading
            session['cost_per_unit'] = cost_per_unit
            session['units_consumed'] = units_consumed
            session['total_amount'] = total_amount
            
            return render_template('results.html', 
                                 previous_reading=previous_reading,
                                 current_reading=current_reading,
                                 cost_per_unit=cost_per_unit,
                                 units_consumed=units_consumed,
                                 total_amount=total_amount)
            
        except ValueError:
            flash('Please enter valid numbers for all fields.')
            return redirect(url_for('bill_calculator'))
    
    return render_template('electricity_bill.html')

@app.route('/download-pdf')
def download_pdf():
    # Recreate the data from the session (if needed)
    if 'previous_reading' not in session or 'current_reading' not in session or 'cost_per_unit' not in session:
        return redirect(url_for('bill_calculator'))
    
    previous_reading = session['previous_reading']
    current_reading = session['current_reading']
    cost_per_unit = session['cost_per_unit']
    units_consumed = session['units_consumed']
    total_amount = session['total_amount']
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    elements.append(Paragraph("Electricity Bill Calculation Results", styles['Title']))
    elements.append(Spacer(1, 12))
    
    # Create a table for the results
    data = [
        ['Item', 'Value'],
        ['Previous Meter Reading', f"{previous_reading} units"],
        ['Current Meter Reading', f"{current_reading} units"],
        ['Cost per Unit', f"{cost_per_unit} currency units"],
        ['Total Units Consumed', f"{units_consumed} units"],
        ['Total Amount to be Paid', f"{total_amount} currency units"]
    ]
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(table)
    
    doc.build(elements)
    buffer.seek(0)
    
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name='electricity_bill.pdf'
    )

if __name__ == '__main__':
    app.run(debug=True)
