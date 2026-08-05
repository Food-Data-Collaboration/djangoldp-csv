from django.urls import path

from djangoldp_csv.views import CSVImportView

urlpatterns = [
    path("djangoldp-csv/import/", CSVImportView.as_view(), name="djangoldp-csv-import")
]
