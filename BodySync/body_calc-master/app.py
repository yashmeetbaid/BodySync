from datetime import date
from math import log, log10, sqrt
from statistics import geometric_mean
from flask import Flask, redirect, render_template, url_for, request, session
import sqlite3
from forms import (AbsPowerCalculatorForm, BodyAttrCalculatorForm,
                   BodyFatCalculatorForm,
                   WeightGoalCalculatorForm)

app = Flask(__name__)
app.config['SECRET_KEY'] = '8746f582de105b3c3f2a7edc2e85ea49'

DIFF_REL = 0.31731050786291404
DIFF_ABS = 28

def init_db():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Route for the signup page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        conn.close()
        return redirect(url_for('login'))

    return render_template('signup.html')

# Route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        conn.close()

        session['logged_in'] = True
        session['username'] = username
        return redirect(url_for('dashboard'))

    return render_template('login.html')

# Route for the dashboard
@app.route('/dashboard')
def dashboard():
    if 'logged_in' in session:
        return render_template('base.html', username=session['username'])
    else:
        return redirect('login.html')

'''# Route for logging out
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('login'))'''

# Redirect root URL to login page
@app.route('/')
def root():
    return redirect('login.html')

@app.route('/weight_goal', methods=['GET', 'POST'])
def weight_goal():
    title = 'Weight Goal Calculator'
    form = WeightGoalCalculatorForm()
    result = None
    if form.validate_on_submit():
        curr_age = (date.today() - form.birth_date.data).days
        goal_age = (form.at_time.data - form.birth_date.data).days
        days_to_goal = goal_age - curr_age
        act_level = form.act_level.data
        curr_weight = form.curr_weight.data
        curr_height = form.curr_height.data
        goal_weight = form.goal_weight.data
        pred_height = form.pred_height.data
        r_raw = act_level * (66.473 + 6.8758 * (curr_weight + goal_weight)
                             + 2.50165 * (curr_height + pred_height) - 6.755
                             * 2 / 1461 * (curr_age + goal_age)) + 7716 * \
            (goal_weight - curr_weight) / days_to_goal
        result = round(r_raw, 2)
    return render_template(
        'weight_goal.html',
        title=title,
        form=form,
        result=result
    )

def normalize(quant, ref, ideal):
    diff = DIFF_REL * ideal
    if abs(quant / ref - ideal) < diff:
        return (1 - abs(quant / ref - ideal) / diff) * 100
    return 0

def normalize_height(quant, ideal_lower, ideal_upper):
    if quant < ideal_lower:
        if ideal_lower - quant < DIFF_ABS:
            return (DIFF_ABS + quant - ideal_lower) * 100 / DIFF_ABS
        return 0
    if quant > ideal_upper:
        if quant - ideal_upper < DIFF_ABS:
            return (DIFF_ABS + ideal_upper - quant) * 100 / DIFF_ABS
        return 0
    return 100

@app.route('/body_attr', methods=['GET', 'POST'])
def body_attr():
    title = 'Body Attractiveness Calculator'
    form = BodyAttrCalculatorForm()
    attractiveness = None
    if form.validate_on_submit():
        points = [
            normalize_height(form.height.data, 180.5, 195.5),
            normalize(form.wrist.data, form.height.data, 9/91),
            normalize(form.chest.data, form.wrist.data, 13/2),
            normalize(form.biceps.data, form.chest.data, 0.36),
            normalize(form.thigh.data, form.chest.data, 0.53),
            normalize(form.calf.data, form.chest.data, 0.34),
            normalize(form.waist.data, form.chest.data, 0.70),
            normalize(form.neck.data, form.chest.data, 0.37),
            normalize(form.hips.data, form.chest.data, 0.85),
            normalize(form.shoulder.data, form.waist.data, 1.61803),
        ]
        attractiveness = round(geometric_mean(points), 2)
    return render_template(
        'body_attr.html',
        title=title,
        form=form,
        attractiveness=attractiveness
    )

@app.route('/body_fat', methods=['GET', 'POST'])
def body_fat():
    title = 'Body Fat Calculator'
    form = BodyFatCalculatorForm()
    b_fat, lean_body_mass = None, None
    if form.validate_on_submit():
        height = form.height.data
        navel = form.navel.data
        neck = form.neck.data
        weight = form.weight.data
        body_fat_raw = 495 / (1.0324 - 0.19077 * log10(navel - neck) +
                              0.15456 * log10(height)) - 450
        b_fat = round(body_fat_raw, 2)
        if weight:
            lean_body_mass = round(weight * (1 - body_fat_raw / 100), 2)
    return render_template(
        'body_fat.html',
        title=title,
        form=form,
        body_fat=b_fat,
        lean_body_mass=lean_body_mass
    )

@app.route('/abs_power', methods=['GET', 'POST'])
def abs_power():
    title = 'Absolute Power Calculator'
    form = AbsPowerCalculatorForm()
    a_power = None
    if form.validate_on_submit():
        weight = form.weight.data
        vertical_jump = form.vertical_jump.data
        a_power = round(4.341249439 * weight * sqrt(vertical_jump), 2)
    return render_template(
        'abs_power.html',
        title=title,
        form=form,
        abs_power=a_power
    )

if __name__ == '__main__':
    app.run(debug=True)
