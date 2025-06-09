# DjangoLDP CSV

The objective of this package is to provide a generic import for CSV files using a specification based on RDF data, backed by DjangoLDP models.

## Testing

The `tests` module contains unit tests for the package. To run the full test suite, use `python -m unittest djangoldp_csv.tests.runner`. The file `server_settings.py` configures the DjangoLDP settings for the test suite, using YAML. `tests.models` contains models which are used in the test application.
