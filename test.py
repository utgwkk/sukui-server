import unittest
import json
from urllib.parse import quote
import main

class AppTest(unittest.TestCase):
    def setUp(self):
        main.app.testing = True
        self.app = main.app.test_client()

    def tearDown(self):
        pass

    def test_get_image(self):
        rv = self.app.get('/sukui/api/image/20000')
        resp_data = json.loads(rv.data)
        self.assertTrue(resp_data['ok'])
        self.assertEqual(
            20000,
            resp_data['data']['id']
        )

    def test_get_image_not_found(self):
        rv = self.app.get('/sukui/api/image/0')
        resp_data = json.loads(rv.data)
        self.assertFalse(resp_data['ok'])

    def test_get_images_default(self):
        rv = self.app.get('/sukui/api/images')
        resp_data = json.loads(rv.data)
        self.assertTrue(resp_data['ok'])
        self.assertEqual(
            20,
            len(resp_data['data'])
        )

    def test_get_images_count_200(self):
        rv = self.app.get('/sukui/api/images?count=200')
        resp_data = json.loads(rv.data)
        self.assertTrue(resp_data['ok'])
        self.assertEqual(
            200,
            len(resp_data['data'])
        )

    def test_get_images_error_count_larger_than_200(self):
        rv = self.app.get('/sukui/api/images?count=201')
        resp_data = json.loads(rv.data)
        self.assertFalse(resp_data['ok'])

    def test_get_images_error_count_smaller_than_1(self):
        rv = self.app.get('/sukui/api/images?count=0')
        resp_data = json.loads(rv.data)
        self.assertFalse(resp_data['ok'])

    def test_get_images_error_count_invalid(self):
        rv = self.app.get('/sukui/api/images?count=hoge')
        resp_data = json.loads(rv.data)
        self.assertFalse(resp_data['ok'])

    def test_get_images_max_id(self):
        rv = self.app.get('/sukui/api/images?max_id=40000')
        resp_data = json.loads(rv.data)
        self.assertTrue(resp_data['ok'])
        self.assertEqual(
            40000,
            resp_data['data'][0]['id']
        )

    def test_get_images_reversed_since_id(self):
        rv = self.app.get('/sukui/api/images?since_id=40000&reversed=1')
        resp_data = json.loads(rv.data)
        self.assertTrue(resp_data['ok'])
        self.assertEqual(
            40001,
            resp_data['data'][0]['id']
        )

    def test_search_images_without_keyword(self):
        rv = self.app.get('/sukui/api/images/search')
        resp_data = json.loads(rv.data)
        self.assertFalse(resp_data['ok'])

    def test_search_images(self):
        rv = self.app.get(f'/sukui/api/images/search?keyword={quote("奈緒")}')
        resp_data = json.loads(rv.data)
        self.assertTrue(resp_data['ok'])
        self.assertIn(
            "奈緒",
            resp_data['data'][0]['comment']
        )

    def test_search_images_max_id(self):
        rv = self.app.get(f'/sukui/api/images/search?keyword={quote("奈緒")}&max_id=40000')
        resp_data = json.loads(rv.data)
        self.assertTrue(resp_data['ok'])
        self.assertIn(
            "奈緒",
            resp_data['data'][0]['comment']
        )
        self.assertLessEqual(
            resp_data['data'][0]['id'],
            40000
        )

    def test_search_images_reversed_since_id(self):
        rv = self.app.get(f'/sukui/api/images/search?keyword={quote("奈緒")}&since_id=40000&reversed=1')
        resp_data = json.loads(rv.data)
        self.assertTrue(resp_data['ok'])
        self.assertIn(
            "奈緒",
            resp_data['data'][0]['comment']
        )
        self.assertGreater(
            resp_data['data'][0]['id'],
            40000
        )

    def test_search_images_error_count_larger_than_200(self):
        rv = self.app.get('/sukui/api/images/search?keyword={quote("奈緒")}&count=201')
        resp_data = json.loads(rv.data)
        self.assertFalse(resp_data['ok'])

    def test_search_images_error_count_smaller_than_1(self):
        rv = self.app.get('/sukui/api/images/search?keyword={quote("奈緒")}&count=0')
        resp_data = json.loads(rv.data)
        self.assertFalse(resp_data['ok'])

    def test_search_images_error_count_invalid(self):
        rv = self.app.get('/sukui/api/images/search?keyword={quote("奈緒")}&count=hoge')
        resp_data = json.loads(rv.data)
        self.assertFalse(resp_data['ok'])


if __name__ == '__main__':
    unittest.main()
