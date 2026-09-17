from functools import wraps
from flask import Blueprint,render_template,request,redirect,url_for,session,flash
from werkzeug.security import check_password_hash, generate_password_hash
from .db import connect
from .services import profile,prediction,factors,drift,goals,goal_risk,what_if,decision_sim,knowledge_graph,timeline,analytics

main=Blueprint("main",__name__)

def db():
    from flask import current_app
    return connect(current_app.config["DATABASE"])

def login_required(fn):
    @wraps(fn)
    def wrapper(*a,**kw):
        return fn(*a,**kw) if "uid" in session else redirect(url_for("main.login"))
    return wrapper

@main.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        con=db();u=con.execute("SELECT * FROM users WHERE username=?",[request.form.get("username","")]).fetchone();con.close()
        if u and check_password_hash(u["password_hash"],request.form.get("password","")):
            session["uid"]=u["id"];session["username"]=u["username"];return redirect(url_for("main.dashboard"))
        flash("Invalid username or password.","error")
    return render_template("login.html")

@main.route("/register", methods=["GET", "POST"])
def register():
    if "uid" in session:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if len(username) < 3:
            flash("Username must contain at least 3 characters.", "error")
            return render_template("register.html")
        if len(password) < 6:
            flash("Password must contain at least 6 characters.", "error")
            return render_template("register.html")
        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        con = db()
        existing = con.execute("SELECT id FROM users WHERE username=?", [username]).fetchone()
        if existing:
            con.close()
            flash("That username is already registered. Please choose another.", "error")
            return render_template("register.html")

        uid = con.execute(
            "INSERT INTO users(username,password_hash) VALUES(?,?)",
            (username, generate_password_hash(password))
        ).lastrowid
        con.commit()
        con.close()

        session["uid"] = uid
        session["username"] = username
        flash("Account created successfully. Your LifeTwin is ready to learn from your activity.", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("register.html")


@main.route("/logout")
def logout():session.clear();return redirect(url_for("main.login"))

@main.route("/")
def index():return redirect(url_for("main.dashboard" if "uid" in session else "main.login"))

@main.route("/dashboard")
@login_required
def dashboard():
    con=db();uid=session["uid"];p=profile(con,uid);pred,conf=prediction(con,uid);risks=goal_risk(con,uid);dr=drift(con,uid);con.close()
    return render_template("dashboard.html",profile=p,pred=pred,confidence=conf,risks=risks,drift=dr)

@main.route("/twin")
@login_required
def twin():
    con=db();uid=session["uid"];p=profile(con,uid);f=factors(con,uid);mem=[dict(x) for x in con.execute("SELECT * FROM memories WHERE user_id=? ORDER BY id DESC",[uid]).fetchall()];con.close()
    return render_template("twin.html",profile=p,factors=f,memories=mem)

@main.route("/predictions",methods=["GET"])
@login_required
def predictions():
    con=db();uid=session["uid"];pred,conf=prediction(con,uid)
    pid=con.execute("INSERT INTO predictions(user_id,predicted,confidence) VALUES(?,?,?)",[uid,pred[0]["label"],conf]).lastrowid
    log=[dict(x) for x in con.execute("SELECT * FROM predictions WHERE user_id=? ORDER BY id DESC LIMIT 8",[uid]).fetchall()]
    con.commit();con.close()
    return render_template("predictions.html",pred=pred,confidence=conf,prediction_id=pid,actuals=log)

@main.route("/feedback",methods=["POST"])
@login_required
def feedback():
    con=db();uid=session["uid"];pid=request.form.get("prediction_id");actual=request.form.get("actual","");text=request.form.get("feedback","")[:500]
    con.execute("UPDATE predictions SET actual=? WHERE id=? AND user_id=?",[actual,pid,uid])
    con.execute("INSERT INTO feedback(user_id,prediction_id,feedback) VALUES(?,?,?)",[uid,pid,text or "Prediction reviewed"])
    if text:con.execute("INSERT INTO memories(user_id,memory_type,content,confidence) VALUES(?,?,?,?)",[uid,"feedback","User feedback: "+text,.65])
    con.commit();con.close();flash("Feedback added. The twin will use it as new evidence.","success");return redirect(url_for("main.predictions"))

@main.route("/what-if",methods=["GET","POST"])
@login_required
def whatif():
    v={"study_hours":2.0,"sleep":7.0,"exercise":3.0,"switches":3.0};result=None
    if request.method=="POST":
        for k in v:
            try:v[k]=float(request.form.get(k,v[k]))
            except:pass
        con=db();result=what_if(con,session["uid"],**v);con.close()
    return render_template("whatif.html",values=v,result=result)

@main.route("/decision",methods=["GET","POST"])
@login_required
def decision():
    a=request.form.get("option_a","High-salary onsite role");b=request.form.get("option_b","Flexible remote role");result=None
    if request.method=="POST":
        con=db();result=decision_sim(con,session["uid"],a,b);con.close()
    return render_template("decision.html",result=result,a=a,b=b)

@main.route("/knowledge")
@login_required
def knowledge():
    nodes,links=knowledge_graph();return render_template("knowledge.html",nodes=nodes,links=links)

@main.route("/timeline")
@login_required
def timeline_page():
    con=db();data=timeline(con,session["uid"]);con.close();return render_template("timeline.html",timeline=data)

@main.route("/goals")
@login_required
def goals_page():
    con=db();gs=goals(con,session["uid"]);risks=goal_risk(con,session["uid"]);con.close();return render_template("goals.html",goals=gs,risks=risks)

@main.route("/analytics")
@login_required
def analytics_page():
    con=db();a=analytics(con,session["uid"]);dr=drift(con,session["uid"]);con.close();return render_template("analytics.html",a=a,drift=dr)

@main.app_context_processor
def globals():
    return {"app_name":"LifeTwin AI","username":session.get("username","")}
