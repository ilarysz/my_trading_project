# Built-in libraries
import smtplib
import json
# Third-party libraries
from flask import *
from tempfile import mkdtemp
from werkzeug.security import generate_password_hash, check_password_hash
# Custom packages
from server_utils import login_required, ThreadedMACalculator, ThreadedPricingRequest, TwitterLogin
from database_methods import DataHandler
# Global variables
from shared_variables_secret import SECRET_KEY, MAIL_LOGIN, MAIL_PASSWORD
from shared_variables import major_pairs, granularity


data_handler = DataHandler()

app = Flask(__name__, template_folder="Templates")
# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.secret_key = SECRET_KEY


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
        user_data = data_handler.execute_db_request("SELECT * FROM users WHERE login = '%s'" % username)
        if not user_data or not check_password_hash(user_data[0][2], password):
            session['message'] = json.dumps("Wrong username or password")
            return redirect('/error')
        session['user_id'] = user_data[0][1]

        return redirect("/")

    else:
        session['message'] = json.dumps('Wrong method')
        return redirect('/error')


@app.route("/twitter/login")
def twitter_login():
    # Obtain request token and redirect user so it can get authorization code
    authorization_url = TwitterLogin.get_request_token()

    return redirect(authorization_url)


@app.route("/twitter/auth")
def create_access_token():
    # Callback uri
    # Acquire oauth verifier from uri and basing on it and earlier information create access token
    oauth_verifier = request.args.get('oauth_verifier')
    access_token = TwitterLogin.get_access_token(oauth_verifier=oauth_verifier)
    session['user_id'] = access_token['screen_name']

    return redirect('/')


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

        # Add user to database and check if the name is not taken
        try:
            data_handler.execute_db_request("SELECT * FROM core WHERE login = %s" % username)
            session['message'] = json.dumps('Username taken')
            return redirect('error.html')
        except:
            data_handler.execute_db_request("INSERT INTO users(login, pass, mail) VALUES ('%s','%s','%s')" %
                                            (username, password, mail), get_data=False)
            # Create for each user table with forecasts
            for pair in major_pairs:
                data_handler.execute_db_request("INSERT INTO core(symbol, login) VALUES ('{pair}','{id}')".
                                                format(pair=pair, id=username), get_data=False)

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

        # Send email, credentials are located in shared_variables_secret.py
        try:
            smtp_server = smtplib.SMTP('smtp.gmail.com:587')
            smtp_server.ehlo()
            smtp_server.starttls()
            smtp_server.login(MAIL_LOGIN, MAIL_PASSWORD)
            smtp_server.sendmail(MAIL_LOGIN, mail, mail_msg)
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
        for row in range(forecasts_df.shape[0]):
            print("Cheking row: ", row)
            # Check changed column, if equals one write whole row into database
            if forecasts_df.at[row, 'changed'] == 1:
                # None and NaN values have to be skipped
                columns = ['first_r', 'first_s', 'h1_trend_f', 'h4_trend_f', 'd1_trend_f', 'w1_trend_f']
                for column in range(len(columns)):
                    print("Checking column: ", column)
                    # Check is uers changed forecast for given pair.
                    # If so, update row for given user and pair with new data
                    if str(forecasts_df.iat[row, column + 1]).lower() != "nan" and forecasts_df.iat[row, column + 1] \
                            is not None:
                        if isinstance(forecasts_df.iat[row, column + 1], str):
                            print("Detected string instance: ", forecasts_df.iat[row, column + 1])
                            data_handler.execute_db_request(
                                "UPDATE core SET {} = '{}' WHERE login = '{}' and symbol = '{}'".
                                format(columns[column], forecasts_df.iat[row, column + 1], session['user_id'],
                                       forecasts_df.iat[row, 0]), get_data=False)
                        else:
                            print("Detected numeric instance: ", forecasts_df.iat[row, column + 1])
                            data_handler.execute_db_request(
                                "UPDATE core SET {} = {} WHERE login = '{}' and symbol = '{}'".
                                format(columns[column], forecasts_df.iat[row, column + 1], session['user_id'],
                                       forecasts_df.iat[row, 0]), get_data=False)

        return redirect('/forecasts')

    else:
        session['message'] = json.dumps('Wrong method')
        return redirect('/error')


@app.route('/trends/<requested_ma_type>/<requested_interval>', methods=['GET', 'POST'])
@login_required
def trends(requested_ma_type, requested_interval=14):
    # Shows if pricing for given pair is above or below MA defined by user

    # Set parameters for MA used for comparisons
    if request.method == 'POST':
        ma_type_form = request.form.get("ma_type")
        interval_form = request.form.get("interval")

        return redirect(url_for("trends", requested_ma_type=ma_type_form, requested_interval=interval_form))

    elif request.method == 'GET':
        # Check query parameters and send them to computation module
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
