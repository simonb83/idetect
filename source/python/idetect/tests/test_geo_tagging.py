import os
from unittest import TestCase, mock

from sqlalchemy import create_engine

from idetect.model import Base, Session, Status, Document, Analysis, DocumentContent, DocumentType, Country, Location, LocationType, Fact
from idetect.load_data import load_countries
from idetect.fact_extractor import extract_facts
from idetect.geotagger import get_geo_info, process_locations, mapzen_coordinates, GeotagException


class TestGeoTagger(TestCase):
 
    def setUp(self):
        db_host = os.environ.get('DB_HOST')
        db_url = 'postgresql://{user}:{passwd}@{db_host}/{db}'.format(
            user='tester', passwd='tester', db_host=db_host, db='idetect_test')
        engine = create_engine(db_url)
        Session.configure(bind=engine)
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        self.session = Session()
        load_countries(self.session)

    def tearDown(self):
        self.session.rollback()

    def test_sets_no_results_flag(self):
        """Sets no-results flag if nothing found"""
        results = get_geo_info("xghijdshfkljdes")
        self.assertEqual(results['flag'], "no-results")

    def test_returns_detail_for_places(self):
        """Returns sufficient level of detail for results"""
        results = get_geo_info("Paris")
        self.assertNotEqual(results['country_code'], '')
        self.assertNotEqual(results['coordinates'], '')
        self.assertNotEqual(results['type'], '')

    def test_accuracy(self):
        """Returns sufficient level of detail for results"""
        results = get_geo_info("Beijing")
        self.assertEqual(results['country_code'], 'CHN')
        self.assertEqual(results['coordinates'],
                         "39.937967,116.417592")

    def test_location_types(self):
        """Corectly distinguishes between Countries, Cities and Subdivisions"""
        results = get_geo_info("London")
        self.assertEqual(results['type'], LocationType.CITY)
        results = get_geo_info("India")
        self.assertEqual(results['type'], LocationType.COUNTRY)
        results = get_geo_info("Alaska")
        self.assertEqual(results['type'], LocationType.SUBDIVISION)

    # DONT RUN geotagging if detail already exists
    @mock.patch('idetect.geotagger.mapzen_coordinates')
    def dont_geotag_if_detail_exists(self, mapzen):
        document = Document(type=DocumentType.WEB,
                            name="Hurricane Katrina Fast Facts")
        analysis = Analysis(document=document, status=Status.NEW)
        self.session.add(analysis)
        content = DocumentContent(
            content_clean="It was early Saturday when a flash flood hit large parts of India and Pakistan and washed away more than 500 houses")
        self.session.add(content)
        self.session.commit()
        analysis.content_id = content.id
        self.session.commit()
        fact = Fact(unit='person', term='displaced')
        self.session.add(fact)
        self.session.commit()
        loc1 = self.session.query(Location).filter(Location.location_name == 'India').one_or_none()
        fact.locations.append(loc1)
        analysis.facts.append(fact)
        self.session.commit()
        process_locations(analysis)
        assert not mapzen.called


    def test_create_duplicate_fact(self):
        """Creates duplicate fact if locations from multiple countries exist"""
        document = Document(type=DocumentType.WEB,
                            name="Hurricane Katrina Fast Facts")
        analysis = Analysis(document=document, status=Status.NEW)
        self.session.add(analysis)
        self.session.commit()
        fact = Fact(unit='person', term='displaced')
        self.session.add(fact)
        self.session.commit()
        loc1 = self.session.query(Location).filter(Location.location_name == 'India').one_or_none()
        loc2 = self.session.query(Location).filter(Location.location_name == 'Pakistan').one_or_none()
        fact.locations.append(loc1)
        fact.locations.append(loc2)
        analysis.facts.append(fact)
        self.session.commit()
        self.assertEqual(1, len(analysis.facts))
        process_locations(analysis)
        self.assertEqual(2, len(analysis.facts))
        fact_countries = [f.iso3 for f in analysis.facts]
        self.assertIn('IND', fact_countries)
        self.assertIn('PAK', fact_countries)
        self.assertEqual(1, len(analysis.facts[0].locations))
        self.assertEqual(1, len(analysis.facts[1].locations))


    @mock.patch('idetect.geotagger.mapzen_coordinates')
    def test_fail_if_geotagging_fails(self, mapzen):
        """Location processing should fail if geotagging fails"""
        mapzen.side_effect = GeotagException()
        document = Document(type=DocumentType.WEB,
                            name="Hurricane Katrina Fast Facts")
        analysis = Analysis(document=document, status=Status.NEW)
        self.session.add(analysis)
        self.session.commit()
        fact = Fact(unit='person', term='displaced')
        self.session.add(fact)
        self.session.commit()
        loc1 = Location(location_name="Ruislip")
        fact.locations.append(loc1)
        analysis.facts.append(fact)
        self.session.commit()
        with self.assertRaises(GeotagException):
            process_locations(analysis)


