from django import forms


class CSVImportForm(forms.Form):
    csv = forms.FileField()
