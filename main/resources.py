from import_export import fields, resources
from import_export.widgets import DateWidget

from .models import Student


class StudentResource(resources.ModelResource):
    """Import žáků z excelu. Třída se nebere ze souboru, ale z importního formuláře
    (viz StudentAdmin) - všichni žáci v souboru se přiřadí k jedné vybrané třídě.
    Sloupce "Rodné číslo" a "Pohlaví" v souboru se ignorují.
    """

    first_name = fields.Field(attribute='first_name', column_name='Jméno')
    last_name = fields.Field(attribute='last_name', column_name='Příjmení')
    birth_date = fields.Field(
        attribute='birth_date',
        column_name='Datum narození',
        widget=DateWidget(format='%d.%m.%Y'),
    )

    class Meta:
        model = Student
        fields = ('id', 'first_name', 'last_name', 'birth_date', 'school_class')
        # Stejný způsob párování jako StudentLookupMixin (main/forms.py) -
        # opakovaný import stejného souboru tak žáky nezdvojí, ale aktualizuje.
        import_id_fields = ('first_name', 'last_name', 'birth_date')

    def __init__(self, school_class=None, **kwargs):
        super().__init__(**kwargs)
        self.school_class = school_class

    def before_import_row(self, row, **kwargs):
        if self.school_class is not None:
            row['school_class'] = self.school_class.pk
