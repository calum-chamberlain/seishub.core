# -*- coding: utf-8 -*-

import sys
from datetime import datetime
from twisted.python import log

from seishub.core import implements, ExtensionPoint
from seishub.exceptions import InvalidObjectError
from seishub.db.util import Serializable, Relation, db_property
from seishub.packages.interfaces import IProcessorIndex
from seishub.xmldb import defaults
from seishub.xmldb.interfaces import IXmlDocument, IXmlIndex
from seishub.xmldb.resource import XmlDocument

TEXT_INDEX = 0
NUMERIC_INDEX = 1
FLOAT_INDEX = 2
DATETIME_INDEX = 3
BOOLEAN_INDEX = 4
NONETYPE_INDEX = 5
PROCESSOR_INDEX = 6

ISO_FORMAT = "%Y%m%d %H:%M:%S"
_FALSE_VALUES = ('no', 'false', 'off', '0', 'disabled')


class XmlIndex(Serializable):
    """A XML index definition.
    
    @param resourcetype: ResourcetypeWrapper instance
    @param xpath: path to node in XML tree to be indexed, or any arbitrary 
    xpath expression, that returns a value of correct type
    @param type: TEXT_INDEX | NUMERIC_INDEX | DATETIME_INDEX | BOOLEAN_INDEX |
                 NONETYPE_INDEX
    @param options: additional options for an index
    
    notes:
     - DATETIME_INDEX:
     options may be a format string (see time.strftime() documentation), but 
     note that strftime / strptime does not support microseconds (!)
     
     without a format string, ISO 8601 strings and timestamps are autodetected.
    """
    # XXX: we REALLY have a problem with circular imports
    from seishub.packages.package import ResourceTypeWrapper
    
    implements(IXmlIndex)
    
    db_table = defaults.index_def_tab
    db_mapping = {'resourcetype':Relation(ResourceTypeWrapper, 
                                          'resourcetype_id'),
                  'xpath':'xpath',
                  'type':'type',
                  'options':'options'}
    
    def __init__(self, resourcetype = None, xpath = None, type = TEXT_INDEX, 
                 options = None):
        self.resourcetype = resourcetype
        self.xpath = xpath
        self.type = type
        self.options = options
    
    def __str__(self):
        return '/' + self.resourcetype.package.package_id + '/' + \
                self.resourcetype.resourcetype_id + self.xpath
                
    def getResourceType(self):
        return self._resourcetype
     
    def setResourceType(self, data):
        self._resourcetype = data
        
    resourcetype = db_property(getResourceType, setResourceType, 
                               "Resource type", attr = '_resourcetype')
    
    def getXPath(self):
        return self._xpath
        
    def setXPath(self, xpath):
        self._xpath = xpath
    
    xpath = property(getXPath, setXPath, "XPath expression")
    
    def getType(self):
        return self._type
    
    def setType(self, type):
        self._type = type
    
    type = property(getType, setType, "Data type")
    
    def getOptions(self):
        return self._options
        
    def setOptions(self, options):
        self._options = options
    
    options = property(getOptions, setOptions, "Options")
    
    def _selectElementCls(self, type):
        return type_classes[type]
        
    def _getElementCls(self):
        return self._selectElementCls(self.type)
    
    def _getProcessorIndex(self, env):
        if hasattr(self, '_processor_idx'):
            return self._processor_idx
        # import the IProcessorIndex implementer class for this index
        pos = self.options.rfind(u".")
        class_name = self.options[pos + 1:]
        mod_name = self.options[:pos]
        mod = sys.modules[mod_name]
        cls = getattr(mod, class_name)
        self._processor_idx = cls(env)
        return self._processor_idx
    
    def _eval(self, xml_doc, env):
        if not IXmlDocument.providedBy(xml_doc):
            raise TypeError("%s is not an IXmlDocument." % str(xml_doc))
        parsed_doc = xml_doc.getXml_doc()
        try:
            nodes = parsed_doc.evalXPath(self.xpath)
        except Exception, e:
            log.err(e)
            return list()
        return [node.getStrContent() for node in nodes]
    
    def eval(self, xml_doc, env = None):
        if self.type == PROCESSOR_INDEX:
            pidx = self._getProcessorIndex(env)
            type = pidx.type
            elements = pidx.eval(xml_doc)
            if not isinstance(elements, list):
                elements = [elements]
        else:
            type = self.type
            elements = self._eval(xml_doc, env)
        res = list()
        for el in elements:
            try:
                res.append(self._selectElementCls(type)(self, el, xml_doc))
            except Exception, e:
                if env:
                    env.log.info(e)
                else:
                    log.err(e)
                    continue
        return res
    
    def prepareKey(self, data):
        return self._getElementCls()()._prepare_key(data)
        

class KeyIndexElement(Serializable):
    db_mapping = {'index':Relation(XmlIndex, 'index_id'),
                  'key':'keyval',
                  'document':Relation(XmlDocument, 'document_id')
                  }
    
    def __init__(self, index = None, key = None, document = None):
        self.index = index
        if key:
            self.key = self._filter_key(key)
        self.document = document
        
    def _filter_key(self, data):
        """Overwritten to do a type specific key handling"""
        return data
    
    def _prepare_key(self, data):
        return str(data)
        
    def getIndex(self):
        return self._index
     
    def setIndex(self, data):
        self._index = data
        
    index = db_property(getIndex, setIndex, "Index", attr = '_index')
    
    def getDocument(self):
        return self._document
     
    def setDocument(self, data):
        self._document = data
        
    document = db_property(getDocument, setDocument, "XmlDocument", 
                           attr = '_document')
    
    def getKey(self):
        return self._key
    
    def setKey(self, data):
        self._key = data
        
    key = property(getKey, setKey, "Index key")
        
    
class QualifierIndexElement(Serializable):
    db_mapping = {'index':Relation(XmlIndex, 'index_id'),
                  'document':Relation(XmlDocument, 'document_id')
                  }
    
    def __init__(self, index = None, key = None, document = None):
        self.index = index
        # ignore key
        self.key = None
        self.document = document
        
    def getIndex(self):
        return self._index
     
    def setIndex(self, data):
        self._index = data
        
    index = db_property(getIndex, setIndex, "Index", attr = '_index')
    
    def getDocument(self):
        return self._document
     
    def setDocument(self, data):
        self._document = data
        
    document = db_property(getDocument, setDocument, "XmlDocument", 
                           attr = '_document')
    

class TextIndexElement(KeyIndexElement):
    db_table = defaults.index_text_tab
    
    def _filter_key(self, data):
        return unicode(data)
    
    def _prepare_key(self, data):
        return unicode(data)
        

class NumericIndexElement(KeyIndexElement):
    db_table = defaults.index_numeric_tab
    
    def _filter_key(self, data):
        # don't pass floats directly to db
        # check if data has correct type
        float(data)
        return data


class FloatIndexElement(KeyIndexElement):
    db_table = defaults.index_float_tab
    
    def _filter_key(self, data):
        # check if data has correct type
        # but don't pass floats to db as string
        float(data)
        return data


class DateTimeIndexElement(KeyIndexElement):
    db_table = defaults.index_datetime_tab
    
    def _filter_key(self, data):
        data = data.strip()
        if self.index.options:
            return datetime.strptime(data, self.index.options)
        try:
            # XXX: this might lead to problems with iso strings that consist of numbers only
            # another solution would be to have a special '%timestamp' option
            return datetime.fromtimestamp(float(data))
        except ValueError:
            pass
        data = data.replace("-", "")
        data = data.replace("T", " ")
        ms = 0
        if '.' in data:
            data, ms = data.split('.')
            ms = int(ms.ljust(6,'0')[:6]) 
        dt = datetime.strptime(data, ISO_FORMAT)
        dt = dt.replace(microsecond = ms)
        return dt
    
    def _prepare_key(self, data):
        data = data.replace("-", "")
        data = data.replace("T", " ")
        ms = 0
        if '.' in data:
            data, ms = data.split('.')
            ms = int(ms.ljust(6,'0')[:6]) 
        dt = datetime.strptime(data, ISO_FORMAT)
        dt = dt.replace(microsecond = ms)
        return dt


class BooleanIndexElement(KeyIndexElement):
    db_table = defaults.index_boolean_tab
    
    def _filter_key(self, data):
        data = data.strip()
        if data.lower() in _FALSE_VALUES:
            return False
        return bool(data)


class NoneTypeIndexElement(QualifierIndexElement):
    db_table = defaults.index_keyless_tab

type_classes = {TEXT_INDEX:TextIndexElement, 
                NUMERIC_INDEX:NumericIndexElement, 
                FLOAT_INDEX:FloatIndexElement, 
                DATETIME_INDEX:DateTimeIndexElement, 
                BOOLEAN_INDEX:BooleanIndexElement, 
                NONETYPE_INDEX:NoneTypeIndexElement
                }