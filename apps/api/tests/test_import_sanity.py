import importlib
import os
import unittest


class ImportSanityTests(unittest.TestCase):
    def test_can_import_main_and_core_routes(self) -> None:
        modules = [
            'main',
            'routes.images',
            'routes.video',
            'routes.script',
            'routes.voiceover',
            'routes.projects',
        ]
        for module_name in modules:
            with self.subTest(module=module_name):
                module = importlib.import_module(module_name)
                self.assertIsNotNone(module)

    def test_main_app_has_expected_route_prefixes(self) -> None:
        main = importlib.import_module('main')
        app = getattr(main, 'app')
        paths = {route.path for route in app.router.routes}

        expected_prefixes = ['/api/images', '/api/video', '/api/voiceover']
        for prefix in expected_prefixes:
            with self.subTest(prefix=prefix):
                self.assertTrue(
                    any(path.startswith(prefix) for path in paths),
                    f'missing route prefix: {prefix}',
                )


if __name__ == '__main__':
    os.environ.setdefault('PYTHONUNBUFFERED', '1')
    unittest.main()
