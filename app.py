from flask import Flask, render_template, request, redirect, send_file, make_response, session
import sqlite3
import datetime as dt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'flask site'


@app.route('/', methods=['POST', 'GET'])   # авторизация
def index():
    dates = []
    today = dt.date.today()
    for i in range(1, 8):
        dates.append(today + dt.timedelta(days=i))
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        mydb = sqlite3.connect('hospital.sqlite')
        mycursor = mydb.cursor()
        mycursor.execute('SELECT * FROM doctors')
        myresult = mycursor.fetchall()
        for doctor in myresult:
            if login in doctor and password in doctor:
                session['login'] = login
                session['password'] = password
                session['person'] = 'doctor'
                return render_template('doctor.html')

        mycursor = mydb.cursor()
        mycursor.execute('SELECT * FROM patients')
        myresult = mycursor.fetchall()
        for patient in myresult:
            if login in patient and password in patient:
                session['login'] = login
                session['password'] = password
                session['person'] = 'patient'
                mydb = sqlite3.connect('hospital.sqlite')
                mycursor = mydb.cursor()
                names_doctors = mycursor.execute("SELECT name, surname FROM doctors").fetchall()
                return render_template('patient.html', dates=dates, names_doctors=names_doctors)


        return render_template('index.html', error='Аккаунт не найден!')
    else:
        if session.get('person') == 'doctor':
            return render_template('doctor.html')
        elif session.get('person') == 'patient':
            mydb = sqlite3.connect('hospital.sqlite')
            mycursor = mydb.cursor()
            names_doctors = mycursor.execute("SELECT name, surname FROM doctors").fetchall()
            return render_template('patient.html', dates=dates, names_doctors=names_doctors)
        return render_template('index.html')


@app.route('/patient')  # страница пациента
def patient_page():
    dates = []
    today = dt.date.today()
    for i in range(1, 8):
        dates.append(today + dt.timedelta(days=i))
    if session.get('person') == 'patient':
        mydb = sqlite3.connect('hospital.sqlite')
        mycursor = mydb.cursor()
        names_doctors = mycursor.execute("SELECT name, surname FROM doctors").fetchall()
        return render_template('patient.html', dates=dates, names_doctors=names_doctors)


@app.route('/doctor')    # страница доктора
def doctor_page():
    if session.get('person') == 'doctor':
        return render_template('doctor.html')


@app.route('/registration', methods=['POST', 'GET'])  # регистрация пациента
def registration():
    dates = []
    today = dt.date.today()
    for i in range(1, 8):
        dates.append(today + dt.timedelta(days=i))
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        login = request.form['login']
        email = request.form['email']
        password = request.form['pass']
        dob = request.form['date']
        mydb = sqlite3.connect('hospital.sqlite')
        mycursor = mydb.cursor()
        mycursor.execute('SELECT name FROM patients')
        myresult = mycursor.fetchall()
        if (name,) not in myresult:
            mycursor.execute("INSERT INTO patients (name, surname, login, password, email, dob)"
                             " VALUES (?, ?, ?, ?, ?, ?)",
                             (name, surname, login, password, email, dob))
            mydb.commit()
            session['login'] = login
            session['password'] = password
            session['person'] = 'patient'
            names_doctors = mycursor.execute("SELECT name, surname FROM doctors").fetchall()
            return render_template('patient.html', dates=dates, names_doctors=names_doctors)

        else:
            return render_template('registration.html', error='Вы ввели неккоректные данные '
                                                              'или такой аккаунт уже создан!')
    else:
        return render_template('registration.html')


@app.route('/table')   # таблица времен записей
def table():
    date = request.args.get('date')
    doctor = request.args.get('doctor')
    doctor_name = doctor.split(' ')[0]
    doctor_surname = doctor.split(' ')[1]
    before_work_time = ['8:00', '8:30', '9:00', '9:30', '10:00', '10:30', '11:00', '11:30', '12:00', '12:30', '13:00', '13:30']
    after_work_time = ['14:00', '14:30', '15:00', '15:30', '16:00', '16:30', '17:00', '17:30', '18:00', '18:30', '19:00', '19:30']
    mydb = sqlite3.connect('hospital.sqlite')
    mycursor = mydb.cursor()
    mycursor.execute('SELECT * FROM doctors WHERE name = ? AND surname = ?', (doctor_name, doctor_surname))
    doctor_information = mycursor.fetchone()
    schedule = dict()
    if doctor_information[5] == 'before':
        for time in before_work_time:
            mycursor.execute('SELECT * FROM bill WHERE date = ? AND time = ? AND doctor = ? AND online = ?', (date, time, doctor, '1'))
            my_article = mycursor.fetchone()
            if my_article is None:
                schedule[time] = 'Записаться'
            else:
                schedule[time] = 'Занято'
    elif doctor_information[5] == 'after':
        for time in after_work_time:
            mycursor.execute('SELECT * FROM bill WHERE date = ? AND time = ? AND doctor = ? AND online = ?', (date, time, doctor, '1'))
            my_article = mycursor.fetchone()
            if my_article is None:
                schedule[time] = 'Записаться'
            else:
                schedule[time] = 'Занято'
    return render_template('table.html', patient=session['login'], date=date,
                           doctor=doctor, schedule=schedule, schedule_keys=list(schedule.keys()))


@app.route('/add/<patient_name>/<date>/<time>/<doctor_name>')   # обработка записи пациента
def add(patient_name, date, time, doctor_name):
    mydb = sqlite3.connect('hospital.sqlite')
    mycursor = mydb.cursor()
    mycursor.execute('INSERT INTO bill(date, time, doctor, '
                     'patient, online) VALUES(?, ?, ?, ?, ?)', (date, time, doctor_name, patient_name, '1'))
    mydb.commit()
    return render_template('thanks_for_the_entry.html')


if __name__ == '__main__':
    app.run(debug=True)

