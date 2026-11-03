"""Hand-built sentences (written by the pilot engineer, not model output). 24 per language (plan said 60: deviation logged)."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from frontier_multilingual_register import label

DE = [("Kannst du mir bitte helfen?", "T"), ("Können Sie mir bitte helfen?", "V"), ("Bring deine Unterlagen mit.", "T"),
 ("Bringen Sie bitte Ihre Unterlagen mit.", "V"), ("Ich habe dich gestern gesehen.", "T"), ("Ich habe Sie gestern gesehen.", "V"),
 ("Der Termin ist um neun Uhr.", "none"), ("Das Wetter ist heute schön.", "none"), ("Hast du Hunger?", "T"),
 ("Haben Sie Hunger?", "V"), ("Wann kommst du heute?", "T"), ("Wann kommen Sie heute?", "V"), ("Sie können morgen kommen.", "ambig"),
 ("Ich gebe Ihnen das Formular.", "V"), ("Ich gebe dir das Formular.", "T"), ("Du kannst Ihnen helfen.", "mixed"),
 ("Wir gehen heute ins Kino.", "none"), ("Bitte warten Sie hier.", "V"), ("Sie ist heute krank.", "ambig"), ("Magst du Kaffee?", "T"),
 ("Das ist dein Buch.", "T"), ("Ist das Ihr Buch?", "V"), ("Ich brauche Hilfe.", "none"), ("Willst du mitkommen?", "T")]
ES = [("¿Puedes ayudarme, por favor?", "T"), ("¿Puede usted ayudarme, por favor?", "V"), ("Trae tus documentos.", "T"),
 ("Traiga sus documentos.", "V"), ("Te vi ayer.", "T"), ("Lo vi ayer, usted estaba allí.", "V"), ("La cita es a las nueve.", "none"),
 ("Hoy hace buen tiempo.", "none"), ("¿Tienes hambre?", "T"), ("¿Tiene usted hambre?", "V"), ("¿Cuándo vienes hoy?", "T"),
 ("¿Podría ayudarme?", "V"), ("Quiero un café.", "none"), ("Dame el formulario.", "T"), ("Le doy el formulario, usted lo firma.", "V"),
 ("Tú puedes ayudarle a usted.", "mixed"), ("Vamos al cine hoy.", "none"), ("Espere aquí, por favor.", "V"), ("Necesito ayuda.", "none"),
 ("¿Es este tu libro?", "T"), ("¿Es este su libro, usted?", "V"), ("Mañana voy al médico.", "none"), ("¿Quieres venir?", "T"), ("Ustedes pueden pasar.", "ambig")]
FR = [("Peux-tu m'aider, s'il te plaît ?", "T"), ("Pouvez-vous m'aider, s'il vous plaît ?", "V"), ("Apporte tes documents.", "T"),
 ("Apportez vos documents.", "V"), ("Je t'ai vu hier.", "T"), ("Je vous ai vu hier.", "V"), ("Le rendez-vous est à neuf heures.", "none"),
 ("Il fait beau aujourd'hui.", "none"), ("As-tu faim ?", "T"), ("Avez-vous faim ?", "V"), ("Quand viens-tu aujourd'hui ?", "T"),
 ("Quand venez-vous aujourd'hui ?", "V"), ("Tu peux venir demain.", "T"), ("Je te donne le formulaire.", "T"), ("Je vous donne le formulaire.", "V"),
 ("Tu peux vous aider.", "mixed"), ("On va au cinéma ce soir.", "none"), ("Attendez ici, s'il vous plaît.", "V"), ("J'ai besoin d'aide.", "none"),
 ("C'est ton livre ?", "T"), ("C'est votre livre ?", "V"), ("Je vais chez le médecin demain.", "none"), ("Tu veux venir ?", "T"), ("Voulez-vous un café ?", "V")]

def test_all():
    bad = []
    for lang, ex in (("de", DE), ("es", ES), ("fr", FR)):
        for s, g in ex:
            if label(lang, s) != g:
                bad.append((lang, s, g, label(lang, s)))
    print(bad)
    assert not bad
