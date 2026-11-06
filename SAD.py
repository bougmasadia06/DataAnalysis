import os
import pandas as pd
import matplotlib.pyplot as plt
from urllib.parse import quote_plus
from sqlalchemy import create_engine, text

# ======================================================================
# CONNEXION A LA BASE (la base "boutique" et ses tables existent deja)
# ======================================================================
# Mise en place de la base (faite dans MySQL, hors de ce script) :
# Le MLD donne : CLIENT(id_client), ARTICLE(id_article, designation_article),
# COMMANDE(id_commande, date_commande, article #, client #).
# Choix des types : INT pour les identifiants (cles primaires AUTO_INCREMENT),
# VARCHAR(100) pour le texte, DATE pour la date.
# Les cles etrangeres garantissent qu'une commande reference un article et
# un client qui existent. Il faut donc remplir CLIENT et ARTICLE avant COMMANDE.

USER = "root"
PWD = ""            
SERVER = "localhost"
PORT = 3306
BD = "boutique"
connexion = create_engine(f"mysql+pymysql://{USER}:{quote_plus(PWD)}@{SERVER}:{PORT}/{BD}")

# ======================================================================
# PARTIE 1 : MANIPULER UN DATAFRAME
# ======================================================================
print("\n========== PARTIE 1 ==========")

# 1. Creation et affichage du DataFrame (l'age de TRAORE est manquant : None)
df = pd.DataFrame({
    "nom": ["KABORE", "OUEDRAOGO", "SAWADOGO", "TRAORE"],
    "note": [20, 5, 12, 15],
    "age": [35, 20, 16, None],
})
print(df)
print("Dimensions (lignes, colonnes) :", df.shape)
print("Nombre de lignes :", len(df), "| Nombre de colonnes :", len(df.columns))

# 2. Les deux dernieres lignes
print("\n--- 2. tail(2) ---")
print(df.tail(2))

# 3. Nom et note de l'etudiant a l'index 1 (avec loc)
print("\n--- 3. loc : nom et note de l'index 1 ---")
print(df.loc[1, ["nom", "note"]])

# 4. Ligne d'index 1 avec loc, puis 2 premieres lignes/colonnes avec iloc
print("\n--- 4. loc[1] puis iloc[:2, :2] ---")
print(df.loc[1])
print(df.iloc[:2, :2])

# 5. Difference entre loc et iloc :
#    - loc selectionne par LABELS (noms de l'index et des colonnes) et la
#      borne de fin est INCLUSE (loc[0:2] donne les lignes 0, 1 et 2).
#    - iloc selectionne par POSITIONS entieres (0, 1, 2...) et la borne de
#      fin est EXCLUE (iloc[0:2] donne les lignes 0 et 1).
#    Avec loc, on ne peut pas donner des chiffres pour les colonnes si leurs
#    noms sont des textes (df.loc[0:2, 0:2] provoque une TypeError).

# 6. Note > 10 ET age < 20, avec seulement nom et note
print("\n--- 6. note > 10 et age < 20 ---")
print(df.loc[(df["note"] > 10) & (df["age"] < 20), ["nom", "note"]])

# 7. Role des parentheses et de l'operateur & :
#    - Chaque condition (df["note"] > 10) produit une serie de True/False.
#    - & fait un "ET" logique ligne par ligne entre deux series. Le mot
#      "and" ne marche pas : Python ne peut pas evaluer une serie entiere
#      comme un seul booleen (erreur "truth value of a Series is ambiguous").
#    - Les parentheses sont obligatoires car & est prioritaire sur > et <.
#      Sans elles, l'expression est mal interpretee et leve une erreur.

# 8. Noms des etudiants ayant une note > 10
print("\n--- 8. noms avec note > 10 ---")
print(df.loc[df["note"] > 10, "nom"])

# 9. La colonne des notes devient l'index
print("\n--- 9. set_index('note') puis selection de la note 15 ---")
df_note = df.set_index("note")
print(df_note)
print(df_note.loc[15])
#    Explication : la colonne "note" sort des colonnes et devient l'index.
#    df_note.loc[15] renvoie la ligne dont l'index vaut 15 (TRAORE : nom et
#    age) sous forme de Series. Si plusieurs etudiants avaient 15, on
#    obtiendrait un DataFrame, car un index peut contenir des doublons.

# 10. Une colonne contre une liste de colonnes
print("\n--- 10. Series ou DataFrame ? ---")
# classe en Series
print(type(df["nom"]))     
#classe en dataframe
print(type(df[["nom"]]))   
#    df["nom"]   : crochets simples  -> Series (une seule colonne)
#    df[["nom"]] : liste de colonnes -> DataFrame (tableau a 2 dimensions)

# 11. Valeurs manquantes
print("\n--- 11. Valeurs manquantes ---")
# tableau de True/False
print(df.isna())       
# nombre de NaN par colonne
print(df.isna().sum())                    
print("Total de valeurs manquantes :", df.isna().sum().sum())
#    La valeur manquante est l'age de TRAORE (NaN : Not a Number). Pandas
#    convertit None en NaN et passe toute la colonne en nombres decimaux.

# ======================================================================
# PARTIE 2 : MYSQL ET PANDAS
# ======================================================================
print("\n========== PARTIE 2 ==========")

# ---------- A. Lecture et export ----------
# 1. Chargement du resultat d'une requete dans un DataFrame
req = text("""
    SELECT a.designation_article AS designation, COUNT(*) AS nb_commandes
    FROM article a
    JOIN commande c ON a.id_article = c.article
    GROUP BY a.designation_article
""")
df_sql = pd.read_sql(req, con=connexion)

# 2. Affichage clair (sans l'index)
print(df_sql.to_string(index=False))

# 3. Les deux parametres principaux de pd.read_sql :
#    - la requete (sql) : le texte SQL a executer, ici enveloppe dans text().
#    - la connexion (con) : le moteur SQLAlchemy qui indique sur quelle base
#      et avec quel compte la requete est executee.
#    Le resultat de la requete est range dans un DataFrame.

# 4. Export en CSV avec le separateur ; et sans index
df_sql.to_csv("commandes.csv", sep=";", index=False)
#    sep=";"       : colonnes separees par des points-virgules (format lu
#                    directement par Excel en version francaise).
#    index=False   : on n'ecrit pas la colonne 0, 1, 2... inutile.

# 5. Relecture du CSV : il faut preciser le meme separateur
df_relu = pd.read_csv("commandes.csv", sep=";")
print(df_relu)
#    Sans sep=";", pandas attend des virgules et met tout dans une seule colonne.

# ---------- B. Ecriture en base ----------
# Insertion d'un DataFrame dans une table avec to_sql.
# Elle est desactivee par defaut pour eviter d'inserer des doublons
# a chaque execution du script. Mettre True UNE SEULE FOIS, sur une base de test.
EXECUTER_ECRITURE = False
if EXECUTER_ECRITURE:
    nouveaux = pd.DataFrame({"designation_article": ["Souris", "Ecran"]})
    nouveaux.to_sql("article", con=connexion, if_exists="append", index=False)

# 1. Role des options :
#    - if_exists="append" : ajoute les lignes a la table existante, sans la
#      supprimer ni la remplacer (les autres choix sont "fail" et "replace").
#    - index=False : n'ecrit pas l'index du DataFrame comme une colonne
#      supplementaire, qui n'existe pas dans la table.
# 2. Risque en mode append : a chaque execution, les memes lignes sont
#    reinserees. Cela cree des doublons dans la table ou une erreur
#    d'integrite si une cle primaire est repetee.
# 3. Pourquoi une base de test : l'ecriture modifie reellement la base. Il
#    faut verifier avant les donnees (types, doublons, cles etrangeres) et
#    que le compte a bien le droit INSERT, pour ne pas abimer des donnees
#    reelles.

# ---------- C. Connexion ----------
# 1. Parametres necessaires : utilisateur, mot de passe, serveur (hote),
#    port, nom de la base, et le type de SGBD avec son pilote.
#    Forme : mysql+pymysql://utilisateur:mot_de_passe@serveur:port/base
# 2. pymysql est le PILOTE (driver) : la bibliotheque Python qui parle le
#    protocole MySQL. SQLAlchemy fournit l'interface generale, et pymysql
#    realise l'echange avec le serveur MySQL.

# ======================================================================
# PARTIE 3 : MATPLOTLIB AVEC DES LISTES
# ======================================================================
print("\n========== PARTIE 3 ==========")

# 1. Les trois listes :
#    - mois     : les categories de l'axe horizontal (abscisse)
#    - ventes_a : premiere serie de ventes (ordonnee)
#    - ventes_b : seconde serie de ventes, comparable a la premiere
mois = ["Jan", "Fev", "Mar", "Avr", "Mai"]
ventes_a = [120, 150, 170, 160, 200]
ventes_b = [100, 130, 140, 180, 190]

# 2. plt.subplots(1, 3, figsize=(8, 4)) cree une figure de 8 x 4 pouces avec
#    une grille de 1 ligne et 3 colonnes (3 zones de graphique).
#    Elle retourne un tuple (fig, ax) :
#      - fig : la figure (la fenetre entiere)
#      - ax  : un tableau NumPy contenant les 3 zones de trace (objets Axes)
fig3, ax3 = plt.subplots(1, 3, figsize=(8, 4))

# 3 et 6. Courbes de chaque serie, avec legende (label= attache a la serie)
ax3[0].plot(mois, ventes_a, marker="o", color="blue", label="Ventes A")
ax3[1].plot(mois, ventes_b, marker="s", color="red", label="Ventes B")

# 5. Titre et etiquettes des axes pour chaque zone utilisee
for i, titre in enumerate(["Serie A : ventes", "Serie B : ventes"]):
    ax3[i].set_title(titre)
    ax3[i].set_xlabel("Mois")
    ax3[i].set_ylabel("Ventes")
    ax3[i].legend()
fig3.tight_layout()

# 4. Zones creees : 3. Zones effectivement utilisees : 2.
# 7. La troisieme zone reste vide car aucun trace n'y est demande :
#    matplotlib cree toutes les zones de la grille, meme sans contenu.

# 8. Observations sur l'objet ax3 et sur une de ses zones
print("len(ax3)           :", len(ax3))          
print("len(dir(ax3))      :", len(dir(ax3)))      # attributs/methodes d'un ndarray
print("len(dir(ax3[0]))   :", len(dir(ax3[0])))   # d'un Axes : bien plus nombreux
print("ax3.size           :", ax3.size)           # nombre total d'elements : 3
#    ax3 est un tableau NumPy (peu de methodes : shape, size, flat...), alors
#    qu'une zone ax3[0] est un objet Axes tres riche (plot, bar, set_title,
#    legend...). len et size donnent la meme valeur ici car le tableau est a
#    une dimension. Dans une grille 2x2, len donnerait 2 et size 4.

# 9. Modification : creer seulement 2 zones pour 2 graphiques
fig3b, ax3b = plt.subplots(1, 2, figsize=(8, 4))
ax3b[0].plot(mois, ventes_a, marker="o", color="blue", label="Ventes A")
ax3b[1].plot(mois, ventes_b, marker="s", color="red", label="Ventes B")
for i, titre in enumerate(["Serie A : ventes", "Serie B : ventes"]):
    ax3b[i].set_title(titre)
    ax3b[i].set_xlabel("Mois")
    ax3b[i].set_ylabel("Ventes")
    ax3b[i].legend()
fig3b.tight_layout()
#    Autres options : fig.delaxes(ax[2]) supprime la zone en trop, ou
#    ax[2].axis("off") la masque.

# ======================================================================
# PARTIE 4 : VISUALISER LES RESULTATS MYSQL
# ======================================================================
print("\n========== PARTIE 4 ==========")

# ---------- A. Comprendre le flux du programme ----------
# 1. Role des deux requetes :
#    - req1 : pour chaque article, la quantite commandee et le nombre de
#      clients differents ayant commande cet article.
#    - req2 : le nombre de commandes passees a chaque date.

# 2. pd.read_sql(requete, con=connexion) execute chaque requete et range le
#    resultat dans un DataFrame (df1 et df2).

# B.7 Requete des ventes par article avec JOIN ... ON explicite
# (les noms de colonnes ont ete verifies avec DESCRIBE commande :
#  article, client, date_commande)
req1 = text("""
    SELECT a.designation_article AS designation,
           COUNT(c.id_commande)      AS quantite,
           COUNT(DISTINCT c.client)  AS nbre_client
    FROM article a
    JOIN commande c ON a.id_article = c.article
    JOIN client cl  ON cl.id_client = c.client
    GROUP BY a.designation_article
    ORDER BY a.designation_article
""")

# B.6 Requete qui compte les commandes par date
req2 = text("""
    SELECT date_commande AS date, COUNT(*) AS nombre
    FROM commande
    GROUP BY date_commande
    ORDER BY date_commande
""")

df1 = pd.read_sql(req1, con=connexion)
df2 = pd.read_sql(req2, con=connexion)
df2["date"] = pd.to_datetime(df2["date"])   # vraie date pour le nuage de points
print(df1)
print(df2)

# 3. Colonnes utilisees pour les graphiques :
#    - df1 : designation (axe x), quantite et nbre_client (axe y)
#    - df2 : date (axe x), nombre (axe y)

# 4. plt.subplots(2, 2, figsize=(12, 6)) cree une figure de 12 x 6 pouces
#    avec une grille de 2 lignes et 2 colonnes. ax[ligne][colonne] designe :
#      ax[0][0] haut gauche   | ax[0][1] haut droite
#      ax[1][0] bas gauche    | ax[1][1] bas droite

# 5. Types de graphique :
#      ax[0][0] : courbes   | ax[0][1] : barres
#      ax[1][0] : histogramme | ax[1][1] : nuage de points

# ---------- B. Verifier les calculs et les dimensions ----------
# 1. Tables du FROM : article, commande, client.
#    Conditions de jointure : a.id_article = c.article
#                             cl.id_client = c.client

# 2. Chaque table possede bien une condition de jointure. Si une condition
#    manquait, on obtiendrait un PRODUIT CARTESIEN : chaque ligne d'une
#    table serait combinee avec toutes les lignes de l'autre, donnant des
#    resultats faux et gonfles.

# 3. COUNT sur l'identifiant d'article compte le nombre de LIGNES de
#    commande de chaque article. Ce n'est pas forcement le nombre d'unites
#    vendues : sans colonne "quantite" dans COMMANDE, une ligne vaut une
#    commande, mais si une commande contenait plusieurs unites il faudrait
#    utiliser SUM(quantite).

# 4. Une liste de clients saisie en dur ne suit pas les donnees de la base.
#    Si sa longueur differe de celle de la serie associee, matplotlib leve
#    ValueError ("x and y must have the same first dimension"). Pire, si les
#    longueurs coincident par hasard, les valeurs seraient associees aux
#    mauvais articles sans aucune erreur.

# 5. Avant d'appeler plot, il faut verifier que les series tracees ont la
#    meme longueur (voir l'assertion ci-dessous).
assert len(df1["designation"]) == len(df1["quantite"]) == len(df1["nbre_client"])
assert len(df2["date"]) == len(df2["nombre"])

# ---------- C. Ameliorer les figures ----------
fig4, ax = plt.subplots(2, 2, figsize=(12, 6))

# Courbes : chaque serie a son label (legende liee directement a la serie)
ax[0][0].plot(df1["designation"], df1["quantite"], marker="x",
              color="pink", label="Quantite commandee")
ax[0][0].plot(df1["designation"], df1["nbre_client"], marker="o",
              color="blue", linestyle="--", label="Clients")
ax[0][0].set(title="Quantites et clients par article",
             xlabel="Articles", ylabel="Valeurs")
ax[0][0].legend()

# Barres : l'axe y commence a zero
ax[0][1].bar(df1["designation"], df1["quantite"])
ax[0][1].set(title="Quantite commandee par article",
             xlabel="Articles", ylabel="Quantite")
ax[0][1].set_ylim(bottom=0)

# Histogramme
ax[1][0].hist(df1["quantite"])
ax[1][0].set(title="Repartition des quantites",
             xlabel="Quantite", ylabel="Nombre d'articles")

# Nuage de points : dates (datetime) contre nombres (entiers), meme longueur
ax[1][1].scatter(df2["date"], df2["nombre"])
ax[1][1].set(title="Commandes par date",
             xlabel="Date", ylabel="Nombre de commandes")

for a in ax.flat:
    a.tick_params(axis="x", rotation=45)
fig4.tight_layout()

# 5. Enregistrement de la figure dans un fichier image,
#    apres avoir verifie que le dossier existe (cree au besoin).
#    savefig doit etre appele AVANT plt.show().
dossier = "figures"
os.makedirs(dossier, exist_ok=True)
fig4.savefig(os.path.join(dossier, "analyse_commandes.png"), dpi=150)
print("Figure enregistree dans :", os.path.abspath(dossier))

# Affiche toutes les figures (bloque jusqu'a la fermeture des fenetres)
plt.show()