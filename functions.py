#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 23 18:08:51 2019

@author: eric
"""


def get_full_team_names():
    full_names = {
        "Aachen": "Alemannia Aachen",
        "Augsburg": "FC Augsburg",
        "Bayern": "FC Bayern München",
        "Bielefeld": "Arminia Bielefeld",
        "Blau-Weiß 90 Ber.": "Blau-Weiß 90 Berlin",
        "Bochum": "VfL Bochum",
        "Braunschweig": "Eintracht Braunschweig",
        "Bremen": "SV Werder Bremen",
        "Cottbus": "Energie Cottbus",
        "Darmstadt": "SV Darmstadt 98",
        "Dortmund": "Borussia Dortmund",
        "Dresden": "Dynamo Dresden",
        "Duisburg": "MSV Duisburg",
        "Düsseldorf": "Fortuna Düsseldorf",
        "F. Köln": "Fortuna Köln",
        "Frankfurt": "Eintracht Frankfurt",
        "Freiburg": "SC Freiburg",
        "Fürth": "Greuther Fürth",
        "Gladbach": "Borussia Mönchengladbach",
        "HSV": "Hamburger SV",
        "Hannover": "Hannover 96",
        "Hertha": "Hertha BSC",
        "Hoffenheim": "1899 Hoffenheim",
        "Homburg": "FC Homburg",
        "Ingolstadt": "1. FC Ingolstadt",
        "K'lautern": "1. FC Kaiserslautern",
        "Karlsruhe": "Karlsruher SC",
        "Köln": "1. FC Köln",
        "Leipzig": "RB Leipzig",
        "Leverkusen": "Bayer 04 Leverkusen",
        "Mainz": "1. FSV Mainz 05",
        "Neunkirchen": "Borussia Neunkirchen",
        "Nürnberg": "1. FC Nürnberg",
        "Oberhausen": "Rot-Weiß Oberhausen",
        "Offenbach": "Offenbacher Kickers",
        "Paderborn": "SC Paderborn 07",
        "Essen": "Rot-Weiß Essen",
        "Rostock": "FC Hansa Rostock",
        "Saarbrücken": "1. FC Saarbrücken",
        "Schalke": "FC Schalke 04",
        "St. Pauli": "FC St. Pauli",
        "Stuttg. Kick.": "Stuttgarter Kickers",
        "Stuttgart": "VfB Stuttgart",
        "TSV 1860": "TSV 1860 München",
        "Tasmania": "Tasmania Berlin",
        "TeBe Berlin": "Tennis Borussia Berlin",
        "Uerdingen": "KFC Uerdingen",
        "Ulm": "SSV Ulm",
        "Unterhaching": "SpVgg Unterhaching",
        "SV Waldhof": "SV Waldhof Mannheim",
        "Wattenscheid": "SV Wattenscheid 09",
        "Wolfsburg": "VfL Wolfsburg",
    }

    return full_names


def correct_signs(s):
    s1 = s.replace("ä", "ae")
    s2 = s1.replace("ö", "oe")
    s3 = s2.replace("ü", "ue")
    s4 = s3.replace("ß", "ss")
    s5 = s4.replace("é", "e")

    return s5
