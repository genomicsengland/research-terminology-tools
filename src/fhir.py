import requests
import urllib3
from typing import List, Iterator
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


#
# Convenience wrapper for accessing a FHIR Parameters resource (https://www.hl7.org/fhir/parameters.html)
#
class Parameters:

    def __init__(self, parameters: List[dict]):
        self.__parameters = parameters

    def __get_values_for_name(self, name, value_key) -> Iterator:
        return (param.get(value_key) for param in self.__parameters if param.get("name") == name)

    def get_boolean(self, name) -> bool:
        return next(self.get_booleans(name))

    def get_booleans(self, name) -> Iterator[bool]:
        return self.__get_values_for_name(name, 'valueBoolean')

    def get_string(self, name) -> str:
        return next(self.get_strings(name))

    def get_strings(self, name) -> Iterator[str]:
        return self.__get_values_for_name(name, 'valueString')

    def get_coding(self, name) -> dict:
        return next(self.get_codings(name))

    def get_codings(self, name) -> Iterator[dict]:
        return self.__get_values_for_name(name, 'valueCoding')

    # the value of a "multi-part" parameter is a new Parameters instance
    def get_part(self, name) -> 'Parameters':
        return next(self.get_parts(name))

    def get_parts(self, name) -> Iterator['Parameters']:
        return (Parameters(params) for params in self.__get_values_for_name(name, 'part'))


#
# FHIR API client implementation of:
# CodeSystem/$validate-code
# ConceptMap/$translate
#
class FHIRClient:

    def __init__(self, url, verify_ssl: bool):
        self.__url = url
        self.__verify_ssl = verify_ssl
        self.__session = requests.Session()

    def __get(self, path, params):
        response = self.__session.get(self.__url + path, params=params, verify=self.__verify_ssl)
        response.raise_for_status()
        return response.json()

    def code_system_validate_code(self, system, version, code) -> Parameters:
        in_params = {
            "url": system,
            "version": version,
            "code": code
        }
        response = self.__get('CodeSystem/$validate-code', in_params)
        return Parameters(response.get("parameter"))

    def concept_map_translate(self, url, system, code, target, reverse) -> Parameters:
        in_params = {
            "url": url,
            "system": system,
            "code": code,
            "target": target,
            "reverse": 'true' if reverse else None
        }
        response = self.__get('ConceptMap/$translate', in_params)
        return Parameters(response.get("parameter"))
