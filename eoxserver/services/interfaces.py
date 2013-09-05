#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2011 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#-------------------------------------------------------------------------------


class OWSServiceHandlerInterface(object):
    """ Interface for OWS Service handlers.
    """

    @property
    def service(self):
        """ The name of the supported service in uppercase letters.
        """

    @property
    def versions(self):
        """ An iterable of all supported versions as strings.
        """

    @property
    def request(self):
        """ The supported request method.
        """

    def handle(self, request):
        """ The main handling method. Takes a `django.http.Request` object as 
            single parameter.
        """


class OWSExceptionHandlerInterface(object): 
    """ Interface for OWS exception handlers.
    """

    @property
    def service(self):
        """ The name of the supported service in uppercase letters.
        """

    @property
    def versions(self):
        """ An iterable of all supported versions as strings.
        """

    @property
    def request(self):
        """ The supported request method.
        """

    def handle_exception(self, request, exception):
        """ The main exception handling method. Parameters are an object of the 
            `django.http.Request` type and the raised exception.
        """


class OWSGetServiceHandlerInterface(OWSServiceHandlerInterface):
    """ Interface for service handlers that support HTTP GET requests.
    """


class OWSPostServiceHandlerInterface(OWSServiceHandlerInterface):
    """ Interface for service handlers that support HTTP POST requests.
    """


class CoverageRendererInterface(object):
    """ Interface for coverage renderers.
    """

    def render(self, coverage, **kwargs):
        """ Render the coverage with the given parameters.
        """

    @property
    def handles(self):
        """ Returns an iterable of all coverage classes that this renderer is 
            able to render.
        """


class OutputFormatInterface(object):
    pass


class MapServerConnectorInterface(object):
    """ Interface for connectors between `mapscript.layerObj` and associated 
        data.
    """

    def supports(self, data_items):
        """ Returns `True` if the given `data_items` are supported and 
            `False` if not.
        """
    
    def connect(self, coverage, data_items, layer, cache):
        """ Connect a layer (a `mapscript.layerObj`) with the given data 
            items and coverage (a list of two-tuples: location and semantic).
        """

    def disconnect(self, coverage, data_items, layer, cache):
        """ Performs all necessary cleanup operations.
        """


class MapServerLayerFactoryInterface(object):
    """ Interface for factories that create `mapscript.layerObj` objects for 
        coverages.
    """

    @property
    def handles(self):
        """ Iterable of all object types that are supported by this connector.
        """

    @property
    def suffix(self):
        """ The suffix associated with layers this factory produces. This is 
            used for "specialized" layers such as "bands" or "outlines" layers.
            For factories that don't use this feature, it can be left out.
        """

    def generate(self, eo_object):
        """ Returns a `mapscript.layerObj` preconfigured for the given EO 
            object.
        """
