from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.card import MDCard
from kivymd.uix.list import MDList, TwoLineListItem, ThreeLineListItem
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.dialog import MDDialog
from kivymd.uix.snackbar import Snackbar

from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore

import random
from datetime import datetime


class StudyHelperApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "StudyHelper"
        
        # Variables principales
        self.notes = []
        self.note_en_cours = None
        self.rappels = []
        self.matieres = {}
        self.sessions = []
        self.session_active = None
        self.debut_session = None
        self.notes_trouvees = []
        
        # Stockage des données
        self.store = JsonStore('studyhelper.json')
        self.charger_donnees()
        
        # Variables pour les dialogues
        self.dialog = None
        
        # Variables pour les quiz
        self.questions_quiz = []
        self.score_quiz = 0
        self.question_actuelle = 0
        self.nb_questions = 5

    def build(self):
        # Configuration de l'app
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        
        # Créer l'écran principal
        self.screen_manager = MDScreenManager()
        screen = MDScreen(name="main")
        
        # Layout principal
        layout_principal = MDBoxLayout(orientation="vertical")
        
        # Barre du haut
        toolbar = MDTopAppBar(title="StudyHelper", elevation=2)
        layout_principal.add_widget(toolbar)
        
        # Navigation du bas
        navigation = MDBottomNavigation()
        
        # Onglet Notes
        onglet_notes = MDBottomNavigationItem(
            name="notes", text="Notes", icon="note-text"
        )
        onglet_notes.add_widget(self.creer_onglet_notes())
        navigation.add_widget(onglet_notes)
        
        # Onglet Éditeur
        onglet_editeur = MDBottomNavigationItem(
            name="editor", text="Éditeur", icon="pencil"
        )
        onglet_editeur.add_widget(self.creer_onglet_editeur())
        navigation.add_widget(onglet_editeur)
        
        # Onglet Rappels
        onglet_rappels = MDBottomNavigationItem(
            name="reminders", text="Rappels", icon="bell"
        )
        onglet_rappels.add_widget(self.creer_onglet_rappels())
        navigation.add_widget(onglet_rappels)
        
        # Onglet Stats
        onglet_stats = MDBottomNavigationItem(
            name="stats", text="Stats", icon="chart-line"
        )
        onglet_stats.add_widget(self.creer_onglet_stats())
        navigation.add_widget(onglet_stats)
        
        layout_principal.add_widget(navigation)
        screen.add_widget(layout_principal)
        self.screen_manager.add_widget(screen)
        
        return self.screen_manager

    def creer_onglet_notes(self):
        # Layout pour l'onglet des notes
        layout = MDBoxLayout(orientation="vertical", padding="10dp", spacing="10dp")
        
        # Zone de recherche
        self.champ_recherche = MDTextField(
            hint_text="Rechercher...",
            size_hint_y=None,
            height="48dp"
        )
        self.champ_recherche.bind(text=self.rechercher_notes)
        layout.add_widget(self.champ_recherche)
        
        # Boutons
        boutons = MDBoxLayout(
            orientation="horizontal",
            spacing="10dp", 
            size_hint_y=None,
            height="48dp"
        )
        
        btn_nouvelle = MDRaisedButton(text="Nouvelle Note")
        btn_nouvelle.bind(on_release=self.nouvelle_note)
        boutons.add_widget(btn_nouvelle)
        
        btn_effacer = MDRaisedButton(text="Effacer")
        btn_effacer.bind(on_release=self.effacer_recherche)
        boutons.add_widget(btn_effacer)
        
        layout.add_widget(boutons)
        
        # Liste des notes
        scroll = MDScrollView()
        self.liste_notes = MDList()
        scroll.add_widget(self.liste_notes)
        layout.add_widget(scroll)
        
        self.mettre_a_jour_notes()
        return layout

    def creer_onglet_editeur(self):
        # Layout pour l'éditeur
        layout = MDBoxLayout(orientation="vertical", padding="10dp", spacing="10dp")
        
        # Champ titre
        self.champ_titre = MDTextField(
            hint_text="Titre de la note",
            size_hint_y=None,
            height="48dp"
        )
        layout.add_widget(self.champ_titre)
        
        # Champ contenu
        carte_contenu = MDCard(
            elevation=2,
            padding="10dp",
            size_hint_y=None,
            height="400dp"
        )
        
        scroll_contenu = MDScrollView()
        
        self.champ_contenu = MDTextField(
            hint_text="Contenu de la note...",
            multiline=True,
            size_hint_y=None,
            height="350dp"
        )
        
        scroll_contenu.add_widget(self.champ_contenu)
        carte_contenu.add_widget(scroll_contenu)
        layout.add_widget(carte_contenu)
        
        # Boutons d'action - SUPPRESSION DU BOUTON SUPPRIMER ICI
        boutons_action = MDBoxLayout(
            orientation="horizontal",
            spacing="10dp",
            size_hint_y=None,
            height="48dp"
        )
        
        btn_sauver = MDRaisedButton(text="Sauvegarder")
        btn_sauver.bind(on_release=self.sauvegarder_note)
        boutons_action.add_widget(btn_sauver)
        
        # Le bouton supprimer a été retiré d'ici
        
        layout.add_widget(boutons_action)
        
        # Boutons outils
        boutons_outils = MDBoxLayout(
            orientation="horizontal",
            spacing="10dp",
            size_hint_y=None,
            height="48dp"
        )
        
        btn_quiz = MDRaisedButton(text="Quiz")
        btn_quiz.bind(on_release=self.creer_quiz)
        boutons_outils.add_widget(btn_quiz)
        
        btn_resume = MDRaisedButton(text="Résumé")
        btn_resume.bind(on_release=self.faire_resume)
        boutons_outils.add_widget(btn_resume)
        
        layout.add_widget(boutons_outils)
        
        return layout

    def creer_onglet_rappels(self):
        # Layout pour les rappels
        layout = MDBoxLayout(orientation="vertical", padding="10dp", spacing="10dp")
        
        # Titre
        titre = MDLabel(
            text="Mes Rappels",
            theme_text_color="Primary",
            font_style="H5",
            size_hint_y=None,
            height="40dp"
        )
        layout.add_widget(titre)
        
        # Boutons
        boutons = MDBoxLayout(
            orientation="horizontal",
            spacing="10dp",
            size_hint_y=None,
            height="48dp"
        )
        
        btn_nouveau = MDRaisedButton(text="Nouveau Rappel")
        btn_nouveau.bind(on_release=self.nouveau_rappel)
        boutons.add_widget(btn_nouveau)
        
        btn_verifier = MDRaisedButton(text="Vérifier")
        btn_verifier.bind(on_release=self.verifier_rappels_manuel)
        boutons.add_widget(btn_verifier)
        
        layout.add_widget(boutons)
        
        # Liste des rappels
        scroll = MDScrollView()
        self.liste_rappels = MDList()
        scroll.add_widget(self.liste_rappels)
        layout.add_widget(scroll)
        
        self.mettre_a_jour_rappels()
        return layout

    def verifier_rappels_manuel(self, *args):
        # Vérification simple quand on clique sur le bouton
        maintenant = datetime.now().strftime("%Y-%m-%d %H:%M")
        rappels_actuels = []
        
        for rappel in self.rappels:
            if rappel.get('active', True):
                # Vérification très simple - juste comparer les strings
                if rappel['date'] <= maintenant:
                    rappels_actuels.append(rappel['titre'])
                    rappel['active'] = False  # Marquer comme lu
        
        if rappels_actuels:
            message = f"Rappels actuels: {', '.join(rappels_actuels)}"
            self.afficher_message(message)
            self.sauvegarder_donnees()
            self.mettre_a_jour_rappels()
        else:
            self.afficher_message("Aucun rappel pour le moment")

    def creer_onglet_stats(self):
        # Layout pour les statistiques
        layout = MDBoxLayout(orientation="vertical", padding="10dp", spacing="10dp")
        
        # Section session active
        carte_session = MDCard(
            elevation=2,
            padding="15dp",
            size_hint_y=None,
            height="120dp"
        )
        
        layout_session = MDBoxLayout(orientation="vertical", spacing="10dp")
        
        self.label_session = MDLabel(
            text="Aucune session active",
            theme_text_color="Primary",
            font_style="Subtitle1"
        )
        layout_session.add_widget(self.label_session)
        
        boutons_session = MDBoxLayout(
            orientation="horizontal",
            spacing="10dp",
            size_hint_y=None,
            height="48dp"
        )
        
        btn_start = MDRaisedButton(text="Démarrer Session")
        btn_start.bind(on_release=self.demarrer_session)
        boutons_session.add_widget(btn_start)
        
        btn_stop = MDRaisedButton(text="Terminer")
        btn_stop.bind(on_release=self.terminer_session)
        boutons_session.add_widget(btn_stop)
        
        layout_session.add_widget(boutons_session)
        carte_session.add_widget(layout_session)
        layout.add_widget(carte_session)
        
        # Section statistiques
        carte_stats = MDCard(
            elevation=2,
            padding="15dp",
            size_hint_y=None,
            height="200dp"
        )
        
        layout_stats = MDBoxLayout(orientation="vertical", spacing="5dp")
        
        titre_stats = MDLabel(text="Statistiques", font_style="H6")
        layout_stats.add_widget(titre_stats)
        
        self.label_temps = MDLabel(text="Temps total: 0 min")
        self.label_sessions = MDLabel(text="Sessions: 0") 
        self.label_matieres = MDLabel(text="Matières: 0")
        self.label_quiz = MDLabel(text="Quiz réalisés: 0")
        
        layout_stats.add_widget(self.label_temps)
        layout_stats.add_widget(self.label_sessions)
        layout_stats.add_widget(self.label_matieres)
        layout_stats.add_widget(self.label_quiz)
        
        carte_stats.add_widget(layout_stats)
        layout.add_widget(carte_stats)
        
        # Liste matières
        scroll_matieres = MDScrollView()
        self.liste_matieres = MDList()
        scroll_matieres.add_widget(self.liste_matieres)
        layout.add_widget(scroll_matieres)
        
        self.mettre_a_jour_stats()
        return layout

    # Méthodes pour les notes
    def nouvelle_note(self, *args):
        self.note_en_cours = None
        self.champ_titre.text = ""
        self.champ_contenu.text = ""
        self.afficher_message("Nouvelle note créée")

    def sauvegarder_note(self, *args):
        titre = self.champ_titre.text.strip()
        contenu = self.champ_contenu.text.strip()
        
        if not titre:
            self.afficher_message("Le titre ne peut pas être vide!")
            return
        
        if self.note_en_cours:
            # Modifier une note existante
            self.note_en_cours['titre'] = titre
            self.note_en_cours['contenu'] = contenu
            self.note_en_cours['date_modification'] = datetime.now().strftime("%Y-%m-%d %H:%M")
            message = "Note modifiée!"
        else:
            # Créer une nouvelle note
            nouvelle_note = {
                'id': len(self.notes) + 1,
                'titre': titre,
                'contenu': contenu,
                'date_creation': datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            self.notes.append(nouvelle_note)
            self.note_en_cours = nouvelle_note
            message = "Note sauvegardée!"
        
        self.mettre_a_jour_notes()
        self.sauvegarder_donnees()
        self.afficher_message(message)

    def mettre_a_jour_notes(self):
        # Vider la liste
        if not hasattr(self, 'liste_notes'):
            return
            
        self.liste_notes.clear_widgets()
        
        # Choisir les notes à afficher (filtrées ou toutes)
        notes_a_afficher = self.notes_trouvees if self.notes_trouvees else self.notes
        
        # Trier par date de création
        notes_triees = sorted(notes_a_afficher, 
                            key=lambda x: x.get('date_creation', ''), 
                            reverse=True)
        
        for note in notes_triees:
            # Couper le contenu si trop long
            contenu_court = note['contenu'][:50] + "..." if len(note['contenu']) > 50 else note['contenu']
            date_creation = note.get('date_creation', 'Inconnue')
            
            item = ThreeLineListItem(
                text=note['titre'],
                secondary_text=f"Créée: {date_creation}",
                tertiary_text=contenu_court
            )
            item.bind(on_release=lambda x, note=note: self.selectionner_note(note))
            self.liste_notes.add_widget(item)

    def selectionner_note(self, note):
        self.note_en_cours = note
        self.champ_titre.text = note['titre']
        self.champ_contenu.text = note['contenu']
        self.afficher_note_complete(note)

    def afficher_note_complete(self, note):
        # Créer le contenu du dialogue
        contenu = MDBoxLayout(
            orientation="vertical", 
            spacing="15dp", 
            size_hint_y=None
        )
        contenu.bind(minimum_height=contenu.setter('height'))
        
        # Infos de la note
        info_text = f"Créée: {note.get('date_creation', 'Inconnue')}"
        if note.get('date_modification'):
            info_text += f"\nModifiée: {note['date_modification']}"
        
        info_label = MDLabel(
            text=info_text,
            font_style="Caption",
            theme_text_color="Secondary",
            size_hint_y=None,
            height="40dp"
        )
        contenu.add_widget(info_label)
        
        # Contenu de la note
        contenu_scroll = MDScrollView(
            size_hint=(1, None),
            height="300dp"
        )
        
        contenu_label = MDLabel(
            text=note['contenu'],
            font_style="Body1",
            text_size=(None, None),
            valign="top",
            size_hint_y=None
        )
        contenu_label.text_size = (280, None)
        contenu_label.bind(texture_size=contenu_label.setter('size'))
        
        contenu_scroll.add_widget(contenu_label)
        contenu.add_widget(contenu_scroll)
        
        # MODIFICATION : Ajout du bouton Supprimer dans les boutons du dialogue
        self.dialog = MDDialog(
            title=note['titre'],
            type="custom",
            content_cls=contenu,
            size_hint=(0.9, 0.8),
            buttons=[
                MDRaisedButton(text="Modifier", on_release=lambda x: self.charger_dans_editeur()),
                MDRaisedButton(text="Supprimer", on_release=lambda x: self.confirmer_suppression_depuis_dialogue()),
                MDRaisedButton(text="Fermer", on_release=self.fermer_dialog)
            ]
        )
        self.dialog.open()

    def charger_dans_editeur(self):
        self.fermer_dialog()
        self.afficher_message(f"Note '{self.note_en_cours['titre']}' chargée dans l'éditeur")

    def rechercher_notes(self, instance, texte):
        if not texte.strip():
            self.notes_trouvees = []
        else:
            self.notes_trouvees = [
                note for note in self.notes
                if texte.lower() in note['titre'].lower() or texte.lower() in note['contenu'].lower()
            ]
        self.mettre_a_jour_notes()

    def effacer_recherche(self, *args):
        self.champ_recherche.text = ""
        self.notes_trouvees = []
        self.mettre_a_jour_notes()

    # MODIFICATION : Nouvelle méthode pour la suppression depuis le dialogue
    def confirmer_suppression_depuis_dialogue(self, *args):
        if not self.note_en_cours:
            self.afficher_message("Aucune note sélectionnée!")
            return
        
        # Fermer le dialogue actuel
        self.fermer_dialog()
        
        # Ouvrir le dialogue de confirmation
        self.dialog = MDDialog(
            text=f"Supprimer la note '{self.note_en_cours['titre']}'?",
            buttons=[
                MDRaisedButton(text="Supprimer", on_release=self.confirmer_suppression),
                MDRaisedButton(text="Annuler", on_release=self.fermer_dialog)
            ]
        )
        self.dialog.open()

    # MODIFICATION : Méthode simplifiée - plus besoin de vérifier s'il y a une note en cours
    def supprimer_note(self, *args):
        # Cette méthode n'est plus utilisée depuis l'éditeur
        # mais on la garde au cas où
        if not self.note_en_cours:
            self.afficher_message("Aucune note sélectionnée!")
            return
        
        self.dialog = MDDialog(
            text=f"Supprimer la note '{self.note_en_cours['titre']}'?",
            buttons=[
                MDRaisedButton(text="Supprimer", on_release=self.confirmer_suppression),
                MDRaisedButton(text="Annuler", on_release=self.fermer_dialog)
            ]
        )
        self.dialog.open()

    def confirmer_suppression(self, *args):
        if self.note_en_cours in self.notes:
            self.notes.remove(self.note_en_cours)
            self.mettre_a_jour_notes()
            self.sauvegarder_donnees()
            
            # Vider l'éditeur
            self.champ_titre.text = ""
            self.champ_contenu.text = ""
            self.note_en_cours = None
            
            self.fermer_dialog()
            self.afficher_message("Note supprimée!")

    # Méthodes pour le résumé et quiz
    def faire_resume(self, *args):
        if not self.note_en_cours:
            self.afficher_message("Sélectionnez une note à résumer!")
            return
        
        contenu = self.note_en_cours['contenu']
        
        if len(contenu) < 100:
            self.afficher_message("Note trop courte pour être résumée")
            return
        
        # Faire un résumé simple
        resume = self.creer_resume_simple(contenu)
        
        # Afficher le résumé
        contenu_dialog = MDBoxLayout(
            orientation="vertical", 
            spacing="15dp", 
            size_hint_y=None
        )
        contenu_dialog.bind(minimum_height=contenu_dialog.setter('height'))
        
        stats_label = MDLabel(
            text=f"Note originale: {len(contenu.split())} mots\nRésumé: {len(resume.split())} mots",
            font_style="Caption",
            theme_text_color="Secondary",
            size_hint_y=None,
            height="40dp"
        )
        contenu_dialog.add_widget(stats_label)
        
        resume_scroll = MDScrollView(
            size_hint=(1, None),
            height="300dp"
        )
        
        resume_label = MDLabel(
            text=resume,
            font_style="Body1",
            text_size=(None, None),
            valign="top",
            size_hint_y=None
        )
        resume_label.text_size = (280, None)
        resume_label.bind(texture_size=resume_label.setter('size'))
        
        resume_scroll.add_widget(resume_label)
        contenu_dialog.add_widget(resume_scroll)
        
        self.dialog = MDDialog(
            title=f"Résumé: {self.note_en_cours['titre']}",
            type="custom",
            content_cls=contenu_dialog,
            size_hint=(0.9, 0.8),
            buttons=[
                MDRaisedButton(text="Sauvegarder comme note", on_release=lambda x: self.sauvegarder_resume(resume)),
                MDRaisedButton(text="Fermer", on_release=self.fermer_dialog)
            ]
        )
        self.dialog.open()

    def sauvegarder_resume(self, resume):
        # Créer une nouvelle note avec le résumé
        titre_original = self.note_en_cours['titre']
        nouvelle_note = {
            'id': len(self.notes) + 1,
            'titre': f"Résumé: {titre_original}",
            'contenu': resume,
            'date_creation': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'type': 'resume',  # Marquer comme résumé
            'note_source_id': self.note_en_cours['id']  # Référence à la note originale
        }
        
        self.notes.append(nouvelle_note)
        self.mettre_a_jour_notes()
        self.sauvegarder_donnees()
        
        self.fermer_dialog()
        self.afficher_message(f"Résumé sauvegardé comme nouvelle note!")

    def creer_resume_simple(self, texte):
        # Découper le texte en phrases
        phrases = []
        phrase_actuelle = ""
        
        for char in texte:
            phrase_actuelle += char
            if char in '.!?':
                phrase_nettoyee = phrase_actuelle.strip()
                if len(phrase_nettoyee) > 20:
                    phrases.append(phrase_nettoyee)
                phrase_actuelle = ""
        
        if len(phrases) <= 3:
            return texte[:200] + "..." if len(texte) > 200 else texte
        
        # Prendre quelques phrases importantes
        phrases_importantes = []
        phrases_importantes.append(phrases[0])  # Première phrase
        
        if len(phrases) > 2:
            phrases_importantes.append(phrases[len(phrases)//2])  # Phrase du milieu
        
        phrases_importantes.append(phrases[-1])  # Dernière phrase
        
        resume = ' '.join(phrases_importantes)
        
        # Limiter le nombre de mots
        mots = resume.split()
        if len(mots) > 100:
            resume = ' '.join(mots[:100]) + '...'
        
        return resume

    def creer_quiz(self, *args):
        if not self.note_en_cours:
            self.afficher_message("Sélectionnez une note pour créer un quiz!")
            return
        
        # Configuration du quiz
        contenu_config = MDBoxLayout(orientation="vertical", spacing="15dp", size_hint_y=None)
        contenu_config.bind(minimum_height=contenu_config.setter('height'))
        
        self.champ_nb_questions = MDTextField(
            hint_text="Nombre de questions (3-10)",
            text="5",
            size_hint_y=None,
            height="48dp"
        )
        contenu_config.add_widget(self.champ_nb_questions)
        
        self.dialog = MDDialog(
            title="Configuration Quiz",
            type="custom",
            content_cls=contenu_config,
            buttons=[
                MDRaisedButton(text="Créer Quiz", on_release=self.generer_quiz),
                MDRaisedButton(text="Annuler", on_release=self.fermer_dialog)
            ]
        )
        self.dialog.open()

    def generer_quiz(self, *args):
        try:
            nb_questions = int(self.champ_nb_questions.text)
            if nb_questions < 3 or nb_questions > 10:
                nb_questions = 5
        except:
            nb_questions = 5
        
        self.nb_questions = nb_questions
        contenu = self.note_en_cours['contenu']
        
        print(f"Génération quiz pour: {len(contenu)} caractères")  # Debug
        
        # Générer les questions
        self.questions_quiz = self.creer_questions_simples(contenu, nb_questions)
        
        print(f"Questions générées: {len(self.questions_quiz)}")  # Debug
        
        if not self.questions_quiz:
            # Si échec, créer des questions très simples
            self.questions_quiz = self.creer_questions_basiques(contenu, nb_questions)
            print(f"Questions basiques: {len(self.questions_quiz)}")  # Debug
        
        if not self.questions_quiz:
            self.afficher_message("Impossible de générer un quiz. Votre note est peut-être trop courte.")
            self.fermer_dialog()
            return
        
        self.question_actuelle = 0
        self.score_quiz = 0
        
        self.fermer_dialog()
        self.commencer_quiz()

    def creer_questions_basiques(self, texte, nb_questions):
        """Méthode de secours pour créer des questions très simples"""
        questions = []
        
        # Questions sur la longueur et le contenu
        if len(texte) > 50:
            questions.append({
                "question": f"Votre note contient-elle plus de {len(texte.split())//2} mots?",
                "options": ["Vrai", "Faux"],
                "correct": 0 if len(texte.split()) > len(texte.split())//2 else 1,
                "explication": f"Votre note contient {len(texte.split())} mots."
            })
        
        # Questions sur les mots présents
        mots = texte.lower().split()
        if len(mots) > 5:
            mot_frequent = max(set(mots), key=mots.count) if mots else "test"
            questions.append({
                "question": f"Le mot '{mot_frequent}' apparaît-il dans votre note?",
                "options": ["Vrai", "Faux"],
                "correct": 0,
                "explication": f"Le mot '{mot_frequent}' est présent dans votre note."
            })
        
        # Question sur la première phrase
        premieres_phrases = texte.split('.')[0] if '.' in texte else texte[:50]
        if len(premieres_phrases) > 10:
            questions.append({
                "question": f"Votre note commence-t-elle par des mots similaires à: '{premieres_phrases[:20]}...'?",
                "options": ["Vrai", "Faux"],
                "correct": 0,
                "explication": "C'est effectivement le début de votre note."
            })
        
        return questions[:nb_questions]

    def creer_questions_simples(self, texte, nb_questions):
        # Créer des vraies questions pédagogiques
        questions = []
        
        # 1. Questions à trous (complétion)
        questions.extend(self.creer_questions_trous(texte, nb_questions // 3))
        
        # 2. Questions de définition
        questions.extend(self.creer_questions_definitions(texte, nb_questions // 3))
        
        # 3. Questions de compréhension
        questions.extend(self.creer_questions_comprehension(texte, nb_questions - len(questions)))
        
        return questions[:nb_questions]

    def creer_questions_trous(self, texte, nb_max):
        """Créer des questions à compléter avec des mots manquants"""
        questions = []
        phrases = [p.strip() for p in texte.split('.') if len(p.strip()) > 30]
        
        for phrase in phrases[:nb_max]:
            mots = phrase.split()
            if len(mots) < 5:
                continue
                
            # Trouver des mots importants (pas "le", "de", "et"...)
            mots_importants = []
            mots_simples = {'le', 'la', 'les', 'de', 'du', 'des', 'et', 'ou', 'un', 'une', 'ce', 'se', 'dans', 'sur', 'avec', 'pour', 'par', 'est', 'sont', 'a', 'ont'}
            
            for i, mot in enumerate(mots):
                mot_propre = mot.lower().strip('.,!?:;')
                if len(mot_propre) > 3 and mot_propre not in mots_simples:
                    mots_importants.append((i, mot))
            
            if not mots_importants:
                continue
            
            # Choisir un mot important à faire deviner
            index_mot, mot_correct = random.choice(mots_importants)
            
            # Créer la phrase à trous
            phrase_trous = mots.copy()
            phrase_trous[index_mot] = "______"
            phrase_incomplete = ' '.join(phrase_trous)
            
            # Créer des fausses réponses
            fausses_reponses = self.generer_fausses_reponses(mot_correct.strip('.,!?:;'), texte)
            
            options = [mot_correct.strip('.,!?:;')] + fausses_reponses[:3]
            random.shuffle(options)
            correct_index = options.index(mot_correct.strip('.,!?:;'))
            
            questions.append({
                "question": f"Complétez: {phrase_incomplete}",
                "options": options,
                "correct": correct_index,
                "explication": f"La bonne réponse est '{mot_correct.strip('.,!?:;')}' selon votre cours."
            })
        
        return questions

    def creer_questions_definitions(self, texte, nb_max):
        """Créer des questions sur les concepts importants"""
        questions = []
        
        # Chercher des phrases qui définissent quelque chose
        phrases_definition = []
        for phrase in texte.split('.'):
            phrase = phrase.strip()
            if any(mot in phrase.lower() for mot in ['est un', 'est une', 'désigne', 'signifie', 'correspond à', 'définit', 'représente']):
                if len(phrase) > 20:
                    phrases_definition.append(phrase)
        
        for phrase in phrases_definition[:nb_max]:
            # Extraire le concept défini
            concept = None
            definition = None
            
            for separateur in [' est un ', ' est une ', ' désigne ', ' signifie ']:
                if separateur in phrase.lower():
                    parties = phrase.lower().split(separateur, 1)
                    if len(parties) == 2:
                        concept = parties[0].strip()
                        definition = parties[1].strip()
                        break
            
            if concept and definition and len(concept) < 50:
                # Créer de fausses définitions
                fausses_definitions = [
                    "un processus complexe",
                    "une méthode d'analyse",
                    "un élément fondamental",
                    "une technique spécialisée"
                ]
                
                options = [definition[:80] + "..." if len(definition) > 80 else definition] + fausses_definitions[:3]
                random.shuffle(options)
                correct_index = options.index(definition[:80] + "..." if len(definition) > 80 else definition)
                
                questions.append({
                    "question": f"Que {concept} ?",
                    "options": options,
                    "correct": correct_index,
                    "explication": f"{concept.capitalize()} {definition[:100]}..."
                })
        
        return questions

    def creer_questions_comprehension(self, texte, nb_max):
        """Créer des questions de compréhension générale"""
        questions = []
        phrases = [p.strip() for p in texte.split('.') if len(p.strip()) > 20]
        
        for phrase in phrases[:nb_max]:
            if len(phrase) < 30:
                continue
                
            # Question vrai/faux intelligente
            if random.choice([True, False]):
                # Phrase vraie
                questions.append({
                    "question": f"D'après votre cours: {phrase}",
                    "options": ["Vrai", "Faux"],
                    "correct": 0,
                    "explication": "Cette information est correcte selon votre cours."
                })
            else:
                # Phrase modifiée (fausse)
                phrase_modifiee = self.modifier_phrase_intelligemment(phrase)
                questions.append({
                    "question": f"D'après votre cours: {phrase_modifiee}",
                    "options": ["Vrai", "Faux"],
                    "correct": 1,
                    "explication": f"Faux. La version correcte est: {phrase}"
                })
        
        return questions

    def generer_fausses_reponses(self, mot_correct, texte):
        """Générer de fausses réponses crédibles"""
        mots_texte = []
        for mot in texte.split():
            mot_propre = mot.lower().strip('.,!?:;')
            if len(mot_propre) > 3 and mot_propre != mot_correct.lower():
                mots_texte.append(mot_propre)
        
        # Prendre des mots du texte comme fausses réponses
        fausses = list(set(mots_texte))[:3]
        
        # Compléter avec des réponses génériques si pas assez
        while len(fausses) < 3:
            generiques = ['système', 'processus', 'méthode', 'élément', 'concept', 'technique', 'structure', 'fonction']
            for g in generiques:
                if g not in fausses and g != mot_correct.lower():
                    fausses.append(g)
                    break
        
        return fausses[:3]

    def modifier_phrase_intelligemment(self, phrase):
        """Modifier une phrase pour créer une question fausse mais crédible"""
        modifications = [
            (' est ', ' n\'est pas '),
            (' sont ', ' ne sont pas '),
            (' peut ', ' ne peut pas '),
            (' permet ', ' ne permet pas '),
            (' augmente ', ' diminue '),
            (' diminue ', ' augmente '),
            (' toujours ', ' jamais '),
            (' jamais ', ' toujours '),
            (' avant ', ' après '),
            (' après ', ' avant ')
        ]
        
        phrase_modifiee = phrase
        for original, remplacement in modifications:
            if original in phrase.lower():
                phrase_modifiee = phrase_modifiee.replace(original, remplacement, 1)
                break
        
        # Si aucune modification trouvée, inverser avec "Il est faux que"
        if phrase_modifiee == phrase:
            phrase_modifiee = f"Il est faux que {phrase.lower()}"
        
        return phrase_modifiee

    def creer_question_vrai_faux(self, phrase):
        # Enlever la ponctuation finale
        phrase_propre = phrase.rstrip('.!?').strip()
        
        # Vérifier que la phrase n'est pas trop courte
        if len(phrase_propre) < 10:
            return None
        
        # 50% de chance de garder la phrase vraie
        if random.choice([True, False]):
            return {
                "question": f"Vrai ou Faux: {phrase_propre}",
                "options": ["Vrai", "Faux"],
                "correct": 0,
                "explication": "Cette affirmation est dans votre note."
            }
        else:
            # Modifier la phrase pour la rendre fausse
            phrase_fausse = phrase_propre
            
            # Essayer différentes modifications
            if " est " in phrase_fausse:
                phrase_fausse = phrase_fausse.replace(" est ", " n'est pas ", 1)
            elif " sont " in phrase_fausse:
                phrase_fausse = phrase_fausse.replace(" sont ", " ne sont pas ", 1)
            elif " a " in phrase_fausse:
                phrase_fausse = phrase_fausse.replace(" a ", " n'a pas ", 1)
            elif " peut " in phrase_fausse:
                phrase_fausse = phrase_fausse.replace(" peut ", " ne peut pas ", 1)
            elif " doit " in phrase_fausse:
                phrase_fausse = phrase_fausse.replace(" doit ", " ne doit pas ", 1)
            else:
                # Si aucune modification possible, ajouter "Il est faux que"
                phrase_fausse = f"Il est faux que {phrase_propre.lower()}"
            
            return {
                "question": f"Vrai ou Faux: {phrase_fausse}",
                "options": ["Vrai", "Faux"],
                "correct": 1,
                "explication": "Cette affirmation a été modifiée par rapport à votre note."
            }

    def commencer_quiz(self):
        self.afficher_question()

    def afficher_question(self):
        if self.question_actuelle >= len(self.questions_quiz):
            self.finir_quiz()
            return
        
        question = self.questions_quiz[self.question_actuelle]
        
        contenu = MDBoxLayout(orientation="vertical", spacing="15dp", size_hint_y=None)
        contenu.bind(minimum_height=contenu.setter('height'))
        
        # Progression
        progress_label = MDLabel(
            text=f"Question {self.question_actuelle + 1}/{len(self.questions_quiz)}",
            font_style="Caption",
            theme_text_color="Secondary",
            size_hint_y=None,
            height="30dp"
        )
        contenu.add_widget(progress_label)
        
        # Question
        question_label = MDLabel(
            text=question['question'],
            font_style="Subtitle1",
            size_hint_y=None,
            height="60dp"
        )
        question_label.bind(texture_size=question_label.setter('size'))
        contenu.add_widget(question_label)
        
        # Options
        for i, option in enumerate(question['options']):
            btn = MDRaisedButton(
                text=f"{option}",
                size_hint_y=None,
                height="48dp"
            )
            btn.bind(on_release=lambda x, index=i: self.repondre_question(index))
            contenu.add_widget(btn)
        
        self.dialog = MDDialog(
            title=f"Quiz: {self.note_en_cours['titre']}",
            type="custom",
            content_cls=contenu,
            size_hint=(0.9, 0.8)
        )
        self.dialog.open()

    def repondre_question(self, reponse):
        question = self.questions_quiz[self.question_actuelle]
        correct = reponse == question['correct']
        
        if correct:
            self.score_quiz += 1
        
        # Afficher la correction
        self.afficher_correction(question, reponse, correct)

    def afficher_correction(self, question, reponse, correct):
        self.fermer_dialog()
        
        contenu = MDBoxLayout(orientation="vertical", spacing="15dp", size_hint_y=None)
        contenu.bind(minimum_height=contenu.setter('height'))
        
        # Résultat
        resultat = "Correct!" if correct else "Incorrect"
        resultat_label = MDLabel(
            text=resultat,
            font_style="H6",
            theme_text_color="Primary" if correct else "Error",
            size_hint_y=None,
            height="40dp"
        )
        contenu.add_widget(resultat_label)
        
        # Réponse donnée
        votre_reponse = MDLabel(
            text=f"Votre réponse: {question['options'][reponse]}",
            font_style="Body1",
            size_hint_y=None,
            height="40dp"
        )
        contenu.add_widget(votre_reponse)
        
        # Bonne réponse si incorrecte
        if not correct:
            bonne_reponse = MDLabel(
                text=f"Bonne réponse: {question['options'][question['correct']]}",
                font_style="Body1",
                theme_text_color="Primary",
                size_hint_y=None,
                height="40dp"
            )
            contenu.add_widget(bonne_reponse)
        
        # Explication
        explication = MDLabel(
            text=f"Explication: {question['explication']}",
            font_style="Caption",
            size_hint_y=None,
            height="60dp"
        )
        explication.bind(texture_size=explication.setter('size'))
        contenu.add_widget(explication)
        
        self.dialog = MDDialog(
            title="Résultat",
            type="custom",
            content_cls=contenu,
            buttons=[MDRaisedButton(text="Suivant", on_release=self.question_suivante)]
        )
        self.dialog.open()

    def question_suivante(self, *args):
        self.fermer_dialog()
        self.question_actuelle += 1
        self.afficher_question()

    def finir_quiz(self):
        # Calculer le pourcentage
        pourcentage = int((self.score_quiz / len(self.questions_quiz)) * 100)
        
        # Afficher les résultats
        contenu = MDBoxLayout(orientation="vertical", spacing="15dp", size_hint_y=None)
        contenu.bind(minimum_height=contenu.setter('height'))
        
        score_label = MDLabel(
            text=f"Score: {self.score_quiz}/{len(self.questions_quiz)} ({pourcentage}%)",
            font_style="H5",
            theme_text_color="Primary",
            size_hint_y=None,
            height="50dp"
        )
        contenu.add_widget(score_label)
        
        # Message selon le score
        if pourcentage >= 80:
            message = "Excellent! Vous maîtrisez bien le sujet."
        elif pourcentage >= 60:
            message = "Bien! Continuez vos efforts."
        elif pourcentage >= 40:
            message = "Passable. Il serait bon de réviser."
        else:
            message = "À revoir. Relisez attentivement la note."
        
        eval_label = MDLabel(
            text=message,
            font_style="Body1",
            size_hint_y=None,
            height="40dp"
        )
        contenu.add_widget(eval_label)
        
        self.dialog = MDDialog(
            title="Résultats du Quiz",
            type="custom",
            content_cls=contenu,
            buttons=[MDRaisedButton(text="Terminer", on_release=self.terminer_quiz)]
        )
        self.dialog.open()
        
        self.sauvegarder_donnees()
        self.mettre_a_jour_stats()

    def terminer_quiz(self, *args):
        self.fermer_dialog()
        self.questions_quiz = []
        self.afficher_message("Quiz terminé!")

    # Méthodes pour les rappels
    def nouveau_rappel(self, *args):
        contenu = MDBoxLayout(orientation="vertical", spacing="15dp", size_hint_y=None)
        contenu.bind(minimum_height=contenu.setter('height'))
        
        self.champ_titre_rappel = MDTextField(
            hint_text="Titre du rappel",
            size_hint_y=None,
            height="48dp"
        )
        contenu.add_widget(self.champ_titre_rappel)
        
        self.champ_date_rappel = MDTextField(
            hint_text="Date (YYYY-MM-DD HH:MM)",
            size_hint_y=None,
            height="48dp"
        )
        contenu.add_widget(self.champ_date_rappel)
        
        self.dialog = MDDialog(
            title="Nouveau Rappel",
            type="custom",
            content_cls=contenu,
            buttons=[
                MDRaisedButton(text="Ajouter", on_release=self.ajouter_rappel),
                MDRaisedButton(text="Annuler", on_release=self.fermer_dialog)
            ]
        )
        self.dialog.open()

    def ajouter_rappel(self, *args):
        titre = self.champ_titre_rappel.text.strip()
        date_str = self.champ_date_rappel.text.strip()
        
        if not titre or not date_str:
            self.afficher_message("Veuillez remplir tous les champs!")
            return
        
        # Validation simple - juste vérifier qu'il y a quelque chose
        if len(date_str) < 5:  # Au minimum "12:30" ou "2024-"
            self.afficher_message("Format de date trop court!")
            return
        
        rappel = {
            'id': len(self.rappels) + 1,
            'titre': titre,
            'date': date_str,
            'active': True
        }
        
        self.rappels.append(rappel)
        self.mettre_a_jour_rappels()
        self.sauvegarder_donnees()
        
        self.fermer_dialog()
        self.afficher_message("Rappel ajouté!")

    def mettre_a_jour_rappels(self):
        if not hasattr(self, 'liste_rappels'):
            return
        
        self.liste_rappels.clear_widgets()
        
        for rappel in sorted(self.rappels, key=lambda x: x['date']):
            # Créer un layout horizontal pour chaque rappel
            rappel_layout = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height="56dp",
                spacing="10dp"
            )
            
            # Info du rappel (prend la plupart de l'espace)
            item = TwoLineListItem(
                text=rappel['titre'],
                secondary_text=f"Date: {rappel['date']}",
                size_hint_x=0.7
            )
            rappel_layout.add_widget(item)
            
            # Bouton supprimer
            btn_supprimer = MDRaisedButton(
                text="Supprimer",
                size_hint_x=0.3,
                size_hint_y=None,
                height="40dp"
            )
            btn_supprimer.bind(on_release=lambda x, rappel_id=rappel['id']: self.supprimer_rappel(rappel_id))
            rappel_layout.add_widget(btn_supprimer)
            
            self.liste_rappels.add_widget(rappel_layout)

    def supprimer_rappel(self, rappel_id):
        # Trouver et supprimer le rappel
        for i, rappel in enumerate(self.rappels):
            if rappel['id'] == rappel_id:
                self.rappels.pop(i)
                break
        
        # Mettre à jour l'affichage
        self.mettre_a_jour_rappels()
        self.sauvegarder_donnees()
        self.afficher_message("Rappel supprimé!")

    # Méthodes pour les sessions d'étude
    def demarrer_session(self, *args):
        if self.session_active:
            self.afficher_message("Une session est déjà en cours!")
            return
        
        contenu = MDBoxLayout(orientation="vertical", spacing="15dp", size_hint_y=None)
        contenu.bind(minimum_height=contenu.setter('height'))
        
        self.champ_matiere = MDTextField(
            hint_text="Matière à étudier",
            size_hint_y=None,
            height="48dp"
        )
        contenu.add_widget(self.champ_matiere)
        
        self.champ_objectif = MDTextField(
            hint_text="Objectif de la session",
            multiline=True,
            size_hint_y=None,
            height="80dp"
        )
        contenu.add_widget(self.champ_objectif)
        
        self.dialog = MDDialog(
            title="Nouvelle Session d'Étude",
            type="custom",
            content_cls=contenu,
            buttons=[
                MDRaisedButton(text="Démarrer", on_release=self.confirmer_session),
                MDRaisedButton(text="Annuler", on_release=self.fermer_dialog)
            ]
        )
        self.dialog.open()

    def confirmer_session(self, *args):
        matiere = self.champ_matiere.text.strip()
        objectif = self.champ_objectif.text.strip()
        
        if not matiere:
            self.afficher_message("Veuillez entrer une matière!")
            return
        
        # Créer la session
        self.session_active = {
            'id': len(self.sessions) + 1,
            'matiere': matiere,
            'objectif': objectif,
            'date_debut': datetime.now(),
            'temps_ecoule': 0,
            'active': True
        }
        
        # Ajouter ou créer la matière
        if matiere not in self.matieres:
            self.matieres[matiere] = {
                'nom': matiere,
                'temps_total': 0,
                'sessions': 0,
                'notes': []
            }
        
        self.debut_session = datetime.now()
        
        # Démarrer le timer
        Clock.schedule_interval(self.mettre_a_jour_timer, 1)
        
        self.fermer_dialog()
        self.mettre_a_jour_stats()
        self.afficher_message(f"Session '{matiere}' démarrée!")

    def mettre_a_jour_timer(self, dt):
        if not self.session_active or not self.debut_session:
            return False
        
        # Calculer le temps écoulé
        temps_ecoule = datetime.now() - self.debut_session
        minutes_ecoulees = int(temps_ecoule.total_seconds() / 60)
        
        # Mettre à jour la session
        self.session_active['temps_ecoule'] = minutes_ecoulees
        
        # Afficher le temps
        heures = minutes_ecoulees // 60
        minutes = minutes_ecoulees % 60
        
        if heures > 0:
            temps_str = f"{heures}h {minutes}min"
        else:
            temps_str = f"{minutes}min"
        
        self.label_session.text = f"Session: {self.session_active['matiere']} - {temps_str}"
        
        return True

    def terminer_session(self, *args):
        if not self.session_active:
            self.afficher_message("Aucune session active!")
            return
        
        # Arrêter le timer
        Clock.unschedule(self.mettre_a_jour_timer)
        
        # Calculer le temps final
        temps_final = datetime.now() - self.debut_session
        minutes_finales = int(temps_final.total_seconds() / 60)
        
        self.session_active['temps_ecoule'] = minutes_finales
        self.session_active['date_fin'] = datetime.now()
        self.session_active['active'] = False
        
        # Mettre à jour les statistiques de la matière
        matiere = self.session_active['matiere']
        if matiere in self.matieres:
            self.matieres[matiere]['temps_total'] += minutes_finales
            self.matieres[matiere]['sessions'] += 1
        
        # Ajouter à l'historique
        self.sessions.append(self.session_active.copy())
        
        # Afficher le résumé
        self.afficher_resume_session()
        
        # Nettoyer
        self.session_active = None
        self.debut_session = None
        
        self.sauvegarder_donnees()
        self.mettre_a_jour_stats()

    def afficher_resume_session(self):
        session = self.session_active
        
        contenu = MDBoxLayout(orientation="vertical", spacing="15dp", size_hint_y=None)
        contenu.bind(minimum_height=contenu.setter('height'))
        
        stats_text = f"Matière: {session['matiere']}\nDurée: {session['temps_ecoule']} minutes"
        
        if session.get('objectif'):
            stats_text += f"\nObjectif: {session['objectif']}"
        
        stats_label = MDLabel(
            text=stats_text,
            font_style="Body1",
            size_hint_y=None
        )
        stats_label.bind(texture_size=stats_label.setter('size'))
        contenu.add_widget(stats_label)
        
        self.dialog = MDDialog(
            title="Session Terminée",
            type="custom",
            content_cls=contenu,
            buttons=[MDRaisedButton(text="OK", on_release=self.fermer_dialog)]
        )
        self.dialog.open()

    def mettre_a_jour_stats(self):
        # Calculer les stats totales
        temps_total = sum(session['temps_ecoule'] for session in self.sessions)
        nombre_sessions = len(self.sessions)
        nombre_matieres = len(self.matieres)
        
        # Mettre à jour les labels
        heures = temps_total // 60
        minutes = temps_total % 60
        
        if heures > 0:
            temps_str = f"{heures}h {minutes}min"
        else:
            temps_str = f"{minutes}min"
        
        self.label_temps.text = f"Temps total: {temps_str}"
        self.label_sessions.text = f"Sessions: {nombre_sessions}"
        self.label_matieres.text = f"Matières: {nombre_matieres}"
        self.label_quiz.text = f"Quiz réalisés: {len([s for s in self.sessions if 'quiz' in str(s)])}"
        
        # Mettre à jour la liste des matières
        self.mettre_a_jour_liste_matieres()

    def mettre_a_jour_liste_matieres(self):
        if not hasattr(self, 'liste_matieres'):
            return
        
        self.liste_matieres.clear_widgets()
        
        for nom, matiere in self.matieres.items():
            temps_matiere = matiere.get('temps_total', 0)
            sessions_matiere = matiere.get('sessions', 0)
            
            heures = temps_matiere // 60
            minutes = temps_matiere % 60
            
            if heures > 0:
                temps_str = f"{heures}h {minutes}min"
            else:
                temps_str = f"{minutes}min"
            
            item = TwoLineListItem(
                text=nom,
                secondary_text=f"{sessions_matiere} sessions - {temps_str}"
            )
            self.liste_matieres.add_widget(item)

    # Méthodes utilitaires
    def afficher_message(self, message):
        # Afficher un message à l'utilisateur
        snackbar = Snackbar(text=message)
        snackbar.open()

    def fermer_dialog(self, *args):
        if self.dialog:
            self.dialog.dismiss()

    def sauvegarder_donnees(self):
        # Sauvegarder de façon simple
        try:
            # Garder les données simples
            data = {
                'notes': self.notes,
                'rappels': self.rappels,
                'matieres': self.matieres,
                'sessions': self.sessions
            }
            
            self.store.put('donnees_app', **data)
            
        except Exception as e:
            print(f"Erreur de sauvegarde: {e}")

    def charger_donnees(self):
        # Charger de façon simple
        try:
            if self.store.exists('donnees_app'):
                data = self.store.get('donnees_app')
                
                self.notes = data.get('notes', [])
                self.rappels = data.get('rappels', [])
                self.matieres = data.get('matieres', {})
                self.sessions = data.get('sessions', [])
        
        except Exception as e:
            print(f"Erreur de chargement: {e}")

    def on_start(self):
        # Rien de spécial au démarrage
        pass

    def verifier_rappels(self, dt):
        # Pas de vérification automatique - trop compliqué pour une débutante
        return True

    def on_pause(self):
        # Sauvegarder quand l'app se met en pause
        self.sauvegarder_donnees()
        return True

    def on_stop(self):
        # Sauvegarder avant de fermer l'app
        self.sauvegarder_donnees()


# Lancement de l'application
def main():
    try:
        app = StudyHelperApp()
        app.run()
    except Exception as e:
        print(f"Erreur: {e}")


if __name__ == '__main__':
    main()