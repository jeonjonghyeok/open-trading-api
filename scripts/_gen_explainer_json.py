#!/usr/bin/env python3
"""Emit scripts/explainer_content.json (ASCII-only source; UTF-8 output)."""

from __future__ import annotations

import codecs
import json
from pathlib import Path


def U(s: str) -> str:
    return codecs.decode(s, "unicode_escape")


def main() -> None:
    data = {
        "meta_title": U(
            "\\u0041\\u0049 \\uc8fc\\uc2dd \\ud2b8\\ub808\\uc774\\ub529 \\u2014 "
            "\\uc27d\\uac8c \\uc77d\\ub294 \\uc548\\ub0b4"
        ),
        "kicker": U(
            "\\uac00\\uc0c1 \\uc5f0\\uc2b5\\uc7a5(\\ubaa8\\uc758\\ud22c\\uc790) \\uc774\\uc57c\\uae30"
        ),
        "hero_title_line1": U("\\ub3c8\\uc774 \\uc6c0\\uc9c1\\uc774\\ub294 \\uc790\\ub9ac,"),
        "hero_title_line2": U("\\uc5b4\\ub5bb\\uac8c \\ub3cc\\uc544\\uac00\\ub098\\uc694?"),
        "hero_deck": U(
            "\\uc774 \\ud398\\uc774\\uc9c0\\ub294 <strong>\\uc6a9\\uc5b4\\ub97c \\ubaa8\\ub974\\ub294 "
            "\\ubd84</strong>\\ub3c4 \\ud558\\ub8e8\\uc758 \\ud750\\ub984\\uc774 \\uba38\\ub9bf\\uc18d\\uc5d0 "
            "\\uadf8\\ub9bc\\ucc98\\ub7fc \\ub0a8\\ub3c4\\ub85d \\uc37c\\uc2b5\\ub2c8\\ub2e4. "
            "\\uc790\\ub3d9\\ud654\\ub294 \\uc0ac\\ub78c\\uc744 \\ub300\\uc2e0\\ud558\\ub294 "
            "<strong>\\ud310\\uc0ac</strong>\\uac00 \\uc544\\ub2c8\\ub77c, \\uaddc\\uce59\\uc744 "
            "\\uc9c0\\ud0a4\\uac8c \\ud574 \\uc8fc\\ub294 <strong>\\ube44\\uc11c</strong>\\uc5d0 "
            "\\uac00\\uae4b\\uc2b5\\ub2c8\\ub2e4. <strong>Claude Code</strong>\\ub294 "
            "\\uc124\\uacc4\\xb7\\uc810\\uac80\\xb7\\uae30\\ub85d\\uc744 \\ub3cc\\ub294 "
            "<strong>\\uc870\\uc218</strong>\\uc785\\ub2c8\\ub2e4."
        ),
        "sec_what_h2": U("\\ud55c \\uc904\\ub85c \\ub9d0\\ud558\\uba74"),
        "sec_what_lead": U(
            "\\ud55c\\uad6d\\ud22c\\uc790\\uc99d\\uad8c <strong>\\ubaa8\\uc758\\ud22c\\uc790 "
            "\\uacc4\\uc88c</strong>\\uc5d0\\uc11c, \\uc815\\ud574\\uc9c4 \\uc2dc\\uac04\\uc5d0 "
            "\\uc2dc\\uc138\\ub97c \\ubaa8\\uc73c\\uace0 \\uc870\\uac74\\uc744 \\ud655\\uc778\\ud558\\uace0, "
            "\\uae30\\ub85d\\uae4c\\uc9c0 \\ubb36\\uc5b4 \\ub461\\ub2c8\\ub2e4."
        ),
        "sec_what_p1": U(
            "\\uc774\\uacf3\\uc740 \\uc2e4\\uc81c \\ub3c8\\uc774 \\uc624\\uac00\\ub294 \\uc2e4\\uc804\\uc774 "
            "\\uc544\\ub2c8\\ub77c <strong>\\uc5f0\\uc2b5\\uc7a5</strong>\\uc785\\ub2c8\\ub2e4. "
            "\\uadf8\\ub798\\uc11c \\ube60\\ub974\\uac8c \\ubc30\\uc6b0\\uace0, \\uc798\\ubabb\\uc744 "
            "\\uc2f8\\uac8c \\uace0\\uce60 \\uc218 \\uc788\\uc2b5\\ub2c8\\ub2e4."
        ),
        "sec_what_p2": U(
            "AI\\uac00 \\uac10\\uc73c\\ub85c \\uc885\\ubaa9\\uc744 \\uace0\\ub974\\uc9c0 \\uc54a\\ub3c4\\ub85d, "
            "<strong>\\ubbf8\\ub9ac \\uc801\\uc5b4 \\ub454 \\uaddc\\uce59</strong>\\uacfc "
            "<strong>\\uc0ac\\ub78c\\uc774 \\ubcfc \\uc218 \\uc788\\ub294 \\ud754\\uc801(\\uae30\\ub85d)</strong>"
            "\\uc744 \\ud568\\uaed8 \\ub450\\uc5c8\\uc2b5\\ub2c8\\ub2e4."
        ),
        "sec_day_h2": U("\\ud558\\ub8e8\\ub294 \\uc138 \\ubc88 \\ud06c\\uac8c \\uc6c0\\uc9c1\\uc785\\ub2c8\\ub2e4"),
        "sec_day_intro": U(
            "\\uc7a5\\uc774 \\uc5f4\\ub9ac\\uba74 \\uc2dc\\uc2a4\\ud15c\\uc740 \\ud558\\ub8e8\\uc5d0 \\uc138 "
            "\\ubc88 \\ud070 \\uc21c\\uc744 \\uc27d\\uc2b5\\ub2c8\\ub2e4. \\uac01\\uac01 \\uc900\\ube44\\xb7"
            "\\uc2e4\\ud589\\xb7\\ub3cc\\uc544\\ubd04\\uc785\\ub2c8\\ub2e4."
        ),
        "badge_morning": chr(0x2600) + chr(0xFE0F),
        "m1_when": U("\\uc544\\uce68 \\xb7 \\uc7a5 \\uc2dc\\uc791 \\uc804\\ud6c4"),
        "m1_title": U(
            "\\uc624\\ub298\\uc758 \\uc7ac\\ub8cc\\ub97c \\uc900\\ube44\\ud574 \\ub461\\ub2c8\\ub2e4"
        ),
        "m1_body": U(
            "\\ucc28\\ud2b8\\uc5d0 \\ud544\\uc694\\ud55c \\uc22b\\uc790\\uc640 \\u2018\\uc0b4\\ud3b4\\ubcfc "
            "\\ub9cc\\ud55c \\uc885\\ubaa9 \\ubaa9\\ub85d\\u2019\\uc744 \\ubbf8\\ub9ac \\uac00\\uc838\\uc635\\ub2c8"
            "\\ub2e4. \\uc774 \\ub2e8\\uacc4\\uc5d0\\uc11c\\ub294 <strong>\\uc8fc\\ubb38\\uc744 \\ub123\\uc9c0 "
            "\\uc54a\\uc2b5\\ub2c8\\ub2e4</strong>. \\uc7a5\\uc744 \\uc5f4\\uae30 \\uc804 \\ubd80\\uc5f5\\uc744 "
            "\\uc815\\ub3c8\\ud558\\ub294 \\uc2dc\\uac04\\uc5d0 \\uac00\\uae4b\\uc2b5\\ub2c8\\ub2e4."
        ),
        "m1_pill": U(
            "\\uc544\\uc9c1 \\u2018\\uc694\\ub9ac(\\ub9e4\\ub9e4)\\u2019\\ub294 \\uc2dc\\uc791\\ud558\\uc9c0 "
            "\\uc54a\\uc2b5\\ub2c8\\ub2e4"
        ),
        "badge_day": chr(0x23F1) + chr(0xFE0F),
        "m2_when": U("\\uc7a5\\uc911 \\xb7 \\uc57d 15\\ubd84\\ub9c8\\ub2e4"),
        "m2_title": U("\\uaddc\\uce59\\uc5d0 \\ub9de\\uc73c\\uba74 \\ubaa8\\uc758 \\uc8fc\\ubb38\\ud569\\ub2c8\\ub2e4"),
        "m2_body": U(
            "\\uc815\\ud574\\uc9c4 \\uac04\\uaca9\\uc73c\\ub85c \\u2018\\uc9c0\\uae08 \\uc774 \\uc885\\ubaa9\\uc774 "
            "\\uc6b0\\ub9ac\\uac00 \\uc815\\ud55c \\uaddc\\uce59\\uc5d0 \\ub4e4\\uc5b4\\ub9de\\ub098\\u2019\\ub97c "
            "\\ubd05\\ub2c8\\ub2e4. \\ub9de\\uc73c\\uba74 \\ubaa8\\uc758\\ud22c\\uc790\\ub85c \\uc8fc\\ubb38\\ud558"
            "\\uace0, \\uc544\\ub2c8\\uba74 \\uadf8\\ub0c5 \\uc9c0\\ub098\\uac11\\ub2c8\\ub2e4. "
            "\\uadf8 \\uaddc\\uce59\\uc740 <strong>\\ud30c\\uc77c\\uc5d0 \\uc801\\ud78c \\uc124\\uc815</strong>"
            "\\uc774\\uace0, \\ub354 \\uc9c4\\uc9c0\\ud558\\uac8c \\uc4f0\\ub824\\uba74 \\uac80\\uc99d\\ub41c "
            "\\uc804\\ub7b5\\uc744 <strong>\\uce74\\ud0c8\\ub85c\\uadf8</strong>\\uc5d0 \\uc62c\\ub824 \\ub450"
            "\\uace0 \\uadf8 \\uc774\\ub984\\uc744 \\ub530\\ub974\\ub3c4\\ub85d \\ud560 \\uc218 \\uc788\\uc2b5"
            "\\ub2c8\\ub2e4."
        ),
        "m2_pill": U(
            "\\uc790\\ub3d9\\uc73c\\ub85c \\uc6c0\\uc9c1\\uc774\\ub294 \\uad6c\\uac04\\uc740 \\ub300\\ubd80\\ubd84 "
            "\\uc774 \\uc2dc\\uac04\\ub300\\uc785\\ub2c8\\ub2e4"
        ),
        "badge_eve": chr(0x1F4DD),
        "m3_when": U("\\uc7a5 \\ub9c8\\uac10 \\uc9c1\\ud6c4"),
        "m3_title": U("\\uc624\\ub298\\uc744 \\uc815\\ub9ac\\ud558\\uace0 \\ub0b4\\uc77c\\uc744 \\uc900\\ube44\\ud569\\ub2c8\\ub2e4"),
        "m3_body": U(
            "\\ubb34\\uc5c7\\uc774 \\uc77c\\uc5b4\\ub0ac\\ub294\\uc9c0, \\uc5b4\\ub514\\uac00 \\uc544\\uc27c"
            "\\uc6cc\\ub294\\uc9c0, \\ub0b4\\uc77c \\ubb34\\uc5c7\\uc744 \\uc870\\uc815\\ud560\\uc9c0\\ub97c "
            "\\ucc28\\ubd84\\ud788 \\ubd05\\ub2c8\\ub2e4. \\ud070 \\ubc29\\ud5a5 \\uc804\\ud658\\uc740 "
            "<strong>\\uc0ac\\ub78c\\uc774 \\ud655\\uc778</strong>\\ud558\\ub3c4\\ub85d \\ub450\\uc5c8\\uace0, "
            "\\uadf8 \\uacb0\\uacfc\\ub294 <strong>Notion \\uac19\\uc740 \\uc6b4\\uc601 \\uc77c\\uc9c0</strong>"
            "\\uc5d0 \\ub0a8\\ub3c4\\ub85d \\ud574 \\ub450\\uc5c8\\uc2b5\\ub2c8\\ub2e4."
        ),
        "m3_pill": U(
            "\\ubc30\\uc6c0\\uc744 \\uc218\\uc775\\ubcf4\\ub2e4 \\uba3c\\uc800 \\uae30\\ub85d\\ud569\\ub2c8\\ub2e4"
        ),
        "sec_roles_h2": U("\\uc5ed\\ud560\\uc744 \\ub098\\ub20c \\uc774\\uc720"),
        "role_builder_h": U("\\uc804\\ub7b5 \\uc124\\uacc4 \\ud654\\uba74"),
        "role_builder_p": U(
            "\\uc870\\uac74\\uc744 \\ub208\\uc73c\\ub85c \\uc815\\ub9ac\\ud558\\uace0, \\ud30c\\uc77c\\ub85c "
            "\\ub0b4\\ubcf4\\ub0bc \\uc218 \\uc788\\ub294 \\ub3c4\\uad6c\\uc785\\ub2c8\\ub2e4. \\ub808\\uc2dc\\ud53c"
            "\\ub97c \\uc801\\ub294 \\uba54\\ubaa8\\uc7a5\\uacfc \\ube44\\uc2b7\\ud569\\ub2c8\\ub2e4."
        ),
        "role_engine_h": U("\\uc790\\ub3d9 \\uc2e4\\ud589 \\uc2dc\\uac04\\ud45c"),
        "role_engine_p": U(
            "\\uc704\\uc5d0\\uc11c \\ub9d0\\ud55c <strong>\\uc138 \\ubc88\\uc758 \\uc21c\\uc11c</strong>\\ub97c "
            "\\uc2e4\\uc81c\\ub85c \\ub3cc\\ub294 \\ud504\\ub85c\\uadf8\\ub7a8\\uc785\\ub2c8\\ub2e4. "
            "\\uc54c\\ub78c\\uc774 \\uc6b8\\ub9ac\\uba74 \\uc815\\ud574\\uc9c4 \\uc77c\\uc744 \\ud569\\ub2c8\\ub2e4."
        ),
        "role_cards_h": U("\\uc804\\ub7b5 \\uce74\\ub4dc \\ubaa9\\ub85d(\\ub9c8\\ucf13\\ud50c\\ub808\\uc774\\uc2a4)"),
        "role_cards_p": U(
            "\\ubc31\\ud14c\\uc2a4\\ud2b8 \\ub4f1\\uc73c\\ub85c \\ud55c \\ubc88 \\uac70\\ub978 \\uc804\\ub7b5\\uc744 "
            "<strong>\\uc774\\ub984\\xb7\\uc124\\uba85\\xb7\\uc885\\ub958</strong>\\uac00 \\ubcf4\\uc774\\ub294 "
            "\\uce74\\ub4dc\\ucc98\\ub7fc \\ubaa8\\uc544 \\ub461\\ub2c8\\ub2e4. \\uc2dc\\uc7a5 \\ub274\\uc2a4\\ub9cc "
            "\\ubaa8\\uc544 \\ub450\\ub294 \\uce74\\ub4dc\\ub3c4 \\ub450\\uc744 \\uc218 \\uc788\\uc2b5\\ub2c8\\ub2e4."
        ),
        "role_claude_h": U("Claude Code\\uc640 \\uc870\\ud68c \\uc5f0\\uacb0(MCP)"),
        "role_claude_p": U(
            "\\ub300\\ud654\\ud558\\uba74\\uc11c \\uc2dc\\uc138\\ub97c \\ubcf4\\uac70\\ub098 \\ub3c4\\uad6c\\ub97c "
            "\\ubd80\\ub97c \\uc218 \\uc788\\uc2b5\\ub2c8\\ub2e4. \\uc774\\uac83\\uc740 \\uc7a5\\uc911 \\uc790\\ub3d9 "
            "\\uc8fc\\ubb38\\uacfc \\ub2e4\\ub978 \\uc120\\uc5d0 \\uc788\\uc2b5\\ub2c8\\ub2e4."
        ),
        "sec_recipe_h2": U(
            "\\uc65c \\u2018\\uac80\\uc99d\\ub41c \\ub808\\uc2dc\\ud53c\\u2019\\ub97c \\ub530\\ub974\\ub098\\uc694"
        ),
        "recipe_lead": U(
            "\\uc694\\ub9ac\\ubc95\\uc774 \\uc11c\\ub78d\\ub9c8\\ub2e4 \\ub2e4\\ub974\\uba74 \\ud63c\\ub780\\uc2a4"
            "\\ub7fd\\uc2b5\\ub2c8\\ub2e4"
        ),
        "recipe_p": U(
            "\\uc804\\ub7b5 \\ud30c\\uc77c\\uc774 \\uac1c\\uc778 \\ucef4\\ud4e8\\ud130\\uc5d0\\ub9cc \\uc788\\uc73c"
            "\\uba74 \\u2018\\uc9c0\\uae08 \\uc6b0\\ub9ac\\uac00 \\ub530\\ub974\\ub294 \\uaddc\\uce59\\uc774 "
            "\\ub9de\\ub098?\\u2019\\uac00 \\uc554\\ub9e4\\ud574\\uc9c1\\ub2c8\\ub2e4. \\uadf8\\ub798\\uc11c "
            "<strong>\\uac80\\uc99d\\uacfc \\ub4f1\\ub85d\\uc744 \\uac70\\uce5c \\uac83\\ub9cc</strong> "
            "\\ubaa9\\ub85d\\uc5d0 \\uc62c\\ub9ac\\uace0, \\uc7a5\\uc911\\uc5d0\\ub294 \\uadf8 \\uc911 \\ud558"
            "\\ub098\\ub97c \\uac00\\ub9ac\\ud0a4\\ub294 <strong>\\uc2e4\\ud589 \\uc124\\uc815</strong>\\ub9cc "
            "\\ub461\\ub2c8\\ub2e4. \\uc0c8 \\ub808\\uc2dc\\ud53c\\ub97c \\uc4f0\\ub824\\uba74 "
            "<strong>\\ud569\\uc758\\uacfc \\uac80\\uc99d</strong>\\uc744 \\uac70\\uce58\\uac8c \\ud574 "
            "\\ub450\\uc5c8\\uc2b5\\ub2c8\\ub2e4."
        ),
        "recipe_li1": U("\\uc124\\uacc4 \\ud654\\uba74\\uc5d0\\uc11c \\uc804\\ub7b5 \\ucd08\\uc548\\uc744 \\ub9cc\\ub4ed\\ub2c8\\ub2e4."),
        "recipe_li2": U(
            "\\uacfc\\uac70 \\ub370\\uc774\\ud130\\ub85c \\ud55c \\ubc88 \\uc131\\uc9c8\\uc744 \\ubd05\\ub2c8\\ub2e4"
            "(\\ubc31\\ud14c\\uc2a4\\ud2b8)."
        ),
        "recipe_li3": U(
            "\\uad1c\\ucc2e\\ub2e4\\uace0 \\ud310\\ub2e8\\ub418\\uba74 \\ubaa9\\ub85d\\uc5d0 \\uce74\\ub4dc\\ub85c "
            "\\uc62c\\ub9bd\\ub2c8\\ub2e4."
        ),
        "recipe_li4": U(
            "\\uc2e4\\uc81c \\uc790\\ub3d9 \\uc2e4\\ud589\\uc5d0 \\ub123\\uae30 \\uc804\\uc5d0 \\uc0ac\\ub78c\\uc774 "
            "\\ud655\\uc778\\ud558\\uace0 \\uc124\\uc815\\uc744 \\uace0\\uc815\\ud569\\ub2c8\\ub2e4."
        ),
        "sec_claude_h2": U("Claude Code\\ub294 \\uc790\\ub3d9 \\ud2b8\\ub808\\uc774\\ub354\\uc778\\uac00\\uc694?"),
        "sec_claude_p": U(
            "\\uc774 \\ud504\\ub85c\\uc81d\\ud2b8\\uc5d0\\uc11c <strong>Claude Code</strong>\\ub294 "
            "\\u2018\\ud63c\\uc790\\uc11c \\ub300\\uc2e0 \\ubc84\\ud2bc\\uc744 \\ub20c\\ub974\\ub294 "
            "\\uc874\\uc7ac\\u2019\\uac00 \\uc544\\ub2c8\\ub77c, <strong>\\uc124\\uacc4\\xb7\\ubd84\\uc11d\\xb7"
            "\\uae30\\ub85d\\uc744 \\ub3cc\\ub294 \\uc870\\uc218</strong>\\uc785\\ub2c8\\ub2e4."
        ),
        "split_auto_h": U("\\uc790\\ub3d9 \\uc2e4\\ud589(\\uc2dc\\uac04\\ud45c)"),
        "split_auto_p": U(
            "\\uc138 \\ubc88\\uc758 \\ub9ac\\ub4ec\\uc740 \\ubbf8\\ub9ac \\uc801\\ud78c \\ud504\\ub85c\\uadf8"
            "\\ub7a8\\uc774 \\uc9c0\\ud0b5\\ub2c8\\ub2e4. \\uc5ec\\uae30\\uac00 \\ubaa8\\uc758 \\ub9e4\\ub9e4\\uc758 "
            "\\uc804\\uc120\\uc785\\ub2c8\\ub2e4."
        ),
        "split_helper_h": U("Claude Code + MCP"),
        "split_helper_p": U(
            "\\uc870\\uc0ac\\ub098 \\uc870\\ud68c \\uac19\\uc740 \\uae30\\ub2a5\\uc744 \\ub3c4\\uad6c\\ub85c "
            "\\ubb36\\uc5b4, \\ud544\\uc694\\ud560 \\ub54c\\ub9cc \\ubd80\\ub985\\ub2c8\\ub2e4."
        ),
        "sec_mcp_p": U(
            "MCP\\ub294 \\uc774\\ub984\\uc774 \\uc0dd\\uc18c\\ud560 \\uc218 \\uc788\\uc2b5\\ub2c8\\ub2e4. "
            "<strong>AI\\uac00 \\uc678\\ubd80 \\uc2dc\\uc2a4\\ud15c\\uc744 \\uc548\\uc804\\ud558\\uac8c \\ubd80"
            "\\ub97c \\uc218 \\uc788\\uac8c \\ub9cc\\ub93c \\uc5f0\\uacb0 \\uaddc\\uaca9</strong>\\uc815\\ub3c4\\ub85c "
            "\\uc774\\ud574\\ud558\\uc2dc\\uba74 \\ucda9\\ubd84\\ud569\\ub2c8\\ub2e4."
        ),
        "sec_goal_h2": U("\\uac00\\uc7a5 \\uc911\\uc694\\ud55c \\uae30\\uc900 \\ud55c \\uac00\\uc9c0"),
        "sec_goal_lead": U(
            "<strong>\\uc218\\uc775\\uc774 \\ub098\\uae30 \\uc27c\\uc6b4 \\ubc29\\ud5a5</strong>\\uc744 \\uba3c"
            "\\uc800 \\ubd05\\ub2c8\\ub2e4."
        ),
        "sec_goal_p": U(
            "\\uc2b9\\ub960\\ub9cc \\ub192\\uc544\\ub3c4 \\ud55c \\ubc88 \\uc774\\uc775\\uc774 \\uc791\\uc73c\\uba74 "
            "\\uc758\\ubbf8\\uac00 \\uc904\\uc5b4\\ub4e0\\ub2e4\\uace0 \\ubcf4\\uace0, \\uc124\\uc815\\uc744 "
            "\\ubc14\\uafc0 \\ub54c\\ub3c4 \\uadf8 \\uae30\\uc900\\uc744 \\uae30\\uc5b5\\ud569\\ub2c8\\ub2e4."
        ),
        "aside_dev_h": U("\\uac1c\\ubc1c\\xb7\\uc6b4\\uc601 \\ub2f4\\ub2f9\\uc790\\uc5d0\\uac8c"),
        "aside_dev_p": U(
            "\\ud3f4\\ub354 \\uad6c\\uc870, \\ud30c\\uc77c \\uc774\\ub984, \\uc5ed\\ud560 \\ubd84\\ub9ac, \\ub85c"
            "\\uadf8 \\ud615\\uc2dd\\uc740 \\uc800\\uc7a5\\uc18c\\uc758 <strong>CLAUDE.md</strong>\\uc640 "
            "<strong>kis-strategy-skills</strong>\\ub97c \\ubcf4\\uc138\\uc694. \\uc774 HTML\\uc740 "
            "\\ub3d9\\ub8cc\\xb7\\uac00\\uc871\\uc5d0\\uac8c \\ubcf4\\uc5ec \\uc8fc\\uae30 \\uc704\\ud55c "
            "\\uc694\\uc57d\\uc785\\ub2c8\\ub2e4."
        ),
        "footer": U(
            "open-trading-api \\xb7 \\ub204\\uad6c\\ub098 \\uc77d\\ub294 \\uc694\\uc57d \\xb7 2026-04-16"
        ),
    }

    for _k, _v in data.items():
        try:
            _v.encode("utf-8")
        except UnicodeEncodeError as exc:
            bad = [hex(ord(c)) for c in _v if 0xD800 <= ord(c) <= 0xDFFF]
            raise RuntimeError(f"bad string {_k!r}: surrogates={bad} sample={_v[:120]!r}") from exc

    out = Path(__file__).resolve().parent / "explainer_content.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
