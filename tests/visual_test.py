import os
import pytest
from selenium import webdriver
from applitools.selenium import Eyes, Target, BatchInfo, ClassicRunner
from webdriver_manager.chrome import ChromeDriverManager

RESOLUTION = {"width": 768, "height": 1024}
# base_url = 'http://127.0.0.1:5000/'
base_url = 'https://clingon.pythonanywhere.com/'


@pytest.fixture(scope="module")
def batch_info():
    """
    Use one BatchInfo for all tests inside module
    """
    return BatchInfo("Some general Test cases name")


@pytest.fixture(name="driver", scope="function")
def driver_setup():
    """
    New browser instance per test and quite.
    """
    driver = webdriver.Chrome(ChromeDriverManager().install())
    yield driver
    # Close the browser.
    driver.quit()


@pytest.fixture(name="runner", scope="session")
def runner_setup():
    """
    One test runner for all tests. Print test results in the end of execution.
    """
    runner = ClassicRunner()
    yield runner
    all_test_results = runner.get_all_test_results()
    print(all_test_results)


@pytest.fixture(name="eyes", scope="function")
def eyes_setup(runner, batch_info):
    """
    Basic Eyes setup. It'll abort test if wasn't closed properly.
    """
    eyes = Eyes(runner)
    # Initialize the eyes SDK and set your private API key.
    eyes.api_key = os.environ["APPLITOOLS_API_KEY"]
    eyes.configure.batch = batch_info
    yield eyes
    # If the test was aborted before eyes.close was called, ends the test as aborted.
    eyes.abort_if_not_closed()


def test_home_page(eyes, driver):
    eyes.open(driver, "QA Job Stat", "First test", RESOLUTION)
    driver.get(base_url)
    eyes.check(f"Home page test", Target.window())
    eyes.close(False)


def test_time_series(eyes, driver):
    name = 'time_series'
    eyes.open(driver, "QA Job Stat", f"{name} page test", RESOLUTION)
    driver.get(f"{base_url}{name}")
    eyes.check(f"{name} page test", Target.window())
    eyes.close(False)


def test_salary(eyes, driver):
    name = 'salary'
    eyes.open(driver, "QA Job Stat", f"{name} page test", RESOLUTION)
    driver.get(f"{base_url}{name}")
    eyes.check(f"{name} page test", Target.window())
    eyes.close(False)


def test_schedule_type(eyes, driver):
    name = 'schedule_type'
    eyes.open(driver, "QA Job Stat", f"{name} page test", RESOLUTION)
    driver.get(f"{base_url}{name}")
    eyes.check(f"{name} page test", Target.window())
    eyes.close(False)


def test_employment_type(eyes, driver):
    name = 'employment_type'
    eyes.open(driver, "QA Job Stat", f"{name} page test", RESOLUTION)
    driver.get(f"{base_url}{name}")
    eyes.check(f"{name} page test", Target.window())
    eyes.close(False)
#
#
def test_experience(eyes, driver):
    name = 'experience'
    eyes.open(driver, "QA Job Stat", f"{name} page test", RESOLUTION)
    driver.get(f"{base_url}{name}")
    eyes.check(f"{name} page test", Target.window())
    eyes.close(False)


def test_with_salary(eyes, driver):
    name = 'with_salary'
    eyes.open(driver, "QA Job Stat", f"{name} page test", RESOLUTION)
    driver.get(f"{base_url}{name}")
    eyes.check(f"{name} page test", Target.window())
    eyes.close(False)


def test_key_skills(eyes, driver):
    name = 'experience'
    eyes.open(driver, "QA Job Stat", f"{name} page test", RESOLUTION)
    driver.get(f"{base_url}{name}")
    eyes.check(f"{name} page test", Target.window())
    eyes.close(False)


def test_programming_languages(eyes, driver):
    name = 'programming_languages'
    eyes.open(driver, "QA Job Stat", f"{name} page test", RESOLUTION)
    driver.get(f"{base_url}{name}")
    eyes.check(f"{name} page test", Target.window())
    eyes.close(False)


def test_unit_test_frameworks(eyes, driver):
    name = 'unit_test_frameworks'
    eyes.open(driver, "QA Job Stat", f"{name} page test", RESOLUTION)
    driver.get(f"{base_url}{name}")
    eyes.check(f"{name} page test", Target.window())
    eyes.close(False)


def test_load_testing_tools(eyes, driver):
    name = 'load_testing_tools'
    eyes.open(driver, "QA Job Stat", f"{name} page test", RESOLUTION)
    driver.get(f"{base_url}{name}")
    eyes.check(f"{name} page test", Target.window())
    eyes.close(False)


def test_bdd_frameworks(eyes, driver):
    name = 'bdd_frameworks'
    eyes.open(driver, "QA Job Stat", f"{name} page test", RESOLUTION)
    driver.get(f"{base_url}{name}")
    eyes.check(f"{name} page test", Target.window())
    eyes.close(False)


def test_web_ui_tools(eyes, driver):
    name = 'web_ui_tools'
    eyes.open(driver, "QA Job Stat", f"{name} page test", RESOLUTION)
    driver.get(f"{base_url}{name}")
    eyes.check(f"{name} page test", Target.window())
    eyes.close(False)


def test_mobile_testing_frameworks(eyes, driver):
    name = 'web_ui_tools'
    eyes.open(driver, "QA Job Stat", f"{name} page test", RESOLUTION)
    driver.get(f"{base_url}{name}")
    eyes.check(f"{name} page test", Target.window())
    eyes.close(False)


def test_bugtracking_n_tms(eyes, driver):
    name = 'bugtracking_n_tms'
    eyes.open(driver, "QA Job Stat", f"{name} page test", RESOLUTION)
    driver.get(f"{base_url}{name}")
    eyes.check(f"{name} page test", Target.window())
    eyes.close(False)


def test_cvs(eyes, driver):
    name = 'cvs'
    eyes.open(driver, "QA Job Stat", f"{name} page test", RESOLUTION)
    driver.get(f"{base_url}{name}")
    eyes.check(f"{name} page test", Target.window())
    eyes.close(False)


def test_ci_cd(eyes, driver):
    name = 'ci_cd'
    eyes.open(driver, "QA Job Stat", f"{name} page test", RESOLUTION)
    driver.get(f"{base_url}{name}")
    eyes.check(f"{name} page test", Target.window())
    eyes.close(False)


def test_word_cloud(eyes, driver):
    name = 'word_cloud'
    eyes.open(driver, "QA Job Stat", f"{name} page test", RESOLUTION)
    driver.get(f"{base_url}{name}")
    eyes.check(f"{name} page test", Target.window())
    eyes.close(False)




















