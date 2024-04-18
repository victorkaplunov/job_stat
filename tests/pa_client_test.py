from pythonanywhere_client import PythonAnywhereClient

api = PythonAnywhereClient()


def test_file_operation():
    """The test suite for file operation methods from API PythonAnywhere client."""

    api.delete_file('dummy_file.txt')
    assert api.get_file('dummy_file.txt') == 404

    assert api.upload_file('dummy_file.txt') == 201

    assert api.get_file('dummy_file.txt') == 200

    assert api.delete_file('dummy_file.txt') == 204

    assert api.get_file('dummy_file.txt') == 404
