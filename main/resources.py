from import_export import resources
from .models import Student

class StudentResource(resources.ModelResource):
    class Meta:
        model = Student
        # fields = ('id', 'name', 'category', 'created_at') # Specify fields if you want to limit imports/exports

