from javim.settings import JavaRunConfiguration, RunConfiguration, RunConfigurationProvider, ProgramArgument
from javim.maven import Maven
from enum import Enum
from os import path
from tempfile import NamedTemporaryFile
import re
from lxml import etree

SUITE_PREAMBLE = '<!DOCTYPE suite SYSTEM "http://testng.org/testng-1.0.dtd">'
CLASS_SUITE_TEMPLATE = '<suite name="{suite_name}" verbose="2"><test name="{test_name}"><classes><class name="{class_name}"/></classes></test></suite>'
METHODS_SUITE_TEMPLATE = '<suite name="{suite_name}" verbose="2"><test name="{test_name}"><classes><class name="{class_name}"><methods>{include_methods}</methods></class></classes></test></suite>'
METHOD_INCLUDE_TEMPLATE = '<include name="{method_name}"/>'


class TestNGTestArguments(Enum):

    SUITE = ProgramArgument("Suite-file",  "Path to the suite.xml file", "{value}")


class TestNGTestRunConfiguration(JavaRunConfiguration):

    TEST_CLASS_REGEX = re.compile("\\s*public\\s+class\\s+([A-Za-z$€][A-Za-z0-9_$€]*)\\s*\\{?")
    TEST_METHOD_REGEX = re.compile("\\s*public\\s+void\\s+\\b([a-zA-Z$€][a-zA-Z_$€0-9]*)\\s*\\(\\s*\\)\\s*(throws [^\\s]+)?\\s*\\{?")

    @staticmethod
    def create_config(line, col, source_file, project, maven):
        class_match = re.fullmatch(TestNGTestRunConfiguration.TEST_CLASS_REGEX, line)
        method_match = re.fullmatch(TestNGTestRunConfiguration.TEST_METHOD_REGEX, line)
        test_class = JavaRunConfiguration.filename_to_class(project, source_file)
        test_methods = [method_match.group(1)] if method_match else None

        name = test_class + "$" + test_methods[0] if test_methods else test_class

        return TestNGTestRunConfiguration(test_class, project, test_class, test_methods)

    @staticmethod
    def mayrun(line, col):
        return re.fullmatch(TestNGTestRunConfiguration.TEST_CLASS_REGEX, line) or re.fullmatch(TestNGTestRunConfiguration.TEST_METHOD_REGEX, line)

    @staticmethod
    def load_config(name, project):
        TestNGTestRunConfiguration(name, project, None).rebuild_commands()

    RunConfiguration.register_provider(RunConfigurationProvider("TestNGTest",
                                       mayrun.__func__,
                                       create_config.__func__,
                                       load_config.__func__))

    def __init__(self, name, project, test_class, test_methods=None):
        format_dict = {'suite_name': name, 'test_name': name, 'class_name': test_class}
        format_str = CLASS_SUITE_TEMPLATE

        if test_methods is not None:
            format_dict['include_methods'] = "\n".join([METHOD_INCLUDE_TEMPLATE.format(method_name=meth) for meth in test_methods])
            format_str = METHODS_SUITE_TEMPLATE

        suite = SUITE_PREAMBLE + "\n" + format_str.format(**format_dict)

        suite_file_name = name + "_suite.xml"
        suite_file_path = path.join(project['settings_dir'], suite_file_name)
        suite_file = open(suite_file_path, "w")
        suite_file.write(suite)
        suite_file.close()
        args = [TestNGTestArguments.SUITE.value.build(suite_file_path)]

        super(TestNGTestRunConfiguration, self).__init__(name,
                                                     project,
                                                     "org.testng.TestNG",
                                                     args)
