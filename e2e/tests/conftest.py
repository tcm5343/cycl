import cycl


def pytest_report_header():
    # shows which cycl the e2e tests run against (see CYCL_SPEC in the makefile)
    return f'cycl under test: {cycl.__version__} ({cycl.__file__})'
