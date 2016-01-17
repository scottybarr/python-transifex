# -*- coding: utf-8 -*-

import json

from mock import patch, Mock, MagicMock
from unittest import TestCase

from transifex.api import TransifexAPI
from transifex.exceptions import InvalidSlugException, TransifexAPIException


def _check_for_new_project_kwargs(*args, **kwargs):
    response = Mock()
    data = json.loads(kwargs.get('data', "{}"))
    required_kwargs = ['source_language_code', 'name', 'slug',
                       'repository_url', 'private']
    missing_keys = set(required_kwargs) - set(data.keys())
    if missing_keys:
        response.status_code = 400
        response.content = missing_keys
    elif not data['private'] and data['repository_url'] is None:
        response.status_code = 400
        response.content = 'repository_url is required for public ' \
                           'repositories'
    else:
        response.status_code = 201

    return response


class TransifexAPITest(TestCase):

    def setUp(self):
        data = {
            'username': 'aaa', 'password': 'aaa',
            'host': 'http://www.mydomain.com'
        }
        self.api = TransifexAPI(**data)

    @patch('requests.post')
    def test_new_public_project_with_required_args(self, mock_requests):
        """
        Test creating a new project with only the required arguments
        """
        mock_requests.side_effect = _check_for_new_project_kwargs
        self.api.new_project(slug='abc', repository_url='http://abc.com')

    def test_new_project_bad_slug(self):
        """
        Test the `new_project` api call when the slug is invalid
        """
        self.assertRaises(
            InvalidSlugException,
            self.api.new_project,
            slug='.'
        )
        self.assertRaises(
            InvalidSlugException,
            self.api.new_project,
            slug='/'
        )
        self.assertRaises(
            InvalidSlugException,
            self.api.new_project,
            slug='%@$'
        )

    def test_new_project_no_repository_url(self):
        """
        Test the `new_project` api call when no repository_url is passed to a
        public project
        """
        self.assertRaises(
            TransifexAPIException,
            self.api.new_project,
            slug='fdsfs',
            private=False
        )

    @patch('requests.post')
    def test_new_project_with_optional_args(self, mock_requests):
        """
        Test creating a new project with the optional arguments
        """

        def side_effect(*args, **kwargs):
            response = Mock()
            data = json.loads(kwargs.get('data', "{}"))
            expected_items = ['source_language_code', 'name', 'slug']
            if all(item in data for item in expected_items):
                response.status_code = 201
            else:
                response.status_code = 400

            return response

        mock_requests.side_effect = side_effect
        self.api.new_project(
            slug='abc', name='abc', source_language_code='pt',
            outsource_project_name='anotherproject'
        )

    @patch('requests.post')
    def test_new_project_with_http_response_400(self, mock_requests):
        """
        Test creating a new project when the transifex server returns a
        '400 BAD REQUEST' response
        """

        def side_effect(*args, **kwargs):
            response = Mock()
            response.status_code = 400
            return response

        mock_requests.side_effect = side_effect
        self.assertRaises(
            TransifexAPIException, self.api.new_project, slug='abc'
        )

    @patch('requests.get')
    def test_list_resources(self, mock_requests):
        """
        Test the `list_resources` api call
        """
        response_content = [{'a': 1}, {'b': 2}]

        def side_effect(*args, **kwargs):
            response = Mock()
            response.status_code = 200
            response.content = json.dumps(response_content)
            return response

        mock_requests.side_effect = side_effect
        resources = self.api.list_resources(project_slug='abc')
        self.assertEqual(resources, response_content)

    @patch('requests.get')
    def test_list_resources_with_bad_project_name(self, mock_requests):
        """
        Test the 'list resources' api call, when the project name given
        doesn't exist on the transifex server
        """
        def side_effect(*args, **kwargs):
            response = Mock()
            response.status_code = 404
            return response

        mock_requests.side_effect = side_effect
        self.assertRaises(
            TransifexAPIException, self.api.list_resources, project_slug='abc'
        )

    @patch('io.open', create=True)
    @patch('requests.post')
    def test_new_resource(self, mock_requests, mock_open):
        """
        Test the `new_resource` api call
        """
        file_contents = 'aaaaaa\nggggg'
        mock_open.return_value = MagicMock()
        mock_open.return_value.read = lambda: file_contents

        required_post_params = ['name', 'slug', 'content', 'i18n_type']

        def side_effect(*args, **kwargs):
            response = Mock()
            response.status_code = 201
            data = json.loads(kwargs.get('data', "{}"))
            for param in required_post_params:
                if param not in data:
                    response.status_code = 400
                    response.content = '%r is required'
                    break

            return response

        mock_requests.side_effect = side_effect

        self.api.new_resource(
            project_slug='abc', path_to_pofile='/abc/pofile.po'
        )
        self.assertTrue(mock_requests.called)
        __, kwargs = mock_requests.call_args
        self.assertTrue('data' in kwargs)
        data = json.loads(kwargs['data'])
        self.assertEqual(data['content'], file_contents)

    @patch('io.open', create=True)
    def test_new_resource_file_not_found(self, mock_open):
        """
        Test the `new_resource` api call when the pofile cannot be found
        """
        def side_effect(*args, **kwargs):
            raise IOError('File not found')

        mock_open.side_effect = side_effect
        self.assertRaises(
            IOError,
            self.api.new_resource,
            project_slug='abc',
            path_to_pofile='/aaa/file.po'
        )

    @patch('io.open', create=True)
    def test_new_resource_bad_slug(self, mock_open):
        """
        Test the `new_resource` api call when the slug is invalid
        """
        file_contents = 'aaaaaa\nggggg'
        mock_open.return_value = MagicMock()
        mock_open.return_value.read = lambda: file_contents

        self.assertRaises(
            InvalidSlugException,
            self.api.new_resource,
            project_slug='aaa',
            resource_slug='.',
            path_to_pofile='/aaa/file.po'
        )
        self.assertRaises(
            InvalidSlugException,
            self.api.new_resource,
            project_slug='aaa',
            resource_slug='/',
            path_to_pofile='/aaa/file.po'
        )
        self.assertRaises(
            InvalidSlugException,
            self.api.new_resource,
            project_slug='aaa',
            resource_slug='%@$',
            path_to_pofile='/aaa/file.po'
        )

    @patch('io.open', create=True)
    @patch('requests.post')
    def test_new_resource_server_error(self, mock_requests, mock_open):
        """
        Test the `new_resource` api call when the transifex server returns an
        error
        """
        file_contents = 'aaaaaa\nggggg'
        mock_open.return_value = MagicMock()
        mock_open.return_value.read = lambda: file_contents

        def side_effect(*args, **kwargs):
            response = Mock()
            response.status_code = 404
            return response

        mock_requests.side_effect = side_effect
        self.assertRaises(
            TransifexAPIException, self.api.new_resource,
            project_slug='abc', path_to_pofile='/aaa/file.po'
        )

    @patch('io.open', create=True)
    @patch('requests.post')
    def test_new_resource_with_optional_args(self, mock_requests, mock_open):
        """
        Test the `new_resource` api call with the optional args
        """
        file_contents = 'aaaaaa\nggggg'
        mock_open.return_value = MagicMock()
        mock_open.return_value.read = lambda: file_contents

        required_post_params = ['name', 'slug', 'content', 'i18n_type']

        def side_effect(*args, **kwargs):
            response = Mock()
            response.status_code = 201
            data = json.loads(kwargs.get('data', "{}"))
            for param in required_post_params:
                if param not in data:
                    response.status_code = 400
                    response.content = '%r is required'
                    break

            return response

        mock_requests.side_effect = side_effect

        self.api.new_resource(
            project_slug='abc', path_to_pofile='/abc/pofile.po',
            resource_slug='def', resource_name='A Name'
        )
        self.assertTrue(mock_requests.called)

    @patch('io.open', create=True)
    @patch('requests.put')
    def test_update_source_translation(self, mock_requests, mock_open):
        """
        Test the `update_source_translation` api call
        """
        file_contents = 'aaaaaa\nggggg'
        mock_open.return_value = MagicMock()
        mock_open.return_value.read = lambda: file_contents

        required_post_params = ['content', ]

        def side_effect(*args, **kwargs):
            response = Mock()
            data = json.loads(kwargs.get('data', "{}"))
            for param in required_post_params:
                if param not in data:
                    response.status_code = 400
                    response.content = '%r is required'
                    return response

            response.status_code = 200
            response.content = json.dumps({'a': 1})
            return response

        mock_requests.side_effect = side_effect

        self.api.update_source_translation(
            project_slug='abc', resource_slug='def',
            path_to_pofile='/abc/pofile.po'
        )
        self.assertTrue(mock_requests.called)

    @patch('io.open', create=True)
    def test_update_source_translation_file_not_found(self, mock_open):
        """
        Test the `update_source_translation` api call
        when the pofile cannot be found
        """
        def side_effect(*args, **kwargs):
            raise IOError('File not found')

        mock_open.side_effect = side_effect
        self.assertRaises(
            IOError,
            self.api.update_source_translation,
            project_slug='abc',
            resource_slug='def',
            path_to_pofile='/aaa/file.po'
        )

    @patch('io.open', create=True)
    @patch('requests.put')
    def test_update_source_translation_server_error(self, mock_requests,
                                                    mock_open):
        """
        Test the `update_source_translation` api call when the transifex server
        returns an error
        """
        file_contents = 'aaaaaa\nggggg'
        mock_open.return_value = MagicMock()
        mock_open.return_value.read = lambda: file_contents

        def side_effect(*args, **kwargs):
            response = Mock()
            response.status_code = 404
            return response

        mock_requests.side_effect = side_effect
        self.assertRaises(
            TransifexAPIException, self.api.update_source_translation,
            project_slug='abc', resource_slug='def',
            path_to_pofile='/aaa/file.po'
        )

    @patch('io.open', create=True)
    @patch('requests.put')
    def test_new_translation(self, mock_requests, mock_open):
        """
        Test the `new_translation` api call
        """
        file_contents = 'aaaaaa\nggggg'
        mock_open.return_value = MagicMock()
        mock_open.return_value.read = lambda: file_contents

        required_post_params = ['content', ]

        def side_effect(*args, **kwargs):
            response = Mock()
            data = json.loads(kwargs.get('data', "{}"))
            for param in required_post_params:
                if param not in data:
                    response.status_code = 400
                    response.content = '%r is required'
                    return response

            response.status_code = 200
            response.content = json.dumps({'s': 1})
            return response

        mock_requests.side_effect = side_effect

        self.api.new_translation(
            project_slug='abc', resource_slug='def', language_code='pt',
            path_to_pofile='/abc/pofile.po'
        )
        self.assertTrue(mock_requests.called)

    @patch('io.open', create=True)
    def test_new_translation_file_not_found(self, mock_open):
        """
        Test the `new_translation` api call when the pofile cannot be found
        """
        def side_effect(*args, **kwargs):
            raise IOError('File not found')

        mock_open.side_effect = side_effect
        self.assertRaises(
            IOError,
            self.api.new_translation,
            project_slug='abc',
            resource_slug='def',
            language_code='pt',
            path_to_pofile='/aaa/file.po'
        )

    @patch('io.open', create=True)
    @patch('requests.put')
    def test_new_translation_server_error(self, mock_requests, mock_open):
        """
        Test the `new_translation` api call when the transifex server
        returns an error
        """
        file_contents = 'aaaaaa\nggggg'
        mock_open.return_value = MagicMock()
        mock_open.return_value.read = lambda: file_contents

        def side_effect(*args, **kwargs):
            response = Mock()
            response.status_code = 404
            return response

        mock_requests.side_effect = side_effect
        self.assertRaises(
            TransifexAPIException, self.api.new_translation,
            project_slug='abc', resource_slug='def', language_code='pt',
            path_to_pofile='/aaa/file.po'
        )

    @patch('io.open', create=True)
    @patch('requests.get')
    def test_get_translation(self, mock_requests, mock_open):
        """
        Test the `get_translation` api call
        """
        mock_open.return_value = MagicMock()

        def side_effect(*args, **kwargs):
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.iter_content = lambda: 'abc\ndef\n'
            return mock_response

        mock_requests.side_effect = side_effect

        self.api.get_translation(
            project_slug='abc', resource_slug='def', language_code='pt',
            path_to_pofile='/abc/pofile.po'
        )
        self.assertTrue(mock_requests.called)

    @patch('io.open', create=True)
    @patch('requests.get')
    def test_get_translation_file_not_found(self, mock_requests, mock_open):
        """
        Test the `get_translation` api call when the pofile cannot be found
        """
        def open_side_effect(*args, **kwargs):
            raise IOError('File not found')

        mock_open.side_effect = open_side_effect

        def requests_side_effect(*args, **kwargs):
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.iter_content = lambda: 'abc\ndef\n'
            return mock_response

        mock_requests.side_effect = requests_side_effect

        self.assertRaises(
            IOError,
            self.api.get_translation,
            project_slug='abc',
            resource_slug='def',
            language_code='pt',
            path_to_pofile='/abc/pofile.po'
        )

    @patch('requests.get')
    def test_get_translation_server_error(self, mock_requests):
        """
        Test the `get_translation` api call when the transifex server
        returns an error
        """

        def side_effect(*args, **kwargs):
            response = Mock()
            response.status_code = 404
            return response

        mock_requests.side_effect = side_effect
        self.assertRaises(
            TransifexAPIException, self.api.get_translation,
            project_slug='abc', resource_slug='def', language_code='pt',
            path_to_pofile='/abc/pofile.po'
        )

    @patch('requests.delete')
    def test_delete_resource(self, mock_requests):
        """
        Test the `delete_resource` api call
        """

        def side_effect(*args, **kwargs):
            mock_response = Mock()
            mock_response.status_code = 204
            return mock_response

        mock_requests.side_effect = side_effect

        self.api.delete_resource(project_slug='abc', resource_slug='def')
        self.assertTrue(mock_requests.called)

    @patch('requests.delete')
    def test_delete_resource_server_error(self, mock_requests):
        """
        Test the `delete_resource` api call when the transifex server
        returns an error
        """

        def side_effect(*args, **kwargs):
            response = Mock()
            response.status_code = 404
            return response

        mock_requests.side_effect = side_effect
        self.assertRaises(
            TransifexAPIException, self.api.delete_resource,
            project_slug='abc', resource_slug='def'
        )

    @patch('requests.get')
    def test_list_languages(self, mock_requests):
        """
        Test the `list_languages` api call
        """
        expected_languages = ['en_GB', 'it']
        response_content = {
            'slug': 'txo',
            'mimetype': 'text/x-po',
            'source_language_code': 'en',
            'wordcount': 6160,
            'total_entities': 1017,
            'last_update': '2011-12-05 19:59:55',
            'available_languages': [
                {
                    'code_aliases': ' ',
                    'code': 'it',
                    'name': 'Italian'
                },
                {
                    'code_aliases': 'en-gb',
                    'code': 'en_GB',
                    'name': 'English (Great Britain)'
                },
            ],
        }

        def side_effect(*args, **kwargs):
            response = Mock()
            response.status_code = 200
            response.content = json.dumps(response_content)
            return response

        mock_requests.side_effect = side_effect
        languages = self.api.list_languages(
            project_slug='abc', resource_slug='def'
        )
        self.assertEqual(sorted(expected_languages), sorted(languages))

    @patch('requests.get')
    def test_list_languages_404(self, mock_requests):
        """
        Test the `list_languages` api call when the project or resource is not
        found
        """
        def side_effect(*args, **kwargs):
            response = Mock()
            response.status_code = 404
            return response

        mock_requests.side_effect = side_effect
        self.assertRaises(
            TransifexAPIException, self.api.list_languages, project_slug='abc',
            resource_slug='defg'
        )

    @patch('requests.get')
    def test_project_exists(self, mock_requests):
        """
        Test the `test_project_exists` api call
        """
        def side_effect(*args, **kwargs):
            response = Mock()
            response.status_code = 200
            return response

        mock_requests.side_effect = side_effect
        self.assertTrue(self.api.project_exists(project_slug='abc'))

    @patch('requests.get')
    def test_project_exists_with_no_project(self, mock_requests):
        """
        Test the `test_project_exists` api call when the project doesn't exist
        """
        def side_effect(*args, **kwargs):
            response = Mock()
            response.status_code = 404
            return response

        mock_requests.side_effect = side_effect
        self.assertFalse(self.api.project_exists(project_slug='abc'))

    @patch('requests.get')
    def test_project_exists_with_error(self, mock_requests):
        """
        Test the `test_project_exists` api call when the api returns an error
        """
        def side_effect(*args, **kwargs):
            response = Mock()
            response.status_code = 400
            return response

        mock_requests.side_effect = side_effect
        self.assertRaises(
            TransifexAPIException, self.api.project_exists, project_slug='abc'
        )
