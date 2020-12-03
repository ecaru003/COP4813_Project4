from flask import Flask, render_template, request, url_for
from flask_pymongo import PyMongo
import main_functions
from flask_wtf import FlaskForm
import requests
from wtforms import StringField, DecimalField, SelectField, DateField

categories = ["rent","electricity","water","insurance","restaurants",
              "groceries","gas","college","party","mortgage", "other"]

currencies = [("USD", "United States Dollar"), ("GBP", "Pound sterling"), ("CAD", "Canadian Dollar"), ("EUR", "Euro"),
              ("JPY", "Japanese Yen"), ("AUD", "Australian Dollar"), ("BRL", "Brazilian real"),
              ("CNY", "Chinese Yuan")]


app = Flask(__name__)
app.config["SECRET_KEY"]="Ks4ShpgSX6ueWU83"
creds = main_functions.read_from_file("jsons/credentials.json")
app.config["MONGO_URI"] = "mongodb+srv://{0}:{1}@learningmongodb.bxoo1.mongodb.net/{2}?retryWrites=true&w=majority".format(creds["username"],creds["password"], creds["database"])
mongo = PyMongo(app)

class Expenses(FlaskForm):
    description = StringField("Expense Description")
    select_cats = []
    for cat in categories:
        select_cats.append((cat, cat.capitalize()))
    category = SelectField("Expense Category", choices=select_cats)
    cost = DecimalField("Expense Cost")
    curr = SelectField("Currency", choices=currencies)
    date = DateField("Expense Date")

def currency_convert(cost, currency):
    if currency == "USD":
        return cost
    url_1="http://apilayer.net/api/live?access_key="
    url_2="&currencies=GBP,CAD,EUR,JPY,AUD,BRL,CNY&source=USD&format=1"
    url = url_1 + creds["currency_api_key"] + url_2
    exchange = requests.get(url).json()
    return str(round(float(cost) / float(exchange["quotes"]["USD"+currency])))

def get_total_expenses(category):
    expenses = mongo.db.expenses.find({"category" : category})
    cat_total = 0
    for exp in expenses:
        cat_total += float(exp["cost"])
    return cat_total

@app.route('/')
def index():
    my_expenses = mongo.db.expenses.find()
    total_cost = 0
    for i in my_expenses:
        total_cost += float(i["cost"])
    expensesByCategory = []
    for cat in categories:
        tup = (cat,get_total_expenses(cat))
        expensesByCategory.append(tup)
    return render_template("index.html", expenses=total_cost, expensesByCategory=expensesByCategory)

@app.route('/addExpenses',methods=["GET","POST"])
def addExpenses():
    expensesForm = Expenses(request.form)
    if request.method == "POST":
        desc = request.form["description"]
        cate = request.form["category"]
        cost = request.form["cost"]
        curr = request.form["curr"]
        date = request.form["date"]

        try:
            input = float(cost)
            cost = currency_convert(input, curr)
        except ValueError:
            return render_template("addExpenses.html", form=expensesForm, valueError=True)

        entry = {"description":desc, "category":cate, "cost":cost,"date":date}
        mongo.db.expenses.insert_one(entry)
        return render_template("expenseAdded.html")
    return render_template("addExpenses.html",form=expensesForm, valueError=False)

app.run()