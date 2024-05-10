import os
from flask import Flask, render_template, request, redirect, url_for,flash, session
import pymysql, string, random
from send_mail import envoicode
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
from datetime import datetime
from flask import jsonify
import math 
from flask_paginate import Pagination, get_page_parameter
import math
import plotly.graph_objs as go
import plotly.express as px


app = Flask(__name__)




# flash message
app.secret_key = 'message' 

# connexion à la base de donnée

conn = pymysql.connect(
    host='localhost',
    user='root',
    password="",
    db='supermarche',)

# Initialiser l'extension Bcrypt pour le hachage des mots de passe
bcrypt = Bcrypt(app)


UPLOAD_FOLDER = 'static/image/upload'  # Remplacez par le chemin de votre choix
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# hashed_password = bcrypt.generate_password_hash('kra1234')
# print(hashed_password)

# cursor = conn.cursor()
# # Exécutez la requête SQL en utilisant des paramètres pour éviter les injections SQL
# sql = "INSERT INTO administrateur (nom, prenom, telephone, email,login, mot_pass) VALUES (%s, %s, %s, %s, %s, %s)"
# values = ('Kra', 'Adephe', '56545678', 'sidiksoum344@gmail.com', 'kra1234', hashed_password)

# # Exécutez la requête avec les valeurs
# cursor.execute(sql, values)
# conn.commit()
# ===================================Admin espace ==============================

# Définir une route et la fonction associée

@app.route('/')
def accueil():
    # Rendre le template index.html
    return render_template('accueil.html')

@app.route('/login')
def login():
    
    # Rendre le template index.html
    return render_template('connexion/login.html')

@app.route('/code/')
def code():
    # Rendre le template index.html
    return render_template('connexion/code.html')

@app.route('/nouveau_mot/')
def nouveau_mot():
    # Rendre le template index.html
    return render_template('connexion/nouveau_mot.html')

@app.route('/recuperation/')
def recuperation():
    # Rendre le template index.html
    return render_template('connexion/recuperation.html')

# connexion de l'admin
@app.route('/admin/', methods=["POST", "GET"])
def adminIndex():
    if request.method == 'POST':
        username = request.form.get('login')
        password = request.form.get('password')
        if not (username and password):
            flash('Please fill all the fields', 'danger')
            return redirect('/admin/')
        else:
            cursor = conn.cursor()
            query = "SELECT * FROM administrateur WHERE login=%s"
            cursor.execute(query, (username,))
            admin = cursor.fetchone()
            cursor.close()
            if admin and bcrypt.check_password_hash(admin[6], password):
                session['admin_id'] = admin[0]
                session['admin_name'] = admin[1]
                # flash('Login Successfully', 'success')
                return redirect('/admin/dashboard')
            else:
                flash('Invalid Username or Password', 'danger')
                return redirect(url_for('adminIndex'))
    else:
        return render_template('admin/login.html')

@app.route('/admin/dashboard', methods=["POST", "GET"])
def base():
    if 'admin_id' in session:  # Vérifie si l'administrateur est connecté
         
         cursor=conn.cursor()
         cursor.execute('''
        SELECT count(*) from vente''')
         total_ventes = cursor.fetchone()
         conn.commit
         cursor.close
         
         cursor=conn.cursor()
         cursor.execute(''' select count(*) from produit ''')
         total_produit = cursor.fetchone()
         conn.commit
         cursor.close

         cursor=conn.cursor()
         cursor.execute(''' select count(*) from client ''')
         total_client = cursor.fetchone()
         conn.commit
         cursor.close
        
         cursor=conn.cursor()
         cursor.execute(''' select SUM(Prix) as CA from produit ''')
         total_CA=cursor.fetchone()
         conn.commit
         cursor.close

         cursor=conn.cursor()
         cursor.execute('select client.nom,client.sexe,produit.produit,produit.Prix,Date from vente,produit,client WHERE vente.produit_id=produit.id and vente.client_id=client.id ')
         dase=cursor.fetchall()
         conn.commit
         cursor.close
         
        
         
         return render_template('admin/dashboard.html', total_ventes=total_ventes,  total_produit=total_produit ,  total_client=total_client , total_CA=total_CA, dase=dase )
    else:
        flash('Please login first', 'danger')  # Message flash indiquant que l'utilisateur doit d'abord se connecter
        return redirect('/admin')  # Redirige vers la page de connexion


# admin logout
@app.route('/admin/logout')
def adminLogout():
    if 'admin_id' in session:
        session.pop('admin_id')
        session.pop('admin_name')
        session.pop('_flashes', None)
        # flash('You have been logged out', 'success')
    return redirect('/admin/')


# ================================Admin Mot de passe oublié================================

@app.route('/forgot_password', methods=["GET", "POST"])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            flash('Please provide your email address', 'danger')
            return redirect('/recuperation/')

        cursor = conn.cursor()
        query = "SELECT * FROM administrateur WHERE email=%s"
        cursor.execute(query, (email,))
        admin = cursor.fetchone()
        cursor.close()

        if not admin:
            flash('This email is not registered', 'danger')
            return redirect('/recuperation/')
        code = ''.join(random.choices(string.digits, k=5))
        session['code'] = code
        session['email'] = email
        envoicode(code, email)
        flash('A verification code has been sent to your email', 'success')
        return redirect('/code/')

    return redirect('/recuperation/')

@app.route('/forgot_password_code', methods=["GET", "POST"])
def forgot_password_code():
    if request.method == 'POST':
        code = session.get('code')
        email = session.get('email')
        if not (code and email):
            flash('Invalid code or email', 'danger')
            return redirect('/forgot_password')

        codesaisir = request.form.get("code")
        if codesaisir == code:
            return redirect('/nouveau_mot')
        else:
            flash('Incorrect verification code', 'danger')
            return redirect('/code/')

    return redirect('/code/')


@app.route('/change_password', methods=["GET", "POST"])
def change_password():
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        email = session.get('email')

        if not (password and confirm_password):
            flash('Please fill all the fields', 'danger')
            return redirect('/change_password')

        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect('/change_password')

        cursor = conn.cursor()
        mot_pass = bcrypt.generate_password_hash(password).decode('utf-8')
        query = "UPDATE administrateur SET mot_pass=%s WHERE email=%s"
        cursor.execute(query, (mot_pass, email))
        conn.commit()
        cursor.close()

        flash('Password updated successfully', 'success')
        session.pop('email', None)
        session.pop('code', None)
        return redirect('/')
        
    return render_template('connexion/nouveau_mot.html')

# ==========================Gestion des membres========================
@app.route('/admin/ajouter_membre', methods=['GET', 'POST'])
def ajouter_membre():
    utilisateur = None
    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        email = request.form['email']
        mot_pass = request.form['password']
        telephone = request.form['tel']
        login = request.form['login']
        poste = request.form['poste']
        photo = request.files['image']  

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM utilisateur WHERE email = %s", (email,))
        utilisateur = cursor.fetchone()

        if utilisateur:
            flash('Cet email est déjà utilisé.', 'danger')
            return redirect(url_for('ajouter_membre'))

        if mot_pass != request.form['confmotpass']:
            flash('Les mots de passe ne correspondent pas.', 'danger')
            return redirect(url_for('ajouter_membre'))

        mot_pass = bcrypt.generate_password_hash(mot_pass).decode('utf-8')

        filename = secure_filename(photo.filename)
        photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        cursor.execute("INSERT INTO utilisateur (nom, prenom,poste,telephone, email, login, mot_pass,image) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                       (nom, prenom, poste,telephone,email,login, mot_pass, filename))
        conn.commit()

        cursor.execute("SELECT * FROM utilisateur WHERE email = %s", (email,))
        utilisateurs = cursor.fetchone()
        cursor.close()
        
        # flash('Nouveau membre ajouté avec succès.', 'success')
        
        return redirect('/admin/equipe/')

    return redirect('/admin/equipe/')

@app.route('/admin/equipe/')
def equipe():
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM utilisateur")
    utilisateurs = cursor.fetchall()
    cursor.close()

    return render_template('membres/equipe.html', utilisateurs=utilisateurs)


@app.route('/userlogin', methods=['GET', 'POST'])
def userLogin():
    if request.method == 'POST':
        email = request.form.get('email')
        print ('Email: %s' % email)
        mot_pass = request.form.get('password')
        print ('Password: %s' % mot_pass)

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM utilisateur WHERE email = %s", (email,))
        utilisateur = cursor.fetchone()

        if utilisateur and bcrypt.check_password_hash(utilisateur[7], mot_pass):
            # Si les informations sont correctes, l'utilisateur est connecté
            session['logged_in'] = True
            session['utilisateur_id'] = utilisateur[0]
            session['email'] = email
            session['nom'] = utilisateur[1]
            session['poste'] = utilisateur[3]  # Poste de l'utilisateur
            flash('Connexion réussie.', 'success')
            return redirect(url_for('userDashboard'))

        else:
            flash('Email ou mot de passe incorrect.', 'danger')

    return render_template('connexion/userlogin.html')

@app.route('/userlogout')
def userLogout():
    if 'logged_in' in session:
        session.clear()  # Effacer toutes les informations de session
        # flash('Vous êtes déconnecté.', 'success')
    return redirect(url_for('userLogin'))

@app.route('/dashboard/vendeur')
def dashboard_vendeur():
    return render_template('membres/dashboard_vendeur.html')

@app.route('/dashboard/gestionnaire')
def dashboard_gestionnaire():
    return render_template('membres/dashboard_gestionnaire.html')

@app.route('/user/dashboard')
def userDashboard():
    if 'logged_in' in session:
        if 'poste' in session:
            if session['poste'] == 'vendeur':
                return redirect(url_for('dashboard_vendeur'))
            elif session['poste'] == 'gestionnaire':
                return redirect(url_for('dashboard_gestionnaire'))
        else:
            return redirect(url_for('accueil'))  # Redirection par défaut si le poste n'est pas spécifié
    else:
        return redirect(url_for('userLogin'))
    
@app.route('/index')
def index():
     # Rendre le template index.html
     return render_template('index.html')

from flask_paginate import Pagination, get_page_args
import math

@app.route('/Produit/')
def Produit():
    
    cursor = conn.cursor()
    
    # Sélectionner les éléments de la page actuelle
    cursor.execute('SELECT * FROM produit')
    total = cursor.rowcount
    cursor.execute('SELECT * FROM produit LIMIT 15')
    resultat = cursor.fetchall()
    # cursor.close()
    return render_template("Produit.html", resultat=resultat)


# ajoutproduit
@app.route('/ajoutprod/', methods=['GET', 'POST'])
def ajoutprod():
   
    if request.method == 'POST':
        
        # Récupéréation des informations du formulaire
        Nom = request.form.get('nom')  
        categorie = request.form.get('categorie' )
        prix = request.form.get('prix')
        

       
        cursor = conn.cursor()
        
        # Exécution d'une requête SQL pour insérer les données du Produit dans la table 'Produit'
        cursor.execute(
            "INSERT INTO produit (nom,Type,Prix) VALUES ( %s, %s, %s)",
            (Nom, categorie, prix))

        # Validation de la transaction en enregistrant les modifications dans la base de données
        conn.commit()
     
        cursor.close()

        # Redirection vers la page 'Produit' après l'ajout du Produit dans la base de données
        return redirect(url_for('Produit'))

    return render_template('ajoutprod.html')

# modifier produit

@app.route("/modproduit/<int:id>", methods=['POST','GET'])
def modproduit(id):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM produit WHERE id = %s", (id,))
    resultat = cursor.fetchone()
    cursor.close()
    
    if request.method == 'POST':
        # Récupération des informations du formulaire
        nom = request.form.get('nom')  
        categorie = request.form.get('categorie')
        prix = request.form.get('prix')
        
        cursor = conn.cursor()
        cursor.execute('UPDATE produit SET produit = %s, Type = %s, Prix = %s WHERE id = %s', (nom, categorie, prix, id))
        conn.commit()
        cursor.close()
        
        return redirect(url_for('Produit', id=id))
    
    return render_template('modproduit.html', resultat=resultat)

# modclient

@app.route("/modclient/<int:id>", methods=['POST','GET'])
def modclient(id):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM client WHERE id = %s", (id,))
    resultat = cursor.fetchone()
    cursor.close()
    
    if request.method == 'POST':
        # Récupération des informations du formulaire
        nom = request.form.get('nom')  
        sexe = request.form.get('sexe')
        
        cursor = conn.cursor()
        cursor.execute('UPDATE client SET nom = %s, sexe = %s WHERE id = %s', (nom, sexe, id))
        conn.commit()
        cursor.close()
        
        return redirect(url_for('clients', id=id))
    
    return render_template('modclient.html', resultat=resultat)

# ajoutclient
@app.route('/ajoutclient/', methods=['GET', 'POST'])
def ajoutclient():
   
    if request.method == 'POST':
        
        # Récupéréation des informations du formulaire
        Nom = request.form.get('nom')  
        sexe = request.form.get('sexe' )
       
        

       
        cursor = conn.cursor()
        
        # Exécution d'une requête SQL pour insérer les données du Produit dans la table 'Produit'
        cursor.execute(
            "INSERT INTO client (nom,sexe) VALUES ( %s, %s)",
            (Nom, sexe, ))

        # Validation de la transaction en enregistrant les modifications dans la base de données
        conn.commit()
     
        cursor.close()

        # Redirection vers la page 'Produit' après l'ajout du Produit dans la base de données
        return redirect(url_for('clients'))

    return render_template('ajoutclient.html')


@app.route('/stock/', methods=["post", "get"])
def stock():

    return render_template("stock.html")

@app.route('/achats/', methods=["post", "get"])
def achats():

    return render_template("achats.html")

@app.route('/clients/', methods=["post", "get"])
def clients():
    cursor = conn.cursor()
    
    # Sélectionner les éléments de la page actuelle

    cursor.execute('SELECT * FROM client')
    cursor.execute('SELECT * FROM client LIMIT 15')
    resultat = cursor.fetchall()




    cursor.close()

    return render_template("clients.html", resultat=resultat)


@app.route('/Supproduit/<int:id>', methods=['GET', 'POST'])
def supproduit(id):

    cursor = conn.cursor()

    # if request.method == 'GET':
        # Récupérer les détails du produit par ID pour confirmation
    # cursor.execute("SELECT * FROM produit WHERE id = %s", (id,))
    # produit = cursor.fetchone()  # Obtenir le produit à supprimer

        # if not produit:
        #     flash("Produit introuvable.", "danger")
        #     return redirect(url_for('Produit'))

        # return render_template(
        #     'supproduit.html',
        #     produit=produit  # Passer le produit au template pour confirmation
        # )
        # try:
            # Supprimer le produit par ID
    cursor.execute("DELETE FROM produit WHERE id = %s", (id,))
    conn.commit()  # Confirmer la suppression
    flash("Produit supprimé avec succès!", "success")
        # except Exception as e:
        #     conn.rollback()  # Annuler en cas d'erreur
        #     flash(f"Erreur lors de la suppression du produit : {e}", "danger")
        # finally:
    conn.close()  # Fermer la connexion à la base de données

        # Redirection vers la liste des produits après suppression
    return redirect(url_for('Produit'))

@app.route('/profil/')
def profil():
    # Rendre le template index.html
    return render_template('profil.html')

@app.route('/profit_gest/')
def profit_gest():
    # Rendre le template index.html
    return render_template('profit_gest.html')

@app.route("/ventes")
def ventes():
    cursor = conn.cursor()
    cursor.execute('SELECT client.nom, client.sexe, produit.produit, produit.Prix, vente.Date, vente.Quantitevendu, (produit.Prix * vente.Quantitevendu) AS PrixTotal FROM vente JOIN produit ON vente.produit_id = produit.id JOIN client ON vente.client_id = client.id;') 



    resultat = cursor.fetchall()
    cursor.close()

    return render_template("ventes.html", resultat=resultat)


# visualisation 

from flask import render_template

# Nouvelle route pour la visualisation des ventes
from flask import render_template

@app.route('/rapport/')
def rapport():
    # Effectuez les requêtes SQL pour récupérer les données nécessaires
    # Exécuter les deux requêtes ensemble
    cursor = conn.cursor()

    # Exécuter les deux requêtes ensemble
    cursor.execute('''
        SELECT DATE_FORMAT(Date, '%Y-%m') AS year, COUNT(id) AS count 
        FROM vente GROUP by year
        order by year
    ''')

    # Récupérer les résultats de la première requête
    total_ventes = cursor.fetchone()[0]

    # Récupérer les résultats de la deuxième requête
    ventes_par_mois = cursor.fetchall()
    year = []  # Liste pour stocker les années
    data = []  # Liste pour stocker les valeurs

    for item in ventes_par_mois:
        year.append(item[0])  # Ajouter l'année du tuple à la liste des années
        data.append(item[1])
   
    fig = px.line(
        ventes_par_mois,
          x=year,
            y=data,
            template='plotly_dark'
                  )
    chart = fig.to_html()
    
    cursor.close()

    # Passez les données récupérées au template HTML pour affichage
    return render_template('rapport.html', total_ventes=total_ventes, ventes_par_mois=ventes_par_mois, chart = chart)

#  ajout_vente

@app.route("/ajout_vente/", methods=["POST"])
def ajout_vente():
    if request.method == 'POST':
        Quantitevendu = request.form["Quantitevendu"]
        Date = request.form["Date"]
        produit_id = request.form["produit"]
        client_id = request.form["nom"]

        cursor = conn.cursor()
        cursor.execute(
            "SELECT Prix FROM produit WHERE id = %s", (produit_id,))
        produit = cursor.fetchone()
        
        if produit:
            PrixUnitaire = produit[0]
            PrixTotal = float(PrixUnitaire) * int(Quantitevendu)

            cursor.execute('''
                INSERT INTO vente (Quantitevendu, Prixtotal, Date, produit_id, client_id)
                VALUES (%s, %s, %s, %s, %s)
            ''', (Quantitevendu, PrixTotal, Date, produit_id, client_id))

            conn.commit()
            flash("Votre vente a été enregistrée avec succès !", 'info')
            return redirect(url_for('ventes'))

    return render_template('ajout_vente.html')


# Point d'entrée de l'application

if __name__=="__main__":
    app.run(debug=True)
