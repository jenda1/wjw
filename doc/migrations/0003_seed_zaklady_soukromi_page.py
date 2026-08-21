from django.db import migrations

SLUG = 'zasady_soukromi'
TITLE = 'Zásady ochrany soukromí'

BODY = """
<p>Spolek Waldorfská Jinonice, z. s. (dále jen „spolek") si váží soukromí svých členů a dětí, jejichž rodiče jsou jeho členy. Na této stránce v krátkosti vysvětlujeme, jaké osobní údaje v členské evidenci zpracováváme, proč a jak s nimi zacházíme.</p>
<p>Tento text je srozumitelným shrnutím pro členy, nenahrazuje formální zásady zpracování osobních údajů podle GDPR.</p>
<h2>Jaké údaje zpracováváme</h2>
<p><b>O členovi spolku (rodiči/zákonném zástupci):</b></p>
<ul>
<li>jméno, příjmení a e-mail</li>
<li>datum narození</li>
<li>adresa (ulice, město, PSČ) – ověřujeme ji automaticky přes Mapy.cz, aby v evidenci nebyly překlepy</li>
<li>telefonní číslo (nepovinné)</li>
<li>typ a stav členství, historie žádosti o členství</li>
</ul>
<p><b>O dětech (studentech):</b></p>
<ul>
<li>jméno, příjmení a datum narození</li>
<li>zařazení do třídy/ročníku</li>
<li>vazba na rodiče/zákonné zástupce a doba jejího trvání</li>
</ul>
<p>Tyto údaje zadáváte vy sami při registraci, nebo je doplňuje administrátor spolku při schvalování žádosti.</p>
<h2>Přihlášení a účet</h2>
<p>Do systému se můžete přihlásit e-mailem a heslem, nebo přes účet Google, Facebook, Seznam či MojeID. V tom případě nám příslušná služba předá jen jméno a e-mail (případně profilovou fotku), abychom vás mohli spárovat s vaším členským profilem. Heslo k vašemu Google/Facebook/Seznam/MojeID účtu nikdy nevidíme ani neukládáme.</p>
<h2>Proč údaje zpracováváme</h2>
<ul>
<li>vedení členské evidence a správa členství (schvalování žádostí, aktivní/pasivní členství)</li>
<li>organizace a komunikace v rámci tříd a spolkových aktivit</li>
<li>plnění povinností vyplývajících ze stanov spolku a příslušných právních předpisů</li>
</ul>
<p>Právním základem je zpravidla plnění smlouvy/členského poměru, oprávněný zájem spolku na fungování komunity a v některých případech váš souhlas (např. u nepovinných údajů jako telefon).</p>
<h2>Kdo má k údajům přístup</h2>
<ul>
<li>administrátoři spolku (výkonná rada) – pro schvalování a správu členství</li>
<li>třídní zástupci – pouze k údajům členů a dětí ve „své" třídě</li>
<li>technický správce systému – pro provoz a údržbu aplikace</li>
</ul>
<p>Ke změnám v evidenci se vede historie (kdo a kdy údaj upravil), abychom mohli případné chyby dohledat a opravit.</p>
<h2>Jak dlouho údaje uchováváme</h2>
<p>Údaje uchováváme po dobu trvání členství a dále po dobu vyžadovanou právními předpisy (např. pro účetní a spolkovou agendu). Po zániku členství jsou vaše údaje a údaje vašich dětí do 60 dní vymazány, pokud jejich další uchování nevyžaduje zákon.</p>
<h2>Vaše práva</h2>
<ul>
<li>na přístup ke svým osobním údajům a údajům svých dětí</li>
<li>na opravu nepřesných údajů (přímo ve svém profilu, nebo požádáním administrátora)</li>
<li>na výmaz nebo omezení zpracování, pokud pro něj pomine důvod</li>
<li>vznést námitku proti zpracování založenému na oprávněném zájmu</li>
<li>podat stížnost u Úřadu pro ochranu osobních údajů (uoou.cz)</li>
</ul>
<p>S jakýmkoliv dotazem k ochraně soukromí se obraťte na předsedu spolku – jeho kontakt najdete v menu <b>Kontakty</b>.</p>
""".strip()


def create_page(apps, schema_editor):
    # Wagtailí stromové operace (add_child) potřebují skutečné modelové třídy,
    # ne "historical" modely z apps.get_model() - viz poznámka o migracích v CLAUDE.md.
    from wagtail.models import Page
    from doc.models import DocPage

    if DocPage.objects.filter(slug=SLUG).exists():
        return

    home_page = Page.objects.get(slug='home')
    home_page.add_child(instance=DocPage(
        title=TITLE,
        slug=SLUG,
        body=BODY,
        live=True,
        show_in_menus=False,
    ))


def delete_page(apps, schema_editor):
    from doc.models import DocPage

    DocPage.objects.filter(slug=SLUG).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('doc', '0002_agendapage_agendapagetag_agendapage_tags'),
    ]

    operations = [
        migrations.RunPython(create_page, delete_page),
    ]
