# DjangoLDP CSV

The objective of this package is to provide a generic import for CSV files using a specification based on RDF data, backed by DjangoLDP models.

## CSV Import

The CSV import is provided by this package via a POST request at the following URL:

* `/djangoldp-csv/import/`

By default, only authenticated superusers can access this view. See "Security" below.

The POST request must include one file upload on the key `csv`, a CSV document. An example CSV document can be found in [tests/import.csv](./djangoldp_csv/tests/import.csv). The structure of the CSV document is important for this package to match the data imported to your models.

| urlid | https://github.com/datafoodconsortium/ontology/releases/latest/download/DFC_BusinessOntology.owl#hasAddress |
| ------------- | ------------- |
| "http://test.host/api/dfc/enterprises/1"  | "http://test.host/api/dfc/addresses/1"  |
| "http://test.host/api/dfc/enterprises/1"  | "http://test.host/api/dfc/addresses/2, http://test.host/api/dfc/addresses/3" |

Each csv must include the data for only one model type, which should be passed using the query parameter `model-type`, with the RDF type configured on the DjangoLDP [Model](https://git.startinblox.com/djangoldp-packages/djangoldp/-/blob/master/docs/create_model.md?ref_type=heads). Note that column headings use the RDF types configured on the model fields, also.

Of course, sending only one model per csv means that for interconnected models with foreign keys, multiple CSV transmissions are required. In the example above we include urlids corresponding to the `Enterprise` model, with a column for the field `dfc-b:hasAddress`, which could be a foreign key pointing to the model `Address`. When djangoldp-csv parses this file, the `Enterprise` instances will be created along with the `Address` instances and these connections, but only the `urlid` of the Address will be populated. This is valid in DjangoLDP (considered as a reference to an external object which can be retrieved at `http://test.host/api/dfc/addresses/2`), but to populate the fields we would send a second CSV, this time with the `model-type` of the Address model.

### CSV Import Model Select

With the correct query parameters you can access the CSV upload for the appropriate model, which means of course that you can include it in your application via an `<a>` element directly. Out-of-the-box this package also supports a view for selecting the model to upload, which can be accessed at the same path simply excluding the query parameter (`/djangoldp-csv/import/`).

You can control which models are available in this list (and which can be targeted for CSV upload), using the setting `DJANGOLDP_CSV_MODELS`:

```python
DJANGOLDP_CSV_MODELS = ["dfc-b:Enterprise", "dfc-b:Product"]
```

By default all models with configured RDF values are accepted.

## Security

In order to protect your data, only super-users can access the import view (`user.is_superuser`).

## Testing

The `tests` module contains unit tests for the package. To run the full test suite, use `python -m unittest djangoldp_csv.tests.runner`. The file `server_settings.py` configures the DjangoLDP settings for the test suite, using YAML. `tests.models` contains models which are used in the test application.
