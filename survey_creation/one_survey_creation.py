#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Wrapper around survey_creation.py script to create only one survey file rather than separated ones as for 2016 and 2017 survey version
"""

__author__ = "Olivier Philippe"


import csv
from collections import OrderedDict


# # Here the list of the countries -- need to be put into a config file rather than hardcoded
# # TODO: config file!
dict_countries = {'de': "Germany",
                  'nl': "Netherlands",
                  'uk': "United Kingdom of Great Britain and Northern Ireland",
                  'us': "United States of America",
                  'zaf': "South Africa",
                  'nzl': "New Zealand",
                  'aus': "Australia",
                  'can': "Canada"}
list_bool = ['yes', 'y', 't', 'true']

filename = './2018/questions.csv'


class gettingQuestions:
    """
    This class parse the file `questions.csv` and create a dictionary with all the questions.
    It also parses all the specific countries folders and create a specific question for each of them when needed.
    """

    def __init__(self, *args, **kwargs):
        """
        """
        self.filename = filename
        self.dict_countries = dict_countries
        self.list_bool = list_bool
        # Dictionary containing the different questions
        self.dict_questions = OrderedDict()

    def read_original_file(self):
        """
        load the file into an OrderedDict with the code of the
        question as key and respecting the order of the question
        """
        with open(self.filename, "r") as f:
            csv_f = csv.DictReader(f)
            for row in csv_f:
                code = row['code']
                del row['code']
                self.dict_questions[code] = row

    def add_world_other(self):
        """
        Check question if it is country specific and one choice
        and if 'world' is also selected. In that case, add a new question
        using the same code and the same text but give a freetext and add the condition
        that should be NOT any country selected
        - create a new question with
            - code: '$code_world'
            - txt: '$txt_of_the_question' (just get the same text)
            - type: freetext
            - condition: (if not countries)
        """
        def check_world_free_txt(question):
            """
            Check if the question is  either one_choice or multiple_choice
            and its is selected as 'country_specific'
            and 'world' is selected then:
            :params:
                question dict(): the question to check
            :return:
                bool: True if match the condition, False if not
            """
            if question['country_specific'].lower() in self.list_bool:
                if question['world'].lower() in self.list_bool:
                    return True

        # recreate a new ordered dict
        new_dict = OrderedDict()
        # parse all the questions to find which one has to be created for world
        for k in self.dict_questions:
            # add the question to the new dict to respect the same order
            new_dict[k] = self.dict_questions[k]
            # check if the questions need to be created
            if check_world_free_txt(new_dict[k]):
                # Create the new question with freetext
                new_code = "{}_world".format(k)
                new_question = new_dict[k].copy()  # copy otherwise modify both dict
                new_question['answer_format'] = 'FREETEXT'
                new_question['answer_file'] = ''
                new_question['other'] = ''
                new_question['country_specific'] = ''
                # new_question['world'] = 'Y'
                for country in self.dict_countries:
                    new_question[country] = ''

                # remove the 'world' in the previous question to
                # ensure no confusion later in the add_condition_about_countries()
                new_dict[k]['world'] = ''
                # append it to the dictionary
                new_dict[new_code] = new_question

        # replace the current dictionary with the new one
        self.dict_questions = new_dict

    def add_condition_about_countries(self):
        """
        Append the existing condition with the conditions about the countries and replace
        that value in the dictionary.
        """
        def create_country_list(question):
            """
            Check which country is associated with the question and
            return a list containing all of them. In case of `country_specific` is
            selected, it will not add the country `world` as a new specific question
            is created within self.add_world_other()
            params:
                question dict(): containing all the params for the question
            return:
                cond_country_to_add list(): all countries that are associated with the question
            """
            list_countries_to_add = list()
            for country in self.dict_countries:
                if question[country].lower() in self.list_bool:
                    list_countries_to_add.append(country)
            if question['world'].lower() in self.list_bool and question['country_specific'].lower() not in self.list_bool:
                list_countries_to_add.append('world')
            return list_countries_to_add

        def create_country_condition(countries, operator, code_question_country="socio1"):
            """
            Create the country condition based on which country need to be include or exclude from a question
            Parse the list provided and output a formated string for each of them.
            :params:
                countries list() of str(): All countries that need to formatted in the condition.
                operator str(): the type of comparison needed for the condition
                code_question_country str(): the code of the question where the country is asked
            :return:
                formatted_condition str(): format the condition as:
                    (if $code_question_country $operator $country1) OR ((if $code_question_country $operator $country2)
            """
            list_str_countries = list()
            for country in countries:
                country_condition = "(if {} {} \"{}\")".format(code_question_country, operator, self.dict_countries[country])
                list_str_countries.append(country_condition)
            return '({})'.format(' OR '.join(list_str_countries))

        for k in self.dict_questions:
            condition = self.dict_questions[k]['condition']
            list_countries_to_add = create_country_list(self.dict_questions[k])

            # In case all the countries and the world option is present too, no need for conditions
            if len(list_countries_to_add) == len(self.dict_countries) +1:  # size of all potential country + 'world'
                final_condition = condition

            # In case world is not present, create an inclusive list of countries
            elif 'world' not in list_countries_to_add:
                condition_to_add = create_country_condition(list_countries_to_add, operator='==')
                if condition:
                    final_condition = "{} AND {}".format(condition, condition_to_add)
                else:
                    final_condition = condition_to_add

            # If there is less country but world is present need to apply exclusion
            elif len(list_countries_to_add) <= len(self.dict_countries) and 'world' in list_countries_to_add:
                # To get the exclusion list, need to invert the list and passing all countries that are NOT present
                # in that list.
                list_countries_to_exclude = [i for i in self.dict_countries.keys() if i not in list_countries_to_add]
                condition_to_add = create_country_condition(list_countries_to_exclude, operator='!=')

                if condition:
                    final_condition = "{} AND {}".format(condition, condition_to_add)
                else:
                    final_condition = condition_to_add
            self.dict_questions[k]['condition'] = final_condition


def main():
    getting_question = gettingQuestions()
    getting_question.read_original_file()
    getting_question.add_world_other()
    getting_question.add_condition_about_countries()


if __name__ == "__main__":
    main()