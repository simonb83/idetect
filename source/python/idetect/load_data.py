import csv

from idetect.model import Country, CountryTerm, Location, LocationType, KeywordType, FactKeyword


def load_countries(session):
    if len(session.query(Country).all()) == 0:
        with open('/home/idetect/data/all_countries.csv', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                country = Country(iso3=row['code_3'],
                                  preferred_term=row['country_name'])
                session.add(country)
                session.commit()

                country_name = CountryTerm(
                    term=row['country_name'], country=row['code_3'])
                session.add(country_name)

                if len(row['common_name']) > 0:
                    common_name = CountryTerm(
                        term=row['common_name'], country=row['code_3'])
                    session.add(common_name)

                if len(row['official_name']) > 0:
                    official_name = CountryTerm(
                        term=row['official_name'], country=row['code_3'])
                    session.add(official_name)

                location = Location(location_name=row['country_name'], location_type=LocationType.COUNTRY,
                                    latlong=row['latlong'], country_iso3=row['code_3'])
                session.add(location)
                session.commit()


def load_terms(session):
    # Load terms used for report extraction
    person_reporting_terms = [
        'displaced', 'evacuated', 'forced', 'flee', 'homeless', 'relief camp',
        'sheltered', 'relocated', 'stranded', 'stuck', 'accommodated', 'refugee camp',
        'refugee center','evicted','eviction','sacked']

    structure_reporting_terms = [
        'destroyed', 'damaged', 'swept', 'collapsed',
        'flooded', 'washed', 'inundated', 'evacuate'
    ]

    person_reporting_units = ["families", "person", "people", "individuals", "locals",
                              "villagers", "residents",
                              "occupants", "citizens", "households", "refugee", "asylum seeker"]

    structure_reporting_units = [
        "home", "house", "hut", "dwelling", "building"]

    relevant_article_terms = ['Rainstorm', 'hurricane',
                              'tornado', 'rain', 'storm', 'earthquake']

    for term_list, keyword_type in zip([person_reporting_terms, structure_reporting_terms,
                                        person_reporting_units, structure_reporting_units, relevant_article_terms],
                                       [KeywordType.PERSON_TERM, KeywordType.STRUCTURE_TERM, KeywordType.PERSON_UNIT,
                                        KeywordType.STRUCTURE_UNIT, KeywordType.ARTICLE_KEYWORD]):
        for term in term_list:
            report_kw = FactKeyword(description=term, keyword_type=keyword_type)
            session.add(report_kw)
            session.commit()
