import os
from unittest import TestCase

from sqlalchemy import create_engine

from idetect.model import Base, Session, Status, Gkg, Analysis, DocumentContent, Country, Location, \
    FactTerm, FactKeyword
from idetect.fact_extractor import extract_facts, process_location
from idetect.load_data import load_countries, load_terms


class TestFactExtractor(TestCase):

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
        load_terms(self.session)

    def tearDown(self):
        self.session.rollback()
        for article in self.session.query(Gkg).all():
            self.session.delete(article)
        self.session.commit()

    def test_extract_facts_simple(self):
        """Extracts simple facts when present and saves to DB"""
        gkg = Gkg()
        analysis = Analysis(gkg=gkg, status=Status.NEW)
        self.session.add(analysis)
        content = DocumentContent(
            content_clean="It was early Saturday when a flash flood hit the area and washed away more than 500 houses")
        self.session.add(content)
        self.session.commit()
        analysis.content_id = content.id
        self.session.commit()
        extract_facts(analysis)
        self.assertEqual(1, len(analysis.facts))


    def test_extract_refugee_facts(self):
        """Extracts refugee-related facts with Refugee Term"""
        gkg = Gkg()
        analysis = Analysis(gkg=gkg, status=Status.NEW)
        self.session.add(analysis)
        content = DocumentContent(
            content_clean="It was early Saturday when government troops entered the area and forced more than 20000 refugees to flee.")
        self.session.add(content)
        self.session.commit()
        analysis.content_id = content.id
        self.session.commit()
        extract_facts(analysis)
        self.assertEqual(FactTerm.REFUGEE, analysis.facts[0].term)

    def test_extract_evicted_facts(self):
        """Extracts eviction-related facts with eviction Term"""
        gkg = Gkg()
        analysis = Analysis(gkg=gkg, status=Status.NEW)
        self.session.add(analysis)
        content = DocumentContent(
            content_clean="2000 people have been evicted from their homes in Bosnia")
        self.session.add(content)
        self.session.commit()
        analysis.content_id = content.id
        self.session.commit()
        extract_facts(analysis)
        self.assertEqual(FactTerm.EVICTED, analysis.facts[0].term)

    def test_extract_eviction_facts(self):
        """Extracts eviction-related facts with eviction Term"""
        gkg = Gkg()
        analysis = Analysis(gkg=gkg, status=Status.NEW)
        self.session.add(analysis)
        content = DocumentContent(
            content_clean="ordered eviction for 2000 people from their homes in Bosnia")
        self.session.add(content)
        self.session.commit()
        analysis.content_id = content.id
        self.session.commit()
        extract_facts(analysis)
        self.assertEqual(FactTerm.EVICTED, analysis.facts[0].term)
    
    def test_extract_forced_eviction_facts(self):
        """Extracts eviction-related facts with eviction Term"""
        gkg = Gkg()
        analysis = Analysis(gkg=gkg, status=Status.NEW)
        self.session.add(analysis)
        content = DocumentContent(
            content_clean="ordered forced eviction for 2000 people from their homes in Bosnia")
        self.session.add(content)
        self.session.commit()
        analysis.content_id = content.id
        self.session.commit()
        extract_facts(analysis)
        self.assertEqual(FactTerm.EVICTED, analysis.facts[0].term)

    def test_extract_forcibly_evicted_facts(self):
        """Extracts eviction-related facts with eviction Term"""
        gkg = Gkg()
        analysis = Analysis(gkg=gkg, status=Status.NEW)
        self.session.add(analysis)
        content = DocumentContent(
            content_clean="2000 people were forcibly evicted from their homes in Bosnia")
        self.session.add(content)
        self.session.commit()
        analysis.content_id = content.id
        self.session.commit()
        extract_facts(analysis)
        self.assertEqual(FactTerm.EVICTED, analysis.facts[0].term)

    def test_extract_sacked_facts(self):
        """Extracts sacked-related facts with eviction Term"""
        gkg = Gkg()
        analysis = Analysis(gkg=gkg, status=Status.NEW)
        self.session.add(analysis)
        content = DocumentContent(
            content_clean="last week 2000 people have been sacked from their homes in Nigeria")
        self.session.add(content)
        self.session.commit()
        analysis.content_id = content.id
        self.session.commit()
        extract_facts(analysis)
        self.assertEqual(FactTerm.SACKED, analysis.facts[0].term)

    def test_create_locations_with_names(self):
        """Creates locations for facts only with location names"""
        gkg = Gkg()
        analysis = Analysis(gkg=gkg, status=Status.NEW)
        self.session.add(analysis)
        content = DocumentContent(
            content_clean="It was early Saturday when a flash flood hit large parts of London and Middlesex and washed away more than 500 houses")
        self.session.add(content)
        self.session.commit()
        analysis.content_id = content.id
        self.session.commit()
        extract_facts(analysis)
        facts = analysis.facts
        self.assertEqual(1, len(facts))
        fact = facts[0]
        self.assertEqual(2, len(fact.locations))
        loc_names = [loc.location_name for loc in fact.locations]
        self.assertIn('London', loc_names)
        self.assertIn('Middlesex', loc_names)
        self.assertEqual([None, None], [loc.country for loc in fact.locations])


    def test_use_existing_location(self):
        """Uses existing locations when they exist"""
        gkg = Gkg()
        analysis = Analysis(gkg=gkg, status=Status.NEW)
        self.session.add(analysis)
        content = DocumentContent(
            content_clean="It was early Saturday when a flash flood hit large parts of Bosnia and washed away more than 500 houses")
        self.session.add(content)
        location = Location(location_name='Bosnia')
        self.session.add(location)
        self.session.commit()
        analysis.content_id = content.id
        self.session.commit()
        extract_facts(analysis)
        fact = analysis.facts[0]
        extracted_location = fact.locations[0]
        self.assertEqual(location.id, extracted_location.id)

