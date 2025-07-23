import csv
import io
import logging

from django import forms
from djangoldp_csv.errors import FieldParsingError


logger = logging.getLogger("djangoldp")


class FileField(forms.FileField):
    model_type = None

    def __init__(self, *args, **kwargs):
        self.model_type = kwargs.pop("model_type", None)
        super().__init__(*args, **kwargs)


class BaseCSVImportForm(forms.Form):
    """
    Form for parsing CSV files of the format specified by this package.

    A view using children of this form should call process_all_files after validating the form is clean.
    """

    def _process_csv_fields(self, model, row):
        """Attempts to resolve a dictionary mapping model field names to RDF properties from the CSV"""
        fields = {}

        for key in row.keys():
            model_field = model.get_field_from_rdf_type(key)
            if model_field is None:
                # NOTE: A future version of DjangoLDP will provide a JSONField where we can store additional fields.
                logger.warning(
                    f"WARN unable to find model field for value {key} on {model}. Not storing this data"
                )
                continue
            fields[model_field.name] = key

        return fields

    def get_unique_kwargs(self, urlid):
        # Hook for subclass in another library.
        return {"urlid": urlid}

    def process_file(self, field, model_type=None):
        file = self.cleaned_data[field.name]
        if model_type is None:
            if field.field.model_type is None:
                raise ValueError("No model type configured on form or field")
            model_type = field.field.model_type
        imported_file = csv.DictReader(io.StringIO(file.read().decode("utf-8")))

        # Attempt to resolve the fields from the document.
        first_row = next(imported_file)
        fields = self._process_csv_fields(model_type, first_row)

        if not len(fields):
            raise FieldParsingError()

        def process_row(row):
            # Fetch instance if it already exists, else create a new row.
            instance = (
                model_type.objects.filter(
                    **self.get_unique_kwargs(row["urlid"])
                ).first()
                if "urlid" in row
                else None
            )
            if instance is None:
                instance = model_type()

            for key in fields.keys():
                # Handle foreign keys
                model_field = model_type.get_field_from_rdf_type(key)
                if model_field.related_model is None:
                    setattr(instance, key, row[fields[key]])
                else:
                    related_model = model_field.related_model
                    unique_kwargs = self.get_unique_kwargs(row[fields[key]])
                    try:
                        sub_instance = related_model.objects.get(**unique_kwargs)
                    except related_model.DoesNotExist:
                        sub_instance = related_model(**unique_kwargs)
                        sub_instance.save()

                    if model_field.one_to_many or model_field.many_to_many:
                        getattr(instance, key).add(sub_instance)
                    else:
                        setattr(instance, key, sub_instance)

            # NOTE: we can't use bulk_create or bulk_update here because we need post-save signals to run.
            instance.save()

        # Workaround for performance:
        # We only want to process the fields once in the CSV, so we used next() once already to process them.
        # Process this row first and then return to the stream.
        process_row(first_row)
        for row in imported_file:
            process_row(row)

    def file_fields(self):
        return [
            field
            for field in self.visible_fields()
            if isinstance(field.field, forms.FileField)
        ]

    def process_all_files(self, model_type=None):
        for field in self.file_fields():
            if self.cleaned_data[field.name] is not None:
                self.process_file(field, model_type)


class CSVImportForm(BaseCSVImportForm):
    """Default implementation of CSV import with a single file field"""

    csv = FileField()
