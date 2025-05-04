from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file

app = Flask(__name__)
app.secret_key = 'your_secret_key'

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
            
            # Store in session for PDF generation
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

@app.route('/download_pdf')
def download_pdf():
    # Implement PDF generation and downloading logic here
    pass

if __name__ == '__main__':
    app.run(debug=True)