from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_mail import Mail, Message
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from dotenv import load_dotenv

# Modify the app creation to allow mounting
app = Flask(__name__)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Mail and app configuration
app.config.update(
    SECRET_KEY='913aa3a2-8fef-4446-a971-2e342e67513f',
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME='michaeldaron191@gmail.com',
    MAIL_PASSWORD='pbcq iczy telx qjom',
    MAIL_DEFAULT_SENDER='morgangeorge608@gmail.com',
    MAIL_USE_SSL=False,
    MAIL_DEBUG=True,
    SQLALCHEMY_DATABASE_URI='sqlite:///site.db',
    DEBUG=True
)

# Initialize mail with error handling
try:
    mail = Mail(app)
    logger.info("Mail initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize mail: {str(e)}")
    raise

@app.route("/")
def home():
    # Get any query parameters
    from_contact = request.args.get('from_contact')
    if (from_contact):
        return render_template("home.html", scroll_to_form=True)
    return render_template("home.html")

@app.route("/index")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/services")
def services():
    return render_template("services.html")

@app.route('/projects')
def projects():
    return render_template('projects.html')

@app.route('/project1')
def project1():
    return render_template('project1.html')

@app.route('/project2')
def project2():
    return render_template('project2.html')

@app.route('/project3')
def project3():
    return render_template('project3.html')    

@app.route('/project4')
def project4():
    return render_template('project4.html')

@app.route('/project5')
def project5():
    return render_template('project5.html')

@app.route('/project6')
def project6():
    return render_template('project6.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        try:
            # Get form data
            form_data = {
                'name': request.form.get('name'),
                'email': request.form.get('email'),
                'phone': request.form.get('phone'),
                'message': request.form.get('message')
            }

            # Validate required fields
            if not all(form_data.values()):
                flash('Please fill in all required fields', 'error')
                return redirect(url_for('contact'))

            # Send email to business
            msg = Message(
                subject=f"New Contact Form Message from {form_data['name']}",
                sender=app.config['MAIL_USERNAME'],
                recipients=[app.config['MAIL_DEFAULT_SENDER']],
                reply_to=form_data['email'],
                body=f"""
New Contact Form Submission:
---------------------------
Name: {form_data['name']}
Email: {form_data['email']}
Phone: {form_data['phone']}

Message:
{form_data['message']}
                """
            )
            mail.send(msg)
            logger.info(f"Sent contact form email from {form_data['name']}")

            # Send confirmation to customer
            confirmation = Message(
                subject="Thank you for contacting Clochanix Electric",
                sender=app.config['MAIL_USERNAME'],
                recipients=[form_data['email']],
                body=f"""
Dear {form_data['name']},

Thank you for contacting Clochanix Electric. We have received your message and will get back to you shortly.

Best regards,
Clochanix Electric Team
Contact: +237 680 547 526
                """
            )
            mail.send(confirmation)
            logger.info(f"Sent confirmation email to {form_data['email']}")

            flash('Your message has been sent successfully!', 'success')
            return redirect(url_for('contact'))
            
        except Exception as e:
            logger.error(f"Error sending contact form: {str(e)}")
            flash('An error occurred while sending your message. Please try again.', 'error')
            return redirect(url_for('contact'))
    
    return render_template('contact.html')

@app.route('/submit-service-request', methods=['POST'])
def submit_service_request():
    try:
        # Get form data with validation
        form_data = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'address': request.form.get('address'),
            'service': request.form.get('service'),
            'preferred_date': request.form.get('preferred_date'),
            'preferred_time': request.form.get('preferred_time'),
            'urgency': request.form.get('urgency'),
            'details': request.form.get('details', ''),
            'budget': request.form.get('budget', 'Not specified'),
            'reference': request.form.get('reference', 'Not specified')
        }

        # Log the request
        logger.info(f"Processing service request for {form_data['name']}")

        # Validate required fields
        required_fields = ['name', 'email', 'phone', 'address', 'service']
        if not all(form_data.get(field) for field in required_fields):
            flash('Please fill in all required fields', 'error')
            return redirect(url_for('home', _anchor='service-request-section'))

        try:
            # Send notification to business
            business_msg = Message(
                subject=f"New Service Request from {form_data['name']}",
                sender=app.config['MAIL_USERNAME'],
                recipients=['morgangeorge608@gmail.com'],  # Your business email
                reply_to=form_data['email'],
                body=f"""
New Service Request Details:
---------------------------
Name: {form_data['name']}
Email: {form_data['email']}
Phone: {form_data['phone']}
Address: {form_data['address']}

Service Information:
------------------
Service Type: {form_data['service']}
Preferred Date: {form_data['preferred_date']}
Preferred Time: {form_data['preferred_time']}
Urgency Level: {form_data['urgency']}
Budget Range: {form_data['budget']}

Project Details:
--------------
{form_data['details']}

Additional Information:
--------------------
Reference Source: {form_data['reference']}
                """
            )
            mail.send(business_msg)
            logger.info(f"Sent business notification email for {form_data['name']}")

            # Send confirmation to customer
            customer_msg = Message(
                subject="Service Request Received - Clochanix Electric",
                sender=app.config['MAIL_USERNAME'],
                recipients=[form_data['email']],
                body=f"""
Dear {form_data['name']},

Thank you for requesting our services. We have received your request and will contact you shortly to confirm the details.

Your Request Details:
-------------------
Service Type: {form_data['service']}
Preferred Date: {form_data['preferred_date']}
Preferred Time: {form_data['preferred_time']}
Service Location: {form_data['address']}

If you need immediate assistance, please call:
Phone: +237 680 547 526
WhatsApp: +237 680 547 526

Best regards,
Clochanix Electric Team
                """
            )
            mail.send(customer_msg)
            logger.info(f"Sent confirmation email to {form_data['email']}")

            flash('Your service request has been sent successfully!', 'success')
            return redirect(url_for('home', _anchor='service-request-section'))

        except Exception as mail_error:
            logger.error(f"Mail sending error: {str(mail_error)}")
            raise

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        flash('An error occurred while sending your request. Please try again.', 'error')
        return redirect(url_for('home', _anchor='service-request-section'))

# Add a test route
@app.route('/test-email')
def test_email():
    try:
        msg = Message(
            'Test Email',
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=['morgangeorge608@gmail.com']
        )
        msg.body = "This is a test email. If you receive this, your SMTP configuration is working."
        mail.send(msg)
        return 'Test email sent! Check your inbox.'
    except Exception as e:
        return f'Error: {str(e)}'

@app.route('/test-service-email')
def test_service_email():
    try:
        test_msg = Message(
            'Test Service Request Email',
            sender=app.config['MAIL_USERNAME'],
            recipients=['morgangeorge608@gmail.com']
        )
        test_msg.body = "This is a test email to verify service request functionality."
        mail.send(test_msg)
        return 'Test email sent! Check your inbox and spam folder.'
    except Exception as e:
        logger.error(f"Test email failed: {str(e)}")
        return f'Error sending test email: {str(e)}'


if __name__ == '__main__':
    app.run(debug=True)