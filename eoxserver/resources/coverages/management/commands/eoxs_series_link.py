#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2014 EOX IT Services GmbH
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

import traceback
from optparse import make_option

from django.core.exceptions import ValidationError
from django.core.management.base import CommandError, BaseCommand
from django.utils.dateparse import parse_datetime
from django.db import transaction
from django.contrib.gis.geos import GEOSGeometry

from eoxserver.resources.coverages.management.commands import (
    CommandOutputMixIn, _variable_args_cb
)

#from eoxserver.resources.coverages import models
from eoxserver.resources.coverages.models import DatasetSeries
from eoxserver.resources.coverages.models import EOObject
from eoxserver.resources.coverages.models import EO_OBJECT_TYPE_REGISTRY 


class Command(CommandOutputMixIn, BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option("-s", "--series", dest="parents",
            action='callback', callback=_variable_args_cb,
            default=None, help=("List of the target dataset series.")
        ), 
        make_option("-a", "--add", dest="children",
            action='callback', callback=_variable_args_cb,
            default=None, help=("List of the inserted child eo-objects.")
        ), 
        make_option('--ignore-missing-parent',
            dest='ignore_missing_parent',
            action="store_true", default=False,
            help=("Optional. Proceed even if the linked parent "
                  "does not exist. By defualt, a missing parent " 
                  "will terminate the command.")
        ),
        make_option('--ignore-missing-child',
            dest='ignore_missing_child',
            action="store_true", default=False,
            help=("Optional. Proceed even if the linked child "
                  "does not exist. By defualt, a missing child " 
                  "will terminate the command.")
        ),
    )

    args = (
        "--series <series-id> [<series-id> ...] --add <eo-object-id> "
        "[<eo-object-id> ...] [--ignore-missing-parent] "
        "[--ignore-missing-child]"
    )
    
    help = (
    """
        Link (insert) one or more EOObjects into one or more dataset series. 

        NOTE: Pre-existing links are ignored.
    """ % ({"name": __name__.split(".")[-1]}))

    @transaction.commit_on_success
    def handle(self, *args, **opt):
        # check the required inputs
        parent_ids = opt.get('parents', None)
        children_ids = opt.get('children', None)
        if not parent_ids: 
            raise CommandError(
                "Missing the mandatory dataset series identifier(s)!"
            )

        if not children: 
            raise CommandError(
                "Missing the mandatory inserted EOObjects identifier(s)!"
            )

        # extract the parents 
        ignore_missing_parent = opt['ignore_missing_parent']
        parents = [] 
        for parent_id in parent_ids: 
            try: 
                parents.append(DatasetSeries.objects.get(identifier=parent_id))
            except DatasetSeries.DoesNotExist: 
                msg = (
                    "There is no Dataset Series matching the given "
                    "identifier: '%s'" % parent_id
                )
                if ignore_missing_parent: 
                    self.print_wrn(msg)
                else: 
                    raise CommandError(msg) 

        # extract the children  
        ignore_missing_child = opt['ignore_missing_child']
        children = [] 
        for child_id in children_ids: 
            try:
                children.append(EOObject.objects.get(identifier=child_id))
            except EOObject.DoesNotExist:
                msg = (
                    "There is no EOObject matching the given identifier: '%s'"
                    % child_id
                )
                if ignore_missing_child:
                    self.print_wrn(msg)
                else:
                    raise CommandError(msg)
        
        try:
            for parent in parents: 
                for child in children:
                    # check whether the link does not exist
                    if child not in parent:
                        self.print_msg(
                            "Unlinking: %s <-x- %s" % (parent, child)
                        )
                        parent.insert(child)

                    else:
                        self.print_wrn(
                            "Collection %s already contains %s" 
                            % (parent, child)
                        )


        except Exception as e:
            # print stack trace if required 
            if opt.get("traceback", False):
                self.print_msg(traceback.format_exc())
            
            raise CommandError("Linking failed! REASON=%s" % (e))
