# -*- coding: utf-8 -*-
"""
Functions to delineate catchments.
"""
from gistools.network import find_upstream_rec
from gistools.vector import closest_line_to_pts
from gistools.util import load_geo_data

###############################################
### Catch del using the REC


def extract_rec_catch(reaches, rec_catch_shp):
    """
    Function to extract the catchment polygons from the rec catchments layer. Appends to reaches layer.

    Parameters
    ----------
    reaches : DataFrame
        The output DataFrame from the find_upstream_rec function.
    rec_catch_shp : str path, dict, or GeoDataFrame
        str path to the REC catchment shapefile, dict of pdsql.mssql.rd_sql parameters, or the equivelant GeoDataFrame.

    Returns
    -------
    GeoDataFrame
    """

    ### Parameters
#    server = 'SQL2012PROD05'
#    db = 'GIS'
#    table = 'MFE_NZTM_RECWATERSHEDCANTERBURY'
#    cols = ['NZREACH']
#
    sites = reaches.NZREACH.unique().astype('int32').tolist()
#
#    ### Extract reaches from SQL
#    catch1 = rd_sql(server, db, table, cols, where_col='NZREACH', where_val=sites, geo_col=True)
#    catch2 = catch1.dissolve('NZREACH')
    catch0 = load_geo_data(rec_catch_shp)

    catch1 = catch0[catch0.NZREACH.isin(sites)]
    catch2 = catch1.dissolve('NZREACH').reset_index()[['NZREACH', 'geometry']]

    ### Combine with original sites
    catch3 = catch2.merge(reaches.reset_index(), on='NZREACH')
    catch3.crs = catch0.crs

    return catch3


def agg_rec_catch(rec_catch):
    """
    Simple function to aggregate rec catchments.

    Parameters
    ----------
    rec_catch : GeoDataFrame
        The output from extract_rec_catch

    Returns
    -------
    GeoDataFrame
    """
    rec_shed = rec_catch[['start', 'geometry']].dissolve('start')
    rec_shed.index = rec_shed.index.astype('int32')
    rec_shed['area'] = rec_shed.area
    rec_shed.crs = rec_catch.crs
    return rec_shed.reset_index()


def rec_catch_del(sites_shp, rec_streams_shp, rec_catch_shp, sites_col='site', buffer_dis=400, catch_output=None):
    """
    Catchment delineation using the REC streams and catchments.

    Parameters
    ----------
    sites_shp : str path or GeoDataFrame
        Points shapfile of the sites along the streams or the equivelant GeoDataFrame.
    rec_streams_shp : str path, GeoDataFrame, or dict
        str path to the REC streams shapefile, the equivelant GeoDataFrame, or a dict of parameters to read in an mssql table using the rd_sql function.
    rec_catch_shp : str path, GeoDataFrame, or dict
        str path to the REC catchment shapefile, the equivelant GeoDataFrame, or a dict of parameters to read in an mssql table using the rd_sql function.
    sites_col : str
        The column name of the site numbers in the sites_shp.
    catch_output : str or None
        The output polygon shapefile path of the catchment delineation.

    Returns
    -------
    GeoDataFrame
        Polygons
    """

    ### Parameters


    ### Modifications {NZREACH: {NZTNODE/NZFNODE: node # to change}}
    mods = {13053151: {'NZTNODE': 13055874}, 13048353: {'NZTNODE': 13048851}, 13048498: {'NZTNODE': 13048851}}

    ### Load data
    rec_catch = load_geo_data(rec_catch_shp)
    rec_streams = load_geo_data(rec_streams_shp)
    pts = load_geo_data(sites_shp)

    ### make mods
    for i in mods:
        rec_streams.loc[rec_streams['NZREACH'] == i, mods[i].keys()] = mods[i].values()

    ### Find closest REC segment to points
    pts_seg = closest_line_to_pts(pts, rec_streams, line_site_col='NZREACH', buffer_dis=buffer_dis)
    nzreach = pts_seg.copy().NZREACH.unique()

    ### Find all upstream reaches
    reaches = find_upstream_rec(nzreach, rec_streams_shp=rec_streams)

    ### Extract associated catchments
    rec_catch = extract_rec_catch(reaches, rec_catch_shp=rec_catch)

    ### Aggregate individual catchments
    rec_shed = agg_rec_catch(rec_catch)
    rec_shed.columns = ['NZREACH', 'geometry', 'area']
    rec_shed1 = rec_shed.merge(pts_seg.drop('geometry', axis=1), on='NZREACH')

    ### Export and return
    if catch_output is not None:
        rec_shed1.to_file(catch_output)
    return rec_shed1










