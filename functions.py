#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 23 18:08:51 2019

@author: eric
"""


def get_full_team_names():
    full_names = {
        "Bayern": "FC Bayern München",
        "Bremen": "SV Werder Bremen",
        "HSV": "Hamburger SV",
        "Dortmund": "Borussia Dortmund",
        "Stuttgart": "VfB Stuttgart",
        "Gladbach": "Borussia Mönchengladbach",
        "Schalke": "FC Schalke 04",
        "Köln": "1. FC Köln",
        "Frankfurt": "Eintracht Frankfurt",
        "Leverkusen": "Bayer 04 Leverkusen",
        "K'lautern": "1. FC Kaiserslautern",
        "Hertha": "Hertha BSC",
        "Bochum": "VfL Bochum",
        "Nürnberg": "1. FC Nürnberg",
        "Hannover": "Hannover 96",
        "Duisburg": "MSV Duisburg",
        "Wolfsburg": "VfL Wolfsburg",
        "Düsseldorf": "Fortuna Düsseldorf",
        "Karlsruhe": "Karlsruher SC",
        "Braunschweig": "Eintracht Braunschweig",
        "TSV 1860": "TSV 1860 München",
        "Freiburg": "SC Freiburg",
        "Bielefeld": "Arminia Bielefeld",
        "Uerdingen": "KFC Uerdingen",
        "Mainz": "1. FSV Mainz 05",
        "Hoffenheim": "1899 Hoffenheim",
        "Rostock": "FC Hansa Rostock",
        "Augsburg": "FC Augsburg",
        "Waldhof Mannheim": "SV Waldhof Mannheim",
        "Offenbach": "Offenbacher Kickers",
        "RW Essen": "Rot-Weiß Essen",
        "St. Pauli": "FC St. Pauli",
        "Cottbus": "Energie Cottbus",
        "Aachen": "Alemannia Aachen",
        "Leipzig": "RB Leipzig",
        "Oberhausen": "Rot-Weiß Oberhausen",
        "Saarbrücken": "1. FC Saarbrücken",
        "Darmstadt": "SV Darmstadt 98",
        "Wattenscheid": "SV Wattenscheid 09",
        "Dresden": "Dynamo Dresden",
        "Homburg": "FC Homburg",
        "Unterhaching": "SpVgg Unterhaching",
        "Ingolstadt": "1. FC Ingolstadt",
        "Neunkirchen": "Borussia Neunkirchen",
        "TeBe Berlin": "Tennis Borussia Berlin",
        "Stuttg. Kick.": "Stuttgarter Kickers",
        "Ulm": "SSV Ulm",
        "F. Köln": "Fortuna Köln",
        "Paderborn": "SC Paderborn 07",
        "Fürth": "Greuther Fürth",
        "Blau-Weiß 90 Ber.": "Blau-Weiß 90 Berlin",
        "Tasmania": "Tasmania Berlin",
    }

    return full_names


def correct_signs(s):
    s1 = s.replace('ä', 'ae')
    s2 = s1.replace('ö', 'oe')
    s3 = s2.replace('ü', 'ue')
    s4 = s3.replace('ß', 'ss')
    s5 = s4.replace('é', 'e')

    return s4
