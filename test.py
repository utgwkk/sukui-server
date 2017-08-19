import unittest
import json
import main

class AppTest(unittest.TestCase):
    def setUp(self):
        main.app.testing = True
        self.app = main.app.test_client()

    def tearDown(self):
        pass

    def test_get_images_default(self):
        rv = self.app.get('/sukui/api/images')
        resp_data = json.loads(rv.data)
        self.assertTrue(resp_data['ok'])
        self.assertEqual(
            20,
            len(resp_data['data'])
        )

if __name__ == '__main__':
    unittest.main()
