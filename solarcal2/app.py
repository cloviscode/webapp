from flask import Flask, render_template, request, redirect, url_for, session, send_file
import os
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for session management

# Constants
PEAK_SUN_HOURS = 5
BUFFER = 0.25
DOD = 0.60  # Depth of Discharge

@app.route('/')
def index():
    return redirect(url_for('equipment'))

@app.route('/solar/equipment', methods=['GET', 'POST'])
def equipment():
    if request.method == 'POST':
        equipment_list = []
        # Process form data
        index = 0
        while True:
            name = request.form.get(f'name_{index}')
            power_str = request.form.get(f'power_{index}')
            runtime_str = request.form.get(f'runtime_{index}')
            quantity_str = request.form.get(f'quantity_{index}', 1)
            
            if not name:
                break
            
            try:
                power = float(power_str)
                runtime = float(runtime_str)
                quantity = int(quantity_str)
                if power <= 0 or runtime <= 0 or runtime > 24 or quantity <= 0:
                    raise ValueError("Invalid input")
                equipment_list.append({
                    'name': name, 
                    'power': power, 
                    'runtime': runtime,
                    'quantity': quantity
                })
            except (ValueError, TypeError):
                return "Error: Invalid input. Please ensure power, runtime, and quantity are positive numbers."
            
            index += 1
        
        session['equipment'] = equipment_list
        return redirect(url_for('battery'))
    
    # Clear session data
    session.pop('equipment', None)
    session.pop('voltage', None)
    session.pop('inverter_efficiency', None)
    return render_template('equipment.html')

@app.route('/solar/battery', methods=['GET', 'POST'])
def battery():
    if 'equipment' not in session:
        return redirect(url_for('equipment'))
    
    if request.method == 'POST':
        try:
            voltage = int(request.form['voltage'])
            if voltage not in [12, 24, 48]:
                raise ValueError
            session['voltage'] = voltage
            return redirect(url_for('location'))  # Changed from 'inverter' to 'location'
        except (ValueError, KeyError):
            return "Error: Invalid battery voltage. Please select 12V, 24V, or 48V."
    
    return render_template('battery.html')

@app.route('/solar/location', methods=['GET', 'POST'])  # New route
def location():
    if 'equipment' not in session or 'voltage' not in session:
        return redirect(url_for('equipment'))
    
    if request.method == 'POST':
        try:
            peak_sun_hours = float(request.form['peak_sun_hours'])
            if peak_sun_hours <= 0 or peak_sun_hours > 24:
                raise ValueError
            session['peak_sun_hours'] = peak_sun_hours
            return redirect(url_for('inverter'))
        except (ValueError, KeyError):
            return "Error: Invalid peak sun hours. Please enter a value between 0 and 24."
    
    return render_template('location.html')

@app.route('/solar/inverter', methods=['GET', 'POST'])
def inverter():
    if 'equipment' not in session or 'voltage' not in session:
        return redirect(url_for('equipment'))
    
    if request.method == 'POST':
        try:
            efficiency_str = request.form['efficiency']
            efficiency = float(efficiency_str)
            if efficiency < 90 or efficiency > 98:
                raise ValueError
            session['inverter_efficiency'] = efficiency / 100.0
            return redirect(url_for('results'))
        except (ValueError, KeyError):
            return "Error: Invalid inverter efficiency. Please enter a value between 90 and 98."
    
    return render_template('inverter.html')

@app.route('/solar/results')
def results():
    if 'equipment' not in session or 'voltage' not in session or 'inverter_efficiency' not in session:
        return redirect(url_for('equipment'))
    
    equipment_list = session['equipment']
    voltage = session['voltage']
    inverter_efficiency = session['inverter_efficiency']
    
    # Calculate total daily energy consumption
    total_energy = sum(item['power'] * item['runtime'] * item['quantity'] for item in equipment_list)
    
    # Solar panel calculation
    solar_panel_power = (total_energy / PEAK_SUN_HOURS) * (1 + BUFFER)
    
    # Battery capacity calculation
    usable_ah = total_energy / voltage
    total_battery_ah = usable_ah / DOD
    
    # Inverter capacity calculation
    total_power_demand = sum(item['power'] * item['quantity'] for item in equipment_list)
    inverter_capacity = total_power_demand / inverter_efficiency
    
    return render_template('results.html', 
                          equipment=equipment_list,
                          total_energy=total_energy,
                          solar_panel_power=solar_panel_power,
                          voltage=voltage,
                          usable_ah=usable_ah,
                          total_battery_ah=total_battery_ah,
                          inverter_capacity=inverter_capacity,
                          inverter_efficiency=inverter_efficiency,
                          assumptions={
                              'sun_hours': PEAK_SUN_HOURS,
                              'buffer': f"{BUFFER*100}%",
                              'dod': f"{DOD*100}%"
                          })

@app.route('/solar/download-pdf')
def download_pdf():
    if 'equipment' not in session or 'voltage' not in session or 'inverter_efficiency' not in session:
        return redirect(url_for('equipment'))
    
    equipment_list = session['equipment']
    voltage = session['voltage']
    inverter_efficiency = session['inverter_efficiency']
    
    # Calculate values
    total_energy = sum(item['power'] * item['runtime'] * item['quantity'] for item in equipment_list)
    solar_panel_power = (total_energy / PEAK_SUN_HOURS) * (1 + BUFFER)
    usable_ah = total_energy / voltage
    total_battery_ah = usable_ah / DOD
    total_power_demand = sum(item['power'] * item['quantity'] for item in equipment_list)
    inverter_capacity = total_power_demand / inverter_efficiency
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    elements.append(Paragraph("Solar Power System Calculation Results", styles['Title']))
    elements.append(Spacer(1, 12))
    
    # Equipment Table
    elements.append(Paragraph("Equipment List", styles['Heading2']))
    table_data = [['Equipment', 'Quantity', 'Power (W)', 'Runtime (h)', 'Daily Energy (Wh)']]
    for item in equipment_list:
        table_data.append([
            item['name'],
            str(item['quantity']),
            f"{item['power']}",
            f"{item['runtime']}",
            f"{(item['power'] * item['runtime'] * item['quantity']):.2f}"
        ])
    table_data.append(['', '', '', 'Total:', f"{total_energy:.2f}"])
    equipment_table = Table(table_data)
    equipment_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(equipment_table)
    elements.append(Spacer(1, 12))
    
    # Solar Panel Requirements
    elements.append(Paragraph("Solar Panel Requirements", styles['Heading2']))
    solar_data = [
        ['Assumptions:', ''],
        ['Average Peak Sun Hours:', f"{PEAK_SUN_HOURS} hours"],
        ['System Buffer:', f"{BUFFER*100}%"],
        ['Estimated Solar Panel Power:', f"{solar_panel_power:.2f} W"]
    ]
    solar_table = Table(solar_data)
    solar_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(solar_table)
    elements.append(Spacer(1, 12))
    
    # Battery Requirements
    elements.append(Paragraph("Battery Requirements", styles['Heading2']))
    battery_data = [
        ['Assumptions:', ''],
        ['Battery Voltage:', f"{voltage} V"],
        ['Depth of Discharge (DoD):', f"{DOD*100}%"],
        ['Usable Battery Capacity:', f"{usable_ah:.2f} Ah"],
        ['Total Required Battery Capacity:', f"{total_battery_ah:.2f} Ah"]
    ]
    battery_table = Table(battery_data)
    battery_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(battery_table)
    elements.append(Spacer(1, 12))
    
    # Inverter Requirements
    elements.append(Paragraph("Inverter Requirements", styles['Heading2']))
    inverter_data = [
        ['Assumptions:', ''],
        ['Inverter Efficiency:', f"{inverter_efficiency*100:.2f}%"],
        ['Total Power Demand:', f"{total_power_demand:.2f} W"],
        ['Estimated Inverter Capacity:', f"{inverter_capacity:.2f} W"]
    ]
    inverter_table = Table(inverter_data)
    inverter_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(inverter_table)
    elements.append(Spacer(1, 12))
    
    # Note
    elements.append(Paragraph("Note: These calculations are estimates. Actual requirements may vary based on location, equipment usage, and system efficiency. Consult a solar professional for precise design.", styles['Normal']))
    
    doc.build(elements)
    buffer.seek(0)
    
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name='solar_power_calculation_results.pdf'
    )

if __name__ == '__main__':
    app.run(debug=True)