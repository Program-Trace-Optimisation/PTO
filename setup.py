# At the root of your project, create a setup.py file if you haven't already
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import sys, os

class PyTest(TestCommand):
    def run_tests(self):
        # Get the project root directory
        project_root = os.path.abspath(os.path.dirname(__file__))
        
        # Remove the current directory and tests from sys.path
        sys.path = [p for p in sys.path if p != '' and not p.endswith('tests')]
        
        # Add the project root to sys.path
        sys.path.insert(0, project_root)
        
        print("Modified Python path:")
        for path in sys.path:
            print(path)
        
        print("\nCurrent working directory:", os.getcwd())
        
        print("\nContents of project root:")
        for item in os.listdir(project_root):
            print(item)

        import unittest
        test_loader = unittest.TestLoader()
        test_suite = test_loader.discover('tests', pattern='test_*.py')
        result = unittest.TextTestRunner(verbosity=2).run(test_suite)
        sys.exit(not result.wasSuccessful())

setup(
    name="pto",
    version="0.1",
    packages=find_packages(),
    tests_require=['pytest'],
    cmdclass={'test': PyTest},
)