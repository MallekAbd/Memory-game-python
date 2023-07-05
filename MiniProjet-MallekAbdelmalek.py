from tkinter import *
from random import *
import time


####################Management##############################################
class G():
    global score;global gameTime
    ball_dia = 50
    rond = None
    but = None
    posx = 0
    posy = 0
    posButx = 0
    posButy = 0
    nbut = 0
    niveau = 1
    gameTime=[time.time(),0]
    score=0

def commencerJeu():
    G.rond = c1.create_oval(G.posx,G.posy,G.posx+G.ball_dia,G.posy+G.ball_dia,fill='#fff')
    But()

def But():

    G.nbut += 1
    G.posButx=randint(0,9)*50
    G.posButy=randint(0,9)*50

    G.but=c1.create_oval(G.posButx,G.posButy,G.posButx+G.ball_dia,G.posButy+G.ball_dia, fill="yellow")
    jouer()

def jouer():

     
    if(G.posx == G.posButx and G.posy == G.posButy):
        if(G.nbut == G.niveau):
            G.nbut = 0
            G.niveau += 1
            gameTime[1]=time.time()
            score=round(1/(gameTime[1]-gameTime[0])*1000,2)
            affichageScore.set("Score =" +str(score))
            l1['text'] = 'Gagné, on passe au niveau : '+str(G.niveau)
            But()
        else:
            But()
####################"Mouvements##############################################
def droite(event):
    c1.delete(ALL)
    G.posx+=50
    if(G.posx > 450): G.posx=450
    G.rond = c1.create_oval(G.posx,G.posy,G.posx+G.ball_dia,G.posy+G.ball_dia,fill='#fff')
    jouer()

def gauche(event):
    c1.delete(ALL)
    G.posx-=50
    if(G.posx < 0): G.posx=0
    G.rond = c1.create_oval(G.posx,G.posy,G.posx+G.ball_dia,G.posy+G.ball_dia,fill='#fff')
    jouer()

def haut(event):
    c1.delete(ALL)
    G.posy-=50
    if(G.posy < 0): G.posy=0
    G.rond = c1.create_oval(G.posx,G.posy,G.posx+G.ball_dia,G.posy+G.ball_dia,fill='#fff')
    jouer()

def bas(event):
    c1.delete(ALL)
    G.posy+=50
    if(G.posy > 450): G.posy=450
    G.rond = c1.create_oval(G.posx,G.posy,G.posx+G.ball_dia,G.posy+G.ball_dia,fill='#fff')
    jouer()
################ fenetre d'acceuil###########




########################### fenetre 1 #################################
window=Tk()
window.title('Python Game Challenge')
window.configure(bg='yellow')
label=Label(window,text='Welcome, Are You Ready To challenge Your Memory! ',fg='yellow',bg='black',font='Helvetica 32 bold italic')
label.pack(padx=120, pady =100)
bouton=Button(window,text='Passer',fg='yellow',bg='black',font='Helvetica 14 bold italic',relief='raised',command=window.destroy)
bouton.pack(side="bottom",ipadx=10,ipady=10)

canvas = Canvas(width=100, height=340, bg='yellow')
canvas.pack(expand=YES, fill=BOTH)
# charger le fichier image 
img1 = PhotoImage(file='33.png')
# mettre l'image sur le canvas
canvas.create_image(670,180, image=img1, anchor=CENTER)
mainloop()
################################# fenetre 2 #######################################

window=Tk()
window.title('Règles')
window.configure(bg='yellow')
label=Label(window,text="C'est facile: \n 1.Cliquez sur Start. \n 2.Mémorisez la position du point jaune. \n 3.En rattrape rapidement pour gagner un max de points",
            fg='yellow',bg='black',font='Helvetica 14 bold italic')
label.pack(padx=90, pady =70)
b5=Button(window,text='Jouer',fg='yellow',bg='black',font='Helvetica 14 bold italic',relief='raised',command=window.destroy)
b5.pack(side="bottom",ipadx=10,ipady=10)
mainloop()

#################### Main ##############################################
f1=Tk()
f1.title("Python Game Challenge")

f1.geometry('1200x680+500+100')
f1.configure(bg='yellow')
f1.bind("<Right>", droite) ; f1.bind("<Left>", gauche)
f1.bind("<Down>", bas) ; f1.bind("<Up>", haut)

c1=Canvas(f1,width=1000,height=500, bg="black")
c1.place(x=180, y=25)

l1 = Label(f1,fg='yellow',bg='black', text = 'Niveau : '+str(G.niveau))
l1.place(x=550, y=650)

affichageScore=StringVar()
affichageScore.set("Score =00.00")
l2 = Label(f1, textvariable=affichageScore,fg='yellow',bg='black')
l2.place(x=800, y=650)

b1=Button(f1,text="Start",fg='yellow',bg='black',font='Helvetica 14 bold italic',relief='raised', command=commencerJeu)
b1.place(x=45, y=20)

b1=Button(f1,text=" Exit ",fg='yellow',bg='black',font='Helvetica 14 bold italic',relief='raised', command=f1.destroy)
b1.place(x=45, y=70)
f1.mainloop()
