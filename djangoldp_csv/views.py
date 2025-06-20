import csv
import io
import logging

from django.core.exceptions import ObjectDoesNotExist
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from djangoldp.models import Model


logger = logging.getLogger("djangoldp")


class CSVImportView(APIView):
    permission_classes = [IsAdminUser]

    def resolve_model_type(self, request):
        # Resolve the model type of the CSV file contents.
        # We consider the query parameter and the explicit contents of the CSV file,
        # but we could expand this in future to fallback on requesting the URI of a given row,
        # or to compare the fields included with the models configured.
        if request.GET.get("model-type") is None:
            raise ObjectDoesNotExist()
        model_type = Model.get_subclass_with_rdf_type(request.GET["model-type"])
        if model_type is not None:
            return model_type
        raise ObjectDoesNotExist()

    def post(self, request, *args, **kwargs):
        if "csv" not in request.FILES:
            return Response(
                {"error": "csv-import is a required parameter"}, status_code=400
            )

        try:
            model_type = self.resolve_model_type(request)
        except KeyError:
            return Response(
                {"error": "No model-type was passed with the CSV"}, status=400
            )
        except ObjectDoesNotExist:
            return Response(
                {"error": "No model could be found with the requested type"}, status=404
            )

        imported_file = csv.DictReader(
            io.StringIO(request.FILES["csv"].read().decode("utf-8"))
        )

        rows_to_create = []
        for row in imported_file:
            instance = model_type()
            for field in row.keys():
                model_field = model_type.get_field_from_rdf_type(field)
                if model_field is None:
                    # NOTE: A future version of DjangoLDP will provide a JSONField where we can store additional fields.
                    logger.warning(
                        f"WARN unable to find model field for value {field} on {model_type}. Not storing this data"
                    )
                    continue
                setattr(instance, model_field.name, row[field])
            rows_to_create.append(instance)

        model_type.objects.bulk_create(rows_to_create)
        return Response(status=201)
