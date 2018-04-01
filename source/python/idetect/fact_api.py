from sqlalchemy import Column, Integer, String, Date,  ForeignKey, text, column

from idetect.values import values
from idetect.model import Base, Analysis, Gkg, Fact, Location, analysis_fact, fact_location

class FactApi(Base):
    __tablename__ = 'idetect_fact_api'

    document_identifier = Column(String)
    source_common_name = Column(String)
    gdelt_day = Column(Date)
    fact = Column(Integer,
                  ForeignKey('idetect_facts.id'),
                  primary_key=True)
    unit = Column(String)
    term = Column(String)
    specific_reported_figure = Column(Integer)
    vague_reported_figure = Column(String)
    iso3 = Column(String)

    location = Column(Integer,
                      ForeignKey('idetect_locations.id'),
                      primary_key=True)

    gkg_id = Column(Integer,
                    ForeignKey('idetect_analyses.gkg_id'),
                    primary_key=True)
    category = Column(String)
    content_id = Column(Integer, ForeignKey('idetect_document_contents.id'))

def filter_by_locations(query, locations):
    loctuples = [(l,) for l in set(locations)]
    locs = values(
        [column('location_id', Integer)],
        *loctuples,
        alias_name='locs'
    )
    return query.filter(FactApi.location == locs.c.location_id)

def add_filters(query, fromdate=None, todate=None, locations=None,
           categories=None, units=None, sources=None,
           terms=None, iso3s=None, figures=None):
    if fromdate:
        query = query.filter(FactApi.gdelt_day >= fromdate)
    if todate:
        query = query.filter(FactApi.gdelt_day >= fromdate)
    if locations:
        query = filter_by_locations(query, locations)
    if categories:
        query = query.filter(FactApi.category.in_(categories))
    if units:
        query = query.filter(FactApi.unit.in_(units))
    if sources:
        query = query.filter(FactApi.source_common_name.in_(sources))
    if terms:
        query = query.filter(FactApi.term.in_(terms))
    if iso3s:
        query = query.filter(FactApi.iso3.in_(iso3s))
    if figures:
        query = query.filter(FactApi.specific_reported_figure.in_(figures))
    return query