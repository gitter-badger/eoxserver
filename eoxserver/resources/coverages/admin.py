#-----------------------------------------------------------------------
# $Id$
#
# This software is named EOxServer, a server for Earth Observation data.
#
# Copyright (C) 2011 EOX IT Services GmbH
# Authors: Stephan Krause, Stephan Meissl
#
# This file is part of EOxServer <http://www.eoxserver.org>.
#
#    EOxServer is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published
#    by the Free Software Foundation, either version 3 of the License,
#    or (at your option) any later version.
#
#    EOxServer is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with EOxServer. If not, see <http://www.gnu.org/licenses/>.
#
#-----------------------------------------------------------------------

from django import forms
from django.contrib.gis import admin
from django.contrib.contenttypes import generic
from django.contrib import messages
from django.db import transaction
from django.conf import settings
from django.http import HttpResponseRedirect

from eoxserver.resources.coverages.models import *
from eoxserver.resources.coverages.synchronize import (
    RectifiedDatasetSeriesSynchronizer,
    RectifiedStitchedMosaicSynchronizer
)
from eoxserver.resources.coverages.metadata import MetadataInterfaceFactory
import os.path
import logging

# TODO: harmonize with core.system
logging.basicConfig(
    filename=os.path.join(settings.PROJECT_DIR, 'logs', 'eoxserver.log'),
    level=logging.DEBUG,
    format="[%(asctime)s][%(levelname)s] %(message)s"
)

# Grid
class AxisInline(admin.TabularInline):
    model = AxisRecord
    extra = 1
class RectifiedGridAdmin(admin.ModelAdmin):
    inlines = (AxisInline, )
admin.site.register(RectifiedGridRecord, RectifiedGridAdmin)

# NilValue
class NilValueInline(admin.TabularInline):
    model = ChannelRecord.nil_values.through
    extra = 1
class NilValueAdmin(admin.ModelAdmin):
    inlines = (NilValueInline, )
admin.site.register(NilValueRecord, NilValueAdmin)

# RangeType
class RangeType2ChannelInline(admin.TabularInline):
    model = RangeType2Channel
    extra = 1
class RangeTypeAdmin(admin.ModelAdmin):
    inlines = (RangeType2ChannelInline, )
class ChannelRecordAdmin(admin.ModelAdmin):
    inlines = (RangeType2ChannelInline, NilValueInline)
    exclude = ('nil_values', )
admin.site.register(RangeType, RangeTypeAdmin)
admin.site.register(ChannelRecord, ChannelRecordAdmin)
#admin.site.register(RangeType2Channel)

# SingleFile Coverage
class SingleFileLayerMetadataInline(admin.TabularInline):
    model = SingleFileCoverageRecord.layer_metadata.through
    extra = 1
class CoverageSingleFileAdmin(admin.ModelAdmin):
    #list_display = ('coverage_id', 'filename', 'range_type')
    #list_editable = ('filename', 'range_type')
    list_filter = ('range_type', )
    ordering = ('coverage_id', )
    search_fields = ('coverage_id', )
    inlines = (SingleFileLayerMetadataInline, )
    exclude = ('layer_metadata',)
admin.site.register(SingleFileCoverageRecord, CoverageSingleFileAdmin)

class StitchedMosaic2DatasetInline(admin.TabularInline):
    model = RectifiedStitchedMosaicRecord.rect_datasets.through
    verbose_name = "Stitched Mosaic to Dataset Relation"
    verbose_name_plural = "Stitched Mosaic to Dataset Relations"
    extra = 1
class DatasetSeries2DatasetInline(admin.TabularInline):
    model = RectifiedDatasetSeriesRecord.rect_datasets.through
    verbose_name = "Dataset Series to Dataset Relation"
    verbose_name_plural = "Dataset Series to Dataset Relations"
    extra = 1
class RectifiedDatasetAdmin(admin.ModelAdmin):
    list_display = ('coverage_id', 'eo_id', 'file', 'range_type', 'grid')
    list_editable = ('file', 'range_type', 'grid')
    list_filter = ('range_type', )
    ordering = ('coverage_id', )
    search_fields = ('coverage_id', )
    inlines = (StitchedMosaic2DatasetInline, DatasetSeries2DatasetInline)

    # We need to override the bulk delete function of the admin to make
    # sure the overrode delete() method of EOCoverageRecord is
    # called.
    actions = ['really_delete_selected', ]
    def get_actions(self, request):
        actions = super(RectifiedDatasetAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions
    def really_delete_selected(self, request, queryset):
        for obj in queryset:
            obj.delete()
        if queryset.count() == 1:
            message_bit = "1 Dataset was"
        else:
            message_bit = "%s Datasets were" % queryset.count()
        self.message_user(request, "%s successfully deleted." % message_bit)
    really_delete_selected.short_description = "Delete selected Dataset(s) entries"

admin.site.register(RectifiedDatasetRecord, RectifiedDatasetAdmin)

class MosaicDataDirInline(admin.TabularInline):
    model = MosaicDataDirRecord
    verbose_name = "Stitched Mosaic Data Directory"
    verbose_name_plural = "Stitched Mosaic Data Directories"
    extra = 1
class DatasetSeries2StichedMosaicInline(admin.TabularInline):
    model = RectifiedDatasetSeriesRecord.rect_stitched_mosaics.through
    verbose_name = "Dataset Series to Stitched Mosaic Relation"
    verbose_name_plural = "Dataset Series to Stitched Mosaic Relations"
    extra = 1
class RectifiedStitchedMosaicAdmin(admin.ModelAdmin):
    list_display = ('eo_id', 'eo_metadata', 'image_pattern')
    list_editable = ('eo_metadata', 'image_pattern')
    list_filter = ('image_pattern', )
    ordering = ('eo_id', )
    search_fields = ('eo_id', )
    filter_horizontal = ('rect_datasets', )
    inlines = (MosaicDataDirInline, DatasetSeries2StichedMosaicInline, )

    # We need to override the bulk delete function of the admin to make
    # sure the overrode delete() method of EOCoverageRecord is
    # called.
    actions = ['really_delete_selected', ]

    def get_actions(self, request):
        actions = super(RectifiedStitchedMosaicAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions

    def really_delete_selected(self, request, queryset):
        for obj in queryset:
            obj.delete()
        self.message_user(request, "%s StitchedMosaics were successfully deleted." % queryset.count())
    really_delete_selected.short_description = "Delete selected entries"

    def save_model(self, request, obj, form, change):
        self.mosaic = obj
        super(RectifiedStitchedMosaicAdmin, self).save_model(request, obj, form, change)
        
    def save_formset(self, request, form, formset, change):
        # the reason why the synchronization method is placed here
        # instead of the save_model() method is that this is the last step
        # in saving the data filled in in the admin view.
        # At the time the save_model() method is called, the data dir
        # is not yet saved and thus not available. We need the data dirs
        # however for synchronization.
        
        if formset.model == RectifiedDatasetRecord:
            changed_datasets = formset.save(commit=False)
            
            synchronizer = RectifiedStitchedMosaicSynchronizer(self.mosaic)
            
            try:
                if change:
                    synchronizer.update()
                else:
                    synchronizer.create()
            except:
                logging.error("Error when synchronizing.")
                #transaction.rollback()
                messages.error(request, "Error when synchronizing with file system.")
                #return
                raise
            
            for dataset in changed_datasets:
                if not dataset.automatic:
                    dataset.save()
        else:
            super(RectifiedStitchedMosaicAdmin, self).save_formset(request, form, formset, change)
        
    def add_view(self, request, form_url="", extra_context=None):
        try:
            return super(RectifiedStitchedMosaicAdmin, self).add_view(request, form_url, extra_context)
        except:
            messages.error(request, "Could not create StitchedMosaic")
            return HttpResponseRedirect("..")
    
    def change_view(self, request, object_id, extra_context=None):
        try:
            return super(RectifiedStitchedMosaicAdmin, self).change_view(request, object_id, extra_context)
        except:
            messages.error(request, "Could not change StitchedMosaic")
            return HttpResponseRedirect("..")
    
    def changelist_view(self, request, extra_context=None):
        try:
            return super(RectifiedStitchedMosaicAdmin, self).changelist_view(request, extra_context)
        except:
            messages.error(request, "Could not change StitchedMosaic")
            return HttpResponseRedirect("..")
    
    def delete_view(self, request, object_id, extra_context=None):
        try:
            return super(RectifiedStitchedMosaicAdmin, self).delete_view(request, object_id, extra_context)
        except:
            messages.error(request, "Could not delete StitchedMosaic")
            return HttpResponseRedirect("..")
            
admin.site.register(RectifiedStitchedMosaicRecord, RectifiedStitchedMosaicAdmin)

class DataDirInline(admin.TabularInline):
    model = DataDirRecord
    extra = 1
    
    def save_model(self, request, obj, form, change):
        raise # TODO
    
class RectifiedDatasetSeriesAdmin(admin.ModelAdmin):
    list_display = ('eo_id', 'eo_metadata', 'image_pattern')
    list_editable = ('eo_metadata', 'image_pattern')
    list_filter = ('image_pattern', )
    ordering = ('eo_id', )
    search_fields = ('eo_id', )
    inlines = (DataDirInline, )
    filter_horizontal = ('rect_stitched_mosaics', 'rect_datasets', )
    

    # We need to override the bulk delete function of the admin to make
    # sure the overrode delete() method of EOCoverageRecord is
    # called.
    actions = ['really_delete_selected', ]
    
    """
        TODO here
    """
    
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "rect_datasets":
            pass
            #raise
            #data_dirs = DataDirRecord.objects.get(dataset_series=
            #TODO: get all data dirs
            # exclude all datasets from the query that are included in the dir
            #kwargs["queryset"] = RectifiedDatasetRecord.objects.get(file__path__istartswith="")
        return super(RectifiedDatasetSeriesAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)
    
    def get_actions(self, request):
        actions = super(RectifiedDatasetSeriesAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions
        
    def really_delete_selected(self, request, queryset):
        for obj in queryset:
            obj.delete()
        self.message_user(request, "%s DatasetSeries were successfully deleted." % queryset.count())
    really_delete_selected.short_description = "Delete selected entries"
    
    def save_model(self, request, obj, form, change):
        self.dataset_series = obj
        error = False
        
        
        #TODO
        """for data_dir in obj.data_dirs.all():
            try:
                files = findFiles(data_dir.dir, obj.image_pattern)
            except OSError, e:
                messages.error(request, "%s: %s"%(e.strerror, e.filename))
                continue
            
            for dataset in obj.rect_datasets.all():
                if dataset.file.path in files:
                    messages.error(request, "The dataset with the id %s is already included in the data directory %s"%(dataset.eo_id, data_dir.dir))
                    error = True"""
        
        #raise
        
        if not error:
            super(RectifiedDatasetSeriesAdmin, self).save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        # the reason why the synchronization method is placed here
        # instead of the save_model() method is that this is the last step
        # in saving the data filled in in the admin view.
        # At the time the save_model() method is called, the data dir
        # is not yet saved and thus not available. We need the data dirs
        # however for synchronization.
        
        if formset.model == RectifiedDatasetRecord:
            changed_datasets = formset.save(commit=False)
            
            synchronizer = RectifiedDatasetSeriesSynchronizer(self.dataset_series)
            
            try:
                if change:
                    synchronizer.update()
                else:
                    synchronizer.create()
            except:
                logging.error("Error when synchronizing.")
                #transaction.rollback()
                messages.error(request, "Error when synchronizing with file system.")
                #return
                raise
            
            for dataset in changed_datasets:
                if not dataset.automatic:
                    dataset.save()
        else:
            super(RectifiedDatasetSeriesAdmin, self).save_formset(request, form, formset, change)
        
    def add_view(self, request, form_url="", extra_context=None):
        try:
            return super(RectifiedDatasetSeriesAdmin, self).add_view(request, form_url, extra_context)
        except:
            messages.error(request, "Could not create DatasetSeries")
            return HttpResponseRedirect("..")
    
    def change_view(self, request, object_id, extra_context=None):
        try:
            return super(RectifiedDatasetSeriesAdmin, self).change_view(request, object_id, extra_context)
        except:
            messages.error(request, "Could not change DatasetSeries")
            return HttpResponseRedirect("..")
    
    def changelist_view(self, request, extra_context=None):
        try:
            return super(RectifiedDatasetSeriesAdmin, self).changelist_view(request, extra_context)
        except:
            messages.error(request, "Could not change DatasetSeries")
            return HttpResponseRedirect("..")
    
    def delete_view(self, request, object_id, extra_context=None):
        try:
            return super(RectifiedDatasetSeriesAdmin, self).delete_view(request, object_id, extra_context)
        except:
            messages.error(request, "Could not delete DatasetSeries")
            return HttpResponseRedirect("..")

admin.site.register(RectifiedDatasetSeriesRecord, RectifiedDatasetSeriesAdmin)


class EOMetadataAdmin(admin.GeoModelAdmin):
    def save_model(self, request, obj, form, change):
        # steps:
        # 1. retrieve EO GML from obj
        # 2. validate against other input values (begin_time, end_time, footprint)
        # 3. validate against schema
        
        self.metadata_object = obj
        super(EOMetadataAdmin, self).save_model(request, obj, form, change)
        """
        if len(self.metadata_object.eo_gml) > 0:
            # not sure about this:
            # get right metadata interface
            # look for metadata given in gml
            # TODO currently error because no filename given 
            iu = EOxSMetadataInterfaceFactory.getMetadataInterface(None, "eogml") #we got no filename, do we?
            # TODO what if metadata is already set?
            self.metadata_object.footprint = interface.getFootprint()
        """
    
    def save_formset(self, request, form, formset, change):
        """raise
        if formset.model == EOMetadataRecord:
            changed_datasets = formset.save(commit=False)
            
            synchronizer = EOMetadataSynchronizer(self.metadata_object)
            
            try:
                if change:
                    synchronizer.update()
                else:
                    synchronizer.create()
            except:
                logging.error("Error when synchronizing.")
                #transaction.rollback()
                messages.error(request, "Error when synchronizing with file system.")
                #return
                raise
            
            for dataset in changed_datasets:
                if not dataset.automatic:
                    dataset.save()
        else:
            super(EOMetadataAdmin, self).save_formset(request, form, formset, change)
        """
        # SK: don't think we need to override this method, as it should
        # not be called; see also the explanation in the save_formset()
        # method of RectifiedStitchedMosaicAdmin,
        # RectifiedDatasetSeriesAdmin
        
        super(EOMetadataAdmin, self).save_formset(request, form, formset, change)
    
admin.site.register(EOMetadataRecord, EOMetadataAdmin)

class LayerMetadataAdmin(admin.ModelAdmin):
    inlines = (SingleFileLayerMetadataInline, )
admin.site.register(LayerMetadataRecord, LayerMetadataAdmin)

admin.site.register(FileRecord)
admin.site.register(LineageRecord)
