from flask import *
from tempfile import mkdtemp
from Server_utils import login_required, ThreadedMACalculator, ThreadedPricingRequest
from Connection import CursorCreator, Database
from Data_Reader import DataHandler
from Utils import secret_key, connection_data, mail_login, mail_password
from shared_variables import major_pairs, granularity
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
import json

Database.create_pool(**connection_data)
data_handler = DataHandler()

app = Flask(__name__, template_folder="Templates")
# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.secret_key = secret_key


# Ensure responses are not cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():

    # Request pricing for every major pair
    pricing_data = []
    while not pricing_data:
        quote = ThreadedPricingRequest()
        pricing_data = quote.core()

    return render_template('index.html', pricing_data=pricing_data)


@app.route("/login", methods=['GET', 'POST'])
def login():

    if request.method == 'GET':
        return render_template('login.html')

    elif request.method == 'POST':
        # Read all data provided by the user
        username = request.form.get('login')
        password = request.form.get('password')

        # Check if all fields were filled
        if not username or not password:
            session['message'] = json.dumps("You need to provide both username and password")
            return redirect('/error')

        # Try to load user from database
        with CursorCreator() as cursor:
            cursor.execute("SELECT * FROM users WHERE login = '%s'" % username)
            user_data = cursor.fetchall()
            if not user_data or not check_password_hash(user_data[0][2], password):
                session['message'] = json.dumps("Wrong username or password")
                return redirect('/error')
            session['user_id'] = user_data[0][1]

        return redirect("/")

    else:
        session['message'] = json.dumps('Wrong method')
        return redirect('/error')


@app.route("/register", methods=['GET', 'POST'])
def register():

    if request.method == 'GET':
        return render_template('register.html')

    elif request.method == 'POST':
        # Fetch all data and check if all fields were filled in

        username = request.form.get('username')
        password = request.form.get('password')
        mail = request.form.get('mail')

        if not (username or password or mail):
            session['message'] = json.dumps('You need to fill in all fields')
            return redirect('error.html')

        # Hash the password
        password = generate_password_hash(password)

        # Add user to database
        try:
            with CursorCreator() as cursor_1:
                cursor_1.execute("SELECT * FROM core WHERE login = %s" % username)
                session['message'] = json.dumps('Username taken')
                return redirect('error.html')
        except:
            with CursorCreator() as cursor_2:
                cursor_2.execute("INSERT INTO users(login, pass, mail) VALUES ('%s','%s','%s')" %
                                (username, password, mail))
                # Create for each user table with forecasts
                for pair in major_pairs:
                    cursor_2.execute("INSERT INTO core(symbol, login) VALUES ('{pair}','{id}')".
                                     format(pair=pair, id=username))

        # Add user_id to session (automatic login after registartion)
        session['user_id'] = username

        # Upon process completion send confirmation e-mail
        mail_msg = "\r\n".join([
            "From: Trading Station Info",
            "To: %s" % mail,
            "MIME-Version: 1.0",
            "Content-type: text/html",
            "Subject: Registration confirmation",
            "",
            "Hello, <br>",
            "User <b>%s</b> has been registered <br>" % session['user_id'],
            "Regards, <br>",
            "Team"
        ])

        try:
            smtp_server = smtplib.SMTP('smtp.gmail.com:587')
            smtp_server.ehlo()
            smtp_server.starttls()
            smtp_server.login(mail_login, mail_password)
            smtp_server.sendmail(mail_login, mail, mail_msg)
            smtp_server.quit()
        except smtplib.SMTPException:
            print("Could not send confirmation email.")

        return redirect('/')

    else:
        session['message'] = json.dumps('Wrong method')
        return redirect('/error')


@app.route('/forecasts')
@login_required
def forecasts():
    # Page presents current user forecasts according to each pair and enables modifications
    # Read all data from the database
    command = "SELECT symbol, first_s, first_r, h1_trend_f, h4_trend_f, d1_trend_f, w1_trend_f FROM core " \
              "WHERE login = '%s' ORDER BY symbol;" % session['user_id']
    forecasts_df = data_handler.create_df(read_method='custom', custom_command=command)

    # Show website that presents data frame and can redirect to another site where data can be changed
    pricing_rows = forecasts_df.itertuples()

    return render_template("forecasts.html", pricing_rows=pricing_rows)


@app.route('/forecasts/modify', methods=['POST', 'GET'])
@login_required
def forecasts_modify():
    # Page allows to change user records in database
    command = "SELECT symbol, first_s, first_r, h1_trend_f, h4_trend_f, d1_trend_f, w1_trend_f FROM core " \
              "WHERE login = '%s' ORDER BY symbol;" % session['user_id']
    forecasts_df = data_handler.create_df(read_method='custom', custom_command=command)

    # Show website that presents data frame and can redirect to another site where data can be changed
    pricing_rows = forecasts_df.itertuples()

    if request.method == 'GET':

        return render_template('forecasts_modify.html', pricing_rows=pricing_rows)

    elif request.method == 'POST':
        # xyz of {{ row[1] }} > xyz of row[1]
        # print(forecasts_df)
        to_read_from_form = ('resistance', 'support', 'h1_trend', 'h4_trend', 'd1_trend', 'w1_trend')
        major_pairs_from_db = [x[1] for x in pricing_rows]

        for item_pos, item in enumerate(to_read_from_form):
            for pair_pos, pair in enumerate(major_pairs_from_db):
                record = request.form.get("%s of %s" % (item, pair))
                if record:
                    forecasts_df.set_value(pair_pos, item_pos+1, record)
                    forecasts_df.set_value(pair_pos, 'changed', 1)
                # print("Retrieving: ", ("%s of %s" % (pair, item)))
                # print("Get command: ", request.form.get("%s of %s" % (item, pair)))
        print(forecasts_df)
        print("Shape of df: ", forecasts_df.shape)

        # Read all rows in data frame
        with CursorCreator() as cursor:
            for row in range(forecasts_df.shape[0]):
                print("Cheking row: ", row)
                # Check changed column, if equals one write whole row into database
                if forecasts_df.at[row, 'changed'] == 1:
                    # None and NaN values have to be skipped
                    columns = ['first_r', 'first_s', 'h1_trend_f', 'h4_trend_f', 'd1_trend_f', 'w1_trend_f']
                    for column in range(len(columns)):
                        print("Checking column: ", column)
                        if str(forecasts_df.iat[row, column+1]).lower() != "nan" and forecasts_df.iat[row, column+1] \
                                is not None:
                            if isinstance(forecasts_df.iat[row, column+1], str):
                                print("Detected string instance: ", forecasts_df.iat[row, column+1])
                                cursor.execute("UPDATE core SET {} = '{}' WHERE login = '{}' and symbol = '{}'".
                                    format(columns[column], forecasts_df.iat[row, column+1], session['user_id'],
                                    forecasts_df.iat[row, 0]))
                            else:
                                print("Detected numeric instance: ", forecasts_df.iat[row, column+1])
                                cursor.execute("UPDATE core SET {} = {} WHERE login = '{}' and symbol = '{}'".
                                    format(columns[column], forecasts_df.iat[row, column+1], session['user_id'],
                                    forecasts_df.iat[row, 0]))

        return redirect('/forecasts')

    else:
        session['message'] = json.dumps('Wrong method')
        return redirect('/error')


@app.route('/trends/<requested_ma_type>/<requested_interval>', methods=['GET', 'POST'])
@login_required
def trends(requested_ma_type, requested_interval=14):
    if request.method == 'POST':
        ma_type_form = request.form.get("ma_type")
        interval_form = request.form.get("interval")

        return redirect(url_for("trends", requested_ma_type=ma_type_form, requested_interval=interval_form))

    elif request.method == 'GET':
        if requested_ma_type == 'Exponential' or requested_ma_type == 'ema':
            requested_ma_type = 'ema'
        elif requested_ma_type == 'Simple' or requested_ma_type == 'sma':
            requested_ma_type = 'sma'
        else:
            raise RuntimeError("MA type not recognized")

        ma_calc = ThreadedMACalculator(ma_type=requested_ma_type, interval=int(requested_interval))
        ma_data = ma_calc.calculate_mas()
        print("Retrieved type of MA: ", requested_ma_type, ' of interval: ', requested_interval)
        return render_template('trends.html', ma_data=ma_data, granularity=granularity, major_pairs=major_pairs,
                               requested_ma_type=requested_ma_type, requested_interval=requested_interval)

    else:
        session['message'] = json.dumps("Wrong method used to access given URL")
        return redirect("error.html", 404)


@app.route("/error")
def error():
    return render_template("error.html", message=json.loads(session['message']))


@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for('index'))


app.run(port='4454', debug=True)
