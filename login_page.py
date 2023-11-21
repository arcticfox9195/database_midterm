import string
from flask import Flask,request,flash,redirect,url_for,jsonify,session
from flask import render_template
import requests
import sqlite3
import random
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from bson.binary import Binary
from PIL import Image

app = Flask(__name__)
app.secret_key = 'your_secret_key' 


@app.route('/login', methods = ['GET', 'POST'])
def index():
    if request.method == 'POST':
        if "loginName" in request.form:
            logN = request.values["loginName"]
            logP = request.values["loginPass"]
            cur.execute("select Password from AccountList where Username = ?",(logN,))
            p = cur.fetchall()
            if p == []:
                return jsonify({'status': 'error', 'message': 'Username not exist'})
            else:
                p_r = p[0][0]
                if p_r == logP:
                    if logN == "admin":
                        return jsonify({'status': 'success', 'message': 'Login successfully.Welcome, ' + str(logN), 'action': 'adminlogin'})
                    else:
                        session['username'] = logN
                        return jsonify({'status': 'success', 'message': 'Login successfully.Welcome, ' + str(logN), 'action': 'userlogin'})
                else:
                    return jsonify({'status': 'error', 'message': 'incorrect password'})
            
        elif "SignName" in request.form:
            SignN = request.values["SignName"]
            SignE = request.values["SignEmail"]
            SignP = request.values["SignPass"]
            ConfP = request.values["ConfirmPass"]
            cur.execute("select * from AccountList where Username = ?",(SignN,))
            userNameRows = cur.fetchall()
            if userNameRows == []:
                cur.execute("select * from AccountList where mail = ?",(SignE,))
                EmailRows = cur.fetchall()
                if EmailRows == []:
                    if SignP != ConfP :
                        return jsonify({'status': 'error', 'message': 'Passwords do not match'})
                    else:
                        if len(SignP) >= 6:
                            cur.execute("Insert into AccountList Values(?, ?, ?)",(SignN, SignP, SignE))
                            conn.commit()
                            return jsonify({'status': 'success', 'message': 'Sign up successfully','action':'signup'})
                            
                        else:
                            return jsonify({'status': 'error', 'message': 'Password needs to be more than 6 characters'})
                else:
                    return jsonify({'status': 'error', 'message': 'Email already in use'})
            else:
                return jsonify({'status': 'error', 'message': 'Username already in use'})
                
            
            
    return render_template('login_page.html')

@app.route('/admin', methods = ['GET', 'POST'])
def admin():
    cur.execute("SELECT Image, Name FROM activitiesList")
    activities = cur.fetchall()
    return render_template('admin.html', activities=activities)


@app.route('/admin/createActivities', methods = ['GET', 'POST'])
def create():
    if request.method == 'POST':
        name = request.values["activity-name"]
        description = request.values["activity-description"]
        image_url = request.values["image-download-link"]
        imageName = request.values['image-save-name']
        imagePath = "C:\\Users\\yaochiliao\\Desktop\\VSCODE\\資料庫程式設計\\資料庫專題\\static/" + request.values['image-save-name']
        time = request.values["activity-time"]
        location = request.values["activity-location"]
        limit = int(request.values["activity-limit"])
        tableName = name
        sql_command = f'''create table {tableName}
            ('Username' text ,
            'Name' text ,
            'Phone' text, 
            'email' text,
            'Address' text,
            'Id' text,
            'DateBirth' text,
             PRIMARY KEY (Username)
             );
             '''
        cur.execute(sql_command)
        conn.commit()
        res = requests.get(image_url, stream=True)
        if res.status_code == 200:
            with open(imagePath,'wb') as file_path:
                for chunck in res:
                    file_path.write(chunck)
            print("The Image has been downloaded")
        else:
            print("Error!! HTTP Request failed")
        try:
            cur.execute("insert into activitiesList values(?,?,?,?,?,?)",(name,description,imageName,time,location,limit))
            conn.commit()
            return jsonify({'status': 'success', 'message': 'Create successfully'})
        except:
            return jsonify({'status': 'error', 'message': 'Create new activity failed.'})
    return render_template('createActivities.html')

@app.route('/deleteActivity', methods = ['GET', 'POST'])
def delete():
    if request.method == 'POST':
        activity_id = request.json.get('activityId') 
        cur.execute("delete from activitiesList where Name = ?",(activity_id,))
        table_name = str(activity_id)
        sql = f"DROP TABLE {table_name};"
        cur.execute(sql)
        cur.execute("delete from SignUp where ActivityName = ?",(activity_id,))
        conn.commit()
        return 'Activity deleted', 200

    return 'Invalid request', 400

@app.route('/admin/manage', methods = ['GET', 'POST'])
def manage():
    if request.method == 'POST':
        activity_id = request.args.get('activityId')
        new_description = request.values["activity-description"]
        new_link = request.values["image-download-link"]
        new_image = request.values["image-save-name"]
        new_time = request.values["activity-time"]
        new_location = request.values["activity-location"]
        new_limit = int(request.values["activity-limit"])
        table_name = str(activity_id)
        sql = f"select Name from {table_name};"
        cur.execute(sql)
        ptcp = cur.fetchall()
        if  int(new_limit) == 0:
            flash("參加人數不能為0", "erroe")
            activity_id = request.args.get('activityId')
            cur.execute("select * from activitiesList where Name = ?",(activity_id,))
            activityInfo = cur.fetchall()
            return render_template('manageActivity.html',
                                activityName = activity_id,
                                default_description = activityInfo[0][1], 
                                default_image = activityInfo[0][2],
                                default_time=activityInfo[0][3], 
                                default_location=activityInfo[0][4], 
                                default_limit=activityInfo[0][5])
        if len(ptcp) > int(new_limit):
            flash("報名人數已經大於輸入的參加人數", "error")
            activity_id = request.args.get('activityId')
            cur.execute("select * from activitiesList where Name = ?",(activity_id,))
            activityInfo = cur.fetchall()
            return render_template('manageActivity.html',
                                activityName = activity_id,
                                default_description = activityInfo[0][1], 
                                default_image = activityInfo[0][2],
                                default_time=activityInfo[0][3], 
                                default_location=activityInfo[0][4], 
                                default_limit=activityInfo[0][5])
        else:
            if new_link != "" :
                res = requests.get(new_link, stream=True)
                if res.status_code == 200:
                    with open(new_image,'wb') as file_path:
                        for chunck in res:
                            file_path.write(chunck)
                            print("The Image has been downloaded")
                        else:
                            print("Error!! HTTP Request failed")    
            cur.execute("update ActivitiesList set Description = ? WHERE Name = ?", (new_description,activity_id))
            cur.execute("update ActivitiesList set Image = ? WHERE Name = ?", (new_image,activity_id))
            cur.execute("update ActivitiesList set Time = ? WHERE Name = ?", (new_time,activity_id))
            cur.execute("update ActivitiesList set Location = ? WHERE Name = ?", (new_location,activity_id))
            cur.execute("update ActivitiesList set 'Limit' = ? WHERE Name = ?", (new_limit,activity_id))
            conn.commit()
            flash("活動資料修改成功", "success")
            return redirect(url_for('admin'))
    activity_id = request.args.get('activityId')
    cur.execute("select * from activitiesList where Name = ?",(activity_id,))
    activityInfo = cur.fetchall()
    return render_template('manageActivity.html',
                           activityName = activity_id,
                           default_description = activityInfo[0][1], 
                           default_image = activityInfo[0][2],
                           default_time=activityInfo[0][3], 
                           default_location=activityInfo[0][4], 
                           default_limit=activityInfo[0][5])


@app.route('/activities', methods = ['GET', 'POST'])
def activities():
    user = session.get('username')
    cur.execute("SELECT Image, Name FROM activitiesList")
    activities = cur.fetchall()
    cur.execute("SELECT Name, Phone, sign_up_mail, Address, Id, BirthDate FROM AccountList where Username = ?",(user,))
    UserInfo = cur.fetchall()
    cur.execute("SELECT ActivityName from SignUp where Username = ?",(user,))
    acts = cur.fetchall()
    all_act = []

    for act in acts:
        print(act)
        
        cur.execute("SELECT Name, Time, Location from ActivitiesList where Name = ?", (act[0],))
        tmp = cur.fetchone()
        
      
        if tmp:
            all_act.append(tmp)
    
    return render_template('activitiespage.html',
                            username = user,
                            activities=activities,
                            acts = all_act,
                            default_n = UserInfo[0][0],
                            default_p = UserInfo[0][1],
                            default_m = UserInfo[0][2],
                            default_a = UserInfo[0][3],
                            default_id = UserInfo[0][4],
                            default_b = UserInfo[0][5])

@app.route('/resetPassword', methods = ['GET', 'POST'])
def resetstep1():
    if request.method == 'POST':
        mail = request.values['resetEmail']
        cur.execute("select * from AccountList where mail = ?",(mail,))
        p = cur.fetchall()
        if p == []:
            return jsonify({'status': 'error', 'message': 'email not correct!'})
        else:
            session['email'] = mail  # Storing the email in the session
            characters = string.ascii_uppercase + string.digits
            idenCode = ''.join(random.choice(characters) for i in range(6))
            session['veri'] = idenCode
            msg=MIMEMultipart() 
            msg["From"] = "joseph910905@gmail.com"
            msg["To"] = mail
            msg["Subject"] = "verification code"
            msg_send = idenCode
            msg.attach(MIMEText(msg_send))
            acc="joseph910905@gmail.com"
                                
            with smtplib.SMTP(host="smtp.gmail.com", port="587") as smtp: 
                    smtp.ehlo() 
                    smtp.starttls()  
                    smtp.login(acc,"ccpofflososaylqz")  
                    smtp.send_message(msg)  
                    print("Complete!")
            return jsonify({'status': 'success', 'message': ''})
    return render_template('resetPassword.html')

@app.route('/resetPassword/identify', methods = ['GET', 'POST'])
def resetstep2():
    mail = session.get('email')

    if request.method == 'POST':
        input_vc = request.values["verificationCode"]
        vericode = session.get('veri')
        if input_vc == vericode:
            return jsonify({'status': 'success', 'message': ''})   
        else:
            return jsonify({'status': 'error', 'message': 'incorrect verification code'}) 
    return render_template('emailidentify.html',email = mail)

@app.route('/resetPassword/resend', methods=['GET', 'POST'])
def resend_verification():
    if request.method == 'POST':
        mail = session.get('email')
        characters = string.ascii_uppercase + string.digits
        new_veriCode = ''.join(random.choice(characters) for i in range(6))

        session['veri'] = new_veriCode

        msg = MIMEMultipart()
        msg["From"] = "joseph910905@gmail.com"
        msg["To"] = mail
        msg["Subject"] = "verification code"
        msg_send = new_veriCode
        msg.attach(MIMEText(msg_send))

        acc = "joseph910905@gmail.com"
        with smtplib.SMTP(host="smtp.gmail.com", port="587") as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(acc, "ccpofflososaylqz")
            smtp.send_message(msg)
            print("Complete!")
            
        return jsonify({'status': 'success', 'message': 'New verification code sent'})

    return render_template('emailidentify.html', email=mail)

@app.route('/resetPassword/reset', methods = ['GET', 'POST'])
def resetsteplast():
    if request.method == 'POST':
        newpass = request.values['newPassword']
        confpass = request.values['confirmPassword']
        if newpass == confpass:
            mail = session.get('email')
            print(newpass)
            cur.execute("update AccountList set Password = ? where mail = ?",(newpass,mail))
            conn.commit()
            return jsonify({'status': 'success', 'message': 'Reset your password successfully !'})   
        else:
            return jsonify({'status': 'error', 'message': 'Confirm password is different from New password'})
    return render_template('reset.html')

@app.route('/ChangeInfo', methods=['POST'])
def change_info():
    try:
        data = request.json
        user = session.get('username')

        cur.execute("UPDATE AccountList SET Name = ? WHERE Username = ?", (data.get('name'), user))
        cur.execute("UPDATE AccountList SET Phone = ? WHERE Username = ?", (data.get('phone'), user))
        cur.execute("UPDATE AccountList SET Address = ? WHERE Username = ?", (data.get('address'), user))
        cur.execute("UPDATE AccountList SET Id = ? WHERE Username = ?", (data.get('idNumber'), user))
        cur.execute("UPDATE AccountList SET sign_up_mail = ? WHERE Username = ?", (data.get('email'), user))
        cur.execute("UPDATE AccountList SET BirthDate = ? WHERE Username = ?", (data.get('birthdate'), user))

        conn.commit()
        return jsonify({'success': True, 'message': '資料修改成功！'})
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': '資料修改失敗！'})

@app.route('/signup', methods=['GET','POST'])
def activities_signup():
    activity_id = request.args.get('activityId')
    user = session.get('username')
    if request.method == 'POST':
        cur.execute("select * from activitiesList where Name = ?",(activity_id,))
        activityInfo = cur.fetchall()
        user = session.get('username')
        signup_n = request.values['name']
        signup_p = request.values['phone']
        signup_e = request.values['email']
        signup_id = request.values['idNumber']
        signup_a = request.values['address']
        signup_b = request.values['birthdate']
        table_name = str(activity_id)
        sql = f"select Name from {table_name};"
        cur.execute(sql)
        ptcp_n = cur.fetchall()
        ptcp = len(ptcp_n)
        cur.execute("select *from SignUp where ActivityName = ? and Username = ?",(activity_id,user))
        p_of_a = cur.fetchall()
        if ptcp >= activityInfo[0][5]:
            flash("人數已滿", "erroe")
            return redirect(url_for('activities'))
        elif len(p_of_a) != 0:
            flash("已報名此活動，請誤重複報名", "erroe")
            return redirect(url_for('activities'))
        else:
            msg=MIMEMultipart() 
            msg["From"] = "joseph910905@gmail.com"
            msg["To"] = signup_e
            msg["Subject"] = "報名成功"
            msg_send = "您已成功報名活動:" + activity_id
            msg.attach(MIMEText(msg_send))
            acc="joseph910905@gmail.com"
                                
            with smtplib.SMTP(host="smtp.gmail.com", port="587") as smtp: 
                    smtp.ehlo() 
                    smtp.starttls()  
                    smtp.login(acc,"ccpofflososaylqz")  
                    smtp.send_message(msg)  
                    print("Complete!")
            table_name = str(activity_id)
            sql = f"INSERT INTO {table_name} (Username, Name, Phone, email, Address, Id, DateBirth) VALUES (?, ?, ?, ?, ?, ?, ?);"
            cur.execute(sql, (user, signup_n, signup_p, signup_e, signup_a, signup_id, signup_b))
            cur.execute("INSERT INTO SignUp VALUES (?, ?)", (user, activity_id))
            conn.commit()
            flash("報名成功", "success")
            return redirect(url_for('activities'))
    
    cur.execute("select * from activitiesList where Name = ?",(activity_id,))
    activityInfo = cur.fetchall()
    cur.execute("select * from AccountList where Username = ?",(user,))
    UserInfo = cur.fetchall()
    table_name = str(activity_id)
    sql = f"select Name from {table_name};"
    cur.execute(sql)
    ptcp = len(cur.fetchall())
    return render_template('activities_sign_up.html',
                            image_url = activityInfo[0][2],
                            activityName = activityInfo[0][0],
                            activityDescription = activityInfo[0][1],
                            activityTime = activityInfo[0][3], 
                            activityLocation = activityInfo[0][4],
                            activityLimit = activityInfo[0][5],
                            currentParticipants = ptcp,
                            nameValue = UserInfo[0][3],
                            phoneValue = UserInfo[0][4], 
                            emailValue = UserInfo[0][5], 
                            idNumberValue = UserInfo[0][7],
                            addressValue = UserInfo[0][6],
                            birthdateValue = UserInfo[0][8]
                            )

@app.route('/cancel_signup', methods=['GET','POST'])
def cancel_signup():
    activity_id = request.args.get('activityId')
    user = session.get('username')
    table_name = str(activity_id)
    sql = f"select email from {table_name} where Username = ?;"
    cur.execute(sql, (user,))
    email = cur.fetchone()
    msg=MIMEMultipart() 
    msg["From"] = "joseph910905@gmail.com"
    msg["To"] = email[0]
    msg["Subject"] = "活動取消通知"
    msg_send = "您已成功取消活動-" + str(activity_id)
    msg.attach(MIMEText(msg_send))
    acc="joseph910905@gmail.com"
                                
    with smtplib.SMTP(host="smtp.gmail.com", port="587") as smtp: 
        smtp.ehlo() 
        smtp.starttls()  
        smtp.login(acc,"ccpofflososaylqz")  
        smtp.send_message(msg)  
        print("Complete!")
    sql = f"delete from {table_name} where Username = ?;"
    cur.execute(sql, (user,))
    cur.execute("delete from SignUp where Username = ? and ActivityName = ?",(user, activity_id))
    conn.commit()
    return redirect(url_for('activities'))

@app.route('/admin/list', methods=['GET','POST'])
def list():
    activity_id = request.args.get('activityId')
    table_name = str(activity_id)
    sql = f"select * from {table_name} ;"
    cur.execute(sql)
    participants = cur.fetchall()
    return render_template('list.html',activityname = activity_id,participants =participants)

if __name__ == '__main__':
    conn = sqlite3.connect(r"C:\Users\yaochiliao\Desktop\VSCODE\資料庫程式設計\資料庫專題\login.db", check_same_thread=False)
    cur = conn.cursor()
    app.debug = True
    app.run()
    conn.commit()
    conn.close()
