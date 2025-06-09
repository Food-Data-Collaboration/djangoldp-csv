yaml_config = """
dependencies:

ldppackages:
  - djangoldp_csv
  - djangoldp_csv.tests

server:
  ALLOWED_HOSTS:
    - '*'
  AUTH_USER_MODEL: tests.User
  EMAIL_HOST: somewhere
  ANONYMOUS_USER_NAME: None
  ROOT_URLCONF: djangoldp.urls
  SEND_BACKLINKS: false
  SITE_URL: https://startinblox.com
  BASE_URL: https://startinblox.com
  REST_FRAMEWORK:
    DEFAULT_PAGINATION_CLASS: djangoldp.pagination.LDPPagination
    PAGE_SIZE: 5
  USE_TZ: false
  SEND_BACKLINKS: false
  GUARDIAN_AUTO_PREFETCH: true
  SERIALIZER_CACHE: false
  STORE_ACTIVITIES: VERBOSE
"""
