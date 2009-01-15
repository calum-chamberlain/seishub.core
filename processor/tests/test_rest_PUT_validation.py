# -*- coding: utf-8 -*-
"""
A test suite for validating PUT requests on REST resources.
"""

from StringIO import StringIO
from seishub.core import Component, implements
from seishub.exceptions import SeisHubError
from seishub.packages.builtins import IResourceType, IPackage
from seishub.packages.installer import registerSchema
from seishub.processor import PUT, DELETE, Processor
from seishub.processor.resources import RESTFolder
from seishub.test import SeisHubEnvironmentTestCase
from twisted.web import http
import os
import unittest


XML_DOC = """<?xml version="1.0" encoding="utf-8"?>

%s"""


XML_VALID_SCHEMATRON = """<?xml version="1.0" encoding="utf-8"?>

<Total>
   <Percent>20</Percent>
   <Percent>30</Percent>
   <Percent>50</Percent>
</Total>"""

XML_INVALID_SCHEMATRON = """<?xml version="1.0" encoding="utf-8"?>

<Total>
   <Percent>21</Percent>
   <Percent>30</Percent>
   <Percent>50</Percent>
</Total>"""


class APackage(Component):
    """
    A test package.
    """
    implements(IPackage)
    
    package_id = 'put-validation-test'


class SchematronResourceType(Component):
    """
    A test resource type which includes a Schematron validation schema.
    """
    implements(IResourceType)
    
    package_id = 'put-validation-test'
    resourcetype_id = 'schematron'
    registerSchema('data' + os.sep + 'schematron.sch', 'Schematron')

class RelaxNGResourceType(Component):
    """
    A test resource type which includes a RelaxNG validation schema.
    """
    implements(IResourceType)
    
    package_id = 'put-validation-test'
    resourcetype_id = 'relaxng'
    
    registerSchema('data' + os.sep + 'relaxng.rng', 'RelaxNG')


class XMLSchemaResourceType(Component):
    """
    A test resource type including a XMLSchema validation schema.
    """
    implements(IResourceType)
    
    package_id = 'put-validation-test'
    resourcetype_id = 'xmlschema'
    
    registerSchema('data' + os.sep + 'xmlschema.xsd', 'XMLSchema')


class ComplexXMLSchemaResourceType(Component):
    """
    A test resource type including a complex XMLSchema validation schema.
    """
    implements(IResourceType)
    
    package_id = 'put-validation-test'
    resourcetype_id = 'complex'
    
    registerSchema('data' + os.sep + 'QuakeML-BED-1.1.xsd', 'XMLSchema')


class MultipleXMLSchemaResourceType(Component):
    """
    A test resource type including multiple validation schema.
    """
    implements(IResourceType)
    
    package_id = 'put-validation-test'
    resourcetype_id = 'multi'
    
    registerSchema('data' + os.sep + 'xmlschema.xsd', 'XMLSchema')
    registerSchema('data' + os.sep + 'relaxng.rng', 'RelaxNG')


class RestPUTValidationTests(SeisHubEnvironmentTestCase):
    """
    A test suite for validating PUT requests on REST resources.
    """
    def setUp(self):
        self.env.enableComponent(APackage)
        self.env.enableComponent(XMLSchemaResourceType)
        self.env.enableComponent(ComplexXMLSchemaResourceType)
        self.env.enableComponent(MultipleXMLSchemaResourceType)
        self.env.enableComponent(RelaxNGResourceType)
        self.env.enableComponent(SchematronResourceType)
        self.env.tree = RESTFolder()
    
    def tearDown(self):
        self.env.disableComponent(XMLSchemaResourceType)
        self.env.disableComponent(ComplexXMLSchemaResourceType)
        self.env.disableComponent(MultipleXMLSchemaResourceType)
        self.env.disableComponent(RelaxNGResourceType)
        self.env.disableComponent(SchematronResourceType)
        self.env.disableComponent(APackage)
    
    def test_validateRelaxNG(self):
        """
        Validate uploaded resource with RelaxNG.
        """
        proc = Processor(self.env)
        # create valid resource
        proc.run(PUT, '/put-validation-test/relaxng/valid.xml', 
                 StringIO(XML_DOC % "<a><b></b></a>"))
        # create invalid resource
        try:
            proc.run(PUT, '/put-validation-test/relaxng/invalid.xml', 
                     StringIO(XML_DOC % "<a><c></c></a>"))
            self.fail("Expected SeisHubError")
        except SeisHubError, e:
            self.assertEqual(e.code, http.CONFLICT)
        # delete resource
        proc.run(DELETE, '/put-validation-test/relaxng/valid.xml')
        try:
            proc.run(DELETE, '/put-validation-test/relaxng/invalid.xml')
            self.fail("Expected SeisHubError")
        except SeisHubError, e:
            self.assertEqual(e.code, http.NOT_FOUND)
    
    def test_validateSchematron(self):
        """
        Validate uploaded resource with Schematron.
        """
        proc = Processor(self.env)
        # create valid resource
        proc.run(PUT, '/put-validation-test/schematron/valid.xml', 
                 StringIO(XML_VALID_SCHEMATRON))
        # create invalid resource
        try:
            proc.run(PUT, '/put-validation-test/schematron/invalid.xml', 
                     StringIO(XML_INVALID_SCHEMATRON))
            self.fail("Expected SeisHubError")
        except SeisHubError, e:
            self.assertEqual(e.code, http.CONFLICT)
        # delete resource
        proc.run(DELETE, '/put-validation-test/schematron/valid.xml')
        try:
            proc.run(DELETE, '/put-validation-test/schematron/invalid.xml')
            self.fail("Expected SeisHubError")
        except SeisHubError, e:
            self.assertEqual(e.code, http.NOT_FOUND)
    
    def test_validateXMLSchema(self):
        """
        Validate uploaded resource with XMLSchema.
        """
        proc = Processor(self.env)
        # create valid resource
        proc.run(PUT, '/put-validation-test/xmlschema/valid.xml', 
                 StringIO(XML_DOC % "<a><b></b></a>"))
        # create invalid resource
        try:
            proc.run(PUT, '/put-validation-test/xmlschema/invalid.xml', 
                     StringIO(XML_DOC % "<b><a/></b>"))
            self.fail("Expected SeisHubError")
        except SeisHubError, e:
            self.assertEqual(e.code, http.CONFLICT)
        # delete resource
        proc.run(DELETE, '/put-validation-test/xmlschema/valid.xml')
        try:
            proc.run(DELETE, '/put-validation-test/xmlschema/invalid.xml')
            self.fail("Expected SeisHubError")
        except SeisHubError, e:
            self.assertEqual(e.code, http.NOT_FOUND)
    
    def test_validateMultipleSchemas(self):
        """
        Validate uploaded resource with multiple schemas.
        """
        proc = Processor(self.env)
        # create valid resource
        proc.run(PUT, '/put-validation-test/multi/valid.xml', 
                 StringIO(XML_DOC % "<a><b></b></a>"))
        # create invalid resource
        try:
            proc.run(PUT, '/put-validation-test/multi/invalid.xml', 
                     StringIO(XML_DOC % "<b><a/></b>"))
            self.fail("Expected SeisHubError")
        except SeisHubError, e:
            self.assertEqual(e.code, http.CONFLICT)
        # delete resource
        proc.run(DELETE, '/put-validation-test/multi/valid.xml')


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(RestPUTValidationTests, 'test'))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')