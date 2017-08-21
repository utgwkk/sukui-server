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
        for data in resp_data['data']:
            self.assertLessEqual(
                data['id'],
                40000
            )

    def test_get_images_reversed_since_id(self):
        rv = self.app.get('/sukui/api/images?since_id=40000&reversed=1')
        resp_data = json.loads(rv.data)
        self.assertTrue(resp_data['ok'])
        for data in resp_data['data']:
            self.assertGreater(
                data['id'],
                40000
            )

    def test_search_images_without_keyword(self):
        rv = self.app.get('/sukui/api/images/search')
        resp_data = json.loads(rv.data)
        self.assertFalse(resp_data['ok'])

    def test_search_images_with_empty_keyword(self):
        rv = self.app.get('/sukui/api/images/search?keyword=')
        resp_data = json.loads(rv.data)
        self.assertFalse(resp_data['ok'])

    def test_search_images(self):
        rv = self.app.get(f'/sukui/api/images/search?keyword={quote("奈緒")}')
        resp_data = json.loads(rv.data)
        self.assertTrue(resp_data['ok'])
        for data in resp_data['data']:
            self.assertIn(
                "奈緒",
                data['comment']
            )

    def test_search_images_with_length_1_query(self):
        rv = self.app.get(f'/sukui/api/images/search?keyword={quote("薫")}')
        resp_data = json.loads(rv.data)
        self.assertTrue(resp_data['ok'])
        for data in resp_data['data']:
            self.assertIn(
                "薫",
                data['comment']
            )

    def test_search_images_with_hyphen_query(self):
        rv = self.app.get(f'/sukui/api/images/search?keyword={quote("r-18")}')
        resp_data = json.loads(rv.data)
        self.assertTrue(resp_data['ok'])

        for data in resp_data['data']:
            # Case-insensitively comparison
            self.assertIn(
                "r-18",
                data['comment'].lower()
            )

    def test_search_images_and_restriction(self):
        rv = self.app.get(
            f'/sukui/api/images/search?keyword={quote("仁奈 みりあ")}')
        resp_data = json.loads(rv.data)
        self.assertTrue(resp_data['ok'])
        for data in resp_data['data']:
            self.assertIn(
                "仁奈",
                data['comment']
            )
            self.assertIn(
                "みりあ",
                data['comment']
            )

    def test_search_images_max_id(self):
        rv = self.app.get(
            f'/sukui/api/images/search?keyword={quote("奈緒")}&max_id=40000')
        resp_data = json.loads(rv.data)
        self.assertTrue(resp_data['ok'])
        for data in resp_data['data']:
            self.assertIn(
                "奈緒",
                data['comment']
            )
            self.assertLessEqual(
                data['id'],
                40000
            )

    def test_search_images_reversed_since_id(self):
        rv = self.app.get(
            f'/sukui/api/images/search'
            '?keyword={quote("奈緒")}&since_id=40000&reversed=1'
        )
        resp_data = json.loads(rv.data)
        self.assertTrue(resp_data['ok'])
        for data in resp_data['data']:
            self.assertIn(
                "奈緒",
                data['comment']
            )
            self.assertGreater(
                data['id'],
                40000
            )

    def test_search_images_error_count_larger_than_200(self):
        rv = self.app.get(
            '/sukui/api/images/search?keyword={quote("奈緒")}&count=201')
        resp_data = json.loads(rv.data)
        self.assertFalse(resp_data['ok'])

    def test_search_images_error_count_smaller_than_1(self):
        rv = self.app.get(
            '/sukui/api/images/search?keyword={quote("奈緒")}&count=0')
        resp_data = json.loads(rv.data)
        self.assertFalse(resp_data['ok'])

    def test_search_images_error_count_invalid(self):
        rv = self.app.get(
            '/sukui/api/images/search?keyword={quote("奈緒")}&count=hoge')
        resp_data = json.loads(rv.data)
        self.assertFalse(resp_data['ok'])

    def test_ngram(self):
        self.assertEqual(
            '+美玲',
            main.ngram('美玲')
        )

    def test_ngram_2(self):
        self.assertEqual(
            '+しょ +ょう +うさ +さち',
            main.ngram('しょうさち')
        )

    def test_ngram_3(self):
        self.assertEqual(
            '薫*',
            main.ngram('薫')
        )


if __name__ == '__main__':
    unittest.main()
