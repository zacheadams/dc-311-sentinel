#!/usr/bin/env python3
"""
Text normalization utilities for DC 311 Sentinel.
Cleans up redundant agency prefixes, parenthetical agency names, and implied DC
prefixes from service request titles, while preserving non-agency program identifiers
such as (ROSA).

Strict standards:
- Strictly zero emojis across code, logs, and outputs
- Zero third-party pip dependencies (standard library only)
"""

import re


def clean_service_desc(desc: str) -> str:
    """
    Normalizes a 311 service request description:
    - Removes agency prefixes with hyphens/colons: DMV, DOB, DOEE, DPW, FEMS, OCTFME, DFHV, DGS
    - Removes specific agency name prefixes: DC Water, DMOI, DC Health, DGS Grounds Landscaping
    - Removes redundant implied DC prefixes on facilities:
      'DC Dog Park Maintenance (DGS)' -> 'Dog Park Maintenance'
      'DC Indoor and Outdoor Pool Maintenance (DGS)' -> 'Indoor and Outdoor Pool Maintenance'
      'DC Spray Parks (DGS)' -> 'Spray Parks'
      'DC Government Information' -> 'Government Information'
      'DC How Am I Driving?' -> 'How Am I Driving?'
    - Removes parenthetical agency suffixes: (DGS), (DOH), (ServeDC)
    - Preserves non-agency program identifiers: (ROSA) is strictly kept intact
    - Simplifies redundant DC in taxi/property references: '(DC Taxi)' -> '(Taxi)'
    """
    if not desc:
        return desc
    s = desc.strip()
    s = re.sub(r"\s+", " ", s)

    # Agency prefixes with hyphen or colon
    s = re.sub(r"^(DMV|DOB|DOEE|DPW|FEMS|OCTFME|DFHV|DGS)\s*[-:]\s*", "", s, flags=re.IGNORECASE)

    # Agency name prefixes
    s = re.sub(r"^DC\s+Water\s*-\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"^DMOI\s+", "", s, flags=re.IGNORECASE)
    s = re.sub(r"^DC\s+Health\s+", "", s, flags=re.IGNORECASE)
    s = re.sub(r"^DGS\s+Grounds\s+Landscaping", "Grounds Landscaping", s, flags=re.IGNORECASE)

    # Redundant implied DC prefixes on facilities & general services
    s = re.sub(r"^DC\s+Government\s+Information", "Government Information", s, flags=re.IGNORECASE)
    s = re.sub(r"^DC\s+How\s+Am\s+I\s+Driving\??", "How Am I Driving?", s, flags=re.IGNORECASE)
    s = re.sub(r"^DC\s+(Dog\s+Park|Indoor\s+and\s+Outdoor\s+Pool|Spray\s+Parks)", r"\1", s, flags=re.IGNORECASE)

    # Parenthetical agency suffixes (ROSA is strictly excluded)
    s = re.sub(r"\s*\((DGS|DOH|ServeDC)\)", "", s, flags=re.IGNORECASE)

    # Clean redundant DC in Taxi claims and Gov Property
    s = re.sub(r"\(DC\s+Taxi\)", "(Taxi)", s, flags=re.IGNORECASE)
    s = re.sub(r"\bon\s+DC\s+Gov\s+Property\b", "on Government Property", s, flags=re.IGNORECASE)

    return s.strip()
